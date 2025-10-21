"""
Search Videos Use Case

Business logic for searching YouTube videos.
"""

from __future__ import annotations
from typing import List, Protocol
from pathlib import Path

from ...core.domain.entities import Video
from ...core.domain.value_objects import SearchQuery


class VideoSearchPort(Protocol):
    """Port for video search adapter."""
    
    def search(self, query: SearchQuery) -> List[Video]:
        """Search for videos matching the query."""
        ...


class SearchVideosUseCase:
    """
    Use case for searching YouTube videos based on book title.
    
    This use case:
    1. Takes a book title and language
    2. Creates a formatted search query
    3. Searches YouTube for matching videos
    4. Returns a list of videos sorted by relevance
    """
    
    def __init__(self, video_search_adapter: VideoSearchPort):
        """
        Initialize use case with required adapter.
        
        Args:
            video_search_adapter: Adapter for searching YouTube videos
        """
        self.video_search = video_search_adapter
    
    def execute(
        self,
        book_title: str,
        language: str = "ar",
        max_results: int = 10,
        min_duration: int = 900,
        max_duration: int = 7200,
    ) -> List[Video]:
        """
        Search for videos about a book.
        
        Args:
            book_title: Title of the book to search for
            language: Language for search (ar, en)
            max_results: Maximum number of results
            min_duration: Minimum video duration in seconds
            max_duration: Maximum video duration in seconds
        
        Returns:
            List of videos matching the criteria
        
        Raises:
            VideoSearchException: If search fails
        """
        # Create search query
        query = SearchQuery(
            raw_query=book_title,
            language=language,
            max_results=max_results
        )
        
        # Search for videos
        videos = self.video_search.search(query)
        
        # Filter by duration
        filtered = [
            v for v in videos
            if min_duration <= v.duration <= max_duration
        ]
        
        # Sort by engagement score (views, likes)
        sorted_videos = sorted(
            filtered,
            key=lambda v: v.engagement_score,
            reverse=True
        )
        
        return sorted_videos
    
    def save_search_results(self, videos: List[Video], output_dir: Path) -> None:
        """
        Save search results to file.
        
        Args:
            videos: List of videos to save
            output_dir: Directory to save results
        """
        import json
        
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = output_dir / "search_results.json"
        
        data = {
            "total_results": len(videos),
            "videos": [v.to_dict() for v in videos]
        }
        
        results_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
