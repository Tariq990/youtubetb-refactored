"""
Base exception classes for YouTubeTB application.

This module provides the foundation for all custom exceptions in the application,
implementing a hierarchical error handling system with recovery strategies.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    """Recovery strategy types"""
    
    NONE = "none"
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    WAIT_AND_RETRY = "wait_and_retry"


class YouTubeTBException(Exception):
    """
    Base exception for all YouTubeTB errors.
    
    This exception provides:
    - Error codes for programmatic handling
    - Severity levels for prioritization
    - Recovery strategies for automatic recovery
    - Detailed context for debugging
    - Structured error information for logging
    
    Attributes:
        message: Human-readable error message
        error_code: Unique error code for programmatic handling
        details: Additional context and debugging information
        severity: Error severity level
        recoverable: Whether the error can be recovered from
        retry_strategy: Strategy to use for recovery
        timestamp: When the error occurred
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recoverable: bool = False,
        retry_strategy: RecoveryStrategy = RecoveryStrategy.NONE,
    ) -> None:
        """
        Initialize YouTubeTB exception.
        
        Args:
            message: Human-readable error message
            error_code: Unique error code (e.g., "VIDEO_NOT_FOUND")
            details: Additional context (e.g., {"video_id": "abc123"})
            severity: Error severity level
            recoverable: Whether automatic recovery should be attempted
            retry_strategy: Strategy to use for recovery
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.severity = severity
        self.recoverable = recoverable
        self.retry_strategy = retry_strategy
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "retry_strategy": self.retry_strategy.value,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        """String representation of the exception"""
        return f"[{self.error_code}] {self.message}"
    
    def __repr__(self) -> str:
        """Detailed representation of the exception"""
        return (
            f"{self.__class__.__name__}("
            f"error_code='{self.error_code}', "
            f"message='{self.message}', "
            f"severity={self.severity.value})"
        )


class ConfigurationException(YouTubeTBException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            **kwargs
        )


class ValidationException(YouTubeTBException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs: Any) -> None:
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            **kwargs
        )


class ResourceNotFoundException(YouTubeTBException):
    """Raised when a required resource is not found"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_strategy=RecoveryStrategy.FALLBACK,
            **kwargs
        )


class ExternalServiceException(YouTubeTBException):
    """Raised when an external service fails"""
    
    def __init__(
        self,
        service_name: str,
        reason: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"{service_name} service failed: {reason}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name, "reason": reason},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            **kwargs
        )


class RateLimitException(YouTubeTBException):
    """Raised when API rate limit is exceeded"""
    
    def __init__(
        self,
        service_name: str,
        retry_after: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        details = {"service": service_name}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=f"Rate limit exceeded for {service_name}",
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            retry_strategy=RecoveryStrategy.WAIT_AND_RETRY,
            **kwargs
        )


class ProcessingException(YouTubeTBException):
    """Raised when processing fails"""
    
    def __init__(
        self,
        stage: str,
        reason: str,
        **kwargs: Any
    ) -> None:
        super().__init__(
            message=f"Processing failed at {stage}: {reason}",
            error_code="PROCESSING_ERROR",
            details={"stage": stage, "reason": reason},
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            retry_strategy=RecoveryStrategy.RETRY,
            **kwargs
        )

