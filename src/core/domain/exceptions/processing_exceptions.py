"""
Processing-related exceptions.

This module contains all exceptions related to content processing,
including AI processing, TTS, rendering, and pipeline execution.
"""

from __future__ import annotations
from typing import Any, Optional
from .base import (
    YouTubeTBException,
    ErrorSeverity,
    RecoveryStrategy,
    ExternalServiceException,
)


class AIProcessingException(ExternalServiceException):
    """Raised when AI processing fails"""
    
    def __init__(
        self,
        stage: str,
        reason: str,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = kwargs.pop("details", {})
        details.update({"stage": stage, "reason": reason})
        if model:
            details["model"] = model
        
        super().__init__(
            service_name="AI Processing",
            reason=f"{stage}: {reason}",
            details=details,
            **kwargs
        )
        self.error_code = "AI_PROCESSING_FAILED"


class TTSException(YouTubeTBException):
    """Raised when Text-to-Speech conversion fails"""
    
    def __init__(
        self,
        reason: str,
        segment_index: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if segment_index is not None:
            details["segment_index"] = segment_index
        
        super().__init__(
            message=f"TTS failed: {reason}",
            error_code="TTS_FAILED",
            details=details,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            **kwargs
        )


class RenderingException(YouTubeTBException):
    """Raised when video rendering fails"""
    
    def __init__(
        self,
        reason: str,
        stage: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if stage:
            details["stage"] = stage
        
        super().__init__(
            message=f"Rendering failed: {reason}",
            error_code="RENDERING_FAILED",
            details=details,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class FFmpegException(YouTubeTBException):
    """Raised when FFmpeg operation fails"""
    
    def __init__(
        self,
        operation: str,
        reason: str,
        command: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"operation": operation, "reason": reason}
        if command:
            details["command"] = command
        
        super().__init__(
            message=f"FFmpeg {operation} failed: {reason}",
            error_code="FFMPEG_FAILED",
            details=details,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class PipelineException(YouTubeTBException):
    """Raised when pipeline execution fails"""
    
    def __init__(
        self,
        stage: str,
        reason: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"Pipeline failed at {stage}: {reason}",
            error_code="PIPELINE_FAILED",
            details={"stage": stage, "reason": reason},
            severity=ErrorSeverity.CRITICAL,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class ScriptProcessingException(YouTubeTBException):
    """Raised when script processing fails"""
    
    def __init__(
        self,
        reason: str,
        script_length: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if script_length is not None:
            details["script_length"] = script_length
        
        super().__init__(
            message=f"Script processing failed: {reason}",
            error_code="SCRIPT_PROCESSING_FAILED",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class ThumbnailGenerationException(YouTubeTBException):
    """Raised when thumbnail generation fails"""
    
    def __init__(
        self,
        reason: str,
        thumbnail_type: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if thumbnail_type:
            details["thumbnail_type"] = thumbnail_type
        
        super().__init__(
            message=f"Thumbnail generation failed: {reason}",
            error_code="THUMBNAIL_GENERATION_FAILED",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )


class AudioMergeException(YouTubeTBException):
    """Raised when audio merging fails"""
    
    def __init__(
        self,
        reason: str,
        segment_count: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        details = {"reason": reason}
        if segment_count is not None:
            details["segment_count"] = segment_count
        
        super().__init__(
            message=f"Audio merge failed: {reason}",
            error_code="AUDIO_MERGE_FAILED",
            details=details,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )

