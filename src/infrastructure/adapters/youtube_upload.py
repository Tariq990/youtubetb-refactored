from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple
import json
import re as regex_module  # Avoid name collision with RuntimeError in exception handlers
import time
import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore

from .database import update_book_youtube_url

# Lazy import Google API client to allow running other stages without this dependency
def _lazy_google():
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.http import MediaFileUpload  # type: ignore
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    return build, MediaFileUpload, InstalledAppFlow, Credentials


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def _sanitize_filename(name: str, max_len: int = 120) -> str:
    name = name.strip()
    name = regex_module.sub(r"[\\/:*?\"<>|]", "-", name)
    name = regex_module.sub(r"[\x00-\x1F]", "", name)
    name = regex_module.sub(r"\s+", " ", name)
    name = regex_module.sub(r"\s*-\s*", "-", name)
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "output"


def _find_video_from_title(run_dir: Path, youtube_title: str, strict_exact: bool = True) -> Optional[Path]:
    target = _sanitize_filename(youtube_title) + ".mp4"
    p = run_dir / target
    if p.exists():
        return p
    if not strict_exact:
        # Allow prefix match if strict mode is disabled
        for f in run_dir.glob("*.mp4"):
            if f.name.startswith(_sanitize_filename(youtube_title)):
                return f
    return None


def _find_thumbnail_file(run_dir: Path, debug: bool = False) -> Optional[Path]:
    """Return a reasonable thumbnail candidate in priority order.

    Priority:
    1) short_thumbnail.(jpg|jpeg|png) (for Shorts - vertical 9:16)
    2) thumbnail.(jpg|jpeg|png) (for main videos - horizontal 16:9)
    3) cover_processed.jpg (produced by render stage if local cover exists)
    4) bookcover.(jpg|jpeg|png)
    """
    candidates: Tuple[str, ...] = (
        "short_thumbnail.jpg",
        "short_thumbnail.jpeg",
        "short_thumbnail.png",
        "thumbnail.jpg",
        "thumbnail.jpeg",
        "thumbnail.png",
        "cover_processed.jpg",
        "bookcover.jpg",
        "bookcover.jpeg",
        "bookcover.png",
    )
    for name in candidates:
        p = run_dir / name
        if p.exists() and p.is_file():
            if debug:
                print(f"[upload] thumbnail candidate found: {p.name}")
            return p
    if debug:
        print("[upload] no thumbnail candidate found in run dir")
    return None


def _load_metadata(titles_json: Path) -> Optional[dict]:
    try:
        return json.loads(Path(titles_json).read_text(encoding="utf-8"))
    except Exception:
        return None


def _resolve_run_dir(run_dir: Path, debug: bool = False) -> Path:
    """Resolve runs/latest pointer by reading path.txt if present."""
    try:
        # If provided path exists, try to follow path.txt pointer
        if run_dir.exists() and run_dir.is_dir():
            path_file = run_dir / "path.txt"
            if path_file.exists():
                target = path_file.read_text(encoding="utf-8").strip()
                p = Path(target)
                if not p.is_absolute():
                    p = run_dir.parent / p
                if p.exists():
                    if debug:
                        print("[upload] resolved latest to:", p)
                    return p
                else:
                    if debug:
                        print("[upload] path.txt points to missing dir:", p)
            return run_dir
        # If path doesn't exist (e.g., runs/latest missing), pick newest under runs/
        root = run_dir.parent if run_dir.parent.name else Path("runs")
        if not root.exists():
            root = Path("runs")
        candidates = [p for p in root.glob("*/") if p.is_dir()]
        if candidates:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            if debug:
                print("[upload] fallback to newest run:", newest)
            return newest
    except Exception as e:
        if debug:
            print("[upload] failed to resolve run dir:", e)
    return run_dir


