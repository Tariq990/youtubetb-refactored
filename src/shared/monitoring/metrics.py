"""
Monitoring and Metrics System.

This module provides comprehensive monitoring capabilities:
- Performance metrics tracking
- Resource usage monitoring
- Pipeline stage timing
- Error rate tracking
- Success rate calculation

Usage:
    from src.shared.monitoring import get_metrics_tracker
    
    tracker = get_metrics_tracker()
    
    with tracker.track_operation("search_videos"):
        # Your code here
        pass
    
    # Get metrics
    metrics = tracker.get_metrics()
"""

from __future__ import annotations
from typing import Optional, Dict, Any, ContextManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
import time
import psutil
from collections import defaultdict

from src.shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""
    
    operation_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_seconds: float = 0.0
    min_duration_seconds: float = float('inf')
    max_duration_seconds: float = 0.0
    last_call_time: Optional[datetime] = None
    
    @property
    def average_duration_seconds(self) -> float:
        """Calculate average duration"""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration_seconds / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)"""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate (0.0 to 1.0)"""
        return 1.0 - self.success_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "operation_name": self.operation_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": f"{self.success_rate * 100:.2f}%",
            "average_duration": f"{self.average_duration_seconds:.2f}s",
            "min_duration": f"{self.min_duration_seconds:.2f}s",
            "max_duration": f"{self.max_duration_seconds:.2f}s",
            "last_call": self.last_call_time.isoformat() if self.last_call_time else None,
        }


@dataclass
class SystemMetrics:
    """System resource metrics"""
    
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_percent": f"{self.cpu_percent:.1f}%",
            "memory_percent": f"{self.memory_percent:.1f}%",
            "memory_used_mb": f"{self.memory_used_mb:.1f}MB",
            "memory_available_mb": f"{self.memory_available_mb:.1f}MB",
            "disk_usage_percent": f"{self.disk_usage_percent:.1f}%",
            "timestamp": self.timestamp.isoformat(),
        }


class MetricsTracker:
    """
    Comprehensive metrics tracking system.
    
    Tracks:
    - Operation performance (duration, success rate)
    - System resources (CPU, memory, disk)
    - Pipeline stage metrics
    - Error rates
    """
    
    def __init__(self):
        """Initialize metrics tracker"""
        self.operations: Dict[str, OperationMetrics] = defaultdict(
            lambda: OperationMetrics(operation_name="unknown")
        )
        self.system_metrics_history: list[SystemMetrics] = []
        self.start_time = datetime.now()
    
    @contextmanager
    def track_operation(
        self,
        operation_name: str,
        auto_log: bool = True
    ) -> ContextManager[OperationMetrics]:
        """
        Context manager to track operation metrics.
        
        Args:
            operation_name: Name of the operation
            auto_log: Whether to log metrics automatically
        
        Yields:
            OperationMetrics instance
        
        Example:
            with tracker.track_operation("search_videos") as metrics:
                # Your code here
                pass
        """
        metrics = self.operations[operation_name]
        metrics.operation_name = operation_name
        
        start_time = time.time()
        success = False
        
        try:
            yield metrics
            success = True
        
        except Exception as e:
            success = False
            raise
        
        finally:
            duration = time.time() - start_time
            
            # Update metrics
            metrics.total_calls += 1
            metrics.total_duration_seconds += duration
            metrics.min_duration_seconds = min(metrics.min_duration_seconds, duration)
            metrics.max_duration_seconds = max(metrics.max_duration_seconds, duration)
            metrics.last_call_time = datetime.now()
            
            if success:
                metrics.successful_calls += 1
            else:
                metrics.failed_calls += 1
            
            # Log if enabled
            if auto_log:
                logger.debug(
                    f"Operation completed: {operation_name}",
                    duration=f"{duration:.2f}s",
                    success=success,
                    total_calls=metrics.total_calls,
                    success_rate=f"{metrics.success_rate * 100:.1f}%"
                )
    
    def record_operation(
        self,
        operation_name: str,
        duration_seconds: float,
        success: bool = True
    ) -> None:
        """
        Manually record operation metrics.
        
        Args:
            operation_name: Name of the operation
            duration_seconds: Duration in seconds
            success: Whether operation succeeded
        """
        metrics = self.operations[operation_name]
        metrics.operation_name = operation_name
        
        metrics.total_calls += 1
        metrics.total_duration_seconds += duration_seconds
        metrics.min_duration_seconds = min(metrics.min_duration_seconds, duration_seconds)
        metrics.max_duration_seconds = max(metrics.max_duration_seconds, duration_seconds)
        metrics.last_call_time = datetime.now()
        
        if success:
            metrics.successful_calls += 1
        else:
            metrics.failed_calls += 1
    
    def capture_system_metrics(self) -> SystemMetrics:
        """
        Capture current system resource metrics.
        
        Returns:
            SystemMetrics instance
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
        )
        
        self.system_metrics_history.append(metrics)
        
        # Keep only last 1000 entries
        if len(self.system_metrics_history) > 1000:
            self.system_metrics_history = self.system_metrics_history[-1000:]
        
        return metrics
    
    def get_operation_metrics(self, operation_name: str) -> Optional[OperationMetrics]:
        """
        Get metrics for specific operation.
        
        Args:
            operation_name: Name of the operation
        
        Returns:
            OperationMetrics or None if not found
        """
        return self.operations.get(operation_name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "operations": {
                name: metrics.to_dict()
                for name, metrics in self.operations.items()
            },
            "system": self.capture_system_metrics().to_dict(),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of key metrics.
        
        Returns:
            Dictionary with summary metrics
        """
        total_calls = sum(m.total_calls for m in self.operations.values())
        total_successes = sum(m.successful_calls for m in self.operations.values())
        total_failures = sum(m.failed_calls for m in self.operations.values())
        
        overall_success_rate = (
            total_successes / total_calls if total_calls > 0 else 0.0
        )
        
        return {
            "uptime": str(datetime.now() - self.start_time),
            "total_operations": len(self.operations),
            "total_calls": total_calls,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": f"{overall_success_rate * 100:.2f}%",
            "most_called_operation": self._get_most_called_operation(),
            "slowest_operation": self._get_slowest_operation(),
        }
    
    def _get_most_called_operation(self) -> Optional[str]:
        """Get the most frequently called operation"""
        if not self.operations:
            return None
        
        return max(
            self.operations.items(),
            key=lambda x: x[1].total_calls
        )[0]
    
    def _get_slowest_operation(self) -> Optional[str]:
        """Get the slowest operation by average duration"""
        if not self.operations:
            return None
        
        return max(
            self.operations.items(),
            key=lambda x: x[1].average_duration_seconds
        )[0]
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.operations.clear()
        self.system_metrics_history.clear()
        self.start_time = datetime.now()
        logger.info("Metrics tracker reset")


# Global metrics tracker instance
_metrics_tracker: Optional[MetricsTracker] = None


def get_metrics_tracker() -> MetricsTracker:
    """
    Get global metrics tracker instance.
    
    Returns:
        MetricsTracker instance
    """
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker

