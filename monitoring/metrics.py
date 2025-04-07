"""
Metrics collection system for tracking server performance and resource usage.
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque

@dataclass
class Metric:
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, deque[Metric]] = {}
        self.max_history = max_history
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the metrics collector."""
        self._running = True
        self._task = asyncio.create_task(self._collect_metrics())

    async def stop(self):
        """Stop the metrics collector."""
        if self._running:
            self._running = False
            if self._task:
                await self._task

    def record(self, name: str, value: float, **labels):
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_history)
        
        metric = Metric(name=name, value=value, labels=labels)
        self.metrics[name].append(metric)

    def get_metric(self, name: str) -> List[Metric]:
        """Get all recorded values for a metric."""
        return list(self.metrics.get(name, []))

    def get_latest(self, name: str) -> Optional[Metric]:
        """Get the most recent value for a metric."""
        metrics = self.metrics.get(name, [])
        return metrics[-1] if metrics else None

    async def _collect_metrics(self):
        """Collect system metrics periodically."""
        while self._running:
            # Record system metrics
            self.record("system.cpu_percent", self._get_cpu_usage())
            self.record("system.memory_percent", self._get_memory_usage())
            
            # Record application metrics
            self.record("app.active_connections", self._get_connection_count())
            self.record("app.active_rooms", self._get_room_count())
            self.record("app.active_games", self._get_game_count())
            
            await asyncio.sleep(1)  # Collect metrics every second

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        import psutil
        return psutil.cpu_percent(interval=None)

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        import psutil
        return psutil.virtual_memory().percent

    def _get_connection_count(self) -> float:
        """Get current number of active connections."""
        # TODO: Implement real connection tracking
        return 0.0

    def _get_room_count(self) -> float:
        """Get current number of active rooms."""
        # TODO: Implement real room tracking
        return 0.0

    def _get_game_count(self) -> float:
        """Get current number of active games."""
        # TODO: Implement real game tracking
        return 0.0
