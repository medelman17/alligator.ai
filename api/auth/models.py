"""
Authentication models for the alligator.ai platform.

Defines user roles, permissions, and authentication-related data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles within a law firm."""

    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    ASSOCIATE = "associate"
    PARTNER = "partner"
    GUEST = "guest"


class SubscriptionTier(str, Enum):
    """Firm subscription tiers with different capabilities."""

    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Permission(str, Enum):
    """Granular permissions for platform features."""

    # Research permissions
    RESEARCH_READ = "research:read"
    RESEARCH_WRITE = "research:write"
    RESEARCH_DELETE = "research:delete"

    # Case permissions
    CASE_READ = "case:read"
    CASE_WRITE = "case:write"
    CASE_DELETE = "case:delete"

    # Document permissions
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_EXPORT = "document:export"

    # Admin permissions
    FIRM_ADMIN = "firm:admin"
    USER_MANAGE = "user:manage"
    BILLING_READ = "billing:read"
    ANALYTICS_READ = "analytics:read"

    # API permissions
    API_ACCESS = "api:access"
    MCP_ACCESS = "mcp:access"


class User(BaseModel):
    """User profile information."""

    id: UUID
    firm_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    bar_number: Optional[str] = None
    practice_areas: list[str] = Field(default_factory=list)
    permissions: list[Permission] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    last_login: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class Firm(BaseModel):
    """Law firm information."""

    id: UUID
    name: str
    short_name: str
    bar_number: Optional[str] = None
    jurisdiction: str
    practice_areas: list[str] = Field(default_factory=list)
    subscription_tier: SubscriptionTier
    settings: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: UUID
    firm_id: UUID
    email: str
    role: UserRole
    permissions: list[Permission]
    subscription_tier: SubscriptionTier
    token_type: str = "access"  # access, refresh, api_key


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response with tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
    firm: Firm


class APIKeyRequest(BaseModel):
    """API key creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: list[Permission]
    expires_in_days: int = Field(365, ge=1, le=3650)  # 1 day to 10 years


class APIKey(BaseModel):
    """API key information."""

    id: UUID
    user_id: UUID
    firm_id: UUID
    name: str
    description: Optional[str] = None
    key_hash: str
    permissions: list[Permission]
    last_used: Optional[datetime] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class RateLimitSettings(BaseModel):
    """Rate limiting configuration for different tiers."""

    tier: SubscriptionTier
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    concurrent_requests: int
    # LLM-specific limits
    llm_calls_per_minute: int
    llm_calls_per_day: int
    # Document limits
    documents_per_day: int
    research_sessions_per_day: int


# Default rate limits by subscription tier
DEFAULT_RATE_LIMITS = {
    SubscriptionTier.BASIC: RateLimitSettings(
        tier=SubscriptionTier.BASIC,
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=2000,
        concurrent_requests=5,
        llm_calls_per_minute=10,
        llm_calls_per_day=100,
        documents_per_day=20,
        research_sessions_per_day=5,
    ),
    SubscriptionTier.PROFESSIONAL: RateLimitSettings(
        tier=SubscriptionTier.PROFESSIONAL,
        requests_per_minute=100,
        requests_per_hour=2000,
        requests_per_day=10000,
        concurrent_requests=15,
        llm_calls_per_minute=50,
        llm_calls_per_day=500,
        documents_per_day=100,
        research_sessions_per_day=25,
    ),
    SubscriptionTier.ENTERPRISE: RateLimitSettings(
        tier=SubscriptionTier.ENTERPRISE,
        requests_per_minute=500,
        requests_per_hour=10000,
        requests_per_day=50000,
        concurrent_requests=50,
        llm_calls_per_minute=200,
        llm_calls_per_day=2000,
        documents_per_day=500,
        research_sessions_per_day=100,
    ),
}

# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.RESEARCH_READ,
        Permission.RESEARCH_WRITE,
        Permission.RESEARCH_DELETE,
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.CASE_DELETE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_EXPORT,
        Permission.FIRM_ADMIN,
        Permission.USER_MANAGE,
        Permission.BILLING_READ,
        Permission.ANALYTICS_READ,
        Permission.API_ACCESS,
        Permission.MCP_ACCESS,
    ],
    UserRole.PARTNER: [
        Permission.RESEARCH_READ,
        Permission.RESEARCH_WRITE,
        Permission.RESEARCH_DELETE,
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.CASE_DELETE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_EXPORT,
        Permission.ANALYTICS_READ,
        Permission.API_ACCESS,
        Permission.MCP_ACCESS,
    ],
    UserRole.ATTORNEY: [
        Permission.RESEARCH_READ,
        Permission.RESEARCH_WRITE,
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_EXPORT,
        Permission.API_ACCESS,
        Permission.MCP_ACCESS,
    ],
    UserRole.ASSOCIATE: [
        Permission.RESEARCH_READ,
        Permission.RESEARCH_WRITE,
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_EXPORT,
        Permission.API_ACCESS,
    ],
    UserRole.PARALEGAL: [
        Permission.RESEARCH_READ,
        Permission.CASE_READ,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
    ],
    UserRole.GUEST: [Permission.RESEARCH_READ, Permission.CASE_READ, Permission.DOCUMENT_READ],
}
