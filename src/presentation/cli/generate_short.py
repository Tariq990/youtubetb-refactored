"""
CLI for YouTube Shorts Generator
"""
import sys
import os
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # Go up to project root

try:
    from dotenv import load_dotenv
    load_dotenv("secrets/.env")
except:
    pass


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube Short from book summary")
    parser.add_argument("--run", required=True, help="Path to run directory")
    parser.add_argument("--upload", action="store_true", help="Upload short after generation")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"],
                        help="Privacy status for upload")

    args = parser.parse_args()

    run_dir = Path(args.run)
    if not run_dir.exists():
        print(f"❌ Run directory not found: {run_dir}")
        return 1

    # Resolve if it's "latest"
    if run_dir.name == "latest":
        path_file = run_dir / "path.txt"
        if path_file.exists():
            actual_path = path_file.read_text().strip()
            run_dir = Path(actual_path)
            print(f"📂 Resolved latest → {run_dir}")

    # Generate short
    from src.infrastructure.adapters.shorts_generator import generate_short, upload_short

    print("=" * 60)
    print("🎬 YouTube Shorts Generator")
    print("=" * 60)

    short_path = generate_short(run_dir)

    if not short_path:
        print("\n❌ Failed to generate short")
        return 1

    print(f"\n✅ Short generated successfully!")
    print(f"📁 Location: {short_path}")

    # Upload if requested
    if args.upload:
        print("\n" + "=" * 60)
        print("📤 Uploading to YouTube...")
        print("=" * 60)

        video_id = upload_short(short_path, run_dir, privacy=args.privacy)

        if video_id:
            print(f"\n🎉 Short uploaded successfully!")
            print(f"🔗 https://youtube.com/watch?v={video_id}")
        else:
            print("\n❌ Upload failed")
            return 1
    else:
        print("\n💡 To upload, run with --upload flag")

    return 0


if __name__ == "__main__":
    sys.exit(main())
