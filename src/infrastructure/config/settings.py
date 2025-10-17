"""
Centralized Configuration Management.

This module provides type-safe configuration management with:
- Environment variable support
- Configuration validation
- Multiple environment support (dev, prod)
- Secrets management

Usage:
    from src.infrastructure.config import get_settings
    
    settings = get_settings()
    api_key = settings.youtube_api_key
"""

from __future__ import annotations
from typing import Optional
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import os


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    All settings can be overridden via environment variables.
    """
    
    # ==================== General ====================
    
    app_name: str = "YouTubeTB"
    app_version: str = "2.0.0"
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # ==================== Paths ====================
    
    base_dir: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    output_dir: Path = Field(default_factory=lambda: Path.cwd() / "output")
    logs_dir: Path = Field(default_factory=lambda: Path.cwd() / "logs")
    config_dir: Path = Field(default_factory=lambda: Path.cwd() / "config")
    
    # ==================== YouTube API ====================
    
    youtube_api_key: str = Field(..., env="YT_API_KEY")
    youtube_client_secrets_file: Optional[Path] = Field(
        default=None,
        env="YT_CLIENT_SECRETS_FILE"
    )
    
    # ==================== Gemini API ====================
    
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.7, env="GEMINI_TEMPERATURE")
    gemini_max_tokens: int = Field(default=8000, env="GEMINI_MAX_TOKENS")
    
    # ==================== ElevenLabs TTS ====================
    
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(
        default="pNInz6obpgDQGcFmaJgB",  # Adam voice
        env="ELEVENLABS_VOICE_ID"
    )
    elevenlabs_model: str = Field(
        default="eleven_multilingual_v2",
        env="ELEVENLABS_MODEL"
    )
    
    # ==================== Processing ====================
    
    max_script_length: int = Field(default=950, env="MAX_SCRIPT_LENGTH")
    min_video_duration_seconds: int = Field(default=900, env="MIN_VIDEO_DURATION")
    max_video_duration_seconds: int = Field(default=7200, env="MAX_VIDEO_DURATION")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    
    # ==================== Rendering ====================
    
    video_width: int = Field(default=1920, env="VIDEO_WIDTH")
    video_height: int = Field(default=1080, env="VIDEO_HEIGHT")
    video_fps: int = Field(default=30, env="VIDEO_FPS")
    video_bitrate: str = Field(default="5000k", env="VIDEO_BITRATE")
    audio_bitrate: str = Field(default="192k", env="AUDIO_BITRATE")
    
    # ==================== Fonts ====================
    
    font_path: Optional[Path] = Field(
        default=None,
        env="FONT_PATH"
    )
    font_size: int = Field(default=72, env="FONT_SIZE")
    
    # ==================== Database ====================
    
    database_path: Path = Field(
        default_factory=lambda: Path.cwd() / "data" / "books.json",
        env="DATABASE_PATH"
    )
    
    # ==================== Logging ====================
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    enable_console_logging: bool = Field(default=True, env="ENABLE_CONSOLE_LOGGING")
    enable_file_logging: bool = Field(default=True, env="ENABLE_FILE_LOGGING")
    
    # ==================== Error Handling ====================
    
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay_seconds: int = Field(default=2, env="RETRY_DELAY_SECONDS")
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    circuit_breaker_timeout_seconds: int = Field(
        default=60,
        env="CIRCUIT_BREAKER_TIMEOUT"
    )
    
    # ==================== Monitoring ====================
    
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_export_interval_seconds: int = Field(
        default=300,
        env="METRICS_EXPORT_INTERVAL"
    )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("youtube_client_secrets_file", "font_path", pre=True)
    def validate_path(cls, v):
        """Convert string paths to Path objects"""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v
    
    def create_directories(self) -> None:
        """Create all required directories"""
        for dir_path in [
            self.data_dir,
            self.output_dir,
            self.logs_dir,
            self.config_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary"""
        return self.dict()
    
    def get_summary(self) -> dict:
        """Get settings summary (without sensitive data)"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "debug": self.debug,
            "gemini_model": self.gemini_model,
            "elevenlabs_model": self.elevenlabs_model,
            "video_resolution": f"{self.video_width}x{self.video_height}",
            "log_level": self.log_level,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance.
    
    Returns:
        Settings instance
    
    Example:
        >>> settings = get_settings()
        >>> print(settings.youtube_api_key)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    
    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    _settings.create_directories()
    return _settings

