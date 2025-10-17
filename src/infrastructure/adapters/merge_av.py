from __future__ import annotations

from pathlib import Path
import json
import os
import re
import shutil
import subprocess
from typing import Optional


def _ensure_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _sanitize_filename(name: str, max_len: int = 120) -> str:
    # Remove/replace characters not allowed on Windows filesystems and collapse spaces
    name = name.strip()
    # Replace forbidden: \/:*?"<>|
    name = re.sub(r"[\\/:*?\"<>|]", "-", name)
    # Remove control chars
    name = re.sub(r"[\x00-\x1F]", "", name)
    # Collapse whitespace and dashes
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s*-\s*", "-", name)
    # Trim length
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    # Fallback if empty
    return name or "output"


def _unique_path(base: Path) -> Path:
    """
    Return the base path, deleting any existing file first.
    This ensures re-runs overwrite incomplete outputs instead of creating numbered duplicates.
    Handles Unicode normalization issues on Windows (e.g., em dash → double space).
    """
    # Try direct deletion first
    if base.exists():
        try:
            print(f"🗑️ Deleting old output: {base.name}")
            base.unlink()
            print(f"✅ Deleted successfully")
            return base
        except Exception as e:
            print(f"⚠️ Could not delete old output: {e}")
            return base

    # File might exist with different Unicode normalization (Windows issue)
    parent = base.parent
    if not parent.exists():
        return base

    # Normalize for comparison: replace em dash, collapse spaces, case-insensitive
    def normalize_for_comparison(name: str) -> str:
        """Normalize filename for fuzzy matching (handles Unicode variants)."""
        # Replace em dash (U+2013) and en dash (U+2014) with space
        name = name.replace('\u2013', ' ').replace('\u2014', ' ')
        # Replace hyphens with spaces for comparison
        name = name.replace('-', ' ')
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name)
        return name.lower().strip()

    target_normalized = normalize_for_comparison(base.stem)  # Without .mp4

    # Search for files matching the expected name (fuzzy match)
    for existing in parent.glob("*.mp4"):
        existing_normalized = normalize_for_comparison(existing.stem)
        if existing_normalized == target_normalized:
            try:
                print(f"🗑️ Deleting old output (fuzzy match): {existing.name}")
                existing.unlink()
                print(f"✅ Deleted successfully")
            except Exception as e:
                print(f"⚠️ Could not delete old output: {e}")
            break

    return base


def _resolve_run_dir(run_dir: Path) -> Path:
    """Resolve runs/latest pointer via path.txt if present; fallback to newest run."""
    try:
        if run_dir.exists() and run_dir.is_dir():
            path_file = run_dir / "path.txt"
            if path_file.exists():
                target = path_file.read_text(encoding="utf-8").strip()
                p = Path(target)
                if not p.is_absolute():
                    p = run_dir.parent / p
                if p.exists():
                    return p
        root = run_dir.parent if run_dir.parent.name else Path("runs")
        if not root.exists():
            root = Path("runs")
        candidates = [p for p in root.glob("*/") if p.is_dir()]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        pass
    return run_dir


def main(
    titles_json: Path,
    video_mp4: Path,
    audio_mp3: Path,
    output_dir: Path,
) -> Optional[Path]:
    """Merge narration with video by looping the video to match audio duration.

    - Video is looped using ffmpeg's -stream_loop and truncated to audio length via -shortest.
    - Output filename is derived from youtube_title in titles_json and saved as .mp4.
    Returns the output path on success, else None.
    """
    if not _ensure_ffmpeg():
        return None
    try:
        meta = json.loads(Path(titles_json).read_text(encoding="utf-8"))
    except Exception:
        meta = {}

    yt_title = meta.get("youtube_title") or meta.get("main_title") or "output"
    safe = _sanitize_filename(str(yt_title), max_len=120)
    out_path = output_dir / f"{safe}.mp4"
    out_path = _unique_path(out_path)

    if not video_mp4.exists() or not audio_mp3.exists():
        return None

    # Build ffmpeg command:
    # - Loop the input video infinitely and cut to shortest stream (audio)
    # - Re-encode video to ensure seamless looping and compatibility
    # - Faststart for web upload
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(video_mp4),
        "-i", str(audio_mp3),
        "-shortest",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except Exception:
        return None

    # If merge succeeded, and the source video is the pipeline render (video_snap.mp4),
    # remove it to avoid confusion during upload (leave only the final titled mp4).
    if out_path.exists():
        try:
            if video_mp4.name.lower() == "video_snap.mp4" and video_mp4.exists():
                video_mp4.unlink()
        except Exception:
            # Non-fatal if deletion fails
            pass
        return out_path
    return None


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Merge video_snap.mp4 with narration.mp3 using youtube_title as output filename")
    p.add_argument("--run", dest="run_dir", default="runs/latest", help="Run directory containing video_snap.mp4, narration.mp3, output.titles.json")
    args = p.parse_args()

    run_dir = _resolve_run_dir(Path(args.run_dir))
    out = main(
        titles_json=run_dir / "output.titles.json",
        video_mp4=run_dir / "video_snap.mp4",
        audio_mp3=run_dir / "narration.mp3",
        output_dir=run_dir,
    )
    print(out if out else "merge failed")
