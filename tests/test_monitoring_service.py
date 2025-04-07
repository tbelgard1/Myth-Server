"""
Tests for the monitoring service.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from core.services import MonitoringService
from core.services.monitoring_service import Alert
from core.monitoring.metrics import Metric

@pytest.fixture
async def monitoring_service():
    service = MonitoringService()
    await service.start()
    yield service
    await service.stop()

class TestMonitoringService:
    async def test_start_stop(self):
        """Test starting and stopping the monitoring service."""
        service = MonitoringService()
        await service.start()
        assert service._running
        assert service._task is not None
        
        await service.stop()
        assert not service._running

    async def test_alert_handling(self, monitoring_service):
        """Test alert registration and handling."""
        alert_received = asyncio.Event()
        alert_data = {}

        async def handle_warning(alert: Alert):
            alert_data["level"] = alert.level
            alert_data["message"] = alert.message
            alert_received.set()

        monitoring_service.register_alert_handler("WARNING", handle_warning)
        monitoring_service.alert("WARNING", "Test alert", test=True)
        
        await asyncio.wait_for(alert_received.wait(), timeout=1.0)
        assert alert_data["level"] == "WARNING"
        assert alert_data["message"] == "Test alert"

    @patch("core.monitoring.metrics.MetricsCollector.get_latest")
    async def test_performance_monitoring(self, mock_get_latest, monitoring_service):
        """Test performance monitoring and alerts."""
        alerts = []
        
        async def collect_alerts(alert: Alert):
            alerts.append(alert)

        monitoring_service.register_alert_handler("WARNING", collect_alerts)

        # Simulate high CPU usage
        mock_get_latest.return_value = Metric(
            name="system.cpu_percent",
            value=85.0,
            timestamp=datetime.now().timestamp()
        )

        # Wait for monitoring cycle
        await asyncio.sleep(6)
        
        assert len(alerts) > 0
        assert any(
            alert.message == "High CPU usage detected"
            for alert in alerts
        )

    async def test_metric_collection(self, monitoring_service):
        """Test metric collection through the service."""
        monitoring_service.metrics.record("test_metric", 42.0, label="test")
        
        metric = monitoring_service.metrics.get_latest("test_metric")
        assert metric is not None
        assert metric.value == 42.0
        assert metric.labels == {"label": "test"}

    async def test_performance_tracking(self, monitoring_service):
        """Test performance tracking through the service."""
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"

        result = await monitoring_service.tracker.track_async(
            "test_operation",
            slow_operation()
        )
        
        assert result == "done"
        metrics = monitoring_service.tracker.get_metrics("test_operation")
        assert len(metrics) == 1
        assert 0.05 < metrics[0].duration < 0.15

    async def test_logging(self, monitoring_service):
        """Test logging through the service."""
        with patch.object(monitoring_service.logger.logger, 'info') as mock_info:
            monitoring_service.logger.info(
                "Test message",
                test=True
            )
            
            mock_info.assert_called_once()
            args = mock_info.call_args[0]
            assert "Test message" in args[0]
            assert "test=True" in args[0]