def _find_fallback_video(run_dir: Path, debug: bool = False) -> Optional[Path]:
    """
    Find video file using fallback priority order.

    Priority:
    1. short_final.mp4 (for shorts)
    2. video_snap.mp4 (render preview)
    3. Newest .mp4 file (last resort)

    Args:
        run_dir: Directory to search in
        debug: Print debug messages

    Returns:
        Path to video file or None if not found
    """
    candidates = [
        ("short_final.mp4", "Short video"),
        ("video_snap.mp4", "Video preview"),
    ]

    for filename, description in candidates:
        path = run_dir / filename
        if path.exists():
            print(f"✓ Found fallback: {filename} ({description})")
            return path

    # Last resort: newest MP4
    mp4s = sorted(run_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if mp4s:
        print(f"✓ Found fallback: {mp4s[0].name} (newest file)")
        if debug:
            print(f"[upload] Using newest MP4: {mp4s[0]}")
        return mp4s[0]

    return None


def _get_or_create_playlist(service, playlist_name: str, debug: bool = False) -> Optional[str]:
    """
    Get playlist ID by name, or create it if not exists.

    Args:
        service: YouTube API service object
        playlist_name: Name of the playlist (e.g., "Self-Development")
        debug: Print debug messages

    Returns:
        Playlist ID if found/created, None on error
    """
    try:
        # Search for existing playlist with this name
        request = service.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        response = request.execute()

        # Check if playlist already exists
        for item in response.get("items", []):
            if item["snippet"]["title"] == playlist_name:
                playlist_id = item["id"]
                if debug:
                    print(f"[playlist] Found existing: {playlist_name} (ID: {playlist_id})")
                return playlist_id

        # Playlist doesn't exist, create it
        if debug:
            print(f"[playlist] Creating new playlist: {playlist_name}")

        request = service.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": f"Book summaries and insights about {playlist_name}",
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
        )
        response = request.execute()
        playlist_id = response["id"]

        if debug:
            print(f"[playlist] ✅ Created: {playlist_name} (ID: {playlist_id})")

        return playlist_id

    except Exception as e:
        if debug:
            print(f"[playlist] Error getting/creating playlist: {e}")
        return None


def _add_video_to_playlist(service, video_id: str, playlist_id: str, debug: bool = False) -> bool:
    """
    Add video to a playlist.

    Args:
        service: YouTube API service object
        video_id: YouTube video ID
        playlist_id: YouTube playlist ID
        debug: Print debug messages

    Returns:
        True if successful, False otherwise
    """
    try:
        request = service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        )
        response = request.execute()

        if debug:
            print(f"[playlist] ✅ Video added to playlist (Item ID: {response.get('id')})")

        return True

    except Exception as e:
        if debug:
            print(f"[playlist] Error adding video to playlist: {e}")
        return False


def _get_service(client_secret: Path, token_file: Path, debug: bool = False):
    build, MediaFileUpload, InstalledAppFlow, Credentials = _lazy_google()
    creds = None
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception:
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request  # type: ignore
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            client_id = os.environ.get("YT_CLIENT_ID") or os.environ.get("YOUTUBE_CLIENT_ID")
            client_secret_env = os.environ.get("YT_CLIENT_SECRET") or os.environ.get("YOUTUBE_CLIENT_SECRET")
            redirect_uri = os.environ.get("YT_REDIRECT_URI")  # optional
            if client_id and client_secret_env:
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret_env,
                        "redirect_uris": [redirect_uri] if redirect_uri else [
                            "http://localhost",
                            "http://127.0.0.1",
                        ],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "project_id": "yt-upload-client",
                    }
                }
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)

            # Set manual redirect URI for console flow
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

            # Use manual authorization (no local server)
            try:
                auth_url, _ = flow.authorization_url(prompt='consent')
                print("\n" + "="*70)
                print("🔗 Please visit this URL to authorize:")
                print(auth_url)
                print("="*70)
                code = input("\n📝 Enter the authorization code from the browser: ").strip()
                flow.fetch_token(code=code)
                creds = flow.credentials
                print("✅ Authorization successful!\n")
            except Exception as e:
                if debug:
                    print("[upload] authentication failed:", e)
                raise
            try:
                token_file.write_text(creds.to_json(), encoding="utf-8")
            except Exception:
                pass
    service = build("youtube", "v3", credentials=creds)
    return service, MediaFileUpload


