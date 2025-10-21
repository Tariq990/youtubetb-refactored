"""
Unit tests for Video entity
"""

import pytest
from datetime import datetime

from src.core.domain.entities import Video


class TestVideoEntity:
    """Tests for Video entity"""
    
    def test_create_video(self):
        """Test creating a video"""
        video = Video(
            video_id="abc123",
            title="Book Summary",
            channel_name="Test Channel",
            duration=1200,
            url="https://youtube.com/watch?v=abc123"
        )
        
        assert video.video_id == "abc123"
        assert video.title == "Book Summary"
        assert video.duration == 1200
    
    def test_create_video_empty_id_raises_error(self):
        """Test that empty video_id raises ValueError"""
        with pytest.raises(ValueError, match="Video ID cannot be empty"):
            Video(
                video_id="",
                title="Test",
                channel_name="Test",
                duration=100,
                url="https://youtube.com"
            )
    
    def test_create_video_empty_title_raises_error(self):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            Video(
                video_id="abc123",
                title="",
                channel_name="Test",
                duration=100,
                url="https://youtube.com"
            )
    
    def test_create_video_negative_duration_raises_error(self):
        """Test that negative duration raises ValueError"""
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            Video(
                video_id="abc123",
                title="Test",
                channel_name="Test",
                duration=-100,
                url="https://youtube.com"
            )
    
    def test_duration_formatted(self):
        """Test formatted duration property"""
        video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=3665,  # 1 hour, 1 minute, 5 seconds
            url="https://youtube.com"
        )
        
        assert video.duration_formatted == "1:01:05"
    
    def test_engagement_score(self):
        """Test engagement score calculation"""
        video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=1000,
            url="https://youtube.com",
            view_count=1000,
            like_count=100
        )
        
        # 100 likes / 1000 views * 100 = 10%
        assert video.engagement_score == 10.0
    
    def test_engagement_score_zero_views(self):
        """Test engagement score with zero views"""
        video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=1000,
            url="https://youtube.com",
            view_count=0,
            like_count=0
        )
        
        assert video.engagement_score == 0.0
    
    def test_has_transcript(self):
        """Test has_transcript method"""
        video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=1000,
            url="https://youtube.com"
        )
        
        assert not video.has_transcript()
        
        video.transcript = "This is a transcript"
        assert video.has_transcript()
    
    def test_is_long_form(self):
        """Test is_long_form method"""
        short_video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=600,  # 10 minutes
            url="https://youtube.com"
        )
        
        long_video = Video(
            video_id="xyz789",
            title="Test",
            channel_name="Test",
            duration=1800,  # 30 minutes
            url="https://youtube.com"
        )
        
        assert not short_video.is_long_form()
        assert long_video.is_long_form()
    
    def test_is_short(self):
        """Test is_short method"""
        short_video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=45,
            url="https://youtube.com"
        )
        
        long_video = Video(
            video_id="xyz789",
            title="Test",
            channel_name="Test",
            duration=120,
            url="https://youtube.com"
        )
        
        assert short_video.is_short()
        assert not long_video.is_short()
    
    def test_mark_as_selected(self):
        """Test mark_as_selected method"""
        video = Video(
            video_id="abc123",
            title="Test",
            channel_name="Test",
            duration=1000,
            url="https://youtube.com"
        )
        
        assert not video.selected
        
        video.mark_as_selected()
        assert video.selected
    
    def test_to_dict(self):
        """Test converting video to dictionary"""
        video = Video(
            video_id="abc123",
            title="Test Video",
            channel_name="Test Channel",
            duration=1200,
            url="https://youtube.com/watch?v=abc123",
            view_count=5000,
            like_count=250
        )
        
        data = video.to_dict()
        
        assert data["video_id"] == "abc123"
        assert data["title"] == "Test Video"
        assert data["view_count"] == 5000
        assert data["like_count"] == 250
    
    def test_from_dict(self):
        """Test creating video from dictionary"""
        data = {
            "video_id": "abc123",
            "title": "Test Video",
            "channel_name": "Test Channel",
            "duration": 1200,
            "url": "https://youtube.com/watch?v=abc123"
        }
        
        video = Video.from_dict(data)
        
        assert video.video_id == "abc123"
        assert video.title == "Test Video"
        assert video.duration == 1200
