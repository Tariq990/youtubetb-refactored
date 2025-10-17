"""
Batch processing script - Process multiple books from a text file.

Reads book names from books.txt and processes them one by one using run_pipeline.
Handles failures gracefully and continues with the next book.
"""

import sys
from pathlib import Path
from typing import List
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

# Import subprocess to call run_pipeline as a command
import subprocess


def read_books_from_file(file_path: Path) -> List[str]:
    """
    Read book names from text file.

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
    privacy: str = "public"
) -> dict:
    """
    Process multiple books sequentially.

    Args:
        books: List of book names
        privacy: YouTube privacy status (public/unlisted/private)

    Returns:
        Dictionary with processing results
    """
    results = {
        "total": len(books),
        "success": [],
        "failed": [],
        "skipped": []
    }

    print("\n" + "="*70)
    print(f"🚀 BATCH PROCESSING: {len(books)} books")
    print("="*70)

    for idx, book_name in enumerate(books, start=1):
        print(f"\n{'='*70}")
        print(f"📖 Processing Book {idx}/{len(books)}: {book_name}")
        print(f"{'='*70}\n")

        try:
            # Call run_pipeline via subprocess (cleaner than importing)
            cmd = [
                sys.executable, "-m", "src.presentation.cli.run_pipeline",
                book_name
            ]

            # Add privacy flag if not default
            if privacy != "unlisted":
                # Note: run_pipeline uses typer, check actual CLI arguments
                pass

            print(f"🔧 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False, text=True)

            if result.returncode == 0:
                # Success - parse video ID from database
                from src.infrastructure.adapters.database import get_book_info
                book_info = get_book_info(book_name)
                video_id = book_info.get("video_id") if book_info else None

                if video_id:
                    results["success"].append({
                        "book": book_name,
                        "video_id": video_id,
                        "url": f"https://youtube.com/watch?v={video_id}"
                    })
                    print(f"\n✅ SUCCESS: {book_name}")
                    print(f"   Video: https://youtube.com/watch?v={video_id}")
                else:
                    results["failed"].append({
                        "book": book_name,
                        "error": "Video uploaded but ID not found in database"
                    })
                    print(f"\n⚠️ WARNING: {book_name} processed but no video ID found")
            else:
                results["failed"].append({
                    "book": book_name,
                    "error": f"Pipeline exited with code {result.returncode}"
                })
                print(f"\n❌ FAILED: {book_name} (exit code {result.returncode})")

        except KeyboardInterrupt:
            print(f"\n\n⚠️ INTERRUPTED by user at book {idx}/{len(books)}")
            print(f"   Stopping batch processing...")
            results["skipped"] = books[idx:]  # Remaining books
            break

        except Exception as e:
            results["failed"].append({
                "book": book_name,
                "error": str(e)
            })
            print(f"\n❌ FAILED: {book_name}")
            print(f"   Error: {e}")
            print(f"   Continuing with next book...\n")

        # Small delay between books to avoid rate limits
        if idx < len(books):
            print("\n⏳ Waiting 5 seconds before next book...")
            time.sleep(5)

    # Print summary
    print("\n" + "="*70)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"Total books: {results['total']}")
    print(f"✅ Success: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⏭️ Skipped: {len(results['skipped'])}")

    if results["success"]:
        print("\n✅ Successful uploads:")
        for item in results["success"]:
            print(f"   • {item['book']}")
            print(f"     {item['url']}")

    if results["failed"]:
        print("\n❌ Failed books:")
        for item in results["failed"]:
            print(f"   • {item['book']}")
            print(f"     Error: {item['error']}")

    if results["skipped"]:
        print("\n⏭️ Skipped books (interrupted):")
        for book in results["skipped"]:
            print(f"   • {book}")

    print("="*70)

    return results


def main():
    """Main entry point for batch processing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process multiple books from books.txt file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.presentation.cli.run_batch
  python -m src.presentation.cli.run_batch --file my_books.txt
  python -m src.presentation.cli.run_batch --privacy public
  python -m src.presentation.cli.run_batch --enable-scriptify
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

    args = parser.parse_args()

    # Resolve file path
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    print("🎬 YouTube Book Video Pipeline - Batch Mode")
    print(f"📂 Reading from: {file_path}")
    print(f"🔒 Privacy: {args.privacy}")
    print()

    # Read books from file
    books = read_books_from_file(file_path)

    if not books:
        print("\n❌ No books found to process!")
        print(f"   Please add book names to {file_path}")
        print("   Example:")
        print("   الأمير")
        print("   فن الحرب")
        return 1

    # Ask for confirmation
    print(f"\n⚠️ About to process {len(books)} books sequentially.")
    print("   This may take several hours depending on video lengths.")
    response = input("\nContinue? (yes/no): ").strip().lower()

    if response not in ['yes', 'y', 'نعم']:
        print("❌ Cancelled by user")
        return 0

    # Process books
    results = process_books_batch(
        books=books,
        privacy=args.privacy
    )

    # Exit code based on results
    if results["failed"]:
        return 1  # Some failures
    return 0  # All success


if __name__ == "__main__":
    sys.exit(main())
