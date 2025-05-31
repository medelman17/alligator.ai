"""
Authentication dependencies for FastAPI endpoints.

Provides dependency injection for authentication, authorization, and rate limiting.
"""

import time
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth.models import (
    DEFAULT_RATE_LIMITS,
    Permission,
    SubscriptionTier,
    TokenData,
    User,
)
from api.auth.service import AuthService


class AuthDependencies:
    """Authentication dependencies for dependency injection."""

    def __init__(self, auth_service: AuthService, redis_client: redis.Redis):
        self.auth_service = auth_service
        self.redis_client = redis_client
        self.security = HTTPBearer()

    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> TokenData:
        """Get current authenticated user from JWT token."""
        token = credentials.credentials

        # Check if token is in blacklist (for logout functionality)
        is_blacklisted = await self.redis_client.exists(f"blacklist:{token}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
            )

        return await self.auth_service.verify_token(token)

    async def get_current_active_user(
        self,
        current_user: TokenData = Depends(lambda: None),  # Will be replaced with actual dependency
    ) -> User:
        """Get current active user with full profile."""
        if current_user is None:
            current_user = await self.get_current_user()

        user = await self.auth_service.get_user_by_id(current_user.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
            )
        return user

    async def verify_api_key(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> TokenData:
        """Verify API key authentication."""
        api_key = credentials.credentials
        return await self.auth_service.verify_api_key(api_key)

    def require_permissions(self, *required_permissions: Permission):
        """Dependency factory for permission-based authorization."""

        async def permission_checker(
            current_user: TokenData = Depends(lambda: None),  # Will be replaced
        ) -> TokenData:
            if current_user is None:
                current_user = await self.get_current_user()

            # Check if user has all required permissions
            for permission in required_permissions:
                if not self.auth_service.has_permission(current_user.permissions, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission.value} required",
                    )

            return current_user

        return permission_checker

    def require_subscription_tier(self, min_tier: SubscriptionTier):
        """Dependency factory for subscription tier-based authorization."""
        tier_levels = {
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3,
        }

        async def tier_checker(
            current_user: TokenData = Depends(lambda: None),  # Will be replaced
        ) -> TokenData:
            if current_user is None:
                current_user = await self.get_current_user()

            user_tier_level = tier_levels.get(current_user.subscription_tier, 0)
            required_tier_level = tier_levels.get(min_tier, 999)

            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Subscription tier {min_tier.value} or higher required",
                )

            return current_user

        return tier_checker

    async def rate_limit_check(
        self,
        request: Request,
        current_user: TokenData = Depends(lambda: None),  # Will be replaced
        endpoint_type: str = "general",
    ) -> TokenData:
        """Rate limiting based on firm subscription tier."""
        if current_user is None:
            current_user = await self.get_current_user()

        # Get rate limit settings for user's subscription tier
        rate_limits = DEFAULT_RATE_LIMITS.get(
            current_user.subscription_tier, DEFAULT_RATE_LIMITS[SubscriptionTier.BASIC]
        )

        # Use firm-level rate limiting
        firm_key = f"rate_limit:firm:{current_user.firm_id}"

        # Check different time windows
        current_time = int(time.time())

        # Check minute limit
        minute_key = f"{firm_key}:minute:{current_time // 60}"
        minute_count = await self.redis_client.incr(minute_key)
        if minute_count == 1:
            await self.redis_client.expire(minute_key, 60)

        if minute_count > rate_limits.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: requests per minute",
                headers={"Retry-After": "60"},
            )

        # Check hour limit
        hour_key = f"{firm_key}:hour:{current_time // 3600}"
        hour_count = await self.redis_client.incr(hour_key)
        if hour_count == 1:
            await self.redis_client.expire(hour_key, 3600)

        if hour_count > rate_limits.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: requests per hour",
                headers={"Retry-After": "3600"},
            )

        # Check day limit
        day_key = f"{firm_key}:day:{current_time // 86400}"
        day_count = await self.redis_client.incr(day_key)
        if day_count == 1:
            await self.redis_client.expire(day_key, 86400)

        if day_count > rate_limits.requests_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded: requests per day",
                headers={"Retry-After": "86400"},
            )

        # Endpoint-specific limits
        if endpoint_type == "llm":
            llm_minute_key = f"{firm_key}:llm:minute:{current_time // 60}"
            llm_minute_count = await self.redis_client.incr(llm_minute_key)
            if llm_minute_count == 1:
                await self.redis_client.expire(llm_minute_key, 60)

            if llm_minute_count > rate_limits.llm_calls_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded: LLM calls per minute",
                    headers={"Retry-After": "60"},
                )

        return current_user

    async def concurrent_request_limit(
        self,
        current_user: TokenData = Depends(lambda: None),  # Will be replaced
    ) -> TokenData:
        """Enforce concurrent request limits."""
        if current_user is None:
            current_user = await self.get_current_user()

        rate_limits = DEFAULT_RATE_LIMITS.get(
            current_user.subscription_tier, DEFAULT_RATE_LIMITS[SubscriptionTier.BASIC]
        )

        # Track concurrent requests per firm
        concurrent_key = f"concurrent:firm:{current_user.firm_id}"

        # Atomic increment and check
        async with self.redis_client.pipeline() as pipe:
            await pipe.incr(concurrent_key)
            await pipe.expire(concurrent_key, 300)  # 5 minute expiry as safety
            results = await pipe.execute()

            concurrent_count = results[0]

            if concurrent_count > rate_limits.concurrent_requests:
                # Decrement since we're rejecting this request
                await self.redis_client.decr(concurrent_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many concurrent requests",
                )

        return current_user

    async def blacklist_token(self, token: str, expires_in: int = 86400) -> None:
        """Add token to blacklist (for logout)."""
        await self.redis_client.setex(f"blacklist:{token}", expires_in, "1")

    async def get_request_context(
        self,
        request: Request,
        current_user: TokenData = Depends(lambda: None),  # Will be replaced
    ) -> dict:
        """Get request context for logging and audit trails."""
        if current_user is None:
            current_user = await self.get_current_user()

        return {
            "user_id": str(current_user.user_id),
            "firm_id": str(current_user.firm_id),
            "role": current_user.role.value,
            "subscription_tier": current_user.subscription_tier.value,
            "token_type": current_user.token_type,
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_id": getattr(request.state, "request_id", "unknown"),
        }


# Global auth dependencies instance (will be initialized in main.py)
auth_deps: Optional[AuthDependencies] = None


# Convenience functions for dependency injection
async def get_current_user() -> TokenData:
    """Get current authenticated user."""
    if not auth_deps:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized",
        )
    return await auth_deps.get_current_user()


async def get_current_active_user() -> User:
    """Get current active user."""
    if not auth_deps:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized",
        )
    return await auth_deps.get_current_active_user()


def require_permissions(*permissions: Permission):
    """Require specific permissions."""
    if not auth_deps:

        async def error_handler():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not initialized",
            )

        return error_handler
    return auth_deps.require_permissions(*permissions)


def require_subscription_tier(tier: SubscriptionTier):
    """Require minimum subscription tier."""
    if not auth_deps:

        async def error_handler():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not initialized",
            )

        return error_handler
    return auth_deps.require_subscription_tier(tier)


async def rate_limit_general(request: Request) -> TokenData:
    """General rate limiting."""
    if not auth_deps:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized",
        )
    return await auth_deps.rate_limit_check(request, endpoint_type="general")


async def rate_limit_llm(request: Request) -> TokenData:
    """LLM-specific rate limiting."""
    if not auth_deps:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized",
        )
    return await auth_deps.rate_limit_check(request, endpoint_type="llm")
