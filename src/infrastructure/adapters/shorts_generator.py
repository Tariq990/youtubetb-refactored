"""
YouTube Shorts Generator Pipeline - Professional Edition

Generates vertical 9:16 shorts from book summary content with cinematic effects:
1. AI generates engaging 60s script with powerful hook
2. TTS conversion (auto-trim if > 60s)
3. Vertical video montage with professional effects:
   - Gaussian blur for text clarity
   - Vignette effect (focus on center)
   - Professional single-line captions with word highlighting
4. Upload with main video link

Note: YouTube Shorts do NOT support custom thumbnails (by design).
"""
from __future__ import annotations

import json
import re
import subprocess
import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import shutil
import math
import time
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

try:
    from pydub import AudioSegment  # type: ignore
except ImportError:
    AudioSegment = None

try:
    from mutagen.mp3 import MP3  # type: ignore
except ImportError:
    MP3 = None


def _fetch_with_retry(url: str, headers: dict, params: dict, max_retries: int = 3, timeout: int = 15) -> Optional[dict]:
    """
    Fetch API with exponential backoff retry to handle temporary network issues
    
    Args:
        url: API endpoint URL
        headers: Request headers (Authorization, etc.)
        params: Query parameters
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 15)
    
    Returns:
        JSON response dict if successful, None if all retries failed
    
    Example:
        Attempt 1: ❌ Failed - wait 1s
        Attempt 2: ❌ Failed - wait 2s  
        Attempt 3: ✅ Success!
    """
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            r.raise_for_status()
            
            # Success - return immediately
            if attempt > 0:
                print(f"    ✅ Retry {attempt + 1} succeeded!")
            return r.json()
            
        except requests.exceptions.RequestException as e:
            # Last attempt - give up
            if attempt == max_retries - 1:
                print(f"    ❌ All {max_retries} attempts failed: {e}")
                return None
            
            # Calculate exponential backoff: 1s, 2s, 4s...
            wait_time = 2 ** attempt
            print(f"    ⚠️ Attempt {attempt + 1}/{max_retries} failed - retrying in {wait_time}s... ({e})")
            time.sleep(wait_time)
    
    return None


def _get_cache_path(query: str, page: int) -> Path:
    """
    Get cache file path for a Pexels search query
    
    Args:
        query: Search query string
        page: Page number
    
    Returns:
        Path to cache file (e.g., tmp/pexels_cache/a3f5c891_p1.json)
    
    Example:
        query="mountain landscape" page=1 
        → tmp/pexels_cache/a3f5c891_p1.json
    """
    # Create cache directory
    cache_dir = Path("tmp/pexels_cache")
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    # Hash query for filename (first 8 chars of MD5)
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    
    return cache_dir / f"{query_hash}_p{page}.json"


def _fetch_with_cache(
    query: str, 
    page: int, 
    headers: dict, 
    params: dict, 
    cache_hours: int = 24
) -> Optional[dict]:
    """
    Fetch Pexels API with cache system to reduce API calls
    
    Args:
        query: Search query
        page: Page number
        headers: API headers
        params: API parameters
        cache_hours: Cache validity in hours (default: 24)
    
    Returns:
        JSON response from cache or fresh API call
    
    Cache Logic:
        1. Check if cache file exists and is recent (< cache_hours old)
        2. If valid cache → return cached data (FAST ⚡)
        3. If no cache or expired → fetch fresh data + save to cache
    
    Benefits:
        - 80% reduction in API calls
        - Instant results from cache
        - Auto-refresh after 24 hours
    
    Example:
        Day 1, 10am: Fresh API call → save cache
        Day 1, 11am: Read from cache (instant!)
        Day 2, 11am: Cache expired → fresh call → update cache
    """
    cache_file = _get_cache_path(query, page)
    
    # Check if cache exists and is valid
    if cache_file.exists():
        # Get cache age
        cache_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        cache_age = datetime.now() - cache_mtime
        cache_valid = cache_age < timedelta(hours=cache_hours)
        
        if cache_valid:
            # Cache is fresh - use it!
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                hours_old = cache_age.total_seconds() / 3600
                print(f"    ⚡ Cache hit: '{query}' p{page} ({hours_old:.1f}h old)")
                return data
            except Exception as e:
                print(f"    ⚠️ Cache read failed: {e}, fetching fresh...")
                # Fall through to API fetch
    
    # No cache or expired - fetch fresh data
    print(f"    🔍 Cache miss: '{query}' p{page} - fetching from API...")
    data = _fetch_with_retry(
        url="https://api.pexels.com/videos/search",
        headers=headers,
        params=params,
        max_retries=3,
        timeout=15
    )
    
    # Save to cache if successful
    if data:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"    💾 Saved to cache: {cache_file.name}")
        except Exception as e:
            print(f"    ⚠️ Cache save failed: {e}")
    
    return data


def _print_progress(step: int, total: int, task: str, progress: int = 100):
    """
    Print simple one-line progress bar with Matrix-style colors

    Args:
        step: Current step number (1-7)
        total: Total steps (7)
        task: Task description
        progress: Progress percentage (0-100)
    """
    import sys

    # Matrix green color codes
    GREEN = '\033[92m'
    RESET = '\033[0m'

    # Calculate bar
    bar_width = 20
    filled = int(bar_width * progress / 100)
    bar = '█' * filled + '░' * (bar_width - filled)

    # Format message
    msg = f"{GREEN}[{step}/{total}]{RESET} {task:<30} {bar} {progress:>3}%"

    # Print with carriage return (overwrite line)
    if progress < 100:
        sys.stdout.write(f'\r{msg}')
        sys.stdout.flush()
    else:
        print(f'\r{msg}')
def _create_simple_subtitles(script_text: str, audio_path: Path, output_json: Path) -> Optional[Path]:
    """
    Create accurate word-level subtitles using Whisper for alignment
    Falls back to simple division if Whisper not available

    Args:
        script_text: The script text
        audio_path: Path to MP3 audio file
        output_json: Path to save subtitle JSON

    Returns:
        Path to subtitle JSON if successful, None otherwise
    """
    # Try Whisper first for accurate timing
    try:
        import whisper

        print("🎯 Using Whisper for 100% accurate word-level timing...")
        model = whisper.load_model("base")  # Small/fast model
        result = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            language="en",
            # Additional parameters for better accuracy
            temperature=0.0,  # Deterministic output
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        # Extract word-level timestamps with validation
        subtitles = []
        if isinstance(result, dict):
            for segment in result.get("segments", []):
                if isinstance(segment, dict) and "words" in segment:
                    for word_info in segment.get("words", []):
                        if isinstance(word_info, dict):
                            word_text = word_info.get("word", "").strip()
                            start_time = float(word_info.get("start", 0.0))
                            end_time = float(word_info.get("end", 0.0))

                            # Validate and fix timing issues
                            if end_time <= start_time:
                                end_time = start_time + 0.15  # Minimum 150ms duration

                            subtitles.append({
                                "word": word_text,
                                "start": round(start_time, 3),
                                "end": round(end_time, 3)
                            })

        if subtitles:
            # Save to JSON
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(subtitles, f, ensure_ascii=False, indent=2)

            print(f"✅ Created Whisper-aligned subtitles: {len(subtitles)} words with 100% accurate timing")
            return output_json

    except ImportError:
        print("⚠️ Whisper not installed. Install with: pip install openai-whisper")
    except Exception as e:
        print(f"⚠️ Whisper failed: {e}")

    # Fallback: Simple division (less accurate)
    print("📝 Falling back to simple time division...")

    # Get audio duration
    try:
        if MP3:
            audio = MP3(str(audio_path))
            audio_duration = audio.info.length
        elif AudioSegment:
            audio = AudioSegment.from_mp3(str(audio_path))
            audio_duration = len(audio) / 1000.0  # Convert ms to seconds
        else:
            print("⚠️ Neither mutagen nor pydub available, using default 60s duration")
            audio_duration = 60.0
    except Exception as e:
        print(f"⚠️ Could not read audio duration: {e}, using default 60s")
        audio_duration = 60.0

    # Split script into words
    words = script_text.split()
    word_count = len(words)

    if word_count == 0:
        print("⚠️ No words in script")
        return None

    # Calculate time per word
    time_per_word = audio_duration / word_count

    # Create subtitle entries
    subtitles = []
    for i, word in enumerate(words):
        start_time = i * time_per_word
        end_time = (i + 1) * time_per_word

        subtitles.append({
            "word": word.strip(),
            "start": round(start_time, 3),
            "end": round(end_time, 3)
        })

    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)

    print(f"✅ Created simple subtitles: {len(subtitles)} words over {audio_duration:.1f}s")
    return output_json