def upload_video(
    run_dir: Path,
    titles_json: Path,
    client_secret: Path,
    token_file: Path,
    privacy_status: str = "public",
    allow_fallbacks: bool = False,
    upload_thumbnail: bool = False,
    thumbnail_path: Optional[Path] = None,
    debug: bool = False,
) -> Optional[str]:
    meta = _load_metadata(titles_json)
    if not meta:
        if debug:
            print("[upload] titles_json missing or invalid:", titles_json)
        return None
    title = meta.get("youtube_title") or meta.get("main_title")
    description = meta.get("youtube_description") or ""

    tags: List[str] = meta.get("TAGS") or []

    # Defensive: ensure tags is a list of strings.
    # Some producers may write TAGS as a single comma-separated string; handle that.
    try:
        if isinstance(tags, str):
            s = tags.strip()
            # If it looks like a JSON array, try to parse it
            if s.startswith("[") and s.endswith("]"):
                try:
                    try:
                        import json as _json
                        parsed = _json.loads(s)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, (list, tuple)):
                        tags = [str(t).strip() for t in parsed if t is not None]
                    else:
                        tags = [s]
                except Exception:
                    # Fallback: split by comma
                    tags = [t.strip() for t in s.split(",") if t.strip()]
            else:
                tags = [t.strip() for t in s.split(",") if t.strip()]
        elif isinstance(tags, (set, tuple)):
            tags = [str(t).strip() for t in list(tags)]
        else:
            # Ensure all elements are strings and stripped
            tags = [str(t).strip() for t in tags if t is not None]
    except Exception:
        # Worst case, fallback to empty list
        tags = []

    # === FIXED TAGS (ALWAYS FIRST) ===
    brand_tag = "InkEcho"
    book_title = meta.get("main_title", "").strip()
    author_name = meta.get("author_name", "").strip()
    
    # Convert fixed tags to natural format (keep spaces)
    fixed_tags = []
    if brand_tag:
        fixed_tags.append(brand_tag)
    if book_title:
        fixed_tags.append(book_title)  # Keep spaces - more readable
    if author_name:
        if author_name not in fixed_tags:
            fixed_tags.append(author_name)  # Keep spaces - more readable
    
    print(f"[upload] Fixed tags (always first): {fixed_tags}")
    
    # === PROCESS EXISTING TAGS ===
    # Remove duplicates of fixed tags from the dynamic tags (case-insensitive)
    fixed_tags_lower = {ft.lower() for ft in fixed_tags}
    tags = [tag for tag in tags if tag.lower() not in fixed_tags_lower]
    
    # Keep tags as-is (YouTube accepts spaces in tags)
    print(f"[upload] Processing {len(tags)} dynamic tags (keeping original format)")
    
    # === SANITIZE TAGS ===
    # YouTube API requirements (official):
    # - Max 500 chars TOTAL (only tag text, commas don't count)
    # - Tags with spaces count as wrapped in quotes: "Foo Bar" = 9 chars (7 + 2 quotes)
    # - Allowed chars: Letters, numbers, spaces ONLY
    # - NO special chars (-, _, commas, etc)
    # Reference: https://developers.google.com/youtube/v3/docs/videos#snippet.tags[]
    def _sanitize_tag_for_api(t: str) -> Optional[str]:
        if not t:
            return None
        try:
            s = str(t)
        except Exception:
            return None
        # Remove control characters and normalize whitespace
        s = regex_module.sub(r"[\x00-\x1F\x7F]+", "", s)
        s = s.replace('"', '').replace("'", '')
        s = s.replace('\n', ' ').replace('\r', ' ')
        # Replace underscores with spaces (more natural tags)
        s = s.replace('_', ' ')
        # Replace hyphens with spaces (YouTube doesn't allow hyphens in tags)
        s = s.replace('-', ' ')
        # Remove commas (commas separate tags in some systems)
        s = s.replace(',', ' ')
        # Keep only alphanumeric and spaces (NO special chars allowed by YouTube)
        s = regex_module.sub(r"[^A-Za-z0-9\s]", "", s)
        s = regex_module.sub(r"\s+", ' ', s).strip()
        # NOTE: No 30-char truncation! YouTube API docs don't specify per-tag limit.
        # Only 500-char total limit applies.
        return s if s else None

    # Apply sanitization to dynamic tags list
    sanitized = []
    for t in tags:
        st = _sanitize_tag_for_api(t)
        if st:
            sanitized.append(st)
    tags = sanitized

    # === REMOVE SPAM/MISLEADING TAGS (YouTube Policy) ===
    # Only block clear spam patterns (subscribe/click/like) per YouTube spam policy
    # Reference: https://support.google.com/youtube/answer/2801973 (spam/deceptive practices)
    BLOCKED_PATTERNS = {
        "subscribe", "link", "playlist", "watch", "channel", "bell", 
        "notification", "unsubscribe", "click here", "like", "comment",
        "full audiobook", "full_audiobook"
        # NOTE: Removed overly restrictive blocks like "trending", "viral", "bestseller"
        # These are NOT in YouTube's official spam policy and CAN be used as tags
    }
    
    # Filter spam tags (keep promotional/descriptive tags like "bestseller", "trending")
    cleaned_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        
        # Skip if it's a spam pattern (subscribe/click/etc)
        if any(blocked in tag_lower for blocked in BLOCKED_PATTERNS):
            print(f"[upload]   ❌ Spam pattern blocked: {tag}")
            continue
        
        # NOTE: No arbitrary 30-char limit! YouTube API only enforces 500 char total.
        # Let YouTube validate tag length itself during upload.
        
        cleaned_tags.append(tag)
    
    tags = cleaned_tags
    print(f"[upload] After spam filtering: {len(tags)} tags remain")
    
    # === REMOVE DUPLICATES (case-insensitive) ===
    seen = {ft.lower() for ft in fixed_tags}  # Start with fixed tags
    unique_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)
    tags = unique_tags
    print(f"[upload] After dedup: {len(tags)} unique tags")
    
    # === CALCULATE CHARACTER LIMIT ===
    def calc_total_chars(tag_list):
        """
        Calculate total characters for YouTube tags.
        NOTE: YouTube API counts ONLY tag characters, NOT commas!
        Each tag is separate, commas are added by YouTube UI for display only.
        """
        if not tag_list:
            return 0
        return sum(len(tag) for tag in tag_list)  # No comma counting!
    
    # === BUILD FINAL TAG LIST ===
    final_tags = fixed_tags.copy()
    
    # === CRITICAL SEO TAGS (ALWAYS ADD - HIGH PRIORITY) ===
    # These tags have proven high search volume and relevance
    critical_seo_tags = [
        "audiobook",
        "book summary",
        "self improvement",
        "productivity",
        "personal development",
        "motivational",
        "educational",
        "book review",
        "self help"
    ]
    
    # Add critical SEO tags (avoid duplicates - case insensitive)
    added_seo = 0
    for tag in critical_seo_tags:
        if not any(t.lower() == tag.lower() for t in final_tags):
            final_tags.append(tag)
            added_seo += 1
    
    print(f"[upload] Added {added_seo}/{len(critical_seo_tags)} critical SEO tags (skipped duplicates)")
    
    reserved_chars = calc_total_chars(final_tags)
    available_chars = 500 - reserved_chars
    
    print(f"[upload] Reserved chars (fixed + SEO): {reserved_chars}")
    print(f"[upload] Available space for dynamic tags: {available_chars} chars")
    
    # === FILL REMAINING SPACE WITH DYNAMIC TAGS (SMART PRIORITIZATION) ===
    # Sort tags by SEO value (shorter = better, common keywords = higher priority)
    def tag_priority_score(tag: str) -> int:
        """
        Calculate priority score for a tag (HIGHER is better).
        Prioritizes:
        1. Short tags (more space for other tags)
        2. Common SEO keywords
        3. Book-related terms
        """
        score = 0
        tag_lower = tag.lower()
        
        # Bonus for short tags (more efficient use of space)
        if len(tag) <= 10:
            score += 30
        elif len(tag) <= 15:
            score += 20
        elif len(tag) <= 20:
            score += 10
        
        # Bonus for high-value SEO keywords
        high_value_keywords = {
            "success": 25, "mindset": 25, "habits": 25, "growth": 25,
            "wealth": 20, "leadership": 20, "communication": 20,
            "psychology": 20, "philosophy": 20, "business": 20,
            "finance": 20, "money": 20, "investing": 20,
            "health": 15, "fitness": 15, "meditation": 15,
            "creativity": 15, "writing": 15, "reading": 15,
            "learning": 15, "memory": 15, "focus": 15,
            "time management": 15, "goal setting": 15
        }
        
        for keyword, bonus in high_value_keywords.items():
            if keyword in tag_lower:
                score += bonus
                break  # Only one bonus per tag
        
        # Penalty for very generic tags
        generic_words = ["tips", "guide", "intro", "basics", "overview"]
        if any(word in tag_lower for word in generic_words):
            score -= 10
        
        return score
    
    # Sort dynamic tags by priority (highest first)
    tags_with_scores = [(tag, tag_priority_score(tag)) for tag in tags]
    tags_sorted = sorted(tags_with_scores, key=lambda x: x[1], reverse=True)
    tags = [tag for tag, score in tags_sorted]
    
    if debug and tags[:5]:
        print(f"[upload] Top 5 priority tags: {[(t, tag_priority_score(t)) for t in tags[:5]]}")
    
    # CRITICAL: YouTube has UNDOCUMENTED limit of ~30 tags maximum!
    # Even if total chars ≤500, API rejects if tag count >30-35
    # This was discovered through production testing (46 tags = rejected)
    MAX_TOTAL_TAGS = 30  # Safe limit based on real-world testing
    
    added_count = 0
    for tag in tags:
        # Check BOTH character limit AND tag count limit
        test_total = calc_total_chars(final_tags + [tag])
        
        if test_total <= 500 and len(final_tags) < MAX_TOTAL_TAGS:
            final_tags.append(tag)
            added_count += 1
        elif len(final_tags) >= MAX_TOTAL_TAGS:
            # Hit tag count limit
            print(f"[upload] ⚠️  Reached YouTube's tag count limit ({MAX_TOTAL_TAGS} tags)")
            break
        else:
            # Hit character limit
            remaining_space = 500 - calc_total_chars(final_tags)
            if remaining_space < 3:  # Less than 3 chars left, stop trying
                break
            # Try to fit short tags in remaining space
            if len(tag) <= remaining_space and len(final_tags) < MAX_TOTAL_TAGS:
                final_tags.append(tag)
                added_count += 1
    
    final_total = calc_total_chars(final_tags)
    efficiency = (final_total / 500) * 100

    # Final validation: YouTube only allows letters, numbers, and spaces
    # NO hyphens, underscores, or special characters allowed!
    # NOTE: Removed arbitrary 30-char limit per tag - YouTube API docs don't specify this!
    # Only the 500-char total limit is documented.
    allowed_re = regex_module.compile(r"^[A-Za-z0-9 ]+$")  # Any length, only alphanumeric + spaces
    validated = []
    dropped = []
    for t in final_tags:
        if allowed_re.match(t):
            validated.append(t)
        else:
            dropped.append(t)

    if dropped:
        print(f"[upload] Dropped {len(dropped)} invalid tags (special chars): {dropped}")

    final_tags = validated

    final_total = calc_total_chars(final_tags)
    efficiency = (final_total / 500) * 100 if final_total else 0

    print(f"\n{'='*60}")
    print(f"📊 TAG STATISTICS (YouTube API Limits Applied)")
    print(f"{'='*60}")
    print(f"✅ Total tags: {len(final_tags)}")
    print(f"   • Fixed tags: {len(fixed_tags)} (InkEcho + Book + Author)")
    print(f"   • SEO tags: 9 (critical keywords)")
    print(f"   • Dynamic tags: {added_count} (AI-generated + prioritized)")
    print(f"✅ Character usage: {final_total} / 500 ({efficiency:.1f}% efficient)")
    print(f"✅ Remaining space: {500 - final_total} chars")
    print(f"\n📋 FINAL TAG LIST:")
    print(f"   Fixed: {', '.join(final_tags[:len(fixed_tags)])}")
    if len(final_tags) > len(fixed_tags):
        dynamic_preview = final_tags[len(fixed_tags):len(fixed_tags)+15]
        remaining = len(final_tags) - len(fixed_tags) - len(dynamic_preview)
        if remaining > 0:
            print(f"   Dynamic: {', '.join(dynamic_preview)}... (+{remaining} more)")
        else:
            print(f"   Dynamic: {', '.join(dynamic_preview)}")
    print(f"\n⚠️  Note: No arbitrary tag count limit! Only 500-char total per YouTube API.")
    print(f"{'='*60}\n")

    # === FINAL DUPLICATE CHECK (SAFETY NET) ===
    # Remove any remaining duplicates (case-insensitive)
    seen_final = set()
    deduped_tags = []
    duplicates_found = []
    
    for tag in final_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen_final:
            seen_final.add(tag_lower)
            deduped_tags.append(tag)
        else:
            duplicates_found.append(tag)
    
    if duplicates_found:
        print(f"⚠️  REMOVED {len(duplicates_found)} DUPLICATE TAGS: {duplicates_found}")
        final_tags = deduped_tags
        print(f"✅ Final tag count after dedup: {len(final_tags)}\n")

    # Use final tags
    tags = final_tags

    if not title:
        if debug:
            print("[upload] youtube_title/main_title missing in:", titles_json)
        return None

    # Check if this is a Short upload with explicit filename
    is_short = meta.get("is_short", False)
    explicit_filename = meta.get("video_filename")

    if is_short and explicit_filename:
        print(f"🎬 Short video mode: using {explicit_filename}")
        video_path = run_dir / explicit_filename
        if not video_path.exists():
            print(f"❌ Short video file not found: {explicit_filename}")
            available = [f.name for f in run_dir.glob("*.mp4")]
            print(f"📋 Available files: {', '.join(available[:5])}")
            return None
    else:
        # Normal video upload - search by title
        expected_name = _sanitize_filename(title) + ".mp4"
        print(f"🔍 Searching for video file: {expected_name}")

        video_path = _find_video_from_title(run_dir, title, strict_exact=not allow_fallbacks)

        if not video_path and allow_fallbacks:
            print("⚠️ Titled video not found, trying fallbacks...")
            video_path = _find_fallback_video(run_dir, debug=debug)

    if not video_path or not video_path.exists():
        print("❌ upload failed")
        if debug:
            if is_short:
                print(f"[upload] Short video not found: {explicit_filename}")
            else:
                expected_name = _sanitize_filename(title) + ".mp4"
                print("[upload] expected titled video not found:", expected_name)
            print("[upload] in directory:", run_dir)
            available = [f.name for f in run_dir.glob("*.mp4")]
            print("[upload] available .mp4 files:", available)
            if allow_fallbacks:
                print("[upload] fallback search order: short_final.mp4 → video_snap.mp4 → newest .mp4")
            else:
                print("[upload] hint: run merge stage to create titled video, or use --allow-fallbacks.")
        else:
            # Print minimal error info even without debug mode
            available = [f.name for f in run_dir.glob("*.mp4")]
            if available:
                if not is_short:
                    expected_name = _sanitize_filename(title) + ".mp4"
                    print(f"📂 Expected: {expected_name}")
                print(f"📋 Available files: {', '.join(available[:5])}")
            else:
                print(f"📂 No .mp4 files found in: {run_dir.name}")
        return None

    print(f"✅ Using video file: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.2f} MB)")

    if debug:
        print(f"[upload] full path: {video_path}")

    # Determine secrets directory from client_secret parameter (fallback to 'secrets')
    try:
        secrets_dir_path = Path(client_secret).parent if client_secret else Path("secrets")
    except Exception:
        secrets_dir_path = Path("secrets")

    # Build list of OAuth client candidates: primary client_secret plus any in secrets/oauth_clients/
    client_candidates_list = []
    # Primary candidate passed into function
    if client_secret:
        client_candidates_list.append(Path(client_secret))
    # Additional candidates directory
    oauth_clients_dir = secrets_dir_path / "oauth_clients"
    try:
        if oauth_clients_dir.exists() and oauth_clients_dir.is_dir():
            for p in sorted(oauth_clients_dir.glob("*.json")):
                if p not in client_candidates_list:
                    client_candidates_list.append(p)
    except Exception:
        pass

    if debug:
        print(f"[upload] OAuth client candidates: {[str(p) for p in client_candidates_list]}")

    # Prepare the request body (same across client attempts)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Try each OAuth client until upload succeeds or all fail
    for client_idx, client_file in enumerate(client_candidates_list, start=1):
        token_candidate = secrets_dir_path / f"token_{client_file.stem}.json"
        print(f"🔐 Attempting authentication with OAuth client {client_idx}/{len(client_candidates_list)}: {client_file.name}")
        try:
            service, MediaFileUpload = _get_service(client_file, token_candidate, debug=debug)
            print("✓ Authentication successful")
        except Exception as e:
            print(f"❌ Authentication failed for {client_file.name}: {e}")
            if debug:
                print("[upload] ensure packages installed: google-api-python-client google-auth google-auth-oauthlib")
            # Try next client
            continue

        print(f"📤 Uploading to YouTube (privacy: {privacy_status}) using client {client_file.name}...")
        print(f"📝 Title: {title[:60]}...")

        try:
            media = MediaFileUpload(str(video_path), chunksize=10 * 1024 * 1024, resumable=True)
            request = service.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

            response = None
            error = None
            retry = 0
            last_progress = -1

            while response is None:
                try:
                    status, response = request.next_chunk()

                    # Show upload progress
                    if status:
                        progress = int(status.progress() * 100)
                        if progress != last_progress and progress % 10 == 0:  # Every 10%
                            print(f"⏳ Upload progress: {progress}%")
                            last_progress = progress

                    if response is not None:
                        if "id" in response:
                            video_id = response["id"]
                            print(f"✅ Video uploaded successfully!")
                            print(f"🆔 Video ID: {video_id}")

                            # Optional thumbnail upload
                            if upload_thumbnail:
                                try:
                                    thumb = thumbnail_path if thumbnail_path else _find_thumbnail_file(run_dir, debug=debug)
                                    if thumb is not None:
                                        print(f"📸 Uploading custom thumbnail: {thumb.name}")
                                        thumb_media = MediaFileUpload(str(thumb))
                                        t_req = service.thumbnails().set(videoId=video_id, media_body=thumb_media)
                                        t_resp = t_req.execute()
                                        print(f"✅ Thumbnail uploaded successfully!")
                                        if debug:
                                            print("[upload] thumbnail set response keys:", list(t_resp.keys()) if isinstance(t_resp, dict) else type(t_resp))
                                    else:
                                        print("⚠️ No thumbnail file found to upload")
                                        if debug:
                                            print("[upload] skip thumbnail: no candidate file found")
                                except Exception as te:
                                    print(f"❌ Thumbnail upload failed: {te}")
                                    if debug:
                                        print("[upload] thumbnail upload failed:", te)

                            # Update database with YouTube URL
                            try:
                                from .database import update_youtube_url, update_book_short_url
                                import json

                                # Read book metadata from titles_json
                                titles_data = json.loads(Path(titles_json).read_text(encoding="utf-8"))
                                book_name = titles_data.get("main_title")
                                author_name = titles_data.get("author_name")
                                playlist_name = titles_data.get("playlist")

                                if book_name:
                                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                                    # Use different function based on video type
                                    if is_short:
                                        update_book_short_url(book_name, youtube_url)
                                    else:
                                        update_book_youtube_url(book_name, youtube_url)

                                # Add to YouTube playlist if playlist name exists (ONLY for main videos, NOT shorts)
                                if playlist_name and not is_short:
                                    try:
                                        if debug:
                                            print(f"[upload] Adding video to playlist: {playlist_name}")
                                        playlist_id = _get_or_create_playlist(service, playlist_name, debug=debug)
                                        if playlist_id:
                                            _add_video_to_playlist(service, video_id, playlist_id, debug=debug)
                                            if debug:
                                                print(f"[upload] ✅ Video added to playlist: {playlist_name}")
                                    except Exception as pl_err:
                                        if debug:
                                            print(f"[upload] playlist error: {pl_err}")
                            except Exception as db_err:
                                if debug:
                                    print(f"[upload] database update failed: {db_err}")

                            return video_id
                        print("⚠️ Upload completed but no video ID in response")
                        return None
                except Exception as e:
                    error = e
                    retry += 1
                    
                    # Enhanced error logging for keyword/tag issues
                    error_str = str(e)
                    print(f"\n{'='*60}")
                    print(f"❌ UPLOAD ERROR (Attempt {retry}/6)")
                    print(f"{'='*60}")
                    print(f"Error Type: {type(e).__name__}")
                    print(f"Error Message: {error_str}")
                    
                    # Special handling for keyword/tag errors
                    if "keyword" in error_str.lower() or "tag" in error_str.lower():
                        print(f"\n⚠️  TAG/KEYWORD ERROR DETECTED!")
                        print(f"\n📋 Tags that were sent to YouTube API:")
                        print(f"   Count: {len(tags)}")
                        print(f"   Tags: {tags}")
                        print(f"\n🔍 Checking each tag:")
                        for i, tag in enumerate(tags, 1):
                            tag_len = len(tag)
                            has_special = any(c for c in tag if not (c.isalnum() or c.isspace()))
                            print(f"   {i}. '{tag}' (len={tag_len}, special_chars={has_special})")
                            if tag_len > 30:
                                print(f"      ⚠️  TOO LONG! (max 30 chars)")
                            if has_special:
                                special_chars = [c for c in tag if not (c.isalnum() or c.isspace())]
                                print(f"      ⚠️  HAS SPECIAL CHARS: {special_chars}")
                        print(f"\n📊 API Request Body snippet:")
                        print(f"   'tags': {tags[:10]}..." if len(tags) > 10 else f"   'tags': {tags}")
                    
                    if debug:
                        print(f"\n[upload] Full exception details:")
                        import traceback
                        traceback.print_exc()
                    
                    print(f"{'='*60}\n")
                    # Detect quota errors in error message and try next OAuth client
                    error_str_l = error_str.lower()
                    if "quotaexceeded" in error_str_l or "quota exceeded" in error_str_l or "exceeded your current quota" in error_str_l:
                        print(f"\n⚠️  Detected YouTube quota exceeded for client {client_file.name} - trying next OAuth client if available")
                        # break out of inner upload loop and try next client
                        break

                    if retry > 5:
                        print("❌ Upload failed after 6 attempts for this client")
                        break
                    sleep_s = min(60, 2 ** retry)
                    print(f"⏳ Retrying in {sleep_s}s...")
                    time.sleep(sleep_s)
        except RuntimeError as re:
            # quotaExceeded surfaced outside inner loop, try next client
            if "quotaExceeded" in str(re) or "quota exceeded" in str(re).lower():
                print(f"⚠️ quotaExceeded from client {client_file.name}: {re} -- trying next client")
                continue
            else:
                raise
        except Exception as outer_e:
            print(f"❌ Upload attempt failed for client {client_file.name}: {outer_e}")
            if debug:
                import traceback
                traceback.print_exc()
            # Try next client
            continue

    # If we exit loop, all clients failed
    print("❌ Upload failed - all OAuth clients exhausted or no suitable client available")
    return None


