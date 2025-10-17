"""
Unified Logging System for YouTubeTB.

This module provides a structured logging system with:
- Multiple output formats (JSON, colored console)
- Automatic log rotation
- Context-aware logging
- Performance tracking
- Error tracking with stack traces

Usage:
    from src.shared.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing started", book_name="Atomic Habits", stage="search")
    logger.error("Processing failed", error=str(e), exc_info=True)
"""

from __future__ import annotations
import logging
import logging.handlers
from pathlib import Path
from typing import Any, Optional
import json
from datetime import datetime
import sys
from rich.console import Console
from rich.logging import RichHandler


class StructuredLogger:
    """
    Structured logger with JSON output and rich console formatting.
    
    This logger provides:
    - Structured logging with key-value pairs
    - JSON output for machine parsing
    - Colored console output for humans
    - Automatic log rotation
    - Context preservation
    """
    
    def __init__(
        self,
        name: str,
        log_dir: Optional[Path] = None,
        level: int = logging.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
    ) -> None:
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            log_dir: Directory for log files
            level: Logging level
            enable_console: Enable console output
            enable_file: Enable file output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        if enable_console:
            self._add_console_handler()
        
        if enable_file and log_dir:
            self._add_file_handlers(log_dir)
    
    def _add_console_handler(self) -> None:
        """Add rich console handler"""
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=False,
        )
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
    
    def _add_file_handlers(self, log_dir: Path) -> None:
        """Add file handlers with rotation"""
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file (JSON format)
        main_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.logger.name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        main_handler.setFormatter(JSONFormatter())
        main_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(main_handler)
        
        # Error log file (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.logger.name}.errors.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
    
    def _log(
        self,
        level: int,
        message: str,
        exc_info: bool = False,
        **kwargs: Any
    ) -> None:
        """Internal logging method with structured data"""
        extra = {"structured_data": kwargs}
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(
        self,
        message: str,
        exc_info: bool = False,
        **kwargs: Any
    ) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(
        self,
        message: str,
        exc_info: bool = False,
        **kwargs: Any
    ) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback"""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logs.
    
    Outputs logs in JSON format for easy parsing and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add structured data if present
        if hasattr(record, "structured_data"):
            log_data["data"] = record.structured_data
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


# Global logger cache
_loggers: dict[str, StructuredLogger] = {}


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (usually __name__)
        log_dir: Directory for log files
        level: Logging level
    
    Returns:
        StructuredLogger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", book="Atomic Habits")
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(
            name=name,
            log_dir=log_dir,
            level=level,
        )
    
    return _loggers[name]


def configure_logging(
    log_dir: Path,
    level: int = logging.INFO,
    enable_console: bool = True,
) -> None:
    """
    Configure global logging settings.
    
    Args:
        log_dir: Directory for log files
        level: Default logging level
        enable_console: Enable console output
    """
    # Clear existing loggers
    _loggers.clear()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    if enable_console:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
        )
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

