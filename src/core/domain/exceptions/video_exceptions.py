"""
Video-related exceptions.

This module contains all exceptions related to video operations,
including search, download, transcription, and upload.
"""

from __future__ import annotations
from typing import Any, Optional
from .base import (
    YouTubeTBException,
    ErrorSeverity,
    RecoveryStrategy,
    ResourceNotFoundException,
)


class VideoNotFoundException(ResourceNotFoundException):
    """Raised when a video cannot be found"""
    
    def __init__(self, video_id: str, **kwargs: Any) -> None:
        super().__init__(
            resource_type="Video",
            resource_id=video_id,
            **kwargs
        )
        self.error_code = "VIDEO_NOT_FOUND"


class VideoSearchException(YouTubeTBException):
    """Raised when video search fails"""
    
    def __init__(self, query: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            message=f"Video search failed for '{query}': {reason}",
            error_code="VIDEO_SEARCH_FAILED",
            details={"query": query, "reason": reason},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            **kwargs
        )


class VideoDownloadException(YouTubeTBException):
    """Raised when video download fails"""
    
    def __init__(
        self,
        video_id: str,
        reason: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"Failed to download video {video_id}: {reason}",
            error_code="VIDEO_DOWNLOAD_FAILED",
            details={"video_id": video_id, "reason": reason},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class TranscriptionNotFoundException(YouTubeTBException):
    """Raised when video transcription/subtitles are not available"""
    
    def __init__(
        self,
        video_id: str,
        language: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"video_id": video_id}
        if language:
            details["language"] = language
        
        super().__init__(
            message=f"No transcription available for video {video_id}",
            error_code="TRANSCRIPTION_NOT_FOUND",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_strategy=RecoveryStrategy.FALLBACK,
            **kwargs
        )


class TranscriptionFailedException(YouTubeTBException):
    """Raised when transcription extraction fails"""
    
    def __init__(
        self,
        video_id: str,
        reason: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"Transcription failed for video {video_id}: {reason}",
            error_code="TRANSCRIPTION_FAILED",
            details={"video_id": video_id, "reason": reason},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            **kwargs
        )


class VideoUploadException(YouTubeTBException):
    """Raised when video upload to YouTube fails"""
    
    def __init__(
        self,
        reason: str,
        video_path: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if video_path:
            details["video_path"] = video_path
        
        super().__init__(
            message=f"Video upload failed: {reason}",
            error_code="VIDEO_UPLOAD_FAILED",
            details=details,
            severity=ErrorSeverity.CRITICAL,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            **kwargs
        )


class VideoValidationException(YouTubeTBException):
    """Raised when video fails validation"""
    
    def __init__(
        self,
        reason: str,
        video_id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if video_id:
            details["video_id"] = video_id
        
        super().__init__(
            message=f"Video validation failed: {reason}",
            error_code="VIDEO_VALIDATION_FAILED",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            recoverable=False,
            **kwargs
        )


class InsufficientVideoCandidatesException(YouTubeTBException):
    """Raised when not enough valid video candidates are found"""
    
    def __init__(
        self,
        found: int,
        required: int,
        query: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"Found only {found} candidates, need {required} for '{query}'",
            error_code="INSUFFICIENT_VIDEO_CANDIDATES",
            details={"found": found, "required": required, "query": query},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.FALLBACK,
            **kwargs
        )

