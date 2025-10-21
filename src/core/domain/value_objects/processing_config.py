"""
ProcessingConfig Value Object

Represents configuration for processing pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProcessingConfig:
    """
    Value object representing processing configuration.
    
    Attributes:
        max_script_length: Maximum script length in characters
        min_video_duration: Minimum video duration in seconds
        max_video_duration: Maximum video duration in seconds
        video_width: Video width in pixels
        video_height: Video height in pixels
        video_fps: Video frames per second
        gemini_model: Gemini AI model name
        elevenlabs_voice_id: ElevenLabs voice ID
        language: Processing language (ar, en)
    """
    
    max_script_length: int = 950
    min_video_duration: int = 900  # 15 minutes
    max_video_duration: int = 3300  # 55 minutes
    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30
    gemini_model: str = "gemini-2.5-flash-latest"
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"
    language: str = "ar"
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_script_length < 100:
            raise ValueError("max_script_length must be at least 100")
        
        if self.min_video_duration < 0:
            raise ValueError("min_video_duration cannot be negative")
        
        if self.max_video_duration <= self.min_video_duration:
            raise ValueError("max_video_duration must be greater than min_video_duration")
        
        if self.video_width < 640 or self.video_height < 480:
            raise ValueError("Video dimensions must be at least 640x480")
        
        if self.video_fps < 1 or self.video_fps > 60:
            raise ValueError("video_fps must be between 1 and 60")
    
    @classmethod
    def from_env(cls) -> ProcessingConfig:
        """Create configuration from environment variables."""
        import os
        
        return cls(
            max_script_length=int(os.getenv("MAX_SCRIPT_LENGTH", "950")),
            min_video_duration=int(os.getenv("MIN_VIDEO_DURATION", "900")),
            max_video_duration=int(os.getenv("MAX_VIDEO_DURATION", "3300")),
            video_width=int(os.getenv("VIDEO_WIDTH", "1920")),
            video_height=int(os.getenv("VIDEO_HEIGHT", "1080")),
            video_fps=int(os.getenv("VIDEO_FPS", "30")),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-latest"),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"),
            language=os.getenv("PROCESSING_LANGUAGE", "ar"),
        )
    
    def with_language(self, language: str) -> ProcessingConfig:
        """Create a new config with different language."""
        return ProcessingConfig(
            max_script_length=self.max_script_length,
            min_video_duration=self.min_video_duration,
            max_video_duration=self.max_video_duration,
            video_width=self.video_width,
            video_height=self.video_height,
            video_fps=self.video_fps,
            gemini_model=self.gemini_model,
            elevenlabs_voice_id=self.elevenlabs_voice_id,
            language=language,
        )
    
    @property
    def video_resolution(self) -> str:
        """Get video resolution as string."""
        return f"{self.video_width}x{self.video_height}"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ProcessingConfig(resolution={self.video_resolution}, lang={self.language})"
