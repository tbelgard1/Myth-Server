"""
Performance tracking system for monitoring application performance.
"""

import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque

@dataclass
class PerformanceMetric:
    operation: str
    duration: float
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, str] = field(default_factory=dict)

class PerformanceTracker:
    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, deque[PerformanceMetric]] = {}
        self.max_history = max_history
        self._active_timers: Dict[str, float] = {}

    def start_operation(self, operation: str):
        """Start timing an operation."""
        self._active_timers[operation] = time.time()

    def stop_operation(self, operation: str, **context) -> Optional[PerformanceMetric]:
        """Stop timing an operation and record its duration."""
        start_time = self._active_timers.pop(operation, None)
        if start_time is None:
            return None

        duration = time.time() - start_time
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            context=context
        )

        if operation not in self.metrics:
            self.metrics[operation] = deque(maxlen=self.max_history)
        self.metrics[operation].append(metric)

        return metric

    def get_metrics(self, operation: str) -> List[PerformanceMetric]:
        """Get all metrics for a specific operation."""
        return list(self.metrics.get(operation, []))

    def get_average_duration(self, operation: str) -> Optional[float]:
        """Get the average duration of an operation."""
        metrics = self.metrics.get(operation, [])
        if not metrics:
            return None
        return sum(m.duration for m in metrics) / len(metrics)

    def get_percentile_duration(self, operation: str, percentile: float) -> Optional[float]:
        """Get the duration at a specific percentile for an operation."""
        metrics = self.metrics.get(operation, [])
        if not metrics:
            return None
        
        sorted_durations = sorted(m.duration for m in metrics)
        index = int(len(sorted_durations) * percentile)
        return sorted_durations[index]

    async def track_async(self, operation: str, coro, **context):
        """Track the duration of an async operation."""
        self.start_operation(operation)
        try:
            result = await coro
            return result
        finally:
            self.stop_operation(operation, **context)

    def track_sync(self, operation: str, func, *args, **kwargs):
        """Track the duration of a sync operation."""
        self.start_operation(operation)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            context = {"args": str(args), "kwargs": str(kwargs)}
            self.stop_operation(operation, **context)
