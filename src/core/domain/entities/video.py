"""
Video Entity - Core Domain Model

This module defines the Video entity for YouTube videos.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Video:
    """
    Video entity representing a YouTube video.
    
    Attributes:
        id: Unique identifier
        video_id: YouTube video ID
        title: Video title
        channel_name: Channel that uploaded the video
        duration: Video duration in seconds
        view_count: Number of views
        like_count: Number of likes
        url: Full YouTube URL
        transcript: Video transcript text (optional)
        published_at: When the video was published
        language: Video language (ar, en)
        selected: Whether this video was selected for processing
    """
    
    video_id: str
    title: str
    channel_name: str
    duration: int  # seconds
    url: str
    id: UUID = field(default_factory=uuid4)
    view_count: int = 0
    like_count: int = 0
    transcript: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str = "ar"
    selected: bool = False
    
    def __post_init__(self) -> None:
        """Validate video data after initialization."""
        if not self.video_id:
            raise ValueError("Video ID cannot be empty")
        
        if not self.title:
            raise ValueError("Video title cannot be empty")
        
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (HH:MM:SS)."""
        return str(timedelta(seconds=self.duration))
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score based on views and likes."""
        if self.view_count == 0:
            return 0.0
        return (self.like_count / self.view_count) * 100
    
    def has_transcript(self) -> bool:
        """Check if video has a transcript."""
        return self.transcript is not None and len(self.transcript.strip()) > 0
    
    def is_long_form(self, min_duration: int = 900) -> bool:
        """Check if video is long-form (default: 15+ minutes)."""
        return self.duration >= min_duration
    
    def is_short(self) -> bool:
        """Check if video is a YouTube Short (<60 seconds)."""
        return self.duration <= 60
    
    def mark_as_selected(self) -> None:
        """Mark this video as selected for processing."""
        self.selected = True
    
    def to_dict(self) -> dict:
        """Convert video to dictionary for serialization."""
        return {
            "id": str(self.id),
            "video_id": self.video_id,
            "title": self.title,
            "channel_name": self.channel_name,
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "url": self.url,
            "transcript": self.transcript,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "language": self.language,
            "selected": self.selected,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Video:
        """Create video from dictionary."""
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            video_id=data["video_id"],
            title=data["title"],
            channel_name=data["channel_name"],
            duration=data["duration"],
            url=data["url"],
            view_count=data.get("view_count", 0),
            like_count=data.get("like_count", 0),
            transcript=data.get("transcript"),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            language=data.get("language", "ar"),
            selected=data.get("selected", False),
        )
    
    def __repr__(self) -> str:
        """String representation of the video."""
        return f"Video(id={self.video_id}, title='{self.title[:50]}...', duration={self.duration_formatted})"