def main(
    run_dir: Path,
    titles_json: Path,
    secrets_dir: Path = Path("secrets"),
    privacy_status: str = "public",
    allow_fallbacks: bool = False,
    upload_thumbnail: bool = False,
    thumbnail_path: Optional[Path] = None,
    playlist_name: Optional[str] = None,
    is_short: bool = False,  # NEW: Flag to indicate if this is a short video
    debug: bool = False,
) -> Optional[str]:
    # Load environment from secrets/.env if available (for standalone runs)
    try:
        if load_dotenv is not None:
            env_path = Path(secrets_dir) / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=str(env_path))
    except Exception:
        pass
    # Resolve latest pointer and recompute titles_json after resolution
    run_dir = _resolve_run_dir(run_dir, debug=debug)
    if not titles_json.exists() or str(titles_json).endswith("runs/latest/output.titles.json"):
        titles_json = run_dir / "output.titles.json"
    if debug:
        print("[upload] run_dir:", run_dir)
        print("[upload] titles_json exists:", titles_json.exists())
    # Discover client secret and token paths
    client_candidates = [
        secrets_dir / "client_secret.json",
        secrets_dir / "oauth_client.json",
        secrets_dir / "youtube_client_secret.json",
    ]
    client_secret = next((p for p in client_candidates if p.exists()), None)
    if debug:
        print("[upload] secrets_dir:", secrets_dir)
        print("[upload] client_secret.json found:", bool(client_secret))
    if client_secret is None:
        # If no file, we can still try env-based flow; pass a dummy path
        client_secret = secrets_dir / "client_secret.json"
    token_file = secrets_dir / "token.json"

    # Override playlist name if provided
    if playlist_name:
        try:
            import json
            meta = json.loads(titles_json.read_text(encoding="utf-8"))
            meta["playlist"] = playlist_name
            titles_json.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            if debug:
                print(f"[upload] Playlist name set to: {playlist_name}")
        except Exception as e:
            if debug:
                print(f"[upload] Failed to set playlist name: {e}")

    return upload_video(
        run_dir,
        titles_json,
        client_secret,
        token_file,
        privacy_status=privacy_status,
        allow_fallbacks=allow_fallbacks,
        upload_thumbnail=upload_thumbnail,
        thumbnail_path=thumbnail_path,
        debug=debug,
    )


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Upload merged video to YouTube using metadata from output.titles.json")
    p.add_argument("--run", dest="run_dir", default="runs/latest", help="Run directory")
    p.add_argument("--privacy", dest="privacy_status", default="public", choices=["private", "unlisted", "public"], help="Video privacy status")
    p.add_argument("--secrets", dest="secrets_dir", default="secrets", help="Directory containing OAuth client_secret.json and token.json")
    p.add_argument("--allow-fallbacks", action="store_true", help="Permit fallback to video_snap.mp4 or newest .mp4 if titled video is missing")
    p.add_argument("--thumbnail", action="store_true", help="Attempt to upload a custom thumbnail (looks for thumbnail.jpg/png, cover_processed.jpg, or bookcover.* in run dir)")
    p.add_argument("--thumbnail-path", dest="thumbnail_path", default=None, help="Explicit path to thumbnail image to upload")
    p.add_argument("--playlist", dest="playlist_name", default=None, help="YouTube playlist name to add video to (creates if doesn't exist). Default: 'Book Summaries' from metadata")
    p.add_argument("--debug", action="store_true", help="Print debug details for troubleshooting")
    args = p.parse_args()

    thumb_path = Path(args.thumbnail_path) if args.thumbnail_path else None
    vid = main(
        Path(args.run_dir),
        Path(args.run_dir) / "output.titles.json",
        Path(args.secrets_dir),
        args.privacy_status,
        allow_fallbacks=bool(args.allow_fallbacks),
        upload_thumbnail=bool(args.thumbnail),
        thumbnail_path=thumb_path,
        playlist_name=args.playlist_name,
        debug=bool(args.debug),
    )
    print(vid if vid else "upload failed")
