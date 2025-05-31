"""
Request logging middleware for the API.

Logs incoming requests and responses for monitoring and debugging.
"""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""

        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Add request ID to state for access in endpoints
        request.state.request_id = request_id

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(f"[{request_id}] {response.status_code} - " f"Duration: {duration:.3f}s")

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(f"[{request_id}] ERROR - {e!s} - " f"Duration: {duration:.3f}s")
            raise
