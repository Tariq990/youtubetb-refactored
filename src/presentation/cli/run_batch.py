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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

# Import subprocess to call run_pipeline as a command
import subprocess

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


def check_book_status(book_name: str) -> Dict:
    """
    Check book status in database to determine processing strategy.
    
    Args:
        book_name: Book name (may include author separated by |)
    
    Returns:
        {
            "exists": bool,
            "status": "done" | "processing" | "new",
            "book_info": dict or None,
            "action": "skip" | "resume" | "process"
        }
    """
    from src.infrastructure.adapters.database import check_book_exists
    
    # Parse book name (format: "Book Title | Author Name" or just "Book Title")
    parts = [p.strip() for p in book_name.split('|')]
    title = parts[0]
    author = parts[1] if len(parts) > 1 else None
    
    # Check database
    book_info = check_book_exists(title, author)
    
    if not book_info:
        return {
            "exists": False,
            "status": "new",
            "book_info": None,
            "action": "process",
            "title": title,
            "author": author
        }
    
    status = book_info.get("status", "unknown")
    
    if status == "done":
        return {
            "exists": True,
            "status": "done",
            "book_info": book_info,
            "action": "skip",
            "title": title,
            "author": author
        }
    elif status == "processing":
        return {
            "exists": True,
            "status": "processing",
            "book_info": book_info,
            "action": "resume",
            "title": title,
            "author": author
        }
    else:
        return {
            "exists": True,
            "status": status,
            "book_info": book_info,
            "action": "process",
            "title": title,
            "author": author
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
    privacy: str = "public",
    skip_completed: bool = True
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
        privacy: YouTube privacy status (public/unlisted/private)
        skip_completed: Skip books already completed (default: True)

    Returns:
        Dictionary with processing results
    """
    results = {
        "total": len(books),
        "success": [],
        "failed": [],
        "skipped": [],
        "resumed": []
    }

    print("\n" + "="*70)
    print(f"🚀 INTELLIGENT BATCH PROCESSING: {len(books)} books")
    print("="*70)
    
    # Step 0: Ensure database is synced (auto-sync from YouTube if empty)
    _ensure_database_synced()
    
    # Step 1: Analyze all books first
    if console:
        console.print("\n[cyan]📊 Analyzing books status...[/cyan]")
    else:
        print("\n📊 Analyzing books status...")
    
    books_status = []
    for book_name in books:
        status = check_book_status(book_name)
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
    
    # Step 2: Process books
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
                pipeline_input
            ]

            if console:
                if action == "resume":
                    console.print(f"[cyan]♻️  RESUMING from last successful stage...[/cyan]")
                else:
                    console.print(f"[green]🚀 PROCESSING from scratch...[/green]")
            
            print(f"🔧 Running: {' '.join(cmd)}\n")
            result = subprocess.run(cmd, capture_output=False, text=True)

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
                    if console:
                        console.print(f"\n[green]✅ SUCCESS (RESUMED): {title}[/green]")
                    else:
                        print(f"\n✅ SUCCESS (RESUMED): {title}")
                else:
                    results["success"].append(result_entry)
                    if console:
                        console.print(f"\n[green]✅ SUCCESS: {title}[/green]")
                    else:
                        print(f"\n✅ SUCCESS: {title}")
                
                if video_url:
                    print(f"   📺 Main Video: {video_url}")
                if short_url:
                    print(f"   🎬 Short: {short_url}")
                    
            else:
                # ❌ CRITICAL: Pipeline failed after max retries
                results["failed"].append({
                    "book": title,
                    "author": author,
                    "error": f"Pipeline exited with code {result.returncode}"
                })
                
                if console:
                    console.print(f"\n[red]❌ CRITICAL FAILURE: {title}[/red]")
                    console.print(f"[dim]   Exit code: {result.returncode}[/dim]")
                    console.print(f"\n[bold red]🛑 BATCH PIPELINE STOPPED[/bold red]")
                    console.print(f"[yellow]   Pipeline failed after max retries. Not continuing to next book.[/yellow]")
                    console.print(f"[dim]   Fix the error and rerun batch processing to resume.[/dim]\n")
                else:
                    print(f"\n❌ CRITICAL FAILURE: {title} (exit code {result.returncode})")
                    print(f"\n🛑 BATCH PIPELINE STOPPED")
                    print(f"   Pipeline failed after max retries. Not continuing to next book.")
                    print(f"   Fix the error and rerun batch processing to resume.\n")
                
                # Mark remaining books as skipped
                for remaining_book in books[idx:]:
                    results["skipped"].append({
                        "book": remaining_book,
                        "reason": "Previous book failed - batch stopped"
                    })
                break  # ← CRITICAL: Stop immediately, don't continue

        except KeyboardInterrupt:
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
            
            if console:
                console.print(f"\n[red]❌ CRITICAL EXCEPTION: {title}[/red]")
                console.print(f"[dim]   Error: {e}[/dim]")
                console.print(f"\n[bold red]🛑 BATCH PIPELINE STOPPED[/bold red]")
                console.print(f"[yellow]   Unexpected error occurred. Not continuing to next book.[/yellow]")
                console.print(f"[dim]   Fix the error and rerun batch processing to resume.[/dim]\n")
            else:
                print(f"\n❌ CRITICAL EXCEPTION: {title}")
                print(f"   Error: {e}")
                print(f"\n🛑 BATCH PIPELINE STOPPED")
                print(f"   Unexpected error occurred. Not continuing to next book.")
                print(f"   Fix the error and rerun batch processing to resume.\n")
            
            # Mark remaining books as skipped
            for remaining_book in books[idx:]:
                results["skipped"].append({
                    "book": remaining_book,
                    "reason": "Previous book failed - batch stopped"
                })
            break  # ← CRITICAL: Stop immediately, don't continue

        # Small delay between books to avoid rate limits
        if idx < total_books:
            print("\n⏳ Waiting 5 seconds before next book...")
            time.sleep(5)

    # Print final summary
    print_final_summary(results)

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
  
  # Combine options
  python -m src.presentation.cli.run_batch --file books.txt --privacy public
        """
    )

    parser.add_argument(
        "--file",
        type=str,
        default="books.txt",
        help="Path to text file with book names (default: books.txt)"
    )

    parser.add_argument(
        "--privacy",
        type=str,
        choices=["public", "unlisted", "private"],
        default="public",
        help="YouTube video privacy status (default: public)"
    )
    
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Process all books, even if already completed (default: skip completed)"
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
    print(f"🔒 Privacy: {args.privacy}")
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
        privacy=args.privacy,
        skip_completed=not args.no_skip  # Invert the flag
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
