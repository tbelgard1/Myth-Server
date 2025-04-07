"""
Monitoring service for coordinating metrics collection, logging, and performance tracking.
"""

import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.monitoring.metrics import MetricsCollector
from core.monitoring.logger import MonitoringLogger
from core.monitoring.tracker import PerformanceTracker

@dataclass
class Alert:
    level: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, str] = field(default_factory=dict)

class MonitoringService:
    def __init__(self):
        self.metrics = MetricsCollector()
        self.logger = MonitoringLogger("myth.monitoring")
        self.tracker = PerformanceTracker()
        self._alert_handlers: Dict[str, callable] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the monitoring service."""
        self._running = True
        await self.metrics.start()
        self._task = asyncio.create_task(self._monitor_performance())
        self.logger.info("Monitoring service started")

    async def stop(self):
        """Stop the monitoring service."""
        if self._running:
            self._running = False
            await self.metrics.stop()
            if self._task:
                await self._task
            self.logger.info("Monitoring service stopped")

    def register_alert_handler(self, level: str, handler: callable):
        """Register a handler for alerts of a specific level."""
        self._alert_handlers[level] = handler

    def alert(self, level: str, message: str, **context):
        """Raise an alert."""
        alert = Alert(level=level, message=message, context=context)
        
        # Log the alert
        self.logger.log_event(level, message, **context)
        
        # Call registered handler if exists
        handler = self._alert_handlers.get(level)
        if handler:
            asyncio.create_task(handler(alert))

    async def _monitor_performance(self):
        """Monitor performance metrics and raise alerts if needed."""
        while self._running:
            # Check CPU usage
            cpu_usage = self.metrics.get_latest("system.cpu_percent")
            if cpu_usage and cpu_usage.value > 80:
                self.alert(
                    "WARNING",
                    "High CPU usage detected",
                    cpu_percent=f"{cpu_usage.value:.1f}%"
                )

            # Check memory usage
            memory_usage = self.metrics.get_latest("system.memory_percent")
            if memory_usage and memory_usage.value > 80:
                self.alert(
                    "WARNING",
                    "High memory usage detected",
                    memory_percent=f"{memory_usage.value:.1f}%"
                )

            # Check connection count
            connections = self.metrics.get_latest("app.active_connections")
            if connections and connections.value > 90:
                self.alert(
                    "WARNING",
                    "High connection count",
                    connection_count=str(int(connections.value))
                )

            # Check operation latencies
            for operation in ["game_update", "room_update", "player_update"]:
                avg_duration = self.tracker.get_average_duration(operation)
                if avg_duration and avg_duration > 0.1:  # 100ms threshold
                    self.alert(
                        "WARNING",
                        f"High {operation} latency",
                        duration=f"{avg_duration*1000:.1f}ms"
                    )

            await asyncio.sleep(5)  # Check every 5 seconds
