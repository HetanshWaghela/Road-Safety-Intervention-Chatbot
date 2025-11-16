"""Structured JSON logging utility with evaluation metrics."""
import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger

from ..config import settings

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class StructuredLogger:
    """Structured logger with JSON formatting and evaluation metrics."""

    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.name = name

    def _get_context(self) -> Dict[str, Any]:
        """Get logging context including request ID."""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.name,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            context["request_id"] = request_id

        return context

    def _log_with_context(
        self, level: int, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs
    ):
        """Log with structured context."""
        context = self._get_context()
        if extra:
            context.update(extra)

        # Merge any additional kwargs
        context.update(kwargs)

        self.logger.log(level, message, extra=context)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def log_evaluation_metrics(
        self,
        query: str,
        relevance_score: float,
        comprehensiveness_score: float,
        confidence_scores: List[float],
        matched_intervention_ids: List[str],
        response_time_ms: int,
        strategy: str,
        **kwargs
    ):
        """Log evaluation metrics for search queries."""
        top_confidence = max(confidence_scores) if confidence_scores else 0.0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        metrics = {
            "query": query,
            "relevance_score": relevance_score,
            "comprehensiveness_score": comprehensiveness_score,
            "confidence_scores": confidence_scores,
            "top_confidence": top_confidence,
            "avg_confidence": avg_confidence,
            "matched_intervention_ids": matched_intervention_ids,
            "response_time_ms": response_time_ms,
            "strategy": strategy,
            "result_count": len(matched_intervention_ids),
        }
        metrics.update(kwargs)

        self.info("Search query evaluation metrics", **metrics)

    def log_operation(
        self,
        operation: str,
        message: str,
        query_id: Optional[str] = None,
        intervention_id: Optional[str] = None,
        strategy: Optional[str] = None,
        **kwargs
    ):
        """Log operation with context."""
        extra = {
            "operation": operation,
        }
        if query_id:
            extra["query_id"] = query_id
        if intervention_id:
            extra["intervention_id"] = intervention_id
        if strategy:
            extra["strategy"] = strategy

        extra.update(kwargs)
        self.info(message, **extra)


def setup_logging():
    """Setup structured JSON logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(levelname)s %(name)s %(message)s",
        timestamp=True,
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set level for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    return StructuredLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID in context. Returns the request ID."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()

