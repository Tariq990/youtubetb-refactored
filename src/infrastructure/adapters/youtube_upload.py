from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple
import json
import re
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
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    name = re.sub(r"[\x00-\x1F]", "", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s*-\s*", "-", name)
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

    # Ensure InkEcho is at the beginning (fixed brand tag)
    brand_tag = "InkEcho"
    if brand_tag not in tags:
        tags.insert(0, brand_tag)
    elif tags[0] != brand_tag:
        # Remove existing InkEcho and put it at the beginning
        tags = [tag for tag in tags if tag != brand_tag]
        tags.insert(0, brand_tag)

    # Add book title and author after InkEcho (required)
    book_title = meta.get("main_title", "").strip()
    author_name = meta.get("author_name", "").strip()
    
    # Remove existing instances to avoid duplicates (except InkEcho which is already handled)
    if book_title in tags and book_title != brand_tag:
        tags = [tag for tag in tags if tag != book_title]
    if author_name in tags and author_name != brand_tag:
        tags = [tag for tag in tags if tag != author_name]
    
    # Insert book title and author after InkEcho
    insert_pos = 1  # After InkEcho
    if book_title and book_title != brand_tag:
        tags.insert(insert_pos, book_title)
        insert_pos += 1
    if author_name and author_name != brand_tag:
        tags.insert(insert_pos, author_name)

    # Convert spaces to underscores in tags (YouTube requirement)
    tags = [tag.replace(' ', '_') for tag in tags]
    print(f"[upload] Converted spaces to underscores in {len(tags)} tags")

    # Remove tags longer than 30 characters (YouTube restriction)
    filtered_tags = [tag for tag in tags if len(tag) <= 30]
    removed_tags = [tag for tag in tags if len(tag) > 30]
    if removed_tags:
        print(f"[upload] Removed {len(removed_tags)} tags longer than 30 chars:")
        for tag in removed_tags:
            print(f"  - {tag} ({len(tag)} chars)")
    tags = filtered_tags

    # Clean tags: YouTube limits total to 500 chars
    def calc_total_chars(tag_list):
        if not tag_list:
            return 0
        return sum(len(tag) for tag in tag_list) + (len(tag_list) - 1)

    initial_total = calc_total_chars(tags)
    initial_count = len(tags)

    if initial_total > 500:
        print(f"⚠️  Tags total ({initial_total} chars) exceeds 500 limit")
        print(f"🔧 Removing longest tags one by one...")
        sorted_tags = sorted(tags, key=len, reverse=True)
        removed = []
        while calc_total_chars(sorted_tags) > 500 and sorted_tags:
            removed_tag = sorted_tags.pop(0)
            removed.append(removed_tag)
            current_total = calc_total_chars(sorted_tags)
            print(f"  ❌ Removed: {removed_tag} ({len(removed_tag)} chars) → Total now: {current_total}")
        tags = sorted_tags
        final_total = calc_total_chars(tags)
        print(f"✅ Final: {len(tags)} tags ({final_total} chars) - Removed {len(removed)} tags")
    else:
        print(f"✅ Tags OK: {initial_count} tags ({initial_total} chars / 500)")

    print(f"[upload] Final tags to be sent: {tags}")

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

    print("🔐 Authenticating with YouTube API...")
    try:
        service, MediaFileUpload = _get_service(client_secret, token_file, debug=debug)
        print("✓ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        if debug:
            print("[upload] failed to initialize Google API client:", e)
            print("[upload] ensure packages installed: google-api-python-client google-auth google-auth-oauthlib")
        return None

    print(f"📤 Uploading to YouTube (privacy: {privacy_status})...")
    print(f"📝 Title: {title[:60]}...")

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
            print(f"❌ Upload error (attempt {retry}/6): {str(e)[:100]}")
            if debug:
                print(f"[upload] chunk error (attempt {retry}):", e)
            if retry > 5:
                print("❌ Upload failed after 6 attempts")
                break
            sleep_s = min(60, 2 ** retry)
            print(f"⏳ Retrying in {sleep_s}s...")
            time.sleep(sleep_s)

    print("❌ Upload failed - no response received")
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
