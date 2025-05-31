"""
Rate limiting middleware for the API.

Implements sophisticated rate limiting based on authentication and subscription tiers.
"""

import time
from collections.abc import Callable
from typing import Optional

import jwt
import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth.models import DEFAULT_RATE_LIMITS, SubscriptionTier


class AuthenticatedRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with authentication awareness."""

    def __init__(
        self,
        app,
        redis_client: redis.Redis,
        secret_key: str,
        default_requests_per_minute: int = 30,
        bypass_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.secret_key = secret_key
        self.default_requests_per_minute = default_requests_per_minute
        self.bypass_paths = bypass_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limits and process request."""

        # Skip rate limiting for certain paths
        if any(request.url.path.startswith(path) for path in self.bypass_paths):
            return await call_next(request)

        # Extract user/firm context from token
        rate_limit_context = await self._get_rate_limit_context(request)

        # Check rate limits
        await self._check_rate_limits(request, rate_limit_context)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        await self._add_rate_limit_headers(response, rate_limit_context)

        return response

    async def _get_rate_limit_context(self, request: Request) -> dict:
        """Extract rate limiting context from request."""
        context = {
            "identifier": request.client.host if request.client else "unknown",
            "subscription_tier": SubscriptionTier.BASIC,
            "firm_id": None,
            "user_id": None,
            "is_authenticated": False,
        }

        # Try to extract JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                context.update(
                    {
                        "identifier": f"firm:{payload.get('firm_id')}",
                        "subscription_tier": SubscriptionTier(
                            payload.get("subscription_tier", "basic")
                        ),
                        "firm_id": payload.get("firm_id"),
                        "user_id": payload.get("user_id"),
                        "is_authenticated": True,
                    }
                )
            except jwt.InvalidTokenError:
                # Token invalid, use IP-based limiting
                pass

        return context

    async def _check_rate_limits(self, request: Request, context: dict) -> None:
        """Check rate limits based on context."""
        current_time = int(time.time())
        identifier = context["identifier"]

        # Get rate limits for subscription tier
        rate_limits = DEFAULT_RATE_LIMITS.get(
            context["subscription_tier"], DEFAULT_RATE_LIMITS[SubscriptionTier.BASIC]
        )

        # Check different time windows
        await self._check_window_limit(
            f"rate_limit:{identifier}:minute:{current_time // 60}",
            rate_limits.requests_per_minute,
            60,
            "requests per minute",
        )

        await self._check_window_limit(
            f"rate_limit:{identifier}:hour:{current_time // 3600}",
            rate_limits.requests_per_hour,
            3600,
            "requests per hour",
        )

        await self._check_window_limit(
            f"rate_limit:{identifier}:day:{current_time // 86400}",
            rate_limits.requests_per_day,
            86400,
            "requests per day",
        )

        # Check concurrent requests for authenticated users
        if context["is_authenticated"]:
            await self._check_concurrent_limit(identifier, rate_limits.concurrent_requests)

    async def _check_window_limit(
        self, key: str, limit: int, window_seconds: int, limit_name: str
    ) -> None:
        """Check rate limit for a specific time window."""
        count = await self.redis_client.incr(key)
        if count == 1:
            await self.redis_client.expire(key, window_seconds)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit_name}",
                headers={"Retry-After": str(window_seconds)},
            )

    async def _check_concurrent_limit(self, identifier: str, limit: int) -> None:
        """Check concurrent request limit."""
        concurrent_key = f"concurrent:{identifier}"

        count = await self.redis_client.incr(concurrent_key)
        await self.redis_client.expire(concurrent_key, 300)  # 5 minute safety expiry

        if count > limit:
            # Decrement since we're rejecting this request
            await self.redis_client.decr(concurrent_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many concurrent requests"
            )

    async def _add_rate_limit_headers(self, response, context: dict) -> None:
        """Add rate limit headers to response."""
        current_time = int(time.time())
        identifier = context["identifier"]

        rate_limits = DEFAULT_RATE_LIMITS.get(
            context["subscription_tier"], DEFAULT_RATE_LIMITS[SubscriptionTier.BASIC]
        )

        # Get current usage
        minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
        minute_count = await self.redis_client.get(minute_key)
        minute_count = int(minute_count) if minute_count else 0

        # Add headers
        response.headers["X-RateLimit-Limit"] = str(rate_limits.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, rate_limits.requests_per_minute - minute_count)
        )
        response.headers["X-RateLimit-Reset"] = str(current_time + (60 - (current_time % 60)))
        response.headers["X-RateLimit-Tier"] = context["subscription_tier"].value


# Legacy middleware for backward compatibility
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic IP-based rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60
        # In-memory storage for development (should use Redis in production)
        self.request_counts: dict[str, dict[str, float]] = {}

    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limits and process request."""
        client_ip = request.client.host if request.client else "unknown"

        if not await self._check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        remaining = await self._get_remaining_requests(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response

    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limits."""
        current_time = time.time()

        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}

        client_data = self.request_counts[client_ip]
        cutoff_time = current_time - self.window_size

        # Clean old entries
        client_data = {
            timestamp: count
            for timestamp, count in client_data.items()
            if float(timestamp) > cutoff_time
        }
        self.request_counts[client_ip] = client_data

        total_requests = sum(client_data.values())

        if total_requests >= self.requests_per_minute:
            return False

        timestamp = str(current_time)
        client_data[timestamp] = 1
        return True

    async def _get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for client."""
        current_time = time.time()

        if client_ip not in self.request_counts:
            return self.requests_per_minute

        client_data = self.request_counts[client_ip]
        cutoff_time = current_time - self.window_size

        total_requests = sum(
            count for timestamp, count in client_data.items() if float(timestamp) > cutoff_time
        )

        return max(0, self.requests_per_minute - int(total_requests))
