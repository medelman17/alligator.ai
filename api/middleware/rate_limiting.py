"""
Rate limiting middleware for the API.

Implements basic rate limiting to prevent abuse.
"""

import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory storage for rate limiting (replace with Redis in production)
request_counts: dict[str, dict[str, float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window

    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limits and process request."""

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        if not await self._check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response

    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits."""
        current_time = time.time()

        # Initialize client data if not exists
        if client_ip not in request_counts:
            request_counts[client_ip] = {}

        client_data = request_counts[client_ip]

        # Clean old entries
        cutoff_time = current_time - self.window_size
        client_data = {
            timestamp: count for timestamp, count in client_data.items()
            if float(timestamp) > cutoff_time
        }
        request_counts[client_ip] = client_data

        # Count requests in current window
        total_requests = sum(client_data.values())

        # Check if limit exceeded
        if total_requests >= self.requests_per_minute:
            return False

        # Record this request
        timestamp = str(current_time)
        client_data[timestamp] = 1

        return True

    async def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for client."""
        current_time = time.time()

        if client_ip not in request_counts:
            return self.requests_per_minute

        client_data = request_counts[client_ip]
        cutoff_time = current_time - self.window_size

        # Count requests in current window
        total_requests = sum(
            count for timestamp, count in client_data.items()
            if float(timestamp) > cutoff_time
        )

        return max(0, self.requests_per_minute - int(total_requests))
