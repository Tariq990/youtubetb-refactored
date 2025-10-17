"""
Process a single YouTube video directly by URL.

Skips the search stage and uses the provided video URL directly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

from src.presentation.cli.run_pipeline import run as pipeline_run


def main():
    """
    Process a single video by URL.

    Usage:
        python -m src.presentation.cli.process_direct_video "https://youtube.com/watch?v=VIDEO_ID"
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Process a single YouTube video by URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.presentation.cli.process_direct_video "https://youtube.com/watch?v=abc123"
  python -m src.presentation.cli.process_direct_video "https://youtube.com/watch?v=abc123" --privacy unlisted
        """
    )

    parser.add_argument(
        "video_url",
        type=str,
        help="YouTube video URL"
    )

    parser.add_argument(
        "--privacy",
        type=str,
        choices=["public", "unlisted", "private"],
        default="public",
        help="YouTube privacy status (default: public)"
    )

    args = parser.parse_args()

    # Call pipeline run function with direct video URL
    # The pipeline will skip search stage and use this URL directly
    from typer import Context
    
    # Call the run function directly with parameters
    try:
        pipeline_run(
            query="direct_video",  # Placeholder query
            direct_url=args.video_url,
            skip_api_check=False
        )
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
