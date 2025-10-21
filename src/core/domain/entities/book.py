"""
Book Entity - Core Domain Model

This module defines the Book entity, representing a book in the domain.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Book:
    """
    Book entity representing a book to be processed.
    
    Attributes:
        id: Unique identifier for the book
        title: Main title of the book
        author: Author name (optional)
        language: Detected language (ar, en)
        status: Processing status (pending, processing, done, failed, uploaded)
        run_folder: Path to the run folder containing processed files
        created_at: When the book was added to the system
        updated_at: Last update timestamp
        youtube_url: YouTube video URL after upload (optional)
        playlist_id: YouTube playlist ID (optional)
        error_message: Error message if processing failed (optional)
    """
    
    title: str
    id: UUID = field(default_factory=uuid4)
    author: Optional[str] = None
    language: str = "ar"
    status: str = "pending"
    run_folder: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    youtube_url: Optional[str] = None
    playlist_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate book data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Book title cannot be empty")
        
        if self.status not in ["pending", "processing", "done", "failed", "uploaded"]:
            raise ValueError(f"Invalid status: {self.status}")
        
        if self.language not in ["ar", "en"]:
            raise ValueError(f"Invalid language: {self.language}")
    
    def mark_as_processing(self, run_folder: str) -> None:
        """Mark book as currently being processed."""
        self.status = "processing"
        self.run_folder = run_folder
        self.updated_at = datetime.now()
    
    def mark_as_done(self) -> None:
        """Mark book as successfully processed."""
        self.status = "done"
        self.updated_at = datetime.now()
    
    def mark_as_uploaded(self, youtube_url: str, playlist_id: Optional[str] = None) -> None:
        """Mark book as uploaded to YouTube."""
        self.status = "uploaded"
        self.youtube_url = youtube_url
        if playlist_id:
            self.playlist_id = playlist_id
        self.updated_at = datetime.now()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark book as failed with error message."""
        self.status = "failed"
        self.error_message = error_message
        self.updated_at = datetime.now()
    
    def is_completed(self) -> bool:
        """Check if book processing is completed."""
        return self.status in ["done", "uploaded"]
    
    def is_processing(self) -> bool:
        """Check if book is currently being processed."""
        return self.status == "processing"
    
    def is_failed(self) -> bool:
        """Check if book processing failed."""
        return self.status == "failed"
    
    def to_dict(self) -> dict:
        """Convert book to dictionary for serialization."""
        return {
            "id": str(self.id),
            "title": self.title,
            "author": self.author,
            "language": self.language,
            "status": self.status,
            "run_folder": self.run_folder,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "youtube_url": self.youtube_url,
            "playlist_id": self.playlist_id,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Book:
        """Create book from dictionary."""
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            title=data["title"],
            author=data.get("author"),
            language=data.get("language", "ar"),
            status=data.get("status", "pending"),
            run_folder=data.get("run_folder"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            youtube_url=data.get("youtube_url"),
            playlist_id=data.get("playlist_id"),
            error_message=data.get("error_message"),
        )
    
    def __repr__(self) -> str:
        """String representation of the book."""
        author_str = f" by {self.author}" if self.author else ""
        return f"Book('{self.title}'{author_str}, status={self.status})"
