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
    repo_root = Path(__file__).resolve().parents[2]
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
    book_lower = book_name.strip().lower()
    author_lower = author_name.strip().lower() if author_name else None

    for book in db.get("books", []):
        title_match = book.get("main_title", "").strip().lower() == book_lower

        # If author provided, check both title and author
        if author_lower:
            author_match = book.get("author_name", "").strip().lower() == author_lower
            if title_match and author_match:
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

    # Find the book
    book_lower = book_name.strip().lower()
    author_lower = author_name.strip().lower() if author_name else None

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


    book_lower = book_name.strip().lower()
    author_lower = author_name.strip().lower() if author_name else None

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

    book_lower = book_name.strip().lower()
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

    book_lower = book_name.strip().lower()
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

    # Find the book
    book_lower = book_name.strip().lower()
    author_lower = author_name.strip().lower() if author_name else None

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
                    book["short_url"] = short_url
                    # Extract short ID
                    import re
                    match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', short_url)
                    if match:
                        book["short_video_id"] = match.group(1)

                updated = True
                break
        elif title_match:
            book["status"] = status
            book["date_updated"] = datetime.now().isoformat(timespec="seconds")

            if youtube_url:
                book["youtube_url"] = youtube_url
            if short_url:
                book["short_url"] = short_url

            updated = True
            break

    if updated and _save_database(db):
        print(f"[Database] ✅ Updated status to '{status}': {book_name}")
        return True

    print(f"[Database] Warning: Book '{book_name}' not found for status update")
    return False


