"""
Authentication module for alligator.ai platform.

Provides user authentication, authorization, rate limiting, and API key management.
"""

from .dependencies import (
    get_current_active_user,
    get_current_user,
    rate_limit_general,
    rate_limit_llm,
    require_permissions,
    require_subscription_tier,
)
from .models import (
    DEFAULT_RATE_LIMITS,
    ROLE_PERMISSIONS,
    APIKey,
    APIKeyRequest,
    Firm,
    LoginRequest,
    LoginResponse,
    Permission,
    SubscriptionTier,
    TokenData,
    User,
    UserRole,
)
from .service import AuthService

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_permissions",
    "require_subscription_tier",
    "rate_limit_general",
    "rate_limit_llm",
    # Models
    "User",
    "Firm",
    "UserRole",
    "Permission",
    "SubscriptionTier",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
    "APIKeyRequest",
    "APIKey",
    "DEFAULT_RATE_LIMITS",
    "ROLE_PERMISSIONS",
    # Service
    "AuthService",
]
