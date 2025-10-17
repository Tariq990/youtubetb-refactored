"""
Channel processing progress tracker.

Saves progress to avoid re-scanning all videos after interruption.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ChannelProgressTracker:
    """Track progress of channel processing."""

    def __init__(self, channel_url: str, progress_dir: Path = Path("channel_progress")):
        """
        Initialize tracker.

        Args:
            channel_url: YouTube channel URL
            progress_dir: Directory to store progress files
        """
        self.channel_url = channel_url
        self.progress_dir = progress_dir
        self.progress_dir.mkdir(exist_ok=True)

        # Generate unique filename from channel URL
        channel_id = channel_url.split("/@")[-1].split("/")[0]
        self.progress_file = progress_dir / f"{channel_id}_progress.json"

        self.data = self._load()

    def _load(self) -> Dict:
        """Load progress from file."""
        if not self.progress_file.exists():
            return {
                "channel_url": self.channel_url,
                "total_videos": 0,
                "processed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "last_updated": None,
                "videos": []  # List of all video URLs with status
            }

        try:
            with self.progress_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._load()  # Return default

    def _save(self):
        """Save progress to file."""
        self.data["last_updated"] = datetime.now().isoformat()
        with self.progress_file.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def initialize_videos(self, videos: List[Dict]):
        """
        Initialize video list at start of processing.

        Args:
            videos: List of video metadata dicts
        """
        self.data["total_videos"] = len(videos)
        self.data["videos"] = [
            {
                "url": v["url"],
                "title": v["title"],
                "duration_min": v["duration_min"],
                "status": "pending",  # pending, processing, done, failed
                "error": None,
                "processed_at": None
            }
            for v in videos
        ]
        self._save()

    def mark_processing(self, video_url: str):
        """Mark video as currently processing."""
        for v in self.data["videos"]:
            if v["url"] == video_url:
                v["status"] = "processing"
                break
        self._save()

    def mark_success(self, video_url: str):
        """Mark video as successfully processed."""
        for v in self.data["videos"]:
            if v["url"] == video_url:
                v["status"] = "done"
                v["processed_at"] = datetime.now().isoformat()
                break

        self.data["processed_count"] = sum(1 for v in self.data["videos"] if v["status"] == "done")
        self._save()

    def mark_failed(self, video_url: str, error: str):
        """Mark video as failed."""
        for v in self.data["videos"]:
            if v["url"] == video_url:
                v["status"] = "failed"
                v["error"] = error
                break

        self.data["failed_count"] = sum(1 for v in self.data["videos"] if v["status"] == "failed")
        self._save()

    def mark_skipped(self, video_url: str, reason: str):
        """Mark video as skipped."""
        for v in self.data["videos"]:
            if v["url"] == video_url:
                v["status"] = "skipped"
                v["error"] = reason
                break

        self.data["skipped_count"] = sum(1 for v in self.data["videos"] if v["status"] == "skipped")
        self._save()

    def get_pending_videos(self) -> List[Dict]:
        """Get list of videos that still need processing."""
        return [v for v in self.data["videos"] if v["status"] in ["pending", "failed"]]

    def get_progress_summary(self) -> str:
        """Get human-readable progress summary."""
        total = self.data["total_videos"]
        done = self.data["processed_count"]
        failed = self.data["failed_count"]
        skipped = self.data["skipped_count"]
        pending = sum(1 for v in self.data["videos"] if v["status"] == "pending")

        percentage = (done / total * 100) if total > 0 else 0

        return f"""
Channel Progress Summary
════════════════════════════════════════
Total Videos: {total}
✅ Completed: {done} ({percentage:.1f}%)
❌ Failed: {failed}
⏭️ Skipped: {skipped}
⏳ Pending: {pending}

Last Updated: {self.data.get("last_updated", "Never")}
        """

    def clear(self):
        """Clear progress (start fresh)."""
        if self.progress_file.exists():
            self.progress_file.unlink()
        self.data = self._load()
