#!/usr/bin/env python3
"""Test uploading a short video with controlled YouTube tags."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Ensure repo imports resolve
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.infrastructure.adapters.youtube_upload import upload_video  # noqa: E402


def create_test_video(output_path: Path, duration: int = 10) -> bool:
    """Create a 10-second silent video with a text overlay for testing."""
    try:
        print(f"🎬 Creating {duration}s test video...")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=1920x1080:d={duration}",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-vf",
            "drawtext=text='YouTube Tags Test Video':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            print(f"✅ Test video created: {output_path}")
            return True
        print(f"❌ FFmpeg failed: {result.stderr}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error creating video: {exc}")
        return False


def _ensure_exact_filename(test_dir: Path, youtube_title: str) -> Path:
    """Return the exact filename the uploader expects (sanitized title)."""
    sanitized_title = (
        youtube_title.replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("?", "")
        .replace("*", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
    )
    return test_dir / f"{sanitized_title}.mp4"


def _sanitize_tag(tag: str, max_len: int = 30) -> str:
    """Mimic uploader sanitization to keep tags API-safe (<=30 chars)."""
    cleaned = tag.replace('_', ' ').strip()
    cleaned = ' '.join(cleaned.split())
    cleaned = ''.join(ch for ch in cleaned if ch.isalnum() or ch.isspace())
    if len(cleaned) > max_len:
        truncated = cleaned[:max_len].rstrip()
        if ' ' in truncated and len(cleaned) > max_len:
            without_last_word = truncated.rsplit(' ', 1)[0].strip()
            if without_last_word:
                truncated = without_last_word
        cleaned = truncated
    return cleaned


def _build_tags(book: str, author: str) -> list[str]:
    """Generate dynamic and fixed tags following requested patterns."""
    combos = [
        f"{book} {author} book summary",
        f"{book} {author}",
        f"{book} {author} audiobook",
        author,
        book,
        f"{book} book summary",
    ]

    fixed = [
        "InkEcho",
        "audiobook",
        "book summary",
        "self improvement",
        "productivity",
        "personal development",
        "motivational",
        "educational",
        "book review",
        "self help",
    ]

    # Preserve order while enforcing sanitization and uniqueness
    seen: set[str] = set()
    ordered: list[str] = []
    for tag in combos + fixed:
        sanitized = _sanitize_tag(tag)
        if sanitized and sanitized.lower() not in seen:
            ordered.append(sanitized)
            seen.add(sanitized.lower())
    return ordered


def _load_source_metadata(path: Path) -> dict | None:
    if not path.exists():
        print(f"⚠️ Source metadata not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if not isinstance(data, dict):
                print("⚠️ Source metadata is not a JSON object")
                return None
            return data
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ Failed to read source metadata: {exc}")
        return None


def test_tags_upload(source_metadata: Path | None = None) -> bool:
    """Generate metadata with 30-char tags and upload a test video."""
    print("=" * 70)
    print("🏷️  YouTube Tags Upload Test")
    print("=" * 70)

    test_dir = repo_root / "tmp" / "test_upload"
    test_dir.mkdir(parents=True, exist_ok=True)

    metadata: dict
    book_name = "Zero to One"
    author_name = "Peter Thiel"

    if source_metadata:
        source = _load_source_metadata(source_metadata)
        if source:
            metadata = {
                "youtube_title": source.get("youtube_title") or "Test Video",
                "youtube_description": source.get("youtube_description") or "Test upload.",
                "TAGS": source.get("TAGS") or [],
                "main_title": source.get("main_title") or source.get("title") or "",
                "author_name": source.get("author_name") or source.get("author") or "",
                "playlist": source.get("playlist") or "",
            }
            book_name = source.get("main_title") or book_name
            author_name = source.get("author_name") or author_name
        else:
            metadata = {
                "youtube_title": "Test Video",
                "youtube_description": "Test upload with fallback metadata.",
                "TAGS": _build_tags(book_name, author_name),
                "main_title": book_name,
                "author_name": author_name,
            }
    else:
        metadata = {
            "youtube_title": "Test Video - 30 Char Tags Validation",
            "youtube_description": """This is a test video to validate hybrid tag patterns.

🎯 Purpose: Confirm the uploader accepts structured book/author tag combinations (≤30 chars after sanitation).

📋 Dynamic Tag Logic:
1. Book + Author + "book summary"
2. Book + Author
3. Book + Author + "audiobook"
4. Author only
5. Book only
6. Book + "book summary"

📌 Fixed Tags Added:
- InkEcho (channel signature)
- audiobook, book summary, self improvement, productivity, personal development, motivational, educational, book review, self help

Expected behavior: All tags comply with the 30-character limit after sanitation.

This video will be deleted after testing.

#ThirtyCharTags #Testing #YouTubeAPI
""",
            "TAGS": _build_tags(book_name, author_name),
        }
    metadata["main_title"] = book_name
    metadata["author_name"] = author_name

    sanitized_tags: list[str] = []
    seen: set[str] = set()
    for tag in metadata.get("TAGS", []):
        cleaned = _sanitize_tag(str(tag))
        if cleaned:
            key = cleaned.casefold()
            if key not in seen:
                sanitized_tags.append(cleaned)
                seen.add(key)
    metadata["TAGS"] = sanitized_tags

    metadata_path = test_dir / "output.titles.json"
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)

    video_path = _ensure_exact_filename(test_dir, metadata["youtube_title"])
    if not create_test_video(video_path, duration=10):
        print("\n❌ Failed to create test video")
        return False

    print("\n📋 Metadata:")
    print(f"   Title: {metadata['youtube_title']}")
    print(f"   Tags: {len(metadata['TAGS'])} tags")
    for idx, tag in enumerate(metadata["TAGS"], 1):
        print(f"      {idx}. {tag} (len={len(tag)})")

    secrets_dir = repo_root / "secrets"
    client_secret = secrets_dir / "client_secret.json"
    token_file = secrets_dir / "token.json"

    if not client_secret.exists():
        print(f"\n❌ client_secret.json not found: {client_secret}")
        return False
    if not token_file.exists():
        print(f"\n❌ token.json not found: {token_file}")
        print("   Run: python scripts/generate_youtube_token.py")
        return False

    print("\n📤 Uploading to YouTube...")
    print("   Privacy: unlisted (for testing)")

    try:
        video_id = upload_video(
            run_dir=test_dir,
            titles_json=metadata_path,
            client_secret=client_secret,
            token_file=token_file,
            privacy_status="unlisted",
            allow_fallbacks=True,
            debug=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Upload error: {exc}")
        import traceback

        traceback.print_exc()
        return False

    if video_id:
        print("\n✅ Upload successful!")
        print(f"   Video ID: {video_id}")
        print(f"   URL: https://youtube.com/watch?v={video_id}")
        print("\n🔍 Check tags in YouTube Studio:")
        print(f"   https://studio.youtube.com/video/{video_id}/edit")
        return True

    print("\n❌ Upload failed (no video ID returned)")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload test video with controlled YouTube tags.")
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Path to an existing output.titles.json to reuse title/description/tags.",
    )
    args = parser.parse_args()

    print("\n" + "🏷️ " * 20)
    print("YouTube Tags Upload Test")
    print("🏷️ " * 20 + "\n")

    source_path = args.metadata if args.metadata else None
    success = test_tags_upload(source_path)

    print("\n" + "=" * 70)
    if success:
        print("✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Open YouTube Studio")
        print("2. Check the uploaded video's tags")
        print("3. Delete the test video when done")
    else:
        print("❌ Test failed - check errors above")
    print("=" * 70 + "\n")

    sys.exit(0 if success else 1)
