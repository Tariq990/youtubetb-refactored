"""
YouTube Search Adapter - Complete Implementation.

This adapter handles video search using YouTube Data API v3.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import requests
import re

from src.core.domain.exceptions import VideoSearchException, RateLimitException
from src.shared.logging import get_logger
from src.shared.errors import get_error_handler


logger = get_logger(__name__)
error_handler = get_error_handler()


@dataclass
class VideoSearchResult:
    """Video search result"""
    
    video_id: str
    title: str
    channel: str
    channel_id: str
    country: str
    published_at: str
    url: str
    duration_seconds: int
    view_count: Optional[int] = None
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        return self.duration_seconds // 60


class YouTubeSearchAdapter:
    """
    YouTube Data API v3 search adapter.
    
    Implements intelligent search with:
    - Multi-phase search (relevance + date)
    - Duration filtering
    - Deduplication
    - View count enrichment
    """
    
    def __init__(self, api_key: str):
        """
        Initialize YouTube search adapter.
        
        Args:
            api_key: YouTube Data API key
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    @error_handler.with_error_handling("youtube_search", max_retries=3)
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        min_duration_seconds: int = 900,
        max_duration_seconds: int = 7200,
    ) -> List[VideoSearchResult]:
        """
        Search for videos with intelligent filtering.
        
        Args:
            query: Search query (book name)
            max_results: Maximum number of results
            min_duration_seconds: Minimum video duration (default: 15 min)
            max_duration_seconds: Maximum video duration (default: 2 hours)
        
        Returns:
            List of VideoSearchResult
        
        Raises:
            VideoSearchException: If search fails
            RateLimitException: If API rate limit exceeded
        """
        logger.info(
            "Starting YouTube search",
            query=query,
            max_results=max_results
        )
        
        try:
            # Phase 1: Search by relevance
            logger.debug("Phase 1: Searching by relevance")
            videos_relevance = self._search_phase(
                query=query,
                max_results=15,
                order="relevance"
            )
            
            # Phase 2: Search by date
            logger.debug("Phase 2: Searching by date")
            videos_date = self._search_phase(
                query=query,
                max_results=10,
                order="date"
            )
            
            # Combine and deduplicate
            all_videos = self._deduplicate_videos(
                videos_relevance + videos_date
            )
            logger.info(f"Found {len(all_videos)} unique videos")
            
            # Enrich with details (duration, channel info)
            enriched_videos = self._enrich_video_details(all_videos)
            
            # Filter by duration
            filtered_videos = self._filter_by_duration(
                enriched_videos,
                min_duration_seconds,
                max_duration_seconds
            )
            logger.info(
                f"After filtering: {len(filtered_videos)} videos",
                excluded=len(enriched_videos) - len(filtered_videos)
            )
            
            # Sort by duration (longest first) and limit
            sorted_videos = sorted(
                filtered_videos,
                key=lambda x: x.duration_seconds,
                reverse=True
            )
            final_results = sorted_videos[:max_results]
            
            # Enrich with view counts
            final_results = self._enrich_view_counts(final_results)
            
            logger.info(
                "Search completed successfully",
                total_results=len(final_results)
            )
            
            return final_results
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitException(
                    service_name="YouTube Data API",
                    retry_after=60
                )
            raise VideoSearchException(
                query=query,
                reason=f"HTTP error: {e}"
            )
        
        except Exception as e:
            logger.error(
                "Search failed",
                query=query,
                error=str(e),
                exc_info=True
            )
            raise VideoSearchException(
                query=query,
                reason=str(e)
            )
    
    def _search_phase(
        self,
        query: str,
        max_results: int,
        order: str
    ) -> List[Dict[str, Any]]:
        """
        Execute single search phase.
        
        Args:
            query: Search query
            max_results: Maximum results
            order: Sort order (relevance, date, rating, etc.)
        
        Returns:
            List of video items
        """
        search_url = f"{self.base_url}/search"
        query_full = f"ملخص كتاب {query}"
        
        params = {
            "part": "snippet",
            "q": query_full,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "key": self.api_key
        }
        
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        videos = []
        
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            
            snippet = item.get("snippet", {})
            videos.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
            })
        
        return videos
    
    def _deduplicate_videos(
        self,
        videos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate videos by video_id"""
        seen = set()
        unique = []
        
        for video in videos:
            video_id = video.get("video_id")
            if video_id and video_id not in seen:
                seen.add(video_id)
                unique.append(video)
        
        return unique
    
    def _enrich_video_details(
        self,
        videos: List[Dict[str, Any]]
    ) -> List[VideoSearchResult]:
        """
        Enrich videos with duration and channel country.
        
        Args:
            videos: List of basic video info
        
        Returns:
            List of enriched VideoSearchResult
        """
        if not videos:
            return []
        
        video_ids = [v["video_id"] for v in videos]
        
        # Get video details (duration)
        details_url = f"{self.base_url}/videos"
        details_params = {
            "part": "contentDetails",
            "id": ",".join(video_ids),
            "key": self.api_key
        }
        
        response = requests.get(details_url, params=details_params)
        response.raise_for_status()
        
        data = response.json()
        duration_map = {}
        
        for item in data.get("items", []):
            video_id = item.get("id")
            duration_iso = item.get("contentDetails", {}).get("duration", "")
            duration_seconds = self._parse_iso8601_duration(duration_iso)
            duration_map[video_id] = duration_seconds
        
        # Get channel countries
        channel_ids = list(set(v["channel_id"] for v in videos if v.get("channel_id")))
        channel_country_map = self._get_channel_countries(channel_ids)
        
        # Build enriched results
        results = []
        for video in videos:
            video_id = video["video_id"]
            duration_seconds = duration_map.get(video_id, 0)
            
            if duration_seconds == 0:
                continue  # Skip videos without duration
            
            channel_id = video.get("channel_id", "")
            country = channel_country_map.get(channel_id, "")
            
            results.append(VideoSearchResult(
                video_id=video_id,
                title=video["title"],
                channel=video["channel"],
                channel_id=channel_id,
                country=country,
                published_at=video["published_at"],
                url=f"https://www.youtube.com/watch?v={video_id}",
                duration_seconds=duration_seconds,
            ))
        
        return results
    
    def _get_channel_countries(
        self,
        channel_ids: List[str]
    ) -> Dict[str, str]:
        """Get country for each channel"""
        if not channel_ids:
            return {}
        
        channel_url = f"{self.base_url}/channels"
        params = {
            "part": "snippet",
            "id": ",".join(channel_ids),
            "key": self.api_key
        }
        
        try:
            response = requests.get(channel_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            country_map = {}
            
            for item in data.get("items", []):
                channel_id = item.get("id")
                country = item.get("snippet", {}).get("country", "")
                country_map[channel_id] = country
            
            return country_map
        
        except Exception as e:
            logger.warning(f"Failed to get channel countries: {e}")
            return {}
    
    def _parse_iso8601_duration(self, duration: str) -> int:
        """
        Parse ISO 8601 duration to seconds.
        
        Args:
            duration: ISO 8601 duration (e.g., PT15M33S)
        
        Returns:
            Total seconds
        """
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _filter_by_duration(
        self,
        videos: List[VideoSearchResult],
        min_seconds: int,
        max_seconds: int
    ) -> List[VideoSearchResult]:
        """Filter videos by duration range"""
        filtered = []
        
        for video in videos:
            if min_seconds <= video.duration_seconds <= max_seconds:
                logger.debug(
                    f"[OK] Accepted: {video.title[:50]}... ({video.duration_minutes} min)"
                )
                filtered.append(video)
            else:
                logger.debug(
                    f"[X] Excluded: {video.title[:50]}... ({video.duration_minutes} min)"
                )
        
        return filtered
    
    def _enrich_view_counts(
        self,
        videos: List[VideoSearchResult]
    ) -> List[VideoSearchResult]:
        """Enrich videos with view counts"""
        if not videos:
            return videos
        
        video_ids = [v.video_id for v in videos]
        
        videos_url = f"{self.base_url}/videos"
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": self.api_key
        }
        
        try:
            response = requests.get(videos_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            stats_map = {}
            
            for item in data.get("items", []):
                video_id = item.get("id")
                view_count = item.get("statistics", {}).get("viewCount")
                try:
                    stats_map[video_id] = int(view_count) if view_count else 0
                except Exception:
                    stats_map[video_id] = 0
            
            # Update view counts
            for video in videos:
                if video.video_id in stats_map:
                    video.view_count = stats_map[video.video_id]
        
        except Exception as e:
            logger.warning(f"Failed to enrich view counts: {e}")
        
        return videos

