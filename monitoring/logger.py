"""
Enhanced logging system with structured logging and performance tracking.
"""

import logging
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class LogEvent:
    timestamp: float = field(default_factory=time.time)
    level: str = "INFO"
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

class MonitoringLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, level: str, message: str, **context):
        """Log an event with context."""
        event = LogEvent(
            level=level,
            message=message,
            context=context
        )
        
        # Format context for logging
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        log_message = f"{message} {context_str}"
        
        # Log at appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(log_message)
        
        return event

    def info(self, message: str, **context):
        """Log an info message."""
        return self.log_event("INFO", message, **context)

    def warning(self, message: str, **context):
        """Log a warning message."""
        return self.log_event("WARNING", message, **context)

    def error(self, message: str, **context):
        """Log an error message."""
        return self.log_event("ERROR", message, **context)

    def critical(self, message: str, **context):
        """Log a critical message."""
        return self.log_event("CRITICAL", message, **context)

    def debug(self, message: str, **context):
        """Log a debug message."""
        return self.log_event("DEBUG", message, **context)

class PerformanceLogger(MonitoringLogger):
    def __init__(self, name: str):
        super().__init__(name)
        self._timers: Dict[str, float] = {}

    def start_timer(self, name: str):
        """Start timing an operation."""
        self._timers[name] = time.time()

    def stop_timer(self, name: str, **context):
        """Stop timing an operation and log the duration."""
        start_time = self._timers.pop(name, None)
        if start_time is None:
            self.warning(f"Timer {name} was not started")
            return
        
        duration = time.time() - start_time
        self.info(
            f"Operation {name} completed",
            duration=f"{duration:.3f}s",
            **context
        )
