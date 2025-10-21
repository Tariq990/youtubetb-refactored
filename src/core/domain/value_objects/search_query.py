"""
SearchQuery Value Object

Represents a search query with language-specific formatting.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchQuery:
    """
    Value object representing a YouTube search query.
    
    Attributes:
        raw_query: Original search query
        language: Query language (ar, en)
        formatted_query: Language-specific formatted query
        max_results: Maximum number of results to return
    """
    
    raw_query: str
    language: str = "ar"
    max_results: int = 10
    
    def __post_init__(self) -> None:
        """Validate search query data."""
        if not self.raw_query or not self.raw_query.strip():
            raise ValueError("Search query cannot be empty")
        
        if self.language not in ["ar", "en"]:
            raise ValueError(f"Invalid language: {self.language}")
        
        if self.max_results < 1 or self.max_results > 50:
            raise ValueError("max_results must be between 1 and 50")
    
    @property
    def formatted_query(self) -> str:
        """Get formatted query based on language."""
        if self.language == "ar":
            return f"ملخص كتاب {self.raw_query}"
        else:
            return f"{self.raw_query} book summary"
    
    @property
    def safe_filename(self) -> str:
        """Get safe filename from query (remove special characters)."""
        import re
        safe = re.sub(r'[^\w\s-]', '', self.raw_query)
        safe = re.sub(r'[-\s]+', '-', safe)
        return safe.strip('-')[:100]  # Limit to 100 chars
    
    def with_max_results(self, max_results: int) -> SearchQuery:
        """Create a new SearchQuery with different max_results."""
        return SearchQuery(
            raw_query=self.raw_query,
            language=self.language,
            max_results=max_results
        )
    
    def __str__(self) -> str:
        """String representation."""
        return self.formatted_query
