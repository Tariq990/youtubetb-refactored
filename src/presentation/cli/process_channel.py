"""
Process all videos from a YouTube channel.

Extracts all videos from a channel and processes them one by one.
Skips videos already processed and handles failures gracefully.
Tracks progress to enable automatic resume after interruption.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from src.presentation.cli.channel_progress import ChannelProgressTracker
from src.infrastructure.adapters.api_validator import validate_apis_before_run

console = Console()


def get_channel_videos(channel_url: str, min_duration: int = 15, max_duration: int = 120) -> List[Dict]:
    """
    Extract all videos from a YouTube channel.

    Args:
        channel_url: YouTube channel URL (e.g., https://youtube.com/@ChannelName)
        min_duration: Minimum video duration in minutes
        max_duration: Maximum video duration in minutes

    Returns:
        List of video metadata dictionaries
    """
    try:
        import yt_dlp
    except ImportError:
        console.print("[red]❌ yt-dlp not installed. Run: pip install yt-dlp[/red]")
        return []

    console.print(f"[cyan]🔍 Fetching videos from channel...[/cyan]")
    console.print(f"[cyan]   Channel: {channel_url}[/cyan]")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Don't download, just get metadata
        'playlistend': 1000,   # Limit to first 1000 videos
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            # Extract channel info
            info = ydl.extract_info(channel_url, download=False)

            if not info:
                console.print("[red]❌ Failed to extract channel info[/red]")
                return []

            # Get all video entries
            entries = info.get('entries', [])
            console.print(f"[green]✅ Found {len(entries)} videos in channel[/green]")

            # Filter and process videos
            min_seconds = min_duration * 60
            max_seconds = max_duration * 60

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get('id')
                title = entry.get('title', 'Unknown')
                duration = entry.get('duration', 0)
                url = f"https://www.youtube.com/watch?v={video_id}"

                # Filter by duration
                if duration < min_seconds or duration > max_seconds:
                    continue

                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'url': url,
                    'duration': duration,
                    'duration_min': duration / 60
                })

            console.print(f"[green]✅ Filtered to {len(videos)} videos ({min_duration}-{max_duration} min)[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error fetching channel videos: {e}[/red]")
        return []

    return videos


def check_if_processed(video_url: str) -> bool:
    """
    Check if video URL has already been processed.

    Args:
        video_url: YouTube video URL

    Returns:
        True if video already processed
    """
    database_file = Path("database.json")
    if not database_file.exists():
        return False

    try:
        with database_file.open("r", encoding="utf-8") as f:
            db = json.load(f)

        books = db.get("books", [])
        for book in books:
            # Check both source_url (old format) and youtube_url (new format)
            source_url = book.get("source_url", "")
            youtube_url = book.get("youtube_url", "")

            if source_url == video_url or youtube_url == video_url:
                status = book.get("status", "unknown")
                if status == "done":
                    return True
        return False

    except Exception:
        return False


def process_channel_videos(
    videos: List[Dict],
    channel_url: str,
    privacy: str = "public",
    dry_run: bool = False,
    resume: bool = True
) -> Dict:
    """
    Process all videos from a channel sequentially.

    Args:
        videos: List of video metadata dictionaries
        channel_url: YouTube channel URL (for progress tracking)
        privacy: YouTube privacy status
        dry_run: If True, only show what would be processed without processing
        resume: If True, resume from last progress (default)

    Returns:
        Dictionary with processing results
    """
    # Initialize progress tracker
    tracker = ChannelProgressTracker(channel_url)

    # Check if resuming from previous run
    if resume and tracker.data.get("total_videos", 0) > 0:
        console.print("\n[yellow]📋 Found previous progress![/yellow]")
        console.print(tracker.get_progress_summary())

        response = Prompt.ask("\nResume from last progress?", choices=["yes", "no"], default="yes")
        if response == "yes":
            # Get only pending/failed videos
            pending = tracker.get_pending_videos()
            console.print(f"\n[cyan]Resuming: {len(pending)} videos remaining[/cyan]")

            # Filter videos to only pending ones
            pending_urls = {v["url"] for v in pending}
            videos = [v for v in videos if v["url"] in pending_urls]
        else:
            # Start fresh
            tracker.clear()
            tracker.initialize_videos(videos)
    else:
        # First run - initialize tracker
        tracker.initialize_videos(videos)

    results = {
        "total": len(videos),
        "success": [],
        "failed": [],
        "skipped": []
    }

    console.rule("[bold]📺 Channel Processing")
    console.print(f"\n[cyan]Total videos: {len(videos)}[/cyan]")

    if dry_run:
        console.print("\n[yellow]🔍 DRY RUN MODE - No videos will be processed[/yellow]\n")

    for idx, video in enumerate(videos, start=1):
        video_url = video['url']
        title = video['title']
        duration_min = video['duration_min']

        console.print(f"\n{'='*70}")
        console.print(f"📹 Video {idx}/{len(videos)}")
        console.print(f"   Title: {title}")
        console.print(f"   URL: {video_url}")
        console.print(f"   Duration: {duration_min:.1f} min")
        console.print(f"{'='*70}\n")

        # Check if already processed
        if check_if_processed(video_url):
            console.print(f"[green]✅ Already processed - Skipping[/green]")
            tracker.mark_skipped(video_url, "Already processed")
            results["skipped"].append({
                "video": title,
                "url": video_url,
                "reason": "Already processed"
            })
            continue

        if dry_run:
            console.print(f"[yellow]Would process: {title}[/yellow]")
            continue

        # Mark as processing
        tracker.mark_processing(video_url)

        # Process video using direct URL transcription
        try:
            cmd = [
                sys.executable, "-m", "src.presentation.cli.process_direct_video",
                video_url
            ]

            console.print(f"🔧 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False, text=True)

            if result.returncode == 0:
                tracker.mark_success(video_url)
                results["success"].append({
                    "video": title,
                    "url": video_url
                })
                console.print(f"\n[green]✅ SUCCESS: {title}[/green]")
            else:
                error_msg = f"Exit code {result.returncode}"
                tracker.mark_failed(video_url, error_msg)
                results["failed"].append({
                    "video": title,
                    "url": video_url,
                    "error": error_msg
                })
                console.print(f"\n[red]❌ FAILED: {title}[/red]")

        except KeyboardInterrupt:
            console.print(f"\n\n[yellow]⚠️ INTERRUPTED by user at video {idx}/{len(videos)}[/yellow]")
            console.print("[cyan]💾 Progress saved! You can resume later with the same command.[/cyan]")
            console.print(tracker.get_progress_summary())
            results["skipped"] = [
                {"video": v['title'], "url": v['url'], "reason": "Interrupted"}
                for v in videos[idx:]
            ]
            break

        except Exception as e:
            error_msg = str(e)
            tracker.mark_failed(video_url, error_msg)
            results["failed"].append({
                "video": title,
                "url": video_url,
                "error": error_msg
            })
            console.print(f"\n[red]❌ FAILED: {title}[/red]")
            console.print(f"[red]   Error: {e}[/red]")

    # Print summary
    console.rule("[bold]📊 Summary")
    console.print(tracker.get_progress_summary())
    console.print(f"[red]❌ Failed: {len(results['failed'])}[/red]")
    console.print(f"[yellow]⏭️ Skipped: {len(results['skipped'])}[/yellow]")

    if results["success"]:
        console.print("\n[green]✅ Successful videos:[/green]")
        for item in results["success"]:
            console.print(f"   • {item['video']}")

    if results["failed"]:
        console.print("\n[red]❌ Failed videos:[/red]")
        for item in results["failed"]:
            console.print(f"   • {item['video']}")
            console.print(f"     Error: {item['error']}")

    if results["skipped"]:
        console.print("\n[yellow]⏭️ Skipped videos:[/yellow]")
        for item in results["skipped"]:
            console.print(f"   • {item['video']} ({item.get('reason', 'Unknown')})")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process all videos from a YouTube channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.presentation.cli.process_channel "https://youtube.com/@ChannelName"
  python -m src.presentation.cli.process_channel "https://youtube.com/@ChannelName" --dry-run
  python -m src.presentation.cli.process_channel "https://youtube.com/@ChannelName" --min 20 --max 60
  python -m src.presentation.cli.process_channel "https://youtube.com/@ChannelName" --privacy unlisted
        """
    )

    parser.add_argument(
        "channel_url",
        type=str,
        help="YouTube channel URL (e.g., https://youtube.com/@ChannelName)"
    )

    parser.add_argument(
        "--min",
        type=int,
        default=15,
        help="Minimum video duration in minutes (default: 15)"
    )

    parser.add_argument(
        "--max",
        type=int,
        default=120,
        help="Maximum video duration in minutes (default: 120)"
    )

    parser.add_argument(
        "--privacy",
        type=str,
        choices=["public", "unlisted", "private"],
        default="public",
        help="YouTube privacy status (default: public)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing"
    )

    parser.add_argument(
        "--skip-api-check",
        action="store_true",
        help="Skip API validation (NOT RECOMMENDED)"
    )

    args = parser.parse_args()

    console.clear()
    console.rule("[bold cyan]📺 YouTube Channel Processor")

    # 🔒 CRITICAL: Validate all APIs before processing channel
    if not args.dry_run and not args.skip_api_check:
        console.print("\n[bold cyan]🔐 Step 0: API Validation[/bold cyan]")
        if not validate_apis_before_run():
            console.print("\n[bold red]❌ CHANNEL PROCESSING ABORTED: API validation failed![/bold red]")
            console.print("[yellow]Fix the API issues above and try again.[/yellow]")
            console.print("[dim]Hint: Check your secrets/.env file and API console quotas[/dim]\n")
            return 1
        console.print("[green]✅ All APIs validated successfully![/green]\n")
    elif args.skip_api_check:
        console.print("[yellow]⚠️ WARNING: API validation skipped (--skip-api-check)[/yellow]\n")

    console.print(f"\n[cyan]Channel: {args.channel_url}[/cyan]")
    console.print(f"[cyan]Duration filter: {args.min}-{args.max} minutes[/cyan]")
    console.print(f"[cyan]Privacy: {args.privacy}[/cyan]")
    if args.dry_run:
        console.print("[yellow]Mode: DRY RUN (no processing)[/yellow]")
    console.print()

    # Get channel videos
    videos = get_channel_videos(
        channel_url=args.channel_url,
        min_duration=args.min,
        max_duration=args.max
    )

    if not videos:
        console.print("\n[red]❌ No videos found matching criteria[/red]")
        return 1

    # Show preview
    table = Table(title="Videos to Process", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="white")
    table.add_column("Duration", justify="right", style="green")

    for idx, video in enumerate(videos[:20], start=1):  # Show first 20
        table.add_row(
            str(idx),
            video['title'][:60] + "..." if len(video['title']) > 60 else video['title'],
            f"{video['duration_min']:.1f} min"
        )

    console.print(table)

    if len(videos) > 20:
        console.print(f"\n[yellow]... and {len(videos) - 20} more videos[/yellow]")

    # Confirm
    if not args.dry_run:
        console.print(f"\n[yellow]⚠️ About to process {len(videos)} videos sequentially.[/yellow]")
        console.print("[yellow]   This may take several hours![/yellow]")

        response = Prompt.ask("\nContinue?", choices=["yes", "no"], default="no")
        if response != "yes":
            console.print("[red]Cancelled[/red]")
            return 0

    # Process videos
    results = process_channel_videos(
        videos=videos,
        channel_url=args.channel_url,
        privacy=args.privacy,
        dry_run=args.dry_run
    )

    # Exit code
    if results["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
