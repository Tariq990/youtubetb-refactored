"""
Batch processing script - Process multiple books from a text file.

INTELLIGENT BATCH PROCESSING:
- ✅ Skips books already completed (status="done" in database)
- ♻️ Resumes incomplete books (status="processing") from last successful stage
- 🆕 Processes new books from scratch
- 📊 Real-time progress tracking with detailed status

Reads book names from books.txt and processes them intelligently.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import time
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

# Import subprocess to call run_pipeline as a command
import subprocess

# Global flag for auto-continue mode
_BATCH_AUTO_CONTINUE = False

# Rich for beautiful console output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False
    # Dummy classes for type hints
    Table = None
    Panel = None
    box = None


def _load_book_names_cache() -> dict:
    """
    Load book names translation cache from JSON file.
    
    Returns:
        Dictionary with cached translations: {arabic_name: {english, author}}
    """
    cache_file = Path(__file__).resolve().parents[3] / "cache" / "book_names.json"
    
    try:
        if cache_file.exists():
            with cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("books", {})
        else:
            # Create cache directory if it doesn't exist
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            return {}
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️  Could not load cache: {e}[/yellow]")
        else:
            print(f"⚠️ Could not load cache: {e}")
        return {}


def _save_book_names_cache(cache: dict) -> None:
    """
    Save book names translation cache to JSON file.
    
    Args:
        cache: Dictionary with translations to save
    """
    cache_file = Path(__file__).resolve().parents[3] / "cache" / "book_names.json"
    
    try:
        # Ensure directory exists
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with pretty formatting
        data = {
            "_comment": "Cache for Arabic to English book name translations",
            "_description": "Stores translations from Gemini to avoid repeated API calls",
            "books": cache
        }
        
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️  Could not save cache: {e}[/yellow]")
        else:
            print(f"⚠️ Could not save cache: {e}")


def _get_english_book_name(book_name: str, cache: dict) -> tuple:
    """
    Get English book name and author, using cache when available.
    
    Args:
        book_name: Book name in any language (Arabic/English)
        cache: Translation cache dictionary
    
    Returns:
        Tuple of (english_title, author_name)
    """
    import json as _json
    
    # Check if already in cache
    if book_name in cache:
        cached = cache[book_name]
        if console:
            console.print(f"[dim]💾 Cache hit: {book_name} → {cached['english']}[/dim]")
        return cached["english"], cached.get("author")
    
    # Not in cache - need to call Gemini
    if console:
        console.print(f"[cyan]🔍 Translating: {book_name}[/cyan]")
    else:
        print(f"🔍 Translating: {book_name}")
    
    try:
        from src.infrastructure.adapters.process import _configure_model, _get_official_book_name
        
        # Get repo root and config
        repo_root = Path(__file__).resolve().parents[3]
        config_dir = repo_root / "config"
        
        # Load prompts
        prompts = {}
        try:
            prompts_json = config_dir / "prompts.json"
            if prompts_json.exists():
                prompts = _json.loads(prompts_json.read_text(encoding="utf-8"))
        except Exception:
            pass
        
        # Configure Gemini model
        model = _configure_model(config_dir)
        
        if model:
            # Get official English name from Gemini
            english_title, author_name = _get_official_book_name(model, book_name, prompts)
            
            if english_title:
                # Save to cache
                cache[book_name] = {
                    "english": english_title,
                    "author": author_name
                }
                _save_book_names_cache(cache)
                
                if console:
                    console.print(f"[green]✅ Translated: {book_name} → {english_title}[/green]")
                else:
                    print(f"✅ Translated: {book_name} → {english_title}")
                
                return english_title, author_name
            else:
                # Gemini failed - use original name
                if console:
                    console.print(f"[yellow]⚠️  Could not translate, using original: {book_name}[/yellow]")
                return book_name, None
        else:
            # Gemini not configured - use original name
            if console:
                console.print(f"[yellow]⚠️  Gemini not configured, using original: {book_name}[/yellow]")
            return book_name, None
            
    except Exception as e:
        if console:
            console.print(f"[red]❌ Translation error: {e}[/red]")
        else:
            print(f"❌ Translation error: {e}")
        return book_name, None


def _ensure_database_synced() -> bool:
    """
    Ensure database.json is synced with YouTube channel.
    If database is empty, attempts to sync from YouTube automatically.
    
    Returns:
        True if database has data (local or synced), False otherwise
    """
    from src.infrastructure.adapters.database import (
        _load_database, 
        sync_database_from_youtube
    )
    
    db = _load_database()
    
    # If database has books, we're good
    if db.get("books"):
        if console:
            console.print("[dim]✓ Using local database[/dim]")
        else:
            print("✓ Using local database")
        return True
    
    # Database is empty - attempt YouTube sync
    if console:
        console.print("\n[yellow]⚠️  Local database is empty![/yellow]")
        console.print("[cyan]   Attempting to sync from YouTube channel...[/cyan]")
    else:
        print("\n⚠️  Local database is empty!")
        print("   Attempting to sync from YouTube channel...")
    
    try:
        synced = sync_database_from_youtube()
        
        if synced:
            if console:
                console.print("[green]✅ Database synced from YouTube successfully![/green]")
                console.print("[dim]   Duplicate detection is now active.[/dim]\n")
            else:
                print("✅ Database synced from YouTube successfully!")
                print("   Duplicate detection is now active.\n")
            return True
        else:
            if console:
                console.print("[yellow]⚠️  YouTube channel has no videos yet.[/yellow]")
                console.print("[dim]   This is normal for new channels.[/dim]")
                console.print("[dim]   Proceeding with empty database (duplicates won't be detected).[/dim]\n")
            else:
                print("⚠️  YouTube channel has no videos yet.")
                print("   This is normal for new channels.")
                print("   Proceeding with empty database (duplicates won't be detected).\n")
            return False
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️  Sync error: {e}[/yellow]")
            console.print("[dim]   Proceeding with empty database.[/dim]\n")
        else:
            print(f"⚠️  Sync error: {e}")
            print("   Proceeding with empty database.\n")
        return False


def check_book_status(book_name: str, cache: dict) -> Dict:
    """
    Check book status in database to determine processing strategy.
    Uses cache to translate Arabic names to English before checking database.
    
    CRITICAL OPTIMIZATION (v2.3.1):
    - If book is in cache → Check database IMMEDIATELY (no Gemini call)
    - Only call Gemini if NOT in cache or NOT in database
    - Saves API calls for duplicate/completed books
    
    Args:
        book_name: Book name (may include author separated by | or in any language)
        cache: Translation cache dictionary
    
    Returns:
        {
            "exists": bool,
            "status": "done" | "processing" | "new",
            "book_info": dict or None,
            "action": "skip" | "resume" | "process",
            "title": str (English title),
            "author": str,
            "original_input": str (original Arabic/English input)
        }
    """
    from src.infrastructure.adapters.database import check_book_exists
    
    # Store original input
    original_input = book_name
    
    # Parse book name (format: "Book Title | Author Name" or just "Book Title")
    parts = [p.strip() for p in book_name.split('|')]
    input_title = parts[0]
    input_author = parts[1] if len(parts) > 1 else None
    
    # CRITICAL OPTIMIZATION: Check cache first WITHOUT calling Gemini
    if input_title in cache:
        cached_data = cache[input_title]
        english_title = cached_data["english"]
        cached_author = cached_data.get("author")
        author = input_author if input_author else cached_author
        
        if console:
            console.print(f"[dim]💾 Cache hit: {input_title} → {english_title}[/dim]")
        
        # Check database with cached translation (NO Gemini call!)
        book_info = check_book_exists(english_title, author)
        
        if book_info:
            status = book_info.get("status", "unknown")
            
            if status in ["done", "uploaded"]:
                # ✅ Book complete - SKIP (saved Gemini API call!)
                return {
                    "exists": True,
                    "status": "done",
                    "book_info": book_info,
                    "action": "skip",
                    "title": english_title,
                    "author": author,
                    "original_input": original_input
                }
            elif status == "processing":
                # ♻️ Incomplete - RESUME (saved Gemini API call!)
                return {
                    "exists": True,
                    "status": "processing",
                    "book_info": book_info,
                    "action": "resume",
                    "title": english_title,
                    "author": author,
                    "original_input": original_input
                }
            # else: status is unknown/new → continue to get full metadata from Gemini
    
    # NOT in cache OR NOT in database OR status is "new"
    # NOW call Gemini to get full metadata (translation + author)
    english_title, gemini_author = _get_english_book_name(input_title, cache)
    
    # Prefer input author over Gemini author
    author = input_author if input_author else gemini_author
    
    # Check database again with Gemini translation
    book_info = check_book_exists(english_title, author)
    
    if not book_info:
        return {
            "exists": False,
            "status": "new",
            "book_info": None,
            "action": "process",
            "title": english_title,
            "author": author,
            "original_input": original_input
        }
    
    status = book_info.get("status", "unknown")
    
    if status in ["done", "uploaded"]:
        return {
            "exists": True,
            "status": "done",
            "book_info": book_info,
            "action": "skip",
            "title": english_title,
            "author": author,
            "original_input": original_input
        }
    elif status == "processing":
        return {
            "exists": True,
            "status": "processing",
            "book_info": book_info,
            "action": "resume",
            "title": english_title,
            "author": author,
            "original_input": original_input
        }
    else:
        return {
            "exists": True,
            "status": status,
            "book_info": book_info,
            "action": "process",
            "title": english_title,
            "author": author,
            "original_input": original_input
        }


def print_book_status_table(books_status: List[Dict]):
    """Print a beautiful table showing status of all books before processing."""
    if console and RICH_AVAILABLE:
        from rich.table import Table
        from rich import box as rich_box
        
        table = Table(
            title="📚 Batch Processing Plan",
            box=rich_box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("#", style="dim", width=4)
        table.add_column("Book", style="white", width=40)
        table.add_column("Status", width=12)
        table.add_column("Action", width=12)
        table.add_column("Details", style="dim", width=30)
        
        for idx, book_status in enumerate(books_status, 1):
            title = book_status["title"]
            author = book_status.get("author", "Unknown")
            status = book_status["status"]
            action = book_status["action"]
            book_info = book_status.get("book_info")
            
            # Color coding
            if status == "done":
                status_text = "[green]✅ Done[/green]"
                action_text = "[yellow]⏭️ Skip[/yellow]"
                details = book_info.get("youtube_url", "") if book_info else ""
            elif status == "processing":
                status_text = "[yellow]♻️ Incomplete[/yellow]"
                action_text = "[cyan]▶️ Resume[/cyan]"
                details = book_info.get("run_folder", "") if book_info else ""
            else:
                status_text = "[blue]🆕 New[/blue]"
                action_text = "[green]🚀 Process[/green]"
                details = "Fresh start"
            
            book_display = f"{title}"
            if author and author != "Unknown":
                book_display += f"\n[dim]{author}[/dim]"
            
            table.add_row(
                str(idx),
                book_display,
                status_text,
                action_text,
                details
            )
        
        console.print(table)
    else:
        print("\n" + "="*70)
        print("📚 BATCH PROCESSING PLAN")
        print("="*70)
        for idx, book_status in enumerate(books_status, 1):
            title = book_status["title"]
            status = book_status["status"]
            action = book_status["action"]
            print(f"{idx}. {title} | Status: {status} | Action: {action}")
        print("="*70)


def read_books_from_file(file_path: Path) -> List[str]:
    """
    Read book names from text file.

    Format:
        Book Title | Author Name
        or
        Book Title
    
    Lines starting with # are comments (ignored).
    Empty lines are ignored.

    Args:
        file_path: Path to books.txt

    Returns:
        List of book names (one per line, ignoring comments and empty lines)
    """
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return []

    books = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                # Strip whitespace
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Add book name
                books.append(line)
                print(f"📚 Book {len(books)}: {line}")

        print(f"\n✅ Found {len(books)} books in {file_path.name}")
        return books

    except Exception as e:
        print(f"❌ Failed to read {file_path}: {e}")
        return []


def process_books_batch(
    books: List[str],
    skip_completed: bool = True,
    auto_continue: bool = False
) -> dict:
    """
    Process multiple books sequentially with intelligent handling.

    INTELLIGENT FEATURES:
    - Auto-syncs database from YouTube if empty (avoids duplicates)
    - Checks database before processing each book
    - Skips books with status="done" (already uploaded)
    - Resumes books with status="processing" (incomplete)
    - Processes new books from scratch

    Args:
        books: List of book names (format: "Title | Author" or just "Title")
        skip_completed: Skip books already completed (default: True)
        auto_continue: Auto-continue without user prompts (default: False)

    Returns:
        Dictionary with processing results
    """
    # Store auto_continue flag globally for subprocess commands
    global _BATCH_AUTO_CONTINUE
    _BATCH_AUTO_CONTINUE = auto_continue
    
    results = {
        "total": len(books),
        "success": [],
        "failed": [],
        "skipped": [],
        "resumed": []
    }

    # Create batch log file
    batch_log_path = Path.cwd() / "books.txt.log"
    
    def log_batch(message: str):
        """Write to both console and batch log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        try:
            with batch_log_path.open("a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass  # Silently ignore log write errors
    
    # Initialize log file with header
    try:
        with batch_log_path.open("w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write(f"BATCH PROCESSING LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Books: {len(books)}\n")
            f.write("="*70 + "\n\n")
    except Exception:
        pass

    print("\n" + "="*70)
    print(f"🚀 INTELLIGENT BATCH PROCESSING: {len(books)} books")
    print("="*70)
    print(f"📝 Batch log: {batch_log_path}")
    
    log_batch(f"🚀 BATCH STARTED: {len(books)} books")
    
    # Step 0: Validate APIs ONCE at the beginning (not per book)
    if console:
        console.print("\n[cyan]🔐 Validating system & API keys (one-time check)...[/cyan]")
    else:
        print("\n🔐 Validating system & API keys (one-time check)...")
    
    try:
        from src.infrastructure.adapters.api_validator import validate_apis_before_run
        
        if not validate_apis_before_run():
            if console:
                console.print("\n[bold red]❌ System validation failed![/bold red]")
                console.print("[yellow]Fix the issues and try again.[/yellow]")
                console.print("[dim]Hint: Run Option 0 for detailed diagnostics[/dim]\n")
            else:
                print("\n❌ System validation failed!")
                print("Fix the issues and try again.")
                print("Hint: Run Option 0 for detailed diagnostics\n")
            
            log_batch("❌ BATCH ABORTED: API validation failed")
            return {
                "total": len(books),
                "success": [],
                "failed": [],
                "skipped": books,
                "resumed": []
            }
        
        if console:
            console.print("[green]✅ All APIs validated successfully![/green]")
        else:
            print("✅ All APIs validated successfully!")
        
        log_batch("✅ API validation passed")
        
    except Exception as e:
        if console:
            console.print(f"[red]❌ Validation error: {e}[/red]")
        else:
            print(f"❌ Validation error: {e}")
        
        log_batch(f"❌ BATCH ABORTED: Validation error - {e}")
        return {
            "total": len(books),
            "success": [],
            "failed": [],
            "skipped": books,
            "resumed": []
        }
    
    # Step 1: Ensure database is synced (auto-sync from YouTube if empty)
    _ensure_database_synced()
    
    # Step 2: Load book names translation cache
    if console:
        console.print("\n[cyan]💾 Loading translation cache...[/cyan]")
    else:
        print("\n💾 Loading translation cache...")
    
    book_names_cache = _load_book_names_cache()
    cache_size = len(book_names_cache)
    
    if cache_size > 0:
        if console:
            console.print(f"[green]✅ Loaded {cache_size} cached translations[/green]")
        else:
            print(f"✅ Loaded {cache_size} cached translations")
    else:
        if console:
            console.print("[dim]Cache is empty - will translate on first use[/dim]")
        else:
            print("Cache is empty - will translate on first use")
    
    log_batch(f"📝 Cache loaded: {cache_size} translations")
    
    # Step 3: Analyze all books first
    if console:
        console.print("\n[cyan]📊 Analyzing books status...[/cyan]")
    else:
        print("\n📊 Analyzing books status...")
    
    books_status = []
    for book_name in books:
        status = check_book_status(book_name, book_names_cache)
        books_status.append(status)
    
    # Display plan
    print_book_status_table(books_status)
    
    # Calculate statistics
    total_books = len(books_status)
    to_skip = sum(1 for b in books_status if b["action"] == "skip")
    to_resume = sum(1 for b in books_status if b["action"] == "resume")
    to_process = sum(1 for b in books_status if b["action"] == "process")
    
    if console and RICH_AVAILABLE:
        from rich.panel import Panel as RichPanel
        stats_text = (
            f"[cyan]Total:[/cyan] {total_books} books\n"
            f"[yellow]⏭️  Skip (already done):[/yellow] {to_skip}\n"
            f"[cyan]♻️  Resume (incomplete):[/cyan] {to_resume}\n"
            f"[green]🚀 Process (new):[/green] {to_process}"
        )
        console.print(RichPanel(stats_text, title="[bold]Processing Summary[/bold]", border_style="blue"))
    else:
        print(f"\n📊 Summary:")
        print(f"   Total: {total_books}")
        print(f"   Skip: {to_skip}")
        print(f"   Resume: {to_resume}")
        print(f"   Process: {to_process}")
    
    # Step 3: Process books
    for idx, (book_name, book_status) in enumerate(zip(books, books_status), start=1):
        action = book_status["action"]
        title = book_status["title"]
        author = book_status.get("author")
        
        print(f"\n{'='*70}")
        print(f"📖 Book {idx}/{total_books}: {title}")
        if author:
            print(f"   Author: {author}")
        print(f"   Status: {book_status['status']} | Action: {action}")
        print(f"{'='*70}\n")
        
        # Log book start
        log_batch(f"\n{'='*50}")
        log_batch(f"📖 Book {idx}/{total_books}: {title}")
        if author:
            log_batch(f"   Author: {author}")
        log_batch(f"   Status: {book_status['status']} | Action: {action}")
        
        # Handle based on action
        if action == "skip" and skip_completed:
            # Already done - skip
            book_info = book_status["book_info"]
            results["skipped"].append({
                "book": title,
                "author": author,
                "reason": "Already completed",
                "youtube_url": book_info.get("youtube_url", ""),
                "date_added": book_info.get("date_added", "")
            })
            
            log_batch(f"⏭️  SKIPPED: Already completed")
            if book_info.get("youtube_url"):
                log_batch(f"   YouTube: {book_info['youtube_url']}")
            
            if console:
                console.print(f"[yellow]⏭️  SKIPPED: Already completed![/yellow]")
                if book_info.get("youtube_url"):
                    console.print(f"[dim]   YouTube: {book_info['youtube_url']}[/dim]")
            else:
                print(f"⏭️  SKIPPED: Already completed!")
                if book_info.get("youtube_url"):
                    print(f"   YouTube: {book_info['youtube_url']}")
            
            continue
        
        # Process or Resume
        try:
            # Build command for run_pipeline
            # Format: "Title | Author" or just "Title"
            pipeline_input = book_name
            
            cmd = [
                sys.executable, "-m", "src.presentation.cli.run_pipeline",
                pipeline_input,
                "--skip-api-check"  # Skip API check since we already validated once
            ]
            
            # Add auto-continue flag if batch is in auto mode
            if _BATCH_AUTO_CONTINUE:
                cmd.append("--auto-continue")

            if console:
                if action == "resume":
                    console.print(f"[cyan]♻️  RESUMING from last successful stage...[/cyan]")
                    log_batch("♻️  RESUMING from last successful stage...")
                else:
                    console.print(f"[green]🚀 PROCESSING from scratch...[/green]")
                    log_batch("🚀 PROCESSING from scratch...")
            
            print(f"🔧 Running: {' '.join(cmd)}\n")
            
            # Monitor pipeline stages from summary.json
            run_folder = None
            stage_start_time = time.time()
            
            result = subprocess.run(cmd, capture_output=False, text=True)

            # Try to read summary.json to log stages
            try:
                from src.infrastructure.adapters.database import check_book_exists
                updated_info = check_book_exists(title, author)
                if updated_info and updated_info.get("run_folder"):
                    run_folder_name = updated_info["run_folder"]
                    summary_path = Path("runs") / run_folder_name / "summary.json"
                    if summary_path.exists():
                        import json as _json
                        with summary_path.open("r", encoding="utf-8") as f:
                            summary_data = _json.load(f)
                        
                        # Log each stage
                        log_batch("\n   📊 Pipeline Stages:")
                        for stage in summary_data.get("stages", []):
                            stage_name = stage.get("name", "unknown")
                            stage_status = stage.get("status", "unknown")
                            duration = stage.get("duration_sec", 0)
                            
                            if stage_status == "ok":
                                log_batch(f"      ✅ {stage_name.title()}: PASS ({duration:.1f}s)")
                            else:
                                error = stage.get("error", "Unknown error")
                                log_batch(f"      ❌ {stage_name.title()}: FAIL - {error}")
            except Exception:
                pass  # Silently ignore if can't read summary

            if result.returncode == 0:
                # Success - get updated info from database
                from src.infrastructure.adapters.database import check_book_exists
                updated_info = check_book_exists(title, author)
                
                video_url = updated_info.get("youtube_url") if updated_info else None
                short_url = updated_info.get("short_youtube_url") if updated_info else None

                result_entry = {
                    "book": title,
                    "author": author,
                    "youtube_url": video_url,
                    "short_url": short_url
                }
                
                if action == "resume":
                    results["resumed"].append(result_entry)
                    log_batch(f"\n✅ SUCCESS (RESUMED): {title}")
                    if console:
                        console.print(f"\n[green]✅ SUCCESS (RESUMED): {title}[/green]")
                    else:
                        print(f"\n✅ SUCCESS (RESUMED): {title}")
                else:
                    results["success"].append(result_entry)
                    log_batch(f"\n✅ SUCCESS: {title}")
                    if console:
                        console.print(f"\n[green]✅ SUCCESS: {title}[/green]")
                    else:
                        print(f"\n✅ SUCCESS: {title}")
                
                if video_url:
                    print(f"   📺 Main Video: {video_url}")
                    log_batch(f"   📺 Main Video: {video_url}")
                if short_url:
                    print(f"   🎬 Short: {short_url}")
                    log_batch(f"   🎬 Short: {short_url}")
                    
            else:
                # ❌ CRITICAL: Pipeline failed after max retries
                results["failed"].append({
                    "book": title,
                    "author": author,
                    "error": f"Pipeline exited with code {result.returncode}"
                })
                
                log_batch(f"\n❌ FAILURE: {title}")
                log_batch(f"   Exit code: {result.returncode}")
                
                if console:
                    console.print(f"\n[red]❌ FAILURE: {title}[/red]")
                    console.print(f"[dim]   Exit code: {result.returncode}[/dim]")
                else:
                    print(f"\n❌ FAILURE: {title} (exit code {result.returncode})")
                
                # Check if we should continue or stop
                if _BATCH_AUTO_CONTINUE:
                    # Auto mode: Skip failed book and continue to next
                    log_batch("   ⚠️  Auto-continue: Moving to next book...")
                    if console:
                        console.print(f"[yellow]⚠️  Auto-continue mode: Skipping failed book[/yellow]")
                        console.print(f"[cyan]   Moving to next book...[/cyan]\n")
                    else:
                        print(f"⚠️  Auto-continue mode: Skipping failed book")
                        print(f"   Moving to next book...\n")
                    continue  # ← Continue to next book
                else:
                    # Manual mode: Ask user what to do
                    if console:
                        console.print(f"\n[bold yellow]🛑 BOOK FAILED[/bold yellow]")
                        console.print(f"[yellow]   What would you like to do?[/yellow]")
                    else:
                        print(f"\n🛑 BOOK FAILED")
                        print(f"   What would you like to do?")
                    
                    try:
                        choice = input("   Continue to next book? (y/n): ").strip().lower()
                        if choice == 'y':
                            if console:
                                console.print(f"[cyan]   Moving to next book...[/cyan]\n")
                            else:
                                print(f"   Moving to next book...\n")
                            continue  # ← Continue to next book
                        else:
                            if console:
                                console.print(f"\n[bold red]🛑 BATCH PIPELINE STOPPED BY USER[/bold red]")
                                console.print(f"[dim]   Rerun batch processing to resume.[/dim]\n")
                            else:
                                print(f"\n🛑 BATCH PIPELINE STOPPED BY USER")
                                print(f"   Rerun batch processing to resume.\n")
                            
                            # Mark remaining books as skipped
                            for remaining_book in books[idx:]:
                                results["skipped"].append({
                                    "book": remaining_book,
                                    "reason": "User stopped batch after previous failure"
                                })
                            break  # ← Stop batch
                    except (KeyboardInterrupt, EOFError):
                        if console:
                            console.print(f"\n[yellow]⚠️  Stopping batch...[/yellow]\n")
                        else:
                            print(f"\n⚠️  Stopping batch...\n")
                        
                        # Mark remaining books as skipped
                        for remaining_book in books[idx:]:
                            results["skipped"].append({
                                "book": remaining_book,
                                "reason": "User interrupted"
                            })
                        break  # ← Stop batch

        except KeyboardInterrupt:
            log_batch(f"\n⚠️  INTERRUPTED by user at book {idx}/{total_books}")
            if console:
                console.print(f"\n\n[yellow]⚠️  INTERRUPTED by user at book {idx}/{total_books}[/yellow]")
                console.print(f"[yellow]   Stopping batch processing...[/yellow]")
            else:
                print(f"\n\n⚠️ INTERRUPTED by user at book {idx}/{total_books}")
                print(f"   Stopping batch processing...")
            
            # Mark remaining books as skipped
            for remaining_book in books[idx:]:
                results["skipped"].append({
                    "book": remaining_book,
                    "reason": "User interrupted"
                })
            break

        except Exception as e:
            # ❌ CRITICAL: Unexpected exception during pipeline execution
            results["failed"].append({
                "book": title,
                "author": author,
                "error": str(e)
            })
            
            log_batch(f"\n❌ EXCEPTION: {title}")
            log_batch(f"   Error: {str(e)}")
            
            if console:
                console.print(f"\n[red]❌ EXCEPTION: {title}[/red]")
                console.print(f"[dim]   Error: {e}[/dim]")
            else:
                print(f"\n❌ EXCEPTION: {title}")
                print(f"   Error: {e}")
            
            # Check if we should continue or stop
            if _BATCH_AUTO_CONTINUE:
                # Auto mode: Skip failed book and continue to next
                log_batch("   ⚠️  Auto-continue: Moving to next book...")
                if console:
                    console.print(f"[yellow]⚠️  Auto-continue mode: Skipping failed book[/yellow]")
                    console.print(f"[cyan]   Moving to next book...[/cyan]\n")
                else:
                    print(f"⚠️  Auto-continue mode: Skipping failed book")
                    print(f"   Moving to next book...\n")
                continue  # ← Continue to next book
            else:
                # Manual mode: Ask user what to do
                if console:
                    console.print(f"\n[bold yellow]🛑 BOOK FAILED[/bold yellow]")
                    console.print(f"[yellow]   What would you like to do?[/yellow]")
                else:
                    print(f"\n🛑 BOOK FAILED")
                    print(f"   What would you like to do?")
                
                try:
                    choice = input("   Continue to next book? (y/n): ").strip().lower()
                    if choice == 'y':
                        if console:
                            console.print(f"[cyan]   Moving to next book...[/cyan]\n")
                        else:
                            print(f"   Moving to next book...\n")
                        continue  # ← Continue to next book
                    else:
                        if console:
                            console.print(f"\n[bold red]🛑 BATCH PIPELINE STOPPED BY USER[/bold red]")
                            console.print(f"[dim]   Rerun batch processing to resume.[/dim]\n")
                        else:
                            print(f"\n🛑 BATCH PIPELINE STOPPED BY USER")
                            print(f"   Rerun batch processing to resume.\n")
                        
                        # Mark remaining books as skipped
                        for remaining_book in books[idx:]:
                            results["skipped"].append({
                                "book": remaining_book,
                                "reason": "User stopped batch after previous failure"
                            })
                        break  # ← Stop batch
                except (KeyboardInterrupt, EOFError):
                    if console:
                        console.print(f"\n[yellow]⚠️  Stopping batch...[/yellow]\n")
                    else:
                        print(f"\n⚠️  Stopping batch...\n")
                    
                    # Mark remaining books as skipped
                    for remaining_book in books[idx:]:
                        results["skipped"].append({
                            "book": remaining_book,
                            "reason": "User interrupted"
                        })
                    break  # ← Stop batch

        # Small delay between books to avoid rate limits
        if idx < total_books:
            print("\n⏳ Waiting 5 seconds before next book...")
            time.sleep(5)

    # Print final summary
    print_final_summary(results)
    
    # Write final summary to log
    log_batch("\n" + "="*70)
    log_batch("📊 BATCH PROCESSING COMPLETE")
    log_batch("="*70)
    log_batch(f"Total books: {results['total']}")
    log_batch(f"✅ Success (New): {len(results['success'])}")
    log_batch(f"♻️  Success (Resumed): {len(results['resumed'])}")
    log_batch(f"❌ Failed: {len(results['failed'])}")
    log_batch(f"⏭️  Skipped: {len(results['skipped'])}")
    
    if results["success"]:
        log_batch("\n✅ Successfully Processed (New):")
        for item in results["success"]:
            log_batch(f"   • {item['book']}")
            if item.get("youtube_url"):
                log_batch(f"     {item['youtube_url']}")
    
    if results["resumed"]:
        log_batch("\n♻️  Successfully Resumed:")
        for item in results["resumed"]:
            log_batch(f"   • {item['book']}")
            if item.get("youtube_url"):
                log_batch(f"     {item['youtube_url']}")
    
    if results["failed"]:
        log_batch("\n❌ Failed Books:")
        for item in results["failed"]:
            log_batch(f"   • {item['book']}")
            log_batch(f"     Error: {item['error']}")
    
    if results["skipped"]:
        log_batch("\n⏭️  Skipped Books:")
        for item in results["skipped"]:
            log_batch(f"   • {item.get('book', 'Unknown')}")
            log_batch(f"     Reason: {item.get('reason', 'Already completed')}")
    
    log_batch("\n" + "="*70)
    log_batch(f"BATCH ENDED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_batch("="*70 + "\n")

    return results


def print_final_summary(results: Dict):
    """Print beautiful final summary of batch processing."""
    if console and RICH_AVAILABLE:
        from rich.table import Table
        from rich import box as rich_box
        
        # Rich table summary
        table = Table(
            title="📊 BATCH PROCESSING COMPLETE",
            box=rich_box.DOUBLE,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Category", style="bold")
        table.add_column("Count", justify="right", style="cyan")
        table.add_column("Percentage", justify="right")
        
        total = results["total"]
        success_count = len(results["success"])
        resumed_count = len(results["resumed"])
        failed_count = len(results["failed"])
        skipped_count = len(results["skipped"])
        
        table.add_row("Total Books", str(total), "100%")
        table.add_row(
            "[green]✅ Success (New)[/green]",
            str(success_count),
            f"{(success_count/total*100) if total > 0 else 0:.1f}%"
        )
        table.add_row(
            "[cyan]♻️  Success (Resumed)[/cyan]",
            str(resumed_count),
            f"{(resumed_count/total*100) if total > 0 else 0:.1f}%"
        )
        table.add_row(
            "[red]❌ Failed[/red]",
            str(failed_count),
            f"{(failed_count/total*100) if total > 0 else 0:.1f}%"
        )
        table.add_row(
            "[yellow]⏭️  Skipped[/yellow]",
            str(skipped_count),
            f"{(skipped_count/total*100) if total > 0 else 0:.1f}%"
        )
        
        console.print("\n")
        console.print(table)
        
        # Details
        if results["success"]:
            console.print("\n[green]✅ Successfully Processed (New):[/green]")
            for item in results["success"]:
                console.print(f"   • {item['book']}")
                if item.get("youtube_url"):
                    console.print(f"     [dim]{item['youtube_url']}[/dim]")
        
        if results["resumed"]:
            console.print("\n[cyan]♻️  Successfully Resumed:[/cyan]")
            for item in results["resumed"]:
                console.print(f"   • {item['book']}")
                if item.get("youtube_url"):
                    console.print(f"     [dim]{item['youtube_url']}[/dim]")

        if results["failed"]:
            console.print("\n[red]❌ Failed Books:[/red]")
            for item in results["failed"]:
                console.print(f"   • {item['book']}")
                console.print(f"     [dim]Error: {item['error']}[/dim]")

        if results["skipped"]:
            console.print("\n[yellow]⏭️  Skipped Books:[/yellow]")
            for item in results["skipped"]:
                console.print(f"   • {item.get('book', 'Unknown')}")
                reason = item.get("reason", "Already completed")
                console.print(f"     [dim]Reason: {reason}[/dim]")
    else:
        # Plain text summary
        print("\n" + "="*70)
        print("📊 BATCH PROCESSING COMPLETE")
        print("="*70)
        print(f"Total books: {results['total']}")
        print(f"✅ Success (New): {len(results['success'])}")
        print(f"♻️  Success (Resumed): {len(results['resumed'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"⏭️  Skipped: {len(results['skipped'])}")

        if results["success"]:
            print("\n✅ Successfully Processed (New):")
            for item in results["success"]:
                print(f"   • {item['book']}")
                if item.get("youtube_url"):
                    print(f"     {item['youtube_url']}")
        
        if results["resumed"]:
            print("\n♻️  Successfully Resumed:")
            for item in results["resumed"]:
                print(f"   • {item['book']}")
                if item.get("youtube_url"):
                    print(f"     {item['youtube_url']}")

        if results["failed"]:
            print("\n❌ Failed Books:")
            for item in results["failed"]:
                print(f"   • {item['book']}")
                print(f"     Error: {item['error']}")

        if results["skipped"]:
            print("\n⏭️  Skipped Books:")
            for item in results["skipped"]:
                print(f"   • {item.get('book', 'Unknown')}")
                print(f"     Reason: {item.get('reason', 'Already completed')}")

        print("="*70)




def main():
    """Main entry point for intelligent batch processing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🚀 Intelligent Batch Processing - Process multiple books from text file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
INTELLIGENT FEATURES:
  ✅ Automatically skips books already completed (status="done")
  ♻️  Resumes incomplete books from last successful stage
  🆕 Processes new books from scratch
  📊 Real-time status analysis and progress tracking

BOOK FILE FORMAT (books.txt):
  Atomic Habits | James Clear
  The 48 Laws of Power | Robert Greene
  Deep Work | Cal Newport
  
  OR (without author):
  Atomic Habits
  Deep Work
  
  # Lines starting with # are comments (ignored)

EXAMPLES:
  # Process books from default books.txt
  python -m src.presentation.cli.run_batch
  
  # Use custom file
  python -m src.presentation.cli.run_batch --file my_books.txt
  
  # Process all books (including already completed)
  python -m src.presentation.cli.run_batch --no-skip
  
  # Use auto-continue for unattended processing
  python -m src.presentation.cli.run_batch --file books.txt --auto-continue
        """
    )

    parser.add_argument(
        "--file",
        type=str,
        default="books.txt",
        help="Path to text file with book names (default: books.txt)"
    )

    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Process all books, even if already completed (default: skip completed)"
    )
    
    parser.add_argument(
        "--auto-continue",
        action="store_true",
        help="Auto-continue without user prompts (for unattended batch processing)"
    )

    args = parser.parse_args()

    # Resolve file path
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    # Print header
    if console and RICH_AVAILABLE:
        from rich.panel import Panel as RichPanel
        console.print(RichPanel(
            "[bold cyan]🎬 YouTube Book Video Pipeline[/bold cyan]\n"
            "[green]Intelligent Batch Mode[/green]",
            border_style="cyan"
        ))
    else:
        print("\n🎬 YouTube Book Video Pipeline - Intelligent Batch Mode")
    
    print(f"📂 Reading from: {file_path}")
    print(f"⏭️  Skip completed: {not args.no_skip}")
    print()

    # Read books from file
    books = read_books_from_file(file_path)

    if not books:
        if console:
            console.print("\n[red]❌ No books found to process![/red]")
            console.print(f"[yellow]   Please add book names to {file_path}[/yellow]")
            console.print("\n[cyan]Example format:[/cyan]")
            console.print("   Atomic Habits | James Clear")
            console.print("   Deep Work | Cal Newport")
            console.print("   # Comments start with #")
        else:
            print("\n❌ No books found to process!")
            print(f"   Please add book names to {file_path}")
            print("\n   Example:")
            print("   Atomic Habits | James Clear")
            print("   Deep Work | Cal Newport")
        return 1

    # Ask for confirmation
    if console:
        console.print(f"\n[yellow]⚠️  About to process {len(books)} books sequentially.[/yellow]")
        console.print("[dim]   This may take several hours depending on video lengths.[/dim]")
    else:
        print(f"\n⚠️ About to process {len(books)} books sequentially.")
        print("   This may take several hours depending on video lengths.")
    
    if args.auto_continue:
        # Auto mode: skip confirmation
        if console:
            console.print("[dim]🤖 Auto-continue mode: Starting batch without confirmation...[/dim]")
        else:
            print("🤖 Auto-continue mode: Starting batch without confirmation...")
    else:
        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y', 'نعم']:
            if console:
                console.print("[red]❌ Cancelled by user[/red]")
            else:
                print("❌ Cancelled by user")
            return 0

    # Process books with intelligent handling
    results = process_books_batch(
        books=books,
        skip_completed=not args.no_skip,  # Invert the flag
        auto_continue=args.auto_continue
    )

    # Exit code based on results
    total_processed = len(results["success"]) + len(results["resumed"])
    total_failed = len(results["failed"])
    
    if total_failed > 0 and total_processed == 0:
        return 1  # All failed
    elif total_failed > 0:
        return 2  # Some failures
    return 0  # All success


if __name__ == "__main__":
    sys.exit(main())
