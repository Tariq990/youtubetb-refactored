"""
Audio Entity - Core Domain Model

This module defines the Audio entity for generated audio files.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Audio:
    """
    Audio entity representing a generated audio file.
    
    Attributes:
        id: Unique identifier
        file_path: Path to the audio file
        duration: Audio duration in seconds
        format: Audio format (mp3, wav, etc.)
        sample_rate: Sample rate in Hz
        bitrate: Bitrate in kbps
        size_bytes: File size in bytes
        created_at: When the audio was generated
        voice_id: TTS voice ID used
        language: Audio language (ar, en)
        script_id: Associated script ID (optional)
    """
    
    file_path: Path
    duration: int  # seconds
    format: str = "mp3"
    id: UUID = field(default_factory=uuid4)
    sample_rate: int = 44100
    bitrate: int = 192
    size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    voice_id: Optional[str] = None
    language: str = "ar"
    script_id: Optional[UUID] = None
    
    def __post_init__(self) -> None:
        """Validate audio data after initialization."""
        if not self.file_path:
            raise ValueError("Audio file path cannot be empty")
        
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        
        if self.format not in ["mp3", "wav", "ogg", "m4a"]:
            raise ValueError(f"Unsupported audio format: {self.format}")
        
        # Get file size if file exists
        if self.file_path.exists():
            self.size_bytes = self.file_path.stat().st_size
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (HH:MM:SS)."""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def exists(self) -> bool:
        """Check if audio file exists."""
        return self.file_path.exists()
    
    def get_metadata(self) -> dict:
        """Get audio metadata."""
        return {
            "duration": self.duration,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "bitrate": self.bitrate,
            "size_mb": round(self.size_mb, 2),
            "voice_id": self.voice_id,
            "language": self.language,
        }
    
    def to_dict(self) -> dict:
        """Convert audio to dictionary for serialization."""
        return {
            "id": str(self.id),
            "file_path": str(self.file_path),
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "bitrate": self.bitrate,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 2),
            "created_at": self.created_at.isoformat(),
            "voice_id": self.voice_id,
            "language": self.language,
            "script_id": str(self.script_id) if self.script_id else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Audio:
        """Create audio from dictionary."""
        audio = cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            file_path=Path(data["file_path"]),
            duration=data["duration"],
            format=data.get("format", "mp3"),
            sample_rate=data.get("sample_rate", 44100),
            bitrate=data.get("bitrate", 192),
            size_bytes=data.get("size_bytes", 0),
            voice_id=data.get("voice_id"),
            language=data.get("language", "ar"),
            script_id=UUID(data["script_id"]) if data.get("script_id") else None,
        )
        if "created_at" in data:
            audio.created_at = datetime.fromisoformat(data["created_at"])
        return audio
    
    def __repr__(self) -> str:
        """String representation of the audio."""
        return f"Audio(file={self.file_path.name}, duration={self.duration_formatted}, size={self.size_mb:.2f}MB)"