def _load_database() -> Dict[str, Any]:
    """Load database.json"""
    db_path = Path("database.json")
    if not db_path.exists():
        return {"books": []}
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"books": []}


def _save_database(data: Dict[str, Any]) -> None:
    """Save database.json"""
    db_path = Path("database.json")
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_book_youtube_url(main_title: str) -> Optional[str]:
    """Get YouTube URL for a book from database"""
    db = _load_database()
    for book in db.get("books", []):
        if book.get("main_title") == main_title:
            return book.get("youtube_url")
    return None


def _load_used_video_ids() -> set[int]:
    """Load set of used Pexels video IDs to avoid duplicates"""
    ids_file = Path("used_pexels_videos.json")
    if not ids_file.exists():
        return set()
    try:
        with open(ids_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("used_ids", []))
    except Exception:
        return set()


def _save_used_video_ids(used_ids: set[int]) -> None:
    """Save used Pexels video IDs"""
    ids_file = Path("used_pexels_videos.json")
    try:
        with open(ids_file, "w", encoding="utf-8") as f:
            json.dump({"used_ids": list(used_ids)}, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save used video IDs: {e}")


def _add_used_video_ids(video_ids: list[int]) -> None:
    """Add new video IDs to the used set. Auto-clean after 50 videos."""
    used = _load_used_video_ids()
    used.update(video_ids)

    # Auto-clean database if we've used 50+ videos
    if len(used) >= 50:
        used = set()  # Reset to empty

    _save_used_video_ids(used)


def _select_queries_by_book_type(book_type: str) -> list[str]:
    """
    Select appropriate video queries based on book type/genre
    
    Args:
        book_type: Book category (Self-Development, Business, Psychology, etc.)
    
    Returns:
        List of search queries appropriate for the book type
    
    Strategy:
        - Nature queries: Self-development, general books
        - Urban queries: Business, technology, professional development
        - Abstract queries: Psychology, philosophy, deep concepts
        - Epic queries: History, classical works, ancient wisdom
    """
    # Category 1: NATURE QUERIES (Default - Pure landscapes, NO living beings)
    NATURE_QUERIES = [
        "mountain landscape nature",
        "forest trees nature",
        "ocean waves water",
        "sunset sky clouds",
        "waterfall nature",
        "clouds timelapse sky",
        "desert sand dunes",
        "northern lights aurora",
        "river flowing water",
        "snow falling winter",
        "galaxy stars space",
        "canyon rocks nature",
        "volcano lava",
        "ice glacier",
        "rock formations cliffs",
        "valley meadow nature",
        "fjord landscape",
        "geyser steam",
    ]
    
    # Category 2: URBAN/MODERN QUERIES (Business, Technology, Professional)
    URBAN_QUERIES = [
        "city skyline timelapse",
        "modern architecture building",
        "business district downtown",
        "traffic lights night city",
        "subway metro underground",
        "skyscraper glass reflection",
        "urban street aerial view",
        "office building windows",
        "city lights night aerial",
        "highway traffic timelapse",
        "modern bridge architecture",
        "airport terminal modern",
        "glass building reflection",
        "urban development timelapse",
        "metropolitan cityscape",
        "downtown skyline sunset",
        "concrete architecture modern",
        "urban infrastructure aerial",
    ]
    
    # Category 3: ABSTRACT/CONCEPTUAL QUERIES (Psychology, Philosophy, Deep Topics)
    ABSTRACT_QUERIES = [
        "colorful ink water abstract",
        "particles motion graphics",
        "light rays bokeh abstract",
        "geometric patterns animation",
        "liquid fluid motion",
        "gradient colors flowing",
        "paint mixing colors",
        "smoke abstract motion",
        "water droplets macro",
        "light refraction prism",
        "oil water abstract",
        "kaleidoscope patterns",
        "glass refraction light",
        "abstract waves motion",
        "color explosion abstract",
        "light particles floating",
        "abstract shapes geometry",
        "fluid dynamics motion",
    ]
    
    # Category 4: EPIC/HISTORICAL QUERIES (History, Classics, Ancient Wisdom)
    EPIC_QUERIES = [
        "ancient ruins historical",
        "old books library vintage",
        "stone architecture heritage",
        "classical sculpture art",
        "historical monument landmark",
        "antique clock time vintage",
        "medieval castle stone",
        "ancient pillars columns",
        "vintage compass map",
        "old manuscript paper",
        "historical building facade",
        "ancient temple architecture",
        "stone wall texture old",
        "vintage globe antique",
        "old library shelves books",
        "classical art museum",
        "heritage site historical",
        "ancient stone carving",
    ]
    
    # Smart category mapping based on book_type
    book_type_lower = book_type.lower()
    
    # Business & Technology → Urban
    if any(keyword in book_type_lower for keyword in ["business", "entrepreneur", "startup", "finance", "economy", "technology", "tech", "digital", "innovation"]):
        print(f"📊 Book type '{book_type}' → Using URBAN queries (modern/business)")
        return URBAN_QUERIES
    
    # Psychology & Philosophy → Abstract
    elif any(keyword in book_type_lower for keyword in ["psychology", "philosophy", "mental", "mind", "thinking", "cognitive", "consciousness", "meditation"]):
        print(f"🧠 Book type '{book_type}' → Using ABSTRACT queries (conceptual)")
        return ABSTRACT_QUERIES
    
    # History & Classics → Epic
    elif any(keyword in book_type_lower for keyword in ["history", "historical", "ancient", "classic", "war", "civilization", "heritage", "legacy"]):
        print(f"📜 Book type '{book_type}' → Using EPIC queries (historical)")
        return EPIC_QUERIES
    
    # Science → Mix of Abstract + Nature
    elif any(keyword in book_type_lower for keyword in ["science", "physics", "biology", "chemistry", "astronomy", "space"]):
        print(f"🔬 Book type '{book_type}' → Using ABSTRACT + NATURE mix (scientific)")
        return ABSTRACT_QUERIES[:9] + NATURE_QUERIES[:9]  # 50/50 mix
    
    # Default: Self-Development & General → Nature
    else:
        print(f"🌿 Book type '{book_type}' → Using NATURE queries (default)")
        return NATURE_QUERIES


def _fetch_pexels_videos(
    output_dir: Path,
    target_duration: float,
    book_type: str = "Self-Development",  # NEW: Book type for smart query selection
    per_page: int = 50,  # Increased to get more results per page
    max_pages: int = 3   # Search multiple pages
) -> list[Path]:
    """
    Fetch vertical stock videos from Pexels with smart query selection based on book type.

    Args:
        output_dir: Directory to save video files
        target_duration: Desired total duration in seconds (audio length)
        book_type: Book category for smart query selection (NEW v2.3.1)
        per_page: How many results to request from API per page
        max_pages: Maximum number of pages to search per query

    Returns:
        List of downloaded video file Paths (4 clips exactly)
    
    Smart Query Selection (NEW):
        - Business/Tech books → Urban scenes (cities, buildings, modern architecture)
        - Psychology/Philosophy → Abstract visuals (colors, patterns, motion graphics)
        - History/Classics → Epic scenes (ancient ruins, monuments, heritage)
        - Science → Mix of abstract + nature
        - Default (Self-Development) → Nature landscapes
    """
    # Select appropriate queries based on book type
    SEARCH_QUERIES = _select_queries_by_book_type(book_type)
    
    # ===== PEXELS API KEY FALLBACK SYSTEM (Multi-file support) =====
    api_key = None
    
    # Get repository root (go up 3 levels from this file)
    repo_root = Path(__file__).resolve().parents[3]
    
    # Priority 1: Environment variable
    api_key = os.getenv("PEXELS_API_KEY")
    
    if not api_key:
        # Priority 2-6: Check multiple API key files
        api_key_paths = [
            repo_root / "secrets" / ".env",           # Priority 2: Main .env
            repo_root / "secrets" / "pexels_key.txt", # Priority 3: Dedicated Pexels key
            repo_root / "secrets" / "api_keys.txt",   # Priority 4: Shared API keys file
            repo_root / "secrets" / "api_key.txt",    # Priority 5: Legacy API key
            repo_root / ".env"                        # Priority 6: Root .env
        ]
        
        api_keys_found = []  # Track all valid API keys
        
        for idx, key_path in enumerate(api_key_paths, 1):
            if key_path.exists():
                try:
                    content = key_path.read_text(encoding="utf-8").strip()
                    
                    # Handle .env format (KEY=value)
                    if key_path.name.endswith('.env'):
                        for line in content.splitlines():
                            line = line.strip()
                            if line.startswith("PEXELS_API_KEY="):
                                extracted_key = line.split("=", 1)[1].strip()
                                if extracted_key and len(extracted_key) > 20:  # Valid key length
                                    api_keys_found.append((key_path, extracted_key))
                                    print(f"[Pexels] ✓ Valid API key {idx}/{len(api_key_paths)}: {key_path.name}")
                                break
                    
                    # Handle plain text format (key only)
                    else:
                        # For multi-line files, try each line
                        for line in content.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#") and len(line) > 20:
                                api_keys_found.append((key_path, line))
                                print(f"[Pexels] ✓ Valid API key {idx}/{len(api_key_paths)}: {key_path.name}")
                                break  # Use first valid key from this file
                
                except Exception as e:
                    print(f"[Pexels] ⚠️  Failed to read file {idx}: {key_path.name} ({e})")
        
        # Use first valid API key (priority order)
        if api_keys_found:
            key_path, api_key = api_keys_found[0]
            print(f"[Pexels] 🔑 Using primary API key from: {key_path.name}")
            if len(api_keys_found) > 1:
                print(f"[Pexels] 📋 {len(api_keys_found)-1} backup API key(s) available for fallback")
        else:
            print("[Pexels] ❌ No valid PEXELS_API_KEY found")
            print("[Pexels] 📂 Locations checked:")
            print("   - Environment variable: PEXELS_API_KEY")
            for kp in api_key_paths:
                print(f"   - {kp}")
            print("[Pexels] 💡 Get free API key from: https://www.pexels.com/api/")
            print("[Pexels] 🔐 Save to secrets/.env or secrets/pexels_key.txt")
    
    # Handle case where API key came from environment variable
    else:
        # Environment variable was used - create single-item list for consistency
        api_keys_found = [(Path("ENV_VAR"), api_key)]

    if not api_key:
        print("ℹ️ PEXELS_API_KEY not set. Skipping Pexels videos fetch.")
        return []

    # Load previously used video IDs to avoid duplicates
    used_video_ids = _load_used_video_ids()

    # Use exactly 4 different search queries for maximum variety
    all_candidates: list[dict] = []

    import random
    random.shuffle(SEARCH_QUERIES)  # Randomize order for variety
    selected_queries = SEARCH_QUERIES[:4]  # Pick first 4 from shuffled list

    # ===== AUTO-RETRY SYSTEM: Try each API key until success =====
    # Start with primary key, fall back to others on 403/429 errors
    current_key_index = 0
    max_key_retries = len(api_keys_found)
    
    # Initial headers with primary key
    headers = {"Authorization": api_key}

    for search_query in selected_queries:

        # Search multiple pages to get variety from each query
        page = 1
        query_candidates = 0
        max_pages_per_query = 5  # Limit pages per query to avoid infinite loops

        while query_candidates < 6 and page <= max_pages_per_query:  # Get up to 6 videos per query (for variety)
            params = {
                "query": search_query,
                "per_page": per_page,
                "page": page,
            }

            # Use cache + retry system for maximum efficiency
            data = _fetch_with_cache(
                query=search_query,
                page=page,
                headers=headers,
                params=params,
                cache_hours=24  # Cache valid for 24 hours
            )
            
            # ===== AUTO-RETRY WITH FALLBACK KEYS ON 403/429 =====
            # If fetch failed and we have backup keys, try them
            if data is None and current_key_index < max_key_retries - 1:
                print(f"    🔄 Primary API key failed - trying backup keys...")
                
                # Try each remaining backup key
                for retry_idx in range(current_key_index + 1, max_key_retries):
                    _, backup_key = api_keys_found[retry_idx]
                    headers = {"Authorization": backup_key}
                    current_key_index = retry_idx
                    
                    print(f"    🔑 Attempting with backup API key {retry_idx + 1}/{max_key_retries}...")
                    
                    # Retry the same request with new key
                    data = _fetch_with_cache(
                        query=search_query,
                        page=page,
                        headers=headers,
                        params=params,
                        cache_hours=24
                    )
                    
                    if data is not None:
                        print(f"    ✅ Success with backup key {retry_idx + 1}!")
                        break  # Success - continue with this key
                else:
                    # All keys failed
                    print(f"    ❌ All {max_key_retries} API keys exhausted for query '{search_query}'")
            
            # Final check after retry attempts
            if data is None:
                print(f"    ❌ Skipping query '{search_query}' page {page} - no valid API keys remaining")
                break  # Move to next query
            
            videos = data.get("videos", [])
            if not videos:
                break  # No more results for this query

            found_in_page = 0
            # Prefer vertical videos and moderate durations, TRY to avoid faces
            for v in videos:
                video_id = v.get("id")

                # Skip if already used
                if video_id in used_video_ids:
                    continue

                width = v.get("width") or 0
                height = v.get("height") or 0
                duration = v.get("duration") or 0

                # Need vertical videos at least 15 seconds (for 4×15s = 60s shorts)
                if height >= width and duration >= 15:
                    # Check for people/face/animal tags (STRICT FILTERING)
                    tags = [tag.lower() for tag in v.get("tags", [])]
                    tag_string = " ".join(tags)

                    # Get video title and user name for additional checks
                    video_title = (v.get("title") or "").lower()
                    video_user = (v.get("user", {}).get("name") or "").lower()
                    combined_text = f"{tag_string} {video_title} {video_user}"

                    # ULTRA STRICT: Filter out people (maximum keywords)
                    has_people = any(keyword in combined_text for keyword in [
                        "people", "person", "human", "face", "man", "woman", "child", "children",
                        "portrait", "guy", "girl", "boy", "baby", "adult", "crowd", "group",
                        "hand", "hands", "finger", "fingers", "body", "skin", "hair", "eye", "eyes",
                        "smile", "smiling", "walking", "running", "standing", "sitting", "jumping",
                        "dancer", "dancing", "worker", "model", "athlete", "player", "people",
                        "selfie", "closeup", "close-up", "headshot", "portrait", "face",
                        "kid", "kids", "teen", "teenager", "senior", "elderly", "youth",
                        "male", "female", "gentleman", "lady", "ladies", "gentlemen",
                        "couple", "family", "friend", "friends", "team", "staff",
                        "arm", "arms", "leg", "legs", "foot", "feet", "shoulder", "shoulders",
                        "person", "anonymous", "silhouette", "shadow", "figure"
                    ])

                    # ULTRA STRICT: Filter out animals (maximum keywords)
                    has_animals = any(keyword in combined_text for keyword in [
                        "animal", "animals", "bird", "birds", "dog", "dogs", "cat", "cats",
                        "fish", "horse", "horses", "cow", "cows", "sheep", "goat", "goats",
                        "deer", "bear", "bears", "lion", "lions", "tiger", "tigers", "leopard",
                        "elephant", "elephants", "monkey", "monkeys", "ape", "gorilla", "chimpanzee",
                        "rabbit", "rabbits", "wildlife", "insect", "insects", "butterfly", "butterflies",
                        "bee", "bees", "wasp", "snake", "snakes", "lizard", "lizards", "reptile",
                        "eagle", "eagles", "hawk", "falcon", "duck", "ducks", "chicken", "chickens",
                        "pet", "pets", "kitten", "kittens", "puppy", "puppies", "wolf", "wolves",
                        "fox", "foxes", "owl", "owls", "parrot", "parrots", "penguin", "penguins",
                        "dolphin", "dolphins", "whale", "whales", "shark", "sharks", "seal", "seals",
                        "frog", "frogs", "toad", "spider", "spiders", "squirrel", "squirrels",
                        "bat", "bats", "mouse", "mice", "rat", "rats", "zebra", "giraffe", "hippo",
                        "crocodile", "alligator", "turtle", "tortoise", "crab", "octopus", "jellyfish",
                        "ant", "ants", "beetle", "fly", "flies", "mosquito", "dragonfly", "ladybug",
                        "creature", "creatures", "fauna", "beast", "paw", "wing", "wings", "tail",
                        "feather", "feathers", "fur", "scale", "scales", "beak", "horn", "antler"
                    ])

                    # STRICT: Filter out religious buildings (NEW)
                    has_religious_buildings = any(keyword in combined_text for keyword in [
                        "church", "mosque", "temple", "cathedral", "chapel", "shrine",
                        "synagogue", "pagoda", "monastery", "abbey", "basilica",
                        "كنيسة", "مسجد", "معبد", "كاتدرائية", "دير",
                        "prayer", "worship", "religion", "religious", "holy", "sacred",
                        "cross", "crucifix", "altar", "dome", "minaret", "steeple"
                    ])

                    # Skip if has people, animals, or religious buildings
                    if has_people or has_animals or has_religious_buildings:
                        continue

                    # choose the best file link (prefer 1080 width if available)
                    best_file = None
                    best_score = -1
                    for vf in v.get("video_files", []):
                        vw = vf.get("width") or 0
                        vh = vf.get("height") or 0
                        link = vf.get("link")
                        if not link:
                            continue
                        # score: prefer vertical, 1080x1920-ish, mp4
                        orient_bonus = 1 if vh >= vw else 0
                        res_score = -abs((vw or 0) - 1080) - abs((vh or 0) - 1920)
                        score = orient_bonus * 1000 + res_score
                        if score > best_score:
                            best_score = score
                            best_file = vf

                    if best_file:
                        video_data = {
                            "id": video_id,
                            "duration": duration,
                            "file": best_file,
                        }
                        all_candidates.append(video_data)
                        found_in_page += 1
                        query_candidates += 1

            # If we have enough from this query OR no more results, move to next query
            if query_candidates >= 6 or not videos:
                break

            # Continue to next page
            page += 1

            # Safety: Stop if reached max pages
            if page > max_pages_per_query:
                break

    # Use candidates without people or animals
    final_candidates = all_candidates

    if not final_candidates:
        return []

    # Download clips using parallel processing for maximum speed
    downloaded: list[Path] = []
    downloaded_ids: list[int] = []
    total_duration = 0.0

    # Calculate minimum duration needed per clip
    min_duration_per_clip = target_duration / 4  # e.g., 57s / 4 = 14.25s
    # Add small buffer (10%) to ensure we have enough footage
    MIN_CLIP_DURATION = max(10.0, min_duration_per_clip * 0.9)  # At least 10s, ideally 90% of target

    # We need exactly 4 videos
    REQUIRED_CLIPS = 4
    
    # Filter candidates by minimum duration and take first 4
    valid_candidates = [
        c for c in final_candidates 
        if c.get("duration", 0) >= MIN_CLIP_DURATION
    ][:REQUIRED_CLIPS]
    
    if len(valid_candidates) < REQUIRED_CLIPS:
        print(f"⚠️ Only found {len(valid_candidates)} videos meeting duration requirement")
    
    # Parallel download function
    def _download_single_video(video_data: dict, clip_index: int) -> Optional[tuple[Path, int, float]]:
        """
        Download single video in parallel thread
        
        Returns:
            Tuple of (path, video_id, duration) if successful, None otherwise
        """
        url = video_data["file"]["link"]
        video_id = video_data["id"]
        duration = video_data.get("duration", 0)
        out_path = output_dir / f"pexels_clip_{clip_index}.mp4"
        
        try:
            # Stream download for large files (more efficient)
            resp = requests.get(url, timeout=30, stream=True)
            resp.raise_for_status()
            
            # Write in chunks
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"    ✅ Downloaded clip {clip_index}/4")
            return (out_path, video_id, duration)
            
        except Exception as e:
            print(f"    ❌ Failed clip {clip_index}: {e}")
            return None
    
    # Download all videos in parallel using ThreadPoolExecutor
    print(f"⚡ Starting parallel download of {len(valid_candidates)} videos...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all download tasks
        futures = [
            executor.submit(_download_single_video, candidate, i + 1)
            for i, candidate in enumerate(valid_candidates)
        ]
        
        # Collect results as they complete
        for future in futures:
            result = future.result()
            if result:
                path, vid_id, duration = result
                downloaded.append(path)
                downloaded_ids.append(vid_id)
                total_duration += duration

    if len(downloaded) == 0:
        print("❌ No videos downloaded")
        return []

    # STRICT CHECK: Warn if not exactly 4 videos
    if len(downloaded) != REQUIRED_CLIPS:
        print(f"\n⚠️⚠️⚠️ WARNING: Expected 4 videos but got {len(downloaded)} ⚠️⚠️⚠️")
        print(f"🎬 Each scene will be {(total_duration/len(downloaded)):.1f}s instead of ~14s")
    else:
        print(f"✅ Successfully downloaded {len(downloaded)} videos in parallel")

    # Save used video IDs to prevent future duplicates
    if downloaded_ids:
        _add_used_video_ids(downloaded_ids)

    return downloaded


def _generate_short_script(
    model,
    book_name: str,
    book_type: str,
    excerpt: str,
    prompts: dict
) -> Optional[str]:
    """
    Generate engaging 60s short script using AI

    Args:
        model: Gemini model instance
        book_name: Name of the book
        book_type: Category (Self-Development, Thriller, etc.)
        excerpt: Powerful excerpt from the book
        prompts: Prompt templates

    Returns:
        Short script (80-120 words) or None
    """
    # Determine tone based on book type
    tone_map = {
        "Self-Development": "motivational and uplifting",
        "Business": "analytical and practical",
        "Psychology": "insightful and thought-provoking",
        "Philosophy": "profound and contemplative",
        "Fiction": "dramatic and suspenseful",
        "Thriller": "dark and mysterious",
        "Science": "curious and enlightening",
        "History": "epic and narrative",
    }
    tone = tone_map.get(book_type, "engaging and informative")

    prompt = f"""You are an expert YouTube Shorts scriptwriter specializing in book summaries.

Book: {book_name}
Genre: {book_type}
Target audience: Mobile viewers (15-35 years old)
Required tone: {tone}

Excerpt from the book:
{excerpt[:500]}

═══════════════════════════════════════════════════════
CRITICAL STRUCTURE (45-60 seconds when spoken aloud)
═══════════════════════════════════════════════════════

PART 1: THE HOOK (0-5 seconds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Choose DIFFERENT hook styles each time to create variety:

Hook Style Options (rotate between them):

a) Shocking Question:
   "What if everything you believed about [topic] was backwards?"
   "Ever wonder why [surprising fact]?"

b) Bold Statement:
   "Here's the truth nobody tells you about [topic]."
   "Most people get [topic] completely wrong."

c) Direct Challenge:
   "Think you know [topic]? Think again."
   "This one idea changed everything about [topic]."

d) Curiosity Gap:
   "The secret to [desirable outcome] isn't what you think."
   "Successful people know this about [topic]."

e) Personal Hook:
   "I discovered something powerful about [topic]."
   "This changed my entire perspective on [topic]."

Hook Requirements:
✓ 8-15 words maximum
✓ Create immediate curiosity
✓ Promise clear value
✓ VARY the style - don't always use the same pattern
✓ AVOID overused phrases like "Stop scrolling"
✓ Make viewers think: "I NEED to know more"

PART 2: MAIN CONTENT (5-55 seconds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transform the excerpt into a fast-paced narrative:

✓ Use short, punchy sentences (max 15 words each)
✓ Fast rhythm (speak like you're telling an exciting story)
✓ Include ONE powerful insight from the book
✓ Build curiosity throughout (don't give everything away)
✓ Use "you" language to speak directly to viewer

PART 3: THE CLOSE (55-60 seconds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
End with the book name in an artistic way:

Example:
"That's the power of {book_name}."
"All in {book_name}."
"Discover more in {book_name}."

═══════════════════════════════════════════════════════
OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════

✓ Length: 70-90 words in English (STRICT - must fit in 55 seconds when spoken)
✓ Style: {tone}, fast-paced, engaging
✓ Format: Plain text ONLY (no stage directions, no visual cues)
✓ NO **(Sound:...)**, NO **(Visual:...)**, NO **Voiceover:**
✓ Just pure spoken narrative that flows naturally
✓ Target speaking time: 50-55 seconds (leaves room for CTA at end)
✓ IMPORTANT: Use DIFFERENT hooks each time - variety is key!

═══════════════════════════════════════════════════════
EXAMPLES OF VARIED HOOKS
═══════════════════════════════════════════════════════

❌ BAD (repetitive):
"Stop scrolling. This book..."
"Stop scrolling. Let me tell you..."
(Using same pattern repeatedly)

✅ GOOD (varied hooks):
Example 1: "What if I told you that one tiny habit could transform your entire life? Most people try to change everything at once and fail. But this book reveals a different approach. Start with just 1% improvement every single day. Compound that over a year, and you're 37 times better. It's not about willpower. It's about systems. Small changes, massive results. That's the genius of Atomic Habits."

Example 2: "Ever wonder why some people achieve their goals while others don't? The difference isn't talent or luck. It's about understanding how habits really work. This book breaks down the science. Make it obvious. Make it attractive. Make it easy. Make it satisfying. Four simple rules that compound into massive change. Master these, and you control your future. All in Atomic Habits."

Example 3: "Here's the truth about building better habits: Motivation is overrated. What you need is a system. This book reveals exactly how. Focus on your identity, not your goals. Every action is a vote for who you want to become. Tiny improvements, repeated daily. That's how you transform. It's not about overnight success. It's about the compound effect. Discover it in Atomic Habits."

═══════════════════════════════════════════════════════

Now write the voice-over script for {book_name}:"""

    try:
        response = model.generate_content(prompt)
        script = response.text.strip()

        # Clean up
        script = re.sub(r'^["\']+|["\']+$', '', script)
        script = script.strip()

        # Validate word count (80-120 words)
        word_count = len(script.split())
        if word_count < 60 or word_count > 150:
            print(f"⚠️ Script word count ({word_count}) outside range, but proceeding...")

        return script
    except Exception as e:
        print(f"❌ Failed to generate short script: {e}")
        return None


def _find_best_excerpt(translate_path: Path, max_chars: int = 800) -> str:
    """
    Find the most impactful excerpt from translation
    For now, uses first 800 chars. Can be enhanced with AI selection.
    """
    try:
        with open(translate_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Take first significant chunk
        # TODO: Use AI to select the most engaging part
        excerpt = text[:max_chars].strip()

        # Try to end at sentence
        last_period = excerpt.rfind('.')
        if last_period > 400:
            excerpt = excerpt[:last_period + 1]

        return excerpt
    except Exception as e:
        print(f"❌ Failed to read translation: {e}")
        return ""


def _tts_to_audio(script: str, output_path: Path, run_dir: Path) -> bool:
    """
    Convert script to audio using the main TTS pipeline (OpenAI.fm)

    Args:
        script: Text to convert
        output_path: Where to save MP3
        run_dir: Run directory for temp files

    Returns:
        True if successful
    """
    try:
        from . import tts

        # Save script to temp file
        temp_script = run_dir / "short_script_temp.txt"
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(script)

        # Create temp segments dir
        temp_segments = run_dir / "short_tts_segments"
        temp_segments.mkdir(exist_ok=True)

        # Use main TTS function
        result = tts.main(
            text_path=temp_script,
            segments_dir=temp_segments,
            output_mp3=output_path,
            voice_name="Shimmer",  # Default OpenAI voice
            headless=True,
            max_chars=950,
            reencode=True,
            delete_parts_after_merge=True,
            run_dir=run_dir
        )

        # Cleanup temp files
        if temp_script.exists():
            temp_script.unlink()

        if result:
            print(f"✅ TTS generated: {output_path}")
            return True
        else:
            print("❌ TTS failed")
            return False

    except Exception as e:
        print(f"❌ TTS failed: {e}")
        return False


def _trim_audio_to_60s(audio_path: Path) -> bool:
    """
    Trim audio to 60 seconds maximum (cut from end)

    Args:
        audio_path: Path to MP3 file

    Returns:
        True if trimming was needed and successful
    """
    if AudioSegment is None:
        print("⚠️ pydub not installed, skipping audio trim check")
        return False

    try:
        audio = AudioSegment.from_mp3(str(audio_path))
        duration_ms = len(audio)
        duration_s = duration_ms / 1000.0

        print(f"📊 Audio duration: {duration_s:.1f}s")

        # YouTube Shorts can be up to 60s, but allow slightly over for natural endings
        if duration_s <= 65.0:
            print(f"✅ Audio within acceptable limit ({duration_s:.1f}s / 65s max)")
            return False

        # Trim to 65 seconds (allows natural sentence completion)
        print(f"✂️ Trimming from {duration_s:.1f}s to 65s...")
        trimmed = audio[:65000]  # First 65 seconds
        trimmed.export(str(audio_path), format="mp3")
        print("✅ Audio trimmed to 65s")
        return True
    except Exception as e:
        print(f"❌ Audio trim failed: {e}")
        return False


def _group_words_into_sentences(words, max_words_per_line=8):
    """
    Group words into sentences based on punctuation and word count.
    Automatically adds line breaks every max_words_per_line words.

    Args:
        words: List of word dicts with 'word', 'start', 'end'
        max_words_per_line: Maximum words per line (adds \n after this many words)

    Returns:
        List of sentence dicts with 'text', 'start', 'end'
    """
    sentences = []
    current_sentence = []

    for i, word_data in enumerate(words):
        current_sentence.append(word_data)
        word = word_data['word']

        # Check if this is end of sentence (punctuation or max words)
        is_end_punctuation = bool(re.search(r'[.!?]', word))
        is_max_words = len(current_sentence) >= max_words_per_line
        is_last_word = i == len(words) - 1

        if is_end_punctuation or is_max_words or is_last_word:
            # Create sentence with line breaks every max_words_per_line words
            words_list = [w['word'] for w in current_sentence]

            # Split into chunks of max_words_per_line and join with \n
            text_lines = []
            for chunk_start in range(0, len(words_list), max_words_per_line):
                chunk = words_list[chunk_start:chunk_start + max_words_per_line]
                text_lines.append(' '.join(chunk))

            text = '\n'.join(text_lines)  # Join lines with newline
            start = current_sentence[0]['start']
            end = current_sentence[-1]['end']

            sentences.append({
                'text': text,
                'start': start,
                'end': end
            })

            current_sentence = []

    return sentences


def _render_short_video_from_videos(
    audio_path: Path,
    videos: list[Path],
    output_path: Path,
    subtitle_json: Optional[Path] = None,
    fps: int = 30,
) -> bool:
    """
    Render vertical 9:16 short from multiple video clips with optional captions:
    - Scale/crop to 1080x1920
    - Trim each segment to equal duration
    - Concat clips without crossfade
    - Add sentence-based captions if subtitle_json provided
    - Limit total to audio duration
    """
    # Get audio duration
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True,
            text=True,
            check=True
        )
        duration = float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Failed to get audio duration: {e}")
        return False

    n = len(videos)
    if n == 0:
        print("❌ No video clips provided")
        return False

    # CRITICAL: Must have exactly 4 videos for consistent quality
    if n < 4:
        print(f"❌ Need exactly 4 videos, got only {n}")
        print(f"⚠️ Short will have only {n} scenes - quality may be inconsistent!")
        # Don't fail, but warn user
    elif n > 4:
        print(f"⚠️ Got {n} videos but using only first 4 for consistency")
        videos = videos[:4]  # Use only first 4
        n = 4

    # Calculate segment duration to match audio exactly (no crossfade)
    # Simple: total_duration = n * seg
    seg = duration / n

    # Inputs: add each video WITH loop to ensure enough frames
    cmd = ["ffmpeg", "-y"]
    for p in videos:
        cmd.extend(["-stream_loop", "-1", "-i", str(p)])  # Infinite loop

    # Add audio
    cmd.extend(["-i", str(audio_path)])
    audio_idx = len(videos)  # Audio comes right after videos

    # Build filters: scale/crop->fps->trim per clip (with loop, we can safely trim)
    parts = []
    for i in range(n):
        parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,fps={fps},trim=duration={seg},setpts=PTS-STARTPTS[v{i}]"
        )

    filt = ";\n".join(parts) + ";\n"

    # Simple concat (no crossfade to avoid frame rate issues)
    filt += "".join(f"[v{i}]" for i in range(n))
    filt += f"concat=n={n}:v=1:a=0[vbase]"

    # Apply cinematic effects: blur for text clarity + vignette for focus
    filt += ";\n[vbase]gblur=sigma=5,vignette=angle=PI/4:mode=forward[veffects]"

    # Prepare audio
    filt += f";\n[{audio_idx}:a]acopy[a_final]"
    audio_map = "a_final"
    next_input = "veffects"

    # Add professional single-line subtitles with word highlighting
    if subtitle_json and subtitle_json.exists():
        try:
            with open(subtitle_json, 'r', encoding='utf-8') as f:
                words = json.load(f)

            # ==========================================
            # STEP 1: Build natural sentence segments
            # ==========================================
            import re

            def has_sentence_end(word: str) -> bool:
                """Check if word ends with sentence-ending punctuation"""
                return bool(re.search(r'[.!?؟]$', word.strip()))

            lines = []  # Each line: {text: str, words: [{word, start, end}], start: float, end: float}
            current_line_words = []
            current_chars = 0
            MAX_LINE_CHARS = 35  # Maximum characters per line for readability
            MAX_LINE_DURATION = 3.0  # Maximum 3 seconds per line

            for i, word_data in enumerate(words):
                word_text = word_data['word']
                word_start = float(word_data['start'])
                word_end = float(word_data['end'])

                # Fix timing issues
                if word_end <= word_start:
                    word_end = word_start + 0.1

                # Check if we should break to new line
                should_break = False

                if current_line_words:
                    line_duration = word_end - current_line_words[0]['start']
                    next_chars = current_chars + len(word_text) + 1  # +1 for space

                    # Natural break points
                    prev_word = current_line_words[-1]['word']
                    silence_gap = word_start - current_line_words[-1]['end']

                    if has_sentence_end(prev_word):
                        should_break = True
                    elif silence_gap > 0.8:  # Long pause
                        should_break = True
                    elif next_chars > MAX_LINE_CHARS:
                        should_break = True
                    elif line_duration > MAX_LINE_DURATION:
                        should_break = True

                if should_break and current_line_words:
                    # Save current line
                    line_text = ' '.join([w['word'] for w in current_line_words])
                    lines.append({
                        'text': line_text,
                        'words': current_line_words,
                        'start': current_line_words[0]['start'],
                        'end': current_line_words[-1]['end']
                    })
                    current_line_words = []
                    current_chars = 0

                # Add word to current line
                current_line_words.append({
                    'word': word_text,
                    'start': word_start,
                    'end': word_end
                })
                current_chars += len(word_text) + (1 if current_chars > 0 else 0)

            # Don't forget last line
            if current_line_words:
                line_text = ' '.join([w['word'] for w in current_line_words])
                lines.append({
                    'text': line_text,
                    'words': current_line_words,
                    'start': current_line_words[0]['start'],
                    'end': current_line_words[-1]['end']
                })

            # ==========================================
            # STEP 2: Generate ASS subtitle file
            # ==========================================
            ass_file = output_path.parent / "captions_highlight.ass"

            # Professional ASS header - simple line-by-line subtitles (Shorts style with transparency)
            ass_header = """[Script Info]
Title: Professional Line-by-Line Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Bebas Neue,95,&H00FFFFFF,&H000000FF,&H00000000,&HC0000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,120,1
Style: CTA,Bebas Neue,60,&H0000FFFF,&H000000FF,&H00000000,&HC0000000,-1,0,0,0,100,100,0,0,1,5,3,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

            def format_ass_time(seconds: float) -> str:
                """Convert seconds to ASS time format H:MM:SS.CC"""
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = seconds % 60
                return f"{hours}:{minutes:02d}:{secs:05.2f}"

            # Subtitle position (centered, bottom third)
            Y_BOTTOM = 1300
            X_CENTER = 540

            events = []

            # No subtitle delay - subtitles start from the beginning
            subtitle_delay = 0.0

            for line_idx, line in enumerate(lines):
                # Start and end times with PRECISE synchronization
                line_start = line['start'] + subtitle_delay

                # End time: seamlessly connect to next line OR use original end
                if line_idx < len(lines) - 1:
                    # Next line exists - end EXACTLY when next one starts (no gap, no overlap)
                    line_end = lines[line_idx + 1]['start'] + subtitle_delay
                else:
                    # Last line - use original end time
                    line_end = line['end'] + subtitle_delay

                line_text = line['text']

                # CRITICAL: Ensure timing is valid (end > start)
                if line_end <= line_start:
                    line_end = line_start + 0.5  # Minimum half-second duration

                # Simple dialogue event with 100% accurate timing
                events.append(
                    f"Dialogue: 0,{format_ass_time(line_start)},{format_ass_time(line_end)},"
                    f"Default,,0,0,0,,{{\\pos({X_CENTER},{Y_BOTTOM})}}{line_text}"
                )

            # ==========================================
            # CTA Overlay: "Full video in description" - LAST 8 SECONDS ONLY
            # ==========================================
            # Add CTA for LAST 8 seconds only - positioned below captions, YELLOW color
            cta_text = "Full video in description ⬇️"
            cta_y_pos = 1450  # تحت الترجمة مباشرة (Y_BOTTOM = 1300 + 150)
            cta_start = max(0, duration - 8.0)  # Start 8 seconds before end
            cta_end = duration + subtitle_delay  # End at video end
            # Yellow text using CTA style
            events.append(
                f"Dialogue: 0,{format_ass_time(cta_start)},{format_ass_time(cta_end)},"
                f"CTA,,0,0,0,,{{\\pos({X_CENTER},{cta_y_pos})}}{cta_text}"
            )

            # Write complete ASS file
            with open(ass_file, 'w', encoding='utf-8') as f:
                f.write(ass_header)
                f.write('\n'.join(events))

            # Add subtitles to the video stream
            ass_path = str(ass_file).replace('\\', '/')
            ass_path = ass_path.replace(':', '\\:')
            filt += f";\n[{next_input}]subtitles={ass_path}[v]"

        except Exception as e:
            print(f"⚠️ Subtitle generation failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback without subtitles
            filt += f";\n[{next_input}]copy[v]"
    else:
        # No subtitles - just copy the stream
        filt += f";\n[{next_input}]copy[v]"

    try:
        cmd.extend([
            "-filter_complex", filt,
            "-map", "[v]",
            "-map", f"[{audio_map}]",  # Use delayed audio if thumbnail added
            # Video encoding with HIGH QUALITY for YouTube Shorts
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.0",
            "-pix_fmt", "yuv420p",
            "-preset", "slow",  # Better compression (slower but higher quality)
            "-crf", "18",  # High quality (18 = near-lossless, 23 = default)
            "-b:v", "5M",  # Target bitrate 5 Mbps (YouTube Shorts recommended)
            "-maxrate", "8M",  # Max bitrate 8 Mbps
            "-bufsize", "10M",  # Buffer size for bitrate control
            "-g", str(fps * 2),  # Keyframe every 2 seconds (GOP size)
            "-keyint_min", str(fps),  # Minimum keyframe interval
            "-sc_threshold", "0",  # Disable scene change detection
            "-force_key_frames", f"expr:gte(t,n_forced*2)",  # Force keyframe every 2s
            # Audio encoding
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            # Sync and compatibility
            "-vsync", "cfr",  # Constant frame rate
            "-async", "1",  # Audio sync
            "-max_muxing_queue_size", "1024",
            "-t", str(duration),  # Video duration matches audio
            "-movflags", "+faststart",
            str(output_path)
        ])

        # DEBUG: Print full FFmpeg command
        print("\n" + "="*60)
        print("🎬 FFmpeg Command Preview")
        print("="*60)
        print("🎨 Filter Complex:")
        filter_idx = cmd.index("-filter_complex") if "-filter_complex" in cmd else -1
        if filter_idx >= 0 and filter_idx + 1 < len(cmd):
            print(cmd[filter_idx + 1])
        print("="*60 + "\n")

        _print_progress(6, 7, "Rendering", 0)
        result = subprocess.run(cmd, check=True, capture_output=True)
        _print_progress(6, 7, "Rendering", 100)

        # Delete source video clips after successful merge
        _print_progress(7, 7, "Cleanup", 0)
        for video_clip in videos:
            if video_clip.exists():
                video_clip.unlink()

        _print_progress(7, 7, "Cleanup", 100)
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        print(f"❌ FFmpeg render failed:")
        print(stderr)
        return False
    except Exception as e:
        print(f"❌ Render failed: {e}")
        return False


def generate_short(run_dir: Path, model=None) -> Optional[Path]:
    """
    Main pipeline: Generate YouTube Short from book summary

    Args:
        run_dir: Path to run directory (e.g., runs/2025-10-06_20-06-04_Atomic-Habits)
        model: Gemini model instance (optional, will load if None)

    Returns:
        Path to generated short video, or None if failed
    """
    run_dir = Path(run_dir)

    # Load metadata
    titles_json = run_dir / "output.titles.json"
    if not titles_json.exists():
        print(f"❌ No output.titles.json in {run_dir}")
        return None

    try:
        with open(titles_json, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load metadata: {e}")
        return None

    book_name = metadata.get("main_title", "Unknown")
    book_type = metadata.get("playlist", "Self-Development")

    # Step 1: Check existing files
    _print_progress(1, 7, "Checking files", 0)

    # Step 1: Find best excerpt
    translate_path = run_dir / "translate.txt"
    if not translate_path.exists():
        print(f"\r❌ translate.txt not found" + " "*40)
        return None

    excerpt = _find_best_excerpt(translate_path)
    if not excerpt:
        return None

    _print_progress(1, 7, "Checking files", 100)

    # Step 2: Generate script with AI
    if model is None:
        # Load Gemini
        try:
            # Suppress STDERR warnings from Google's C++ libraries during import
            import sys
            _original_stderr = sys.stderr
            try:
                sys.stderr = open(os.devnull, 'w')
                import google.generativeai as genai
            finally:
                if sys.stderr != _original_stderr:
                    sys.stderr.close()
                sys.stderr = _original_stderr

            # ===== GEMINI API KEY FALLBACK SYSTEM (Multi-file support) =====
            # Same order as cookies_helper for consistency
            api_key = None
            
            # Get repository root (go up 3 levels from this file)
            repo_root = Path(__file__).resolve().parents[3]
            
            # Priority 1: Environment variable
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                # Priority 2-5: Check multiple API key files (same as cookies_helper)
                api_key_paths = [
                    repo_root / "secrets" / ".env",           # Priority 2: Main .env
                    repo_root / "secrets" / "api_keys.txt",   # Priority 3: Shared API keys
                    repo_root / "secrets" / "api_key.txt",    # Priority 4: Legacy single key
                    repo_root / ".env"                        # Priority 5: Root .env
                ]
                
                for idx, key_path in enumerate(api_key_paths, 1):
                    if key_path.exists():
                        try:
                            content = key_path.read_text(encoding="utf-8").strip()
                            
                            # Handle .env format (KEY=value)
                            if key_path.name.endswith('.env'):
                                for line in content.splitlines():
                                    line = line.strip()
                                    if line.startswith("GEMINI_API_KEY="):
                                        extracted_key = line.split("=", 1)[1].strip()
                                        if extracted_key and len(extracted_key) == 39:  # Valid Gemini key length
                                            api_key = extracted_key
                                            print(f"[Gemini] ✓ Found API key in: {key_path.name}")
                                            break
                            
                            # Handle plain text format (key only)
                            else:
                                # For multi-line files, try each line
                                for line in content.splitlines():
                                    line = line.strip()
                                    # Skip comments and check for valid Gemini key format
                                    if line and not line.startswith("#") and len(line) == 39 and line.startswith("AIzaSy"):
                                        api_key = line
                                        print(f"[Gemini] ✓ Found API key in: {key_path.name}")
                                        break  # Use first valid key from this file
                            
                            if api_key:
                                break  # Stop after finding first valid key
                        
                        except Exception as e:
                            print(f"[Gemini] ⚠️  Failed to read {key_path.name}: {e}")
            
            if not api_key:
                print("[Gemini] ❌ No valid GEMINI_API_KEY found")
                print("[Gemini] 📂 Locations checked:")
                print("   - Environment variable: GEMINI_API_KEY")
                print("   - secrets/.env (GEMINI_API_KEY=...)")
                print("   - secrets/api_keys.txt")
                print("   - secrets/api_key.txt")
                print("   - .env (root)")
                print("[Gemini] 💡 Get free API key from: https://makersuite.google.com/app/apikey")
                print("[Gemini] 🔐 Save with cookies_helper.py or manually")
                return None

            genai.configure(api_key=api_key)  # type: ignore[attr-defined]
            model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore[attr-defined]
        except Exception as e:
            print(f"❌ Failed to load Gemini: {e}")
            return None

    # Check if audio already exists (to skip TTS steps)
    audio_path = run_dir / "short_narration.mp3"

    if audio_path.exists():
        _print_progress(2, 7, "Audio exists (skip)", 100)
        # Don't print step 3, just move to step 4
    else:
        # Step 2: Generate script with AI
        _print_progress(2, 7, "AI script", 0)
        script = _generate_short_script(model, book_name, book_type, excerpt, {})
        if not script:
            return None

        # Save script
        script_path = run_dir / "short_script.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        _print_progress(2, 7, "AI script", 100)

        # Step 3: TTS
        _print_progress(3, 7, "TTS", 0)
        if not _tts_to_audio(script, audio_path, run_dir):
            return None

        # Step 4: Trim if > 60s
        _trim_audio_to_60s(audio_path)
        _print_progress(3, 7, "TTS", 100)

    # Step 5: Fetch Pexels videos with varied search queries and duplicate prevention
    output_path = run_dir / "short_final.mp4"  # Final output with captions
    subtitle_json = run_dir / "short_video_subtitle.json"

    # Delete old short if exists (for re-runs)
    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    # Clean up old Pexels clips (for re-runs)
    try:
        for old_clip in run_dir.glob("pexels_clip_*.mp4"):
            old_clip.unlink()
    except Exception:
        pass

    # Get actual audio duration first
    audio_path = run_dir / "short_narration.mp3"
    actual_duration = 60.0  # Default fallback

    _print_progress(3, 7, "Loading audio", 0)

    if audio_path.exists():
        try:
            if MP3:
                audio = MP3(str(audio_path))
                actual_duration = audio.info.length
            elif AudioSegment:
                audio = AudioSegment.from_mp3(str(audio_path))
                actual_duration = len(audio) / 1000.0
        except Exception as e:
            pass  # Use default 60s

    _print_progress(3, 7, f"Audio ({actual_duration:.1f}s)", 100)

    # Fetch Pexels clips based on actual audio duration + book type for smart query selection
    _print_progress(4, 7, "Pexels videos", 0)
    pexels_clips = _fetch_pexels_videos(run_dir, target_duration=actual_duration, book_type=book_type)

    if not pexels_clips:
        print("\r❌ Pexels fetch failed" + " "*40)
        return None

    _print_progress(4, 7, "Pexels videos", 100)

    # Check if we need to generate subtitles
    _print_progress(5, 7, "Subtitles", 0)
    if not subtitle_json.exists():
        script_path = run_dir / "short_script.txt"
        audio_path = run_dir / "short_narration.mp3"

        if script_path.exists() and audio_path.exists():
            try:
                script_text = script_path.read_text(encoding='utf-8')
                subtitle_json = _create_simple_subtitles(script_text, audio_path, subtitle_json)
            except Exception as e:
                print(f"⚠️ Failed to create subtitles: {e}")
                import traceback
                traceback.print_exc()
                subtitle_json = None
        else:
            print("⚠️ Missing script or audio file. Rendering without captions.")
            subtitle_json = None

    _print_progress(5, 7, "Subtitles", 100)

    # Render video from Pexels clips WITH captions in one step
    _print_progress(6, 7, "Rendering", 0)
    if not _render_short_video_from_videos(audio_path, pexels_clips, output_path, subtitle_json):
        print("\r❌ Failed to render short video" + " "*40)
        return None

    _print_progress(6, 7, "Rendering", 100)

    # Get file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)

    # Success message
    GREEN = '\033[92m'
    RESET = '\033[0m'
    print(f"\n{GREEN}✓{RESET} {output_path.name} ({actual_duration:.1f}s, {file_size_mb:.1f}MB)")
    return output_path


def upload_short(
    short_video: Path,
    run_dir: Path,
    title: Optional[str] = None,
    privacy: str = "public"
) -> Optional[str]:
    """
    Upload short to YouTube with main video link in description

    Args:
        short_video: Path to short MP4
        run_dir: Run directory
        title: Optional custom title
        privacy: Privacy status (default: public)

    Returns:
        YouTube video ID or None
    """
    # Load metadata
    titles_json = run_dir / "output.titles.json"
    try:
        with open(titles_json, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load metadata: {e}")
        return None

    book_name = metadata.get("main_title", "Unknown")

    # Get main video URL from database
    main_video_url = _get_book_youtube_url(book_name)

    # Load script for description
    script_path = run_dir / "short_script.txt"
    if not script_path.exists():
        raise FileNotFoundError(
            f"Short script not found: {script_path}. "
            f"Run generate_short() first to create the script."
        )

    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read().strip()

    if not script:
        raise ValueError(
            f"Short script is empty in {script_path}. "
            f"Generate the script properly before uploading."
        )

    # Build description - put link FIRST for clickability
    description = ""
    if main_video_url:
        # Link at the very top (most clickable position)
        description += f"🎬 Full Video:\n{main_video_url}\n\n"

    # Add script content after link
    description += f"{script}\n\n"

    if not main_video_url:
        description += f"📖 Watch Full Summary on our channel\n\n"

    # ==========================================
    # Generate Smart Tags using Gemini AI (REQUIRED - NO FALLBACK)
    # ==========================================
    print("🏷️ Generating optimized tags with AI (hashtags + video_tags)...")

    hashtags = []
    video_tags = []

    try:
        # Load prompt template
        import json as json_lib
        from pathlib import Path
        prompts_file = Path("config/prompts.json")

        if not prompts_file.exists():
            raise FileNotFoundError("config/prompts.json not found")

        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json_lib.load(f)

        # Prepare prompt data
        script_preview = script[:200] if len(script) > 200 else script
        category = metadata.get("playlist", "Self-Development")

        prompt_template = "\n".join(prompts.get("short_tags_template", []))
        prompt = prompt_template.format(
            book_name=book_name,
            author_name=metadata.get("author_name", "Unknown"),
            category=category,
            script_preview=script_preview
        )

        # Call Gemini API
        import os
        import sys
        
        # Suppress STDERR warnings from Google's C++ libraries during import
        _original_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            import google.generativeai as genai
        finally:
            if sys.stderr != _original_stderr:
                sys.stderr.close()
            sys.stderr = _original_stderr

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Try loading from secrets/.env
            env_path = Path("secrets/.env")
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break

        if not api_key:
            raise ValueError(
                "❌ GEMINI_API_KEY not found!\n"
                "Add GEMINI_API_KEY to environment or secrets/.env\n"
                "Short upload requires AI-generated tags (no fallback)."
            )

        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore[attr-defined]

        print("🤖 Calling Gemini API for tags generation...")
        response = model.generate_content(prompt)
        tags_text = response.text.strip()

        # Parse JSON response
        # Remove markdown code blocks if present
        if tags_text.startswith("```"):
            tags_text = tags_text.split("```")[1]
            if tags_text.startswith("json"):
                tags_text = tags_text[4:]
            tags_text = tags_text.strip()

        tags_data = json_lib.loads(tags_text)

        # Extract both arrays
        if isinstance(tags_data, dict):
            hashtags = tags_data.get("hashtags", [])
            video_tags = tags_data.get("video_tags", [])
        else:
            # Old format compatibility (single array)
            hashtags = tags_data
            video_tags = [tag.replace("#", "") for tag in hashtags]

        # ALWAYS add InkEcho as first video tag (channel branding)
        if "InkEcho" not in video_tags:
            video_tags.insert(0, "InkEcho")

        # Validate video_tags length (YouTube limit: 500 chars)
        video_tags_str = ", ".join(video_tags)
        if len(video_tags_str) > 500:
            print(f"⚠️ Video tags too long ({len(video_tags_str)} chars), trimming to 500...")
            # Trim tags to fit 500 char limit
            trimmed_tags = []
            current_length = 0
            for tag in video_tags:
                tag_length = len(tag) + 2  # +2 for ", "
                if current_length + tag_length > 498:  # Leave margin
                    break
                trimmed_tags.append(tag)
                current_length += tag_length
            video_tags = trimmed_tags
            video_tags_str = ", ".join(video_tags)

        print(f"✅ Generated {len(hashtags)} hashtags + {len(video_tags)} video tags")
        print(f"📊 Video tags total: {len(video_tags_str)} chars (limit: 500)")

        # Limit hashtags to best 10 for optimal YouTube Shorts discoverability
        # (YouTube only indexes first 15, but 10 is sweet spot to avoid spam)
        if len(hashtags) > 10:
            print(f"📌 Trimming hashtags from {len(hashtags)} to best 10 for description...")
            hashtags = hashtags[:10]

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: AI tag generation failed!")
        print(f"Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"  1. Check GEMINI_API_KEY is set in secrets/.env")
        print(f"  2. Verify API key is valid")
        print(f"  3. Check internet connection")
        print(f"  4. Review config/prompts.json format")
        print(f"\nShort upload ABORTED (no fallback tags).")
        return None

    # Add hashtags to description (limited to best 10)
    description += " ".join(hashtags)

    # Use youtube_upload module
    from . import youtube_upload

    # Extract hook from script (first sentence)
    hook = script.split('.')[0] if '.' in script else script[:50]
    base_title = title or f"{hook[:40]}... {book_name}"

    # Add hashtags to title (YouTube limit: 100 chars total)
    # Prioritize: #shorts + #BookName (sanitized) + #AuthorName (if space allows)
    hashtag_shorts = " #shorts"

    # Sanitize book name for hashtag (remove spaces, special chars, limit to 20 chars)
    book_hashtag = "#" + "".join(c for c in book_name.replace(" ", "") if c.isalnum())[:20]

    # Calculate remaining space
    title_length = len(base_title)
    hashtags_part = hashtag_shorts + " " + book_hashtag

    # Add author hashtag if space allows (100 - base_title - existing_hashtags - buffer)
    author_name = metadata.get("author_name", "")
    if author_name and (title_length + len(hashtags_part) + 25) < 100:
        author_hashtag = " #" + "".join(c for c in author_name.replace(" ", "") if c.isalnum())[:15]
        hashtags_part += author_hashtag

    # Final title (ensure under 100 chars)
    upload_title = (base_title + hashtags_part)[:100]

    print(f"\n📤 Uploading Short...")
    print(f"Title: {upload_title}")
    print(f"Description preview: {description[:100]}...")
    print(f"📊 Using {len(video_tags)} AI-generated video tags ({len(', '.join(video_tags))} chars)")

    # Use AI-generated video_tags directly (NO old system)
    short_tags = video_tags  # Already optimized by Gemini (40-50 tags, <500 chars)

    # Create temporary titles JSON for short upload
    short_titles_json = run_dir / "short_titles.json"
    short_metadata = {
        "youtube_title": upload_title,
        "youtube_description": description,
        "TAGS": short_tags,  # AI-generated video tags (optimized for 500 char limit)
        "main_title": book_name,
        "author_name": metadata.get("author_name"),
        "is_short": True,  # Flag to force using short_final.mp4
        "video_filename": "short_final.mp4"  # Explicit filename
    }

    try:
        with open(short_titles_json, "w", encoding="utf-8") as f:
            json.dump(short_metadata, f, ensure_ascii=False, indent=2)
        print(f"✓ Created short metadata: {short_titles_json.name}")
    except Exception as e:
        raise IOError(f"Failed to save short metadata to {short_titles_json}: {e}")

    # Get secrets paths
    from pathlib import Path as PathLib
    secrets_dir = PathLib("secrets")
    client_secret = secrets_dir / "client_secret.json"
    token_file = secrets_dir / "token.json"

    # Upload using existing upload_video function
    video_id = youtube_upload.upload_video(
        run_dir=run_dir,
        titles_json=short_titles_json,
        client_secret=client_secret,
        token_file=token_file,
        privacy_status=privacy,
        allow_fallbacks=True,  # Allow finding short_final.mp4
        debug=True
    )

    if not video_id:
        raise RuntimeError(
            f"Failed to upload short video. "
            f"Expected file: short_final.mp4 in {run_dir}. "
            f"Check upload logs above for details."
        )

    print(f"✅ Short uploaded: https://youtube.com/watch?v={video_id}")

    # Save short video ID to metadata (re-read to avoid race conditions)
    try:
        with open(titles_json, "r", encoding="utf-8") as f:
            latest_metadata = json.load(f)
    except Exception as e:
        print(f"⚠️ Warning: Could not re-read metadata, using cached version: {e}")
        latest_metadata = metadata

    # Update only short-related fields
    latest_metadata["short_video_id"] = video_id
    latest_metadata["short_video_url"] = f"https://youtube.com/watch?v={video_id}"

    try:
        with open(titles_json, "w", encoding="utf-8") as f:
            json.dump(latest_metadata, f, ensure_ascii=False, indent=2)
        print(f"✓ Updated metadata with short video info")
    except Exception as e:
        print(f"⚠️ Warning: Failed to update metadata: {e}")

    return video_id


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline.shorts_generator <run_dir>")
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    short_path = generate_short(run_dir)

    if short_path:
        print(f"\n🎉 Success! Short video: {short_path}")
    else:
        print("\n❌ Failed to generate short")
        sys.exit(1)
