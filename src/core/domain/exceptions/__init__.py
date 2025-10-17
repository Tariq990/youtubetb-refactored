"""
YouTubeTB Exception System.

This package provides a comprehensive exception hierarchy for the YouTubeTB application,
enabling intelligent error handling, recovery strategies, and detailed error reporting.

Exception Hierarchy:
    YouTubeTBException (base)
    ├── ConfigurationException
    ├── ValidationException
    ├── ResourceNotFoundException
    │   └── VideoNotFoundException
    ├── ExternalServiceException
    │   └── AIProcessingException
    ├── RateLimitException
    ├── ProcessingException
    ├── VideoSearchException
    ├── VideoDownloadException
    ├── TranscriptionNotFoundException
    ├── TranscriptionFailedException
    ├── VideoUploadException
    ├── VideoValidationException
    ├── InsufficientVideoCandidatesException
    ├── TTSException
    ├── RenderingException
    ├── FFmpegException
    ├── PipelineException
    ├── ScriptProcessingException
    ├── ThumbnailGenerationException
    └── AudioMergeException

Usage:
    from src.core.domain.exceptions import VideoNotFoundException, ErrorSeverity
    
    raise VideoNotFoundException(
        video_id="abc123",
        details={"query": "Atomic Habits"}
    )
"""

# Base exceptions
from .base import (
    YouTubeTBException,
    ConfigurationException,
    ValidationException,
    ResourceNotFoundException,
    ExternalServiceException,
    RateLimitException,
    ProcessingException,
    ErrorSeverity,
    RecoveryStrategy,
)

# Video exceptions
from .video_exceptions import (
    VideoNotFoundException,
    VideoSearchException,
    VideoDownloadException,
    TranscriptionNotFoundException,
    TranscriptionFailedException,
    VideoUploadException,
    VideoValidationException,
    InsufficientVideoCandidatesException,
)

# Processing exceptions
from .processing_exceptions import (
    AIProcessingException,
    TTSException,
    RenderingException,
    FFmpegException,
    PipelineException,
    ScriptProcessingException,
    ThumbnailGenerationException,
    AudioMergeException,
)

__all__ = [
    # Base
    "YouTubeTBException",
    "ConfigurationException",
    "ValidationException",
    "ResourceNotFoundException",
    "ExternalServiceException",
    "RateLimitException",
    "ProcessingException",
    "ErrorSeverity",
    "RecoveryStrategy",
    # Video
    "VideoNotFoundException",
    "VideoSearchException",
    "VideoDownloadException",
    "TranscriptionNotFoundException",
    "TranscriptionFailedException",
    "VideoUploadException",
    "VideoValidationException",
    "InsufficientVideoCandidatesException",
    # Processing
    "AIProcessingException",
    "TTSException",
    "RenderingException",
    "FFmpegException",
    "PipelineException",
    "ScriptProcessingException",
    "ThumbnailGenerationException",
    "AudioMergeException",
]

