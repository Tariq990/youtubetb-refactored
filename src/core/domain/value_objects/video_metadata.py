"""
VideoMetadata Value Object

Represents metadata for YouTube video uploads.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VideoMetadata:
    """
    Value object representing YouTube video metadata.
    
    Attributes:
        title: Video title (max 100 chars)
        description: Video description (max 5000 chars)
        tags: List of tags (max 500 chars total)
        category_id: YouTube category ID
        privacy_status: Privacy status (public, unlisted, private)
        language: Video language (ar, en)
        default_language: Default language for metadata
        made_for_kids: Whether video is made for kids
        thumbnail_path: Path to thumbnail image (optional)
    """
    
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    category_id: str = "27"  # Education
    privacy_status: str = "unlisted"
    language: str = "ar"
    default_language: str = "ar"
    made_for_kids: bool = False
    thumbnail_path: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate metadata."""
        if not self.title or len(self.title) > 100:
            raise ValueError("Title must be between 1 and 100 characters")
        
        if len(self.description) > 5000:
            raise ValueError("Description must be less than 5000 characters")
        
        if self.privacy_status not in ["public", "unlisted", "private"]:
            raise ValueError(f"Invalid privacy status: {self.privacy_status}")
        
        # Ensure tags don't exceed 500 chars total
        tags_text = ",".join(self.tags)
        if len(tags_text) > 500:
            raise ValueError("Tags total length must be less than 500 characters")
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't exceed limit."""
        new_tags = self.tags + [tag]
        tags_text = ",".join(new_tags)
        if len(tags_text) <= 500:
            object.__setattr__(self, 'tags', new_tags)
        else:
            raise ValueError("Adding this tag would exceed 500 character limit")
    
    def to_youtube_format(self) -> dict:
        """Convert to YouTube API format."""
        return {
            "snippet": {
                "title": self.title,
                "description": self.description,
                "tags": self.tags,
                "categoryId": self.category_id,
                "defaultLanguage": self.default_language,
            },
            "status": {
                "privacyStatus": self.privacy_status,
                "selfDeclaredMadeForKids": self.made_for_kids,
            }
        }
    
    @classmethod
    def from_book(
        cls,
        book_title: str,
        author: Optional[str] = None,
        language: str = "ar",
        privacy: str = "unlisted",
        description_template: Optional[str] = None,
    ) -> VideoMetadata:
        """Create metadata from book information."""
        # Construct title
        if author:
            title = f"ملخص كتاب {book_title} | {author}" if language == "ar" else f"{book_title} by {author} - Summary"
        else:
            title = f"ملخص كتاب {book_title}" if language == "ar" else f"{book_title} - Book Summary"
        
        # Truncate if too long
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Default description
        if not description_template:
            if language == "ar":
                description = f"ملخص شامل لكتاب {book_title}\n\n"
                if author:
                    description += f"المؤلف: {author}\n\n"
                description += "🔔 اشترك في القناة للمزيد من ملخصات الكتب"
            else:
                description = f"Comprehensive summary of {book_title}\n\n"
                if author:
                    description += f"Author: {author}\n\n"
                description += "🔔 Subscribe for more book summaries"
        else:
            description = description_template
        
        # Default tags
        tags = [
            book_title,
            "book summary" if language == "en" else "ملخص كتاب",
            "books" if language == "en" else "كتب",
        ]
        if author:
            tags.append(author)
        
        return cls(
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            language=language,
            default_language=language,
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"VideoMetadata(title='{self.title[:50]}...', privacy={self.privacy_status})"
