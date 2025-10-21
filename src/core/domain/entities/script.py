"""
Script Entity - Core Domain Model

This module defines the Script entity for generated video scripts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Script:
    """
    Script entity representing a generated video script.
    
    Attributes:
        id: Unique identifier
        content: Script text content
        language: Script language (ar, en)
        word_count: Number of words in the script
        estimated_duration: Estimated narration duration in seconds
        created_at: When the script was generated
        book_title: Associated book title
        source_video_id: Source YouTube video ID (optional)
        cleaned: Whether script has been cleaned of markers
    """
    
    content: str
    language: str = "ar"
    id: UUID = field(default_factory=uuid4)
    word_count: int = field(init=False)
    estimated_duration: int = field(init=False)
    created_at: datetime = field(default_factory=datetime.now)
    book_title: Optional[str] = None
    source_video_id: Optional[str] = None
    cleaned: bool = False
    
    def __post_init__(self) -> None:
        """Calculate derived fields after initialization."""
        if not self.content:
            raise ValueError("Script content cannot be empty")
        
        self.word_count = self._count_words()
        self.estimated_duration = self._estimate_duration()
    
    def _count_words(self) -> int:
        """Count words in the script."""
        return len(self.content.split())
    
    def _estimate_duration(self) -> int:
        """
        Estimate narration duration in seconds.
        
        Average speaking rate:
        - English: ~150 words per minute
        - Arabic: ~120 words per minute (slightly slower due to complexity)
        """
        words_per_minute = 120 if self.language == "ar" else 150
        minutes = self.word_count / words_per_minute
        return int(minutes * 60)
    
    @property
    def character_count(self) -> int:
        """Get character count."""
        return len(self.content)
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (MM:SS)."""
        minutes = self.estimated_duration // 60
        seconds = self.estimated_duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def is_within_limit(self, max_chars: int = 950) -> bool:
        """Check if script is within character limit."""
        return self.character_count <= max_chars
    
    def truncate(self, max_chars: int = 950) -> None:
        """Truncate script to fit within character limit."""
        if self.character_count > max_chars:
            self.content = self.content[:max_chars].rsplit(' ', 1)[0] + "..."
            self.word_count = self._count_words()
            self.estimated_duration = self._estimate_duration()
    
    def clean_markers(self) -> None:
        """Remove prompt structure markers from the script."""
        import re
        
        # Remove bold markers with square brackets
        self.content = re.sub(
            r'\*\*\s*\[([^\]]+)\]\s*\*\*',
            '',
            self.content,
            flags=re.IGNORECASE
        )
        
        # Remove non-bold square bracket markers
        self.content = re.sub(
            r'^\s*\[(?:HOOK|CONTEXT|MAIN CONTENT|CLOSING)(?:\s*-[^\]]+)?\]\s*$',
            '',
            self.content,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Clean up extra blank lines
        self.content = re.sub(r'\n\s*\n\s*\n+', '\n\n', self.content)
        self.content = self.content.strip()
        
        self.cleaned = True
        self.word_count = self._count_words()
        self.estimated_duration = self._estimate_duration()
    
    def to_dict(self) -> dict:
        """Convert script to dictionary for serialization."""
        return {
            "id": str(self.id),
            "content": self.content,
            "language": self.language,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "estimated_duration": self.estimated_duration,
            "duration_formatted": self.duration_formatted,
            "created_at": self.created_at.isoformat(),
            "book_title": self.book_title,
            "source_video_id": self.source_video_id,
            "cleaned": self.cleaned,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Script:
        """Create script from dictionary."""
        script = cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            content=data["content"],
            language=data.get("language", "ar"),
            book_title=data.get("book_title"),
            source_video_id=data.get("source_video_id"),
            cleaned=data.get("cleaned", False),
        )
        if "created_at" in data:
            script.created_at = datetime.fromisoformat(data["created_at"])
        return script
    
    def __repr__(self) -> str:
        """String representation of the script."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Script(words={self.word_count}, duration={self.duration_formatted}, preview='{preview}')"
