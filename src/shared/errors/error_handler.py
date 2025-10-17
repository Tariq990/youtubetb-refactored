"""
Central Error Handling System.

This module provides intelligent error handling with:
- Automatic error logging
- Recovery strategies
- Error reporting
- Circuit breaker pattern
- Retry with backoff

Usage:
    from src.shared.errors import ErrorHandler, get_error_handler
    
    error_handler = get_error_handler()
    
    # Decorator usage
    @error_handler.with_error_handling("search_videos")
    def search_videos(query: str):
        # Your code here
        pass
    
    # Manual usage
    try:
        result = risky_operation()
    except Exception as e:
        error_handler.handle_error(e, context={"operation": "search"})
"""

from __future__ import annotations
from typing import Callable, TypeVar, ParamSpec, Any, Optional
from functools import wraps
import time
from datetime import datetime, timedelta

from src.core.domain.exceptions import (
    YouTubeTBException,
    RecoveryStrategy,
    ErrorSeverity,
)
from src.shared.logging import get_logger


P = ParamSpec('P')
T = TypeVar('T')


class ErrorHandler:
    """
    Central error handling system with recovery strategies.
    
    This class provides:
    - Automatic error logging
    - Error recovery with multiple strategies
    - Circuit breaker pattern
    - Error reporting and notifications
    """
    
    def __init__(self, logger_name: str = "youtubetb.errors"):
        """
        Initialize error handler.
        
        Args:
            logger_name: Name for the error logger
        """
        self.logger = get_logger(logger_name)
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.error_counts: dict[str, int] = {}
        self.last_errors: dict[str, datetime] = {}
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[dict[str, Any]] = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        """
        Handle an error with logging and recovery.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            notify: Whether to send notifications
        
        Returns:
            Dictionary with error handling result
        """
        context = context or {}
        
        # Convert to YouTubeTBException if needed
        if not isinstance(error, YouTubeTBException):
            error = self._wrap_exception(error)
        
        # Log the error
        self.logger.error(
            f"Error occurred: {error.message}",
            exc_info=True,
            error_code=error.error_code,
            severity=error.severity.value,
            **context
        )
        
        # Track error
        self._track_error(error, context)
        
        # Send notification if needed
        if notify and self._should_notify(error):
            self._notify_error(error, context)
        
        # Attempt recovery if possible
        if error.recoverable:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result["success"]:
                self.logger.info(
                    f"Successfully recovered from error: {error.error_code}",
                    strategy=error.retry_strategy.value,
                    **context
                )
                return recovery_result
        
        # Return error info
        return {
            "success": False,
            "error": error.to_dict(),
            "recovered": False,
            "context": context,
        }
    
    def with_error_handling(
        self,
        operation_name: str,
        context: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """
        Decorator for automatic error handling.
        
        Args:
            operation_name: Name of the operation
            context: Additional context
            max_retries: Maximum retry attempts
        
        Returns:
            Decorated function
        
        Example:
            @error_handler.with_error_handling("search_videos")
            def search_videos(query: str):
                # Your code here
                pass
        """
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                error_context = {
                    "operation": operation_name,
                    "function": func.__name__,
                    **(context or {}),
                }
                
                last_error = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    
                    except Exception as e:
                        last_error = e
                        error_context["attempt"] = attempt + 1
                        
                        result = self.handle_error(e, error_context, notify=False)
                        
                        if result.get("recovered"):
                            return result.get("result")
                        
                        if attempt < max_retries - 1:
                            # Wait before retry
                            delay = 2 ** attempt  # Exponential backoff
                            self.logger.warning(
                                f"Retrying {operation_name} after {delay}s",
                                attempt=attempt + 1,
                                max_retries=max_retries,
                            )
                            time.sleep(delay)
                        else:
                            # Final attempt failed
                            self.logger.error(
                                f"All retry attempts failed for {operation_name}",
                                attempts=max_retries,
                                **error_context
                            )
                
                # Re-raise the last error
                raise last_error
            
            return wrapper
        return decorator
    
    def _wrap_exception(self, error: Exception) -> YouTubeTBException:
        """Wrap unknown exceptions"""
        return YouTubeTBException(
            message=str(error),
            error_code="UNKNOWN_ERROR",
            details={
                "original_type": type(error).__name__,
                "original_message": str(error),
            },
            severity=ErrorSeverity.HIGH,
        )
    
    def _track_error(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> None:
        """Track error occurrence"""
        error_key = f"{error.error_code}:{context.get('operation', 'unknown')}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = datetime.now()
    
    def _should_notify(self, error: YouTubeTBException) -> bool:
        """Determine if error should trigger notification"""
        # Notify for critical errors
        if error.severity == ErrorSeverity.CRITICAL:
            return True
        
        # Notify if error occurs frequently
        error_key = error.error_code
        if self.error_counts.get(error_key, 0) > 5:
            return True
        
        return False
    
    def _notify_error(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> None:
        """Send error notification"""
        # Log critical error
        self.logger.critical(
            f"Critical error notification: {error.message}",
            error_code=error.error_code,
            severity=error.severity.value,
            **context
        )
        
        # TODO: Implement actual notification (email, Slack, etc.)
    
    def _attempt_recovery(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Attempt to recover from error"""
        strategy = error.retry_strategy
        
        if strategy == RecoveryStrategy.RETRY:
            return self._retry_simple(error, context)
        
        elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return self._retry_with_backoff(error, context)
        
        elif strategy == RecoveryStrategy.FALLBACK:
            return self._fallback(error, context)
        
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            return self._circuit_breaker(error, context)
        
        elif strategy == RecoveryStrategy.WAIT_AND_RETRY:
            return self._wait_and_retry(error, context)
        
        return {"success": False, "recovered": False}
    
    def _retry_simple(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Simple retry without delay"""
        return {"success": False, "recovered": False, "strategy": "retry"}
    
    def _retry_with_backoff(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Retry with exponential backoff"""
        return {"success": False, "recovered": False, "strategy": "retry_with_backoff"}
    
    def _fallback(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Try fallback approach"""
        candidates = context.get("candidates", [])
        if candidates:
            self.logger.info(
                "Attempting fallback to next candidate",
                candidates_remaining=len(candidates)
            )
            return {
                "success": True,
                "recovered": True,
                "strategy": "fallback",
                "next_candidate": candidates[0] if candidates else None,
            }
        
        return {"success": False, "recovered": False}
    
    def _circuit_breaker(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Circuit breaker pattern"""
        service = error.details.get("service", "unknown")
        
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker(service)
        
        breaker = self.circuit_breakers[service]
        breaker.record_failure()
        
        if breaker.is_open():
            self.logger.warning(
                f"Circuit breaker open for {service}",
                failures=breaker.failure_count,
            )
            return {"success": False, "recovered": False, "circuit_open": True}
        
        return {"success": False, "recovered": False}
    
    def _wait_and_retry(
        self,
        error: YouTubeTBException,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Wait for specified time then retry"""
        retry_after = error.details.get("retry_after", 60)
        self.logger.info(
            f"Waiting {retry_after}s before retry",
            error_code=error.error_code,
        )
        time.sleep(retry_after)
        
        return {"success": False, "recovered": False, "waited": retry_after}


class CircuitBreaker:
    """
    Circuit breaker for external services.
    
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            service_name: Name of the service
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds before attempting to close circuit
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def record_failure(self) -> None:
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def record_success(self) -> None:
        """Record a success"""
        self.failure_count = 0
        self.state = "closed"
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state != "open":
            return False
        
        # Check if timeout has passed
        if self.last_failure_time:
            if datetime.now() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                return False
        
        return True


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get global error handler instance.
    
    Returns:
        ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

