"""
Database management for tracking processed books.
Prevents duplicate processing and stores YouTube URLs for future use.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import json


def _get_database_path() -> Path:
    """Get the path to database.json in repo root."""
    repo_root = Path(__file__).resolve().parents[3]  # Fixed: parents[3] to reach repo root
    return repo_root / "database.json"


def _load_database() -> Dict:
    """Load database.json or return empty structure if not exists."""
    db_path = _get_database_path()
    if not db_path.exists():
        return {"books": []}

    try:
        return json.loads(db_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Database] Warning: Failed to load database.json: {e}")
        return {"books": []}


def _save_database(data: Dict) -> bool:
    """Save database.json to disk."""
    db_path = _get_database_path()
    try:
        db_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        print(f"[Database] Error: Failed to save database.json: {e}")
        return False


def check_book_exists(book_name: str, author_name: Optional[str] = None) -> Optional[Dict]:
    """
    Check if a book already exists in the database.

    Args:
        book_name: The main title of the book
        author_name: The author name (optional but recommended for accuracy)

    Returns:
        Book entry dict if found, None otherwise
    """
    db = _load_database()

    # Normalize for comparison (case-insensitive, strip whitespace)
    # Use defensive (value or "") to avoid None.strip() crashes
    book_lower = (book_name or "").strip().lower()
    author_lower = (author_name or "").strip().lower() if author_name is not None else None

    for book in db.get("books", []):
        # CRITICAL FIX: Ensure main_title exists and is not None
        db_title = book.get("main_title")
        if not db_title:
            continue  # Skip books with no title
        
        title_match = db_title.strip().lower() == book_lower

        # If author provided, check both title and author
        if author_lower:
            db_author = book.get("author_name")
            # Match if:
            # 1. DB has same author (exact match)
            # 2. DB has no author (null) - match by title only
            if db_author:
                # CRITICAL FIX: Check if db_author is string before strip()
                author_match = str(db_author).strip().lower() == author_lower
                if title_match and author_match:
                    return book
            else:
                # DB author is null, match by title only
                if title_match:
                    return book
        # If no author provided, match by title only
        elif title_match:
            return book

    return None


def add_book(
    book_name: str,
    author_name: Optional[str],
    run_folder: str,
    status: str = "processing",
    playlist: Optional[str] = None
) -> bool:
    """
    Add a new book to the database.

    Args:
        book_name: The main title of the book
        author_name: The author name
        run_folder: The run folder name (e.g., "2025-10-06_16-07-59_Book-Title")
        status: Initial status (default: "processing")
        playlist: YouTube playlist category (optional)

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    # Check if already exists (防止重复添加)
    existing = check_book_exists(book_name, author_name)
    if existing:
        print(f"[Database] Warning: Book '{book_name}' already exists in database")
        return False

    entry = {
        "main_title": book_name,
        "author_name": author_name,
        "date_added": datetime.now().isoformat(timespec="seconds"),
        "run_folder": run_folder,
        "status": status
    }

    # Add playlist if provided
    if playlist:
        entry["playlist"] = playlist

    db["books"].append(entry)

    if _save_database(db):
        print(f"[Database] ✅ Added: {book_name} by {author_name or 'Unknown'}")
        if playlist:
            print(f"[Database]    Playlist: {playlist}")
        return True
    return False


