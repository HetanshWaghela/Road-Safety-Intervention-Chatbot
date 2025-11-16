"""Request/Response logging middleware."""
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...utils.logger import get_logger, set_request_id

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    def __init__(self, app: ASGIApp):
        """Initialize middleware."""
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = set_request_id()

        # Start time
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Read request body if available (for POST/PUT requests)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        request_body = json.loads(body.decode())
                        # Sanitize sensitive data
                        if isinstance(request_body, dict):
                            request_body = self._sanitize_request_body(request_body)
                    except json.JSONDecodeError:
                        request_body = "<non-json body>"
            except Exception:
                request_body = "<unable to read body>"

        # Log request
        self.logger.info(
            "Incoming request",
            operation="request",
            method=method,
            path=path,
            query_params=query_params,
            request_body=request_body,
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Log error
            self.logger.error(
                "Request processing error",
                operation="request_error",
                method=method,
                path=path,
                response_time_ms=response_time_ms,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Get response details
        status_code = response.status_code

        # Extract result count for search endpoints
        result_count = None
        if path.startswith("/api/v1/search") and status_code == 200:
            # Try to get result count from response body
            # Note: This requires reading the response body, which consumes it
            # For now, we'll log without result count to avoid issues
            pass

        # Log response
        log_data = {
            "operation": "response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
        }

        if result_count is not None:
            log_data["result_count"] = result_count

        if status_code >= 400:
            self.logger.warning("Request completed with error", **log_data)
        else:
            self.logger.info("Request completed successfully", **log_data)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    def _sanitize_request_body(self, body: dict) -> dict:
        """Sanitize sensitive data from request body."""
        sanitized = body.copy()

        # Remove sensitive fields if present
        sensitive_fields = ["api_key", "password", "token", "secret"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "***REDACTED***"

        return sanitized

