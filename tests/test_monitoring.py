"""
Tests for the monitoring system components.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from core.monitoring.metrics import MetricsCollector, Metric
from core.monitoring.logger import MonitoringLogger, LogEvent
from core.monitoring.tracker import PerformanceTracker, PerformanceMetric

@pytest.fixture
def metrics_collector():
    collector = MetricsCollector(max_history=100)
    return collector

@pytest.fixture
def monitoring_logger():
    return MonitoringLogger("test_logger")

@pytest.fixture
def performance_tracker():
    return PerformanceTracker(max_history=100)

class TestMetricsCollector:
    async def test_start_stop(self, metrics_collector):
        """Test starting and stopping the metrics collector."""
        await metrics_collector.start()
        assert metrics_collector._running
        assert metrics_collector._task is not None
        
        await metrics_collector.stop()
        assert not metrics_collector._running
        assert metrics_collector._task is not None

    def test_record_metric(self, metrics_collector):
        """Test recording a metric."""
        metrics_collector.record("test_metric", 42.0, label="test")
        metrics = metrics_collector.get_metric("test_metric")
        
        assert len(metrics) == 1
        assert metrics[0].name == "test_metric"
        assert metrics[0].value == 42.0
        assert metrics[0].labels == {"label": "test"}

    def test_get_latest_metric(self, metrics_collector):
        """Test getting the latest metric value."""
        metrics_collector.record("test_metric", 1.0)
        metrics_collector.record("test_metric", 2.0)
        
        latest = metrics_collector.get_latest("test_metric")
        assert latest is not None
        assert latest.value == 2.0

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_system_metrics(self, mock_memory, mock_cpu, metrics_collector):
        """Test collecting system metrics."""
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=75.0)
        
        cpu_usage = metrics_collector._get_cpu_usage()
        memory_usage = metrics_collector._get_memory_usage()
        
        assert cpu_usage == 50.0
        assert memory_usage == 75.0

class TestMonitoringLogger:
    def test_log_levels(self, monitoring_logger):
        """Test different log levels."""
        event = monitoring_logger.info("test info")
        assert event.level == "INFO"
        assert event.message == "test info"

        event = monitoring_logger.error("test error")
        assert event.level == "ERROR"
        assert event.message == "test error"

    def test_context_logging(self, monitoring_logger):
        """Test logging with context."""
        event = monitoring_logger.info(
            "test with context",
            user_id="123",
            action="test"
        )
        assert event.context == {"user_id": "123", "action": "test"}

class TestPerformanceTracker:
    def test_operation_timing(self, performance_tracker):
        """Test timing operations."""
        performance_tracker.start_operation("test_op")
        time.sleep(0.1)
        metric = performance_tracker.stop_operation("test_op")
        
        assert metric is not None
        assert metric.operation == "test_op"
        assert 0.05 < metric.duration < 0.15

    async def test_async_operation_timing(self, performance_tracker):
        """Test timing async operations."""
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"

        result = await performance_tracker.track_async(
            "async_op",
            slow_operation()
        )
        
        assert result == "done"
        metrics = performance_tracker.get_metrics("async_op")
        assert len(metrics) == 1
        assert 0.05 < metrics[0].duration < 0.15

    def test_performance_statistics(self, performance_tracker):
        """Test performance statistics calculations."""
        # Record some test metrics
        for duration in [0.1, 0.2, 0.3, 0.4, 0.5]:
            performance_tracker.start_operation("test_op")
            time.sleep(duration)
            performance_tracker.stop_operation("test_op")
        
        avg_duration = performance_tracker.get_average_duration("test_op")
        p95_duration = performance_tracker.get_percentile_duration("test_op", 0.95)
        
        assert 0.25 < avg_duration < 0.35
        assert 0.45 < p95_duration < 0.55