def update_youtube_url(
    book_name: str,
    author_name: Optional[str],
    youtube_url: str,
    youtube_id: Optional[str] = None
) -> bool:
    """
    Update YouTube URL for an existing book after successful upload.

    Args:
        book_name: The main title of the book
        author_name: The author name
        youtube_url: Full YouTube URL (e.g., "https://www.youtube.com/watch?v=...")
        youtube_id: YouTube video ID (optional, extracted from URL if not provided)

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    # Find the book (defensive normalization)
    book_lower = (book_name or "").strip().lower()
    author_lower = (author_name or "").strip().lower() if author_name is not None else None

    for book in db.get("books", []):
        title_match = book.get("main_title", "").strip().lower() == book_lower
        author_match = True
        if author_lower:
            author_match = book.get("author_name", "").strip().lower() == author_lower

        if title_match and author_match:
            # Extract video ID from URL if not provided
            if not youtube_id and "youtube.com/watch?v=" in youtube_url:
                import re
                match = re.search(r"v=([a-zA-Z0-9_-]+)", youtube_url)
                if match:
                    youtube_id = match.group(1)

            # Update the entry
            book["youtube_url"] = youtube_url
            if youtube_id:
                book["youtube_id"] = youtube_id
            book["status"] = "uploaded"
            book["date_uploaded"] = datetime.now().isoformat(timespec="seconds")

            if _save_database(db):
                print(f"[Database] ✅ Updated YouTube URL for: {book_name}")
                return True
            return False

    print(f"[Database] Warning: Book '{book_name}' not found in database")
    return False


def get_all_books(status_filter: Optional[str] = None) -> List[Dict]:
    """
    Get all books from database, optionally filtered by status.

    Args:
        status_filter: Optional status to filter by ("processing", "uploaded", etc.)

    Returns:
        List of book entries
    """
    db = _load_database()
    books = db.get("books", [])

    if status_filter:
        books = [b for b in books if b.get("status") == status_filter]

    return books


def get_book_info(book_name: str, author_name: Optional[str] = None) -> Optional[Dict]:
    """
    Get full information for a specific book.
    Alias for check_book_exists with more descriptive name.
    """
    return check_book_exists(book_name, author_name)


def remove_book(book_name: str, author_name: Optional[str] = None) -> bool:
    """
    Remove a book from the database (use with caution).

    Args:
        book_name: The main title of the book
        author_name: The author name (optional)

    Returns:
        True if removed, False if not found
    """
    db = _load_database()


    book_lower = (book_name or "").strip().lower()
    author_lower = (author_name or "").strip().lower() if author_name is not None else None

    original_count = len(db.get("books", []))

    db["books"] = [
        book for book in db.get("books", [])
        if not (
            book.get("main_title", "").strip().lower() == book_lower
            and (not author_lower or book.get("author_name", "").strip().lower() == author_lower)
        )
    ]

    if len(db["books"]) < original_count:
        if _save_database(db):
            print(f"[Database] ✅ Removed: {book_name}")
            return True

    print(f"[Database] Warning: Book '{book_name}' not found")
    return False


def update_book_youtube_url(book_name: str, youtube_url: str) -> bool:
    """
    Update YouTube URL for a book in the database.
    IMPORTANT: This is for MAIN VIDEO only. Use update_book_short_url() for shorts.

    Args:
        book_name: Main title of the book
        youtube_url: Full YouTube URL (e.g., https://youtube.com/watch?v=abc123)

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    book_lower = (book_name or "").strip().lower()
    updated = False

    for book in db.get("books", []):
        if book.get("main_title", "").strip().lower() == book_lower:
            book["youtube_url"] = youtube_url
            # Extract video ID
            import re
            match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', youtube_url)
            if match:
                book["youtube_video_id"] = match.group(1)
            updated = True
            break

    if updated and _save_database(db):
        print(f"[Database] ✅ Updated YouTube URL for: {book_name}")
        return True

    print(f"[Database] Warning: Book '{book_name}' not found")
    return False


def update_book_short_url(book_name: str, short_url: str) -> bool:
    """
    Update YouTube Short URL for a book in the database.
    This does NOT overwrite the main video URL.

    Args:
        book_name: Main title of the book
        short_url: Full YouTube Short URL (e.g., https://youtube.com/watch?v=xyz789)

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    book_lower = (book_name or "").strip().lower()
    updated = False

    for book in db.get("books", []):
        if book.get("main_title", "").strip().lower() == book_lower:
            book["youtube_short_url"] = short_url
            # Extract video ID
            import re
            match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', short_url)
            if match:
                book["youtube_short_video_id"] = match.group(1)
            book["date_updated"] = datetime.now().isoformat(timespec="seconds")
            updated = True
            break

    if updated and _save_database(db):
        print(f"[Database] ✅ Updated YouTube Short URL for: {book_name}")
        return True

    print(f"[Database] Warning: Book '{book_name}' not found")
    return False


def update_book_status(
    book_name: str,
    author_name: Optional[str],
    status: str,
    youtube_url: Optional[str] = None,
    short_url: Optional[str] = None
) -> bool:
    """
    Update book status in database after pipeline completion.

    Args:
        book_name: The main title of the book
        author_name: The author name
        status: New status ("processing", "done", "failed")
        youtube_url: Main video URL (optional)
        short_url: Short video URL (optional)

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    # Find the book (defensive normalization)
    book_lower = (book_name or "").strip().lower()
    author_lower = (author_name or "").strip().lower() if author_name is not None else None

    updated = False
    for book in db.get("books", []):
        title_match = book.get("main_title", "").strip().lower() == book_lower

        if author_lower:
            author_match = book.get("author_name", "").strip().lower() == author_lower
            if title_match and author_match:
                book["status"] = status
                book["date_updated"] = datetime.now().isoformat(timespec="seconds")

                # Update URLs if provided
                if youtube_url:
                    book["youtube_url"] = youtube_url
                    # Extract video ID
                    import re
                    match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', youtube_url)
                    if match:
                        book["youtube_video_id"] = match.group(1)

                if short_url:
                    book["youtube_short_url"] = short_url
                    # Extract short ID
                    import re
                    match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', short_url)
                    if match:
                        book["youtube_short_video_id"] = match.group(1)

                updated = True
                break
        elif title_match:
            book["status"] = status
            book["date_updated"] = datetime.now().isoformat(timespec="seconds")

            if youtube_url:
                book["youtube_url"] = youtube_url
            if short_url:
                book["youtube_short_url"] = short_url

            updated = True
            break

    if updated and _save_database(db):
        print(f"[Database] ✅ Updated status to '{status}': {book_name}")
        return True

    print(f"[Database] Warning: Book '{book_name}' not found for status update")
    return False


def update_book_run_folder(
    book_name: str,
    author_name: Optional[str],
    new_run_folder: str
) -> bool:
    """
    Update the run_folder name for a book in the database.
    Used when renaming folders after getting book metadata.

    Args:
        book_name: The main title of the book
        author_name: The author name
        new_run_folder: New folder name (e.g., "2025-10-23_12-34-56_Book-Name")

    Returns:
        True if successful, False otherwise
    """
    db = _load_database()

    # Find the book (defensive normalization)
    book_lower = (book_name or "").strip().lower()
    author_lower = (author_name or "").strip().lower() if author_name is not None else None

    updated = False
    for book in db.get("books", []):
        title_match = book.get("main_title", "").strip().lower() == book_lower

        if author_lower:
            author_match = book.get("author_name", "").strip().lower() == author_lower
            if title_match and author_match:
                book["run_folder"] = new_run_folder
                book["date_updated"] = datetime.now().isoformat(timespec="seconds")
                updated = True
                break
        elif title_match:
            book["run_folder"] = new_run_folder
            book["date_updated"] = datetime.now().isoformat(timespec="seconds")
            updated = True
            break

    if updated and _save_database(db):
        print(f"[Database] ✅ Updated run_folder to '{new_run_folder}': {book_name}")
        return True

    print(f"[Database] Warning: Book '{book_name}' not found for run_folder update")
    return False


# ============================================================================
# YouTube Channel Sync - NEW SYSTEM
# ============================================================================
# استخلاص أسماء الكتب من قناة اليوتيوب لمزامنة database.json
# يحل مشكلة فقدان البيانات عند التبديل بين البيئات (Local/Colab)
# راجع: docs/DUPLICATE_CHECK_SYSTEM.md للتفاصيل الكاملة
# ============================================================================

import re
import os


def extract_book_from_youtube_title(title: str) -> Optional[str]:
    """
    استخلاص اسم الكتاب من عنوان فيديو YouTube.
    
    الصيغة المتوقعة: "[مقدمة] – [اسم الكتاب] | Book Summary"
    
    أمثلة:
        "How To FINALLY Break Free – Atomic Habits | Book Summary"
        → "Atomic Habits"
        
        "Master Your Money – Rich Dad Poor Dad | Book Summary"
        → "Rich Dad Poor Dad"
    
    Args:
        title: عنوان الفيديو من YouTube
        
    Returns:
        اسم الكتاب أو None إذا لم يتم العثور على تطابق
    """
    if not title:
        return None
    
    # Pattern 1: "– Book Name | Book Summary" (الصيغة الأساسية)
    pattern1 = r'–\s*(.+?)\s*\|\s*Book Summary'
    match = re.search(pattern1, title, re.IGNORECASE)
    if match:
        book_name = match.group(1).strip()
        # تنظيف: إزالة emoji و أحرف خاصة زائدة
        book_name = re.sub(r'[🎯💡🔥✨]+', '', book_name).strip()
        return book_name
    
    # Pattern 2: "– Book Name" (fallback بدون "| Book Summary")
    pattern2 = r'–\s*(.+?)$'
    match = re.search(pattern2, title)
    if match:
        candidate = match.group(1).strip()
        candidate = re.sub(r'[🎯💡🔥✨]+', '', candidate).strip()
        # تأكد أنه ليس جملة طويلة (أسماء الكتب عادة < 10 كلمات)
        if len(candidate.split()) <= 10:
            return candidate
    
    return None


def _get_youtube_api_key() -> Optional[str]:
    """الحصول على YouTube API key من البيئة أو secrets."""
    # جرّب من environment variables أولاً
    api_key = os.environ.get("YT_API_KEY") or os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # جرّب من secrets folder
    repo_root = Path(__file__).resolve().parents[3]  # adapters → infrastructure → src → root
    for f in (repo_root / "secrets" / "api_key.txt", repo_root / "api_key.txt"):
        if f.exists():
            try:
                return f.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    
    return None


def _get_channel_id_from_config() -> Optional[str]:
    """الحصول على Channel ID من config/settings.json"""
    try:
        repo_root = Path(__file__).resolve().parents[3]  # adapters → infrastructure → src → root
        config_path = repo_root / "config" / "settings.json"
        
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            
            # دعم الصيغتين: القديمة والجديدة
            if "youtube_sync" in config:
                return config["youtube_sync"].get("channel_id")
            return config.get("youtube_channel_id")
    except Exception:
        pass
    
    return None


def _is_youtube_sync_enabled() -> bool:
    """فحص إذا الـ YouTube sync مفعّل في الإعدادات."""
    try:
        repo_root = Path(__file__).resolve().parents[3]  # adapters → infrastructure → src → root
        config_path = repo_root / "config" / "settings.json"
        
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            
            if "youtube_sync" in config:
                return config["youtube_sync"].get("enabled", True)
            
            # افتراضياً: مفعّل
            return True
        else:
            # الملف غير موجود: مفعّل افتراضياً
            return True
    except Exception:
        # خطأ في القراءة: مفعّل افتراضياً
        return True


def sync_database_from_youtube(channel_id: Optional[str] = None) -> bool:
    """
    مزامنة database.json من فيديوهات قناة YouTube.
    
    يجلب جميع الفيديوهات من القناة، يستخلص أسماء الكتب من العناوين،
    ويبني database.json بناءً على ذلك.
    
    Args:
        channel_id: معرّف قناة YouTube (اختياري، يستخدم الإعدادات إذا لم يُحدد)
        
    Returns:
        True إذا نجحت المزامنة، False إذا فشلت
    """
    # فحص إذا الـ sync مفعّل
    if not _is_youtube_sync_enabled():
        print("[Sync] ⏭️  YouTube sync disabled in settings")
        return False
    
    print("\n" + "="*60)
    print("🔄 SYNCING DATABASE FROM YOUTUBE CHANNEL")
    print("="*60 + "\n")
    
    # 1. الحصول على API key
    api_key = _get_youtube_api_key()
    if not api_key:
        print("[Sync] ❌ YouTube API key not found")
        print("[Sync]    Set YOUTUBE_API_KEY env or add secrets/api_key.txt")
        print("[Sync]    Or add YT_API_KEY to .env file")
        print("[Sync]    Database will remain empty - manual entry required")
        return False
    
    # 2. الحصول على Channel ID
    if not channel_id:
        channel_id = _get_channel_id_from_config()
    
    if not channel_id:
        print("[Sync] ❌ Channel ID not configured")
        print("[Sync]    Add 'youtube_channel_id' to config/settings.json under 'youtube_sync' section")
        print("[Sync]    Example:")
        print('[Sync]      "youtube_sync": {')
        print('[Sync]        "enabled": true,')
        print('[Sync]        "channel_id": "YOUR_CHANNEL_ID_HERE"')
        print('[Sync]      }')
        return False
    
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("[Sync] ❌ google-api-python-client not installed")
        print("[Sync]    Run: pip install google-api-python-client")
        return False
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 3. الحصول على uploads playlist ID
        print("[Sync] 📡 Fetching channel information...")
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            print(f"[Sync] ❌ Channel not found: {channel_id}")
            return False
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # 4. جلب جميع الفيديوهات (مع pagination)
        print("[Sync] 📥 Fetching videos...")
        videos = []
        next_page_token = None
        page_num = 0

        from googleapiclient.errors import HttpError
        try:
            # Primary approach: use the uploads playlist
            while True:
                page_num += 1
                response = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()

                for item in response.get('items', []):
                    videos.append({
                        'title': item['snippet']['title'],
                        'video_id': item['snippet']['resourceId']['videoId'],
                        'published_at': item['snippet']['publishedAt']
                    })

                print(f"[Sync]    Page {page_num}: {len(response.get('items', []))} videos")

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
        except HttpError as e:
            # Handle missing/invalid playlist (404 playlistNotFound)
            # Don't print the ugly error - will show friendly message later
            
            # Fallback 1: try deriving the uploads playlist id from channel id (existing heuristic)
            try:
                if channel_id and channel_id.startswith('UC'):
                    derived_uploads = 'UU' + channel_id[2:]
                    if derived_uploads != uploads_playlist_id:
                        print(f"[Sync] 🔁 Attempting fallback uploads playlist id: {derived_uploads}")
                        uploads_playlist_id = derived_uploads
                        # Try a single page to validate
                        resp = youtube.playlistItems().list(part='snippet', playlistId=uploads_playlist_id, maxResults=5).execute()
                        if resp.get('items'):
                            next_page_token = resp.get('nextPageToken')
                            for item in resp.get('items', []):
                                videos.append({
                                    'title': item['snippet']['title'],
                                    'video_id': item['snippet']['resourceId']['videoId'],
                                    'published_at': item['snippet']['publishedAt']
                                })
                            print(f"[Sync]    Fallback seed: {len(resp.get('items', []))} videos")
                            # continue paginating using uploads_playlist_id
                            while True:
                                page_num += 1
                                resp = youtube.playlistItems().list(part='snippet', playlistId=uploads_playlist_id, maxResults=50, pageToken=next_page_token).execute()
                                for item in resp.get('items', []):
                                    videos.append({
                                        'title': item['snippet']['title'],
                                        'video_id': item['snippet']['resourceId']['videoId'],
                                        'published_at': item['snippet']['publishedAt']
                                    })
                                print(f"[Sync]    Page {page_num}: {len(resp.get('items', []))} videos")
                                next_page_token = resp.get('nextPageToken')
                                if not next_page_token:
                                    break
                        else:
                            print("[Sync] ❌ Fallback playlist also returned no items")
                    # If derived uploads is same or no items, fall through to search-based fallback
            except Exception as fallback_err:
                print(f"[Sync] ❌ Fallback attempt failed: {fallback_err}")

            # Fallback 2: use search.list by channelId to fetch videos directly (more robust)
            try:
                # Silent fallback - only show results
                next_page_token = None
                # Reset page counter for search pages
                search_page = 0
                while True:
                    search_page += 1
                    resp = youtube.search().list(
                        part='snippet',
                        channelId=channel_id,
                        maxResults=50,
                        order='date',
                        pageToken=next_page_token,
                        type='video'
                    ).execute()

                    items = resp.get('items', [])
                    for item in items:
                        videos.append({
                            'title': item['snippet']['title'],
                            'video_id': item['id']['videoId'],
                            'published_at': item['snippet']['publishedAt']
                        })

                    # Only show count if videos found
                    if len(items) > 0:
                        print(f"[Sync]    Found {len(items)} videos")

                    next_page_token = resp.get('nextPageToken')
                    if not next_page_token:
                        break

                if not videos:
                    print("[Sync] ⚠️  Channel has no public videos yet")
                    print("[Sync]    This is normal for new channels")
                    print("[Sync]    Database will remain empty until first video is uploaded")
                    return False
            except Exception as search_err:
                print(f"[Sync] ❌ Search-based fallback failed: {search_err}")
                return False
        
        # Check if any videos were found
        if not videos:
            print("[Sync] ⚠️  No videos found on channel")
            print("[Sync]    Channel may be new or all videos are private/unlisted")
            print("[Sync]    Database will remain empty - this is OK for new channels")
            return False
        
        print(f"[Sync] ✅ Found {len(videos)} total videos\n")
        
        # 5. استخلاص أسماء الكتب وبناء database
        print("[Sync] 📖 Extracting book names...")
        db = {"books": []}
        processed_books = set()  # لتجنب التكرار
        skipped = 0
        duplicates = 0
        
        for video in videos:
            # استخلاص اسم الكتاب
            book_name = extract_book_from_youtube_title(video['title'])
            
            if not book_name:
                print(f"[Sync] ⏭️  No match: {video['title'][:60]}...")
                skipped += 1
                continue
            
            # تجنب التكرار (case-insensitive)
            book_lower = book_name.lower()
            if book_lower in processed_books:
                print(f"[Sync] ⏭️  Duplicate: {book_name}")
                duplicates += 1
                continue
            
            processed_books.add(book_lower)
            
            # إضافة إلى database
            entry = {
                "main_title": book_name,
                "author_name": None,  # يمكن استخلاصه لاحقاً
                "date_added": video['published_at'],
                "status": "uploaded",
                "youtube_video_id": video['video_id'],
                "youtube_url": f"https://www.youtube.com/watch?v={video['video_id']}",
                "youtube_title": video['title'],  # حفظ العنوان الأصلي
                "source": "youtube_sync"
            }
            
            db["books"].append(entry)
            print(f"[Sync] ✅ Added: {book_name}")
        
        # 6. حفظ database
        if _save_database(db):
            print(f"\n{'='*60}")
            print(f"✅ DATABASE SYNCED SUCCESSFULLY!")
            print(f"   Total books: {len(db['books'])}")
            print(f"   Skipped: {skipped}")
            print(f"   Duplicates: {duplicates}")
            print(f"{'='*60}\n")
            return True
        else:
            print(f"\n❌ Failed to save database")
            return False
            
    except ImportError:
        print("[Sync] ❌ google-api-python-client not installed")
        print("[Sync]    Install with: pip install google-api-python-client")
        return False
    except Exception as e:
        print(f"[Sync] ❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_database_synced() -> bool:
    """
    التأكد من أن database.json محدّث.
    
    الاستراتيجية:
    1. فحص database.json المحلي
    2. إذا كان فارغاً → محاولة sync من YouTube
    3. إذا فشل الـ sync → الاستمرار بـ database فارغ
    
    Returns:
        True إذا database جاهز (محلي أو من YouTube)
        False إذا database فارغ ولم ينجح الـ sync
    """
    db = _load_database()
    
    # إذا في بيانات محلية
    if db.get("books"):
        print("[Database] ✅ Using local database ({} books)".format(len(db["books"])))
        return True
    
    # database فارغ → محاولة sync
    print("\n" + "="*60)
    print("⚠️  LOCAL DATABASE EMPTY!")
    print("   Attempting to sync from YouTube channel...")
    print("="*60 + "\n")
    
    synced = sync_database_from_youtube()
    
    if synced:
        print("[Database] ✅ Database restored from YouTube!")
        return True
    else:
        print("[Database] ⚠️  Sync failed. Proceeding with empty database.")
        print("[Database]     (Duplicate detection will not work)")
        return False


# ============================================================================
# CLI Entry Point للاختبار
# ============================================================================

def main():
    """نقطة دخول CLI لاختبار الـ sync."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        print("🚀 Manual YouTube Sync\n")
        success = sync_database_from_youtube()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python -m src.infrastructure.adapters.database sync")
        sys.exit(1)


if __name__ == "__main__":
    main()



