"""
Authentication endpoints for user login, token management, and API keys.

Provides REST API endpoints for authentication operations.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth.dependencies import get_current_user, require_permissions
from api.auth.models import (
    APIKeyRequest,
    LoginRequest,
    LoginResponse,
    Permission,
    TokenData,
    User,
)
from api.auth.service import AuthService
from api.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """
    Authenticate user and return access/refresh tokens.

    Returns JWT tokens for API access and user/firm information.
    """
    return await auth_service.login(request)


@router.post("/refresh")
async def refresh_token(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Refresh access token using refresh token.

    Returns new access token for continued API access.
    """
    new_access_token = await auth_service.refresh_access_token(refresh_token)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 minutes
    }


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: TokenData = Depends(get_current_user),
) -> dict:
    """
    Logout user by blacklisting current token.

    Invalidates the current access token to prevent further use.
    """
    from api.auth.dependencies import auth_deps

    if auth_deps:
        # Add token to blacklist
        await auth_deps.blacklist_token(credentials.credentials)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current user profile information.

    Returns detailed user profile including permissions and preferences.
    """
    user = await auth_service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/api-keys", response_model=dict)
async def create_api_key(
    request: APIKeyRequest,
    current_user: TokenData = Depends(require_permissions(Permission.API_ACCESS)),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Create a new API key for programmatic access.

    Generates a secure API key with specified permissions and expiration.
    """
    # Validate that user can grant requested permissions
    for permission in request.permissions:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot grant permission you don't have: {permission.value}",
            )

    api_key_obj, api_key = await auth_service.create_api_key(current_user.user_id, request)

    return {
        "api_key": api_key,  # Only returned once!
        "api_key_id": str(api_key_obj.id),
        "name": api_key_obj.name,
        "permissions": [p.value for p in api_key_obj.permissions],
        "expires_at": api_key_obj.expires_at.isoformat(),
        "message": "Save this API key securely - it won't be shown again",
    }


@router.get("/api-keys", response_model=list[dict])
async def list_api_keys(
    current_user: TokenData = Depends(require_permissions(Permission.API_ACCESS)),
    auth_service: AuthService = Depends(get_auth_service),
) -> list[dict]:
    """
    List user's API keys (without showing actual keys).

    Returns metadata about existing API keys for management purposes.
    """
    async with auth_service.db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, description, permissions, last_used,
                   created_at, expires_at, is_active
            FROM api_keys
            WHERE user_id = $1
            ORDER BY created_at DESC
        """,
            current_user.user_id,
        )

        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "permissions": row["permissions"],
                "last_used": row["last_used"].isoformat() if row["last_used"] else None,
                "created_at": row["created_at"].isoformat(),
                "expires_at": row["expires_at"].isoformat(),
                "is_active": row["is_active"],
                "is_expired": row["expires_at"] < datetime.utcnow(),
            }
            for row in rows
        ]


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: TokenData = Depends(require_permissions(Permission.API_ACCESS)),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Revoke an API key.

    Deactivates the specified API key to prevent further use.
    """
    async with auth_service.db_pool.acquire() as conn:
        # Check if API key belongs to user
        result = await conn.execute(
            """
            UPDATE api_keys
            SET is_active = false, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """,
            api_key_id,
            current_user.user_id,
        )

        if result == "UPDATE 0":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    return {"message": "API key revoked successfully"}


@router.get("/permissions", response_model=list[dict])
async def list_available_permissions(
    current_user: TokenData = Depends(get_current_user),
) -> list[dict]:
    """
    List available permissions for the current user.

    Returns permissions that can be granted to API keys.
    """
    return [
        {
            "permission": permission.value,
            "description": _get_permission_description(permission),
            "available": permission in current_user.permissions,
        }
        for permission in Permission
    ]


@router.get("/rate-limits", response_model=dict)
async def get_rate_limits(current_user: TokenData = Depends(get_current_user)) -> dict:
    """
    Get current rate limits for the user's subscription tier.

    Returns rate limiting information for planning API usage.
    """
    from api.auth.models import DEFAULT_RATE_LIMITS

    rate_limits = DEFAULT_RATE_LIMITS.get(current_user.subscription_tier)
    if not rate_limits:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Rate limits not configured"
        )

    return {
        "subscription_tier": current_user.subscription_tier.value,
        "limits": {
            "requests_per_minute": rate_limits.requests_per_minute,
            "requests_per_hour": rate_limits.requests_per_hour,
            "requests_per_day": rate_limits.requests_per_day,
            "concurrent_requests": rate_limits.concurrent_requests,
            "llm_calls_per_minute": rate_limits.llm_calls_per_minute,
            "llm_calls_per_day": rate_limits.llm_calls_per_day,
            "documents_per_day": rate_limits.documents_per_day,
            "research_sessions_per_day": rate_limits.research_sessions_per_day,
        },
    }


@router.get("/usage", response_model=dict)
async def get_usage_stats(
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Get current usage statistics for rate limiting.

    Returns current usage counts against rate limits.
    """
    import time

    from api.auth.dependencies import auth_deps

    if not auth_deps:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized",
        )

    current_time = int(time.time())
    firm_key = f"rate_limit:firm:{current_user.firm_id}"

    # Get current usage from Redis
    minute_key = f"{firm_key}:minute:{current_time // 60}"
    hour_key = f"{firm_key}:hour:{current_time // 3600}"
    day_key = f"{firm_key}:day:{current_time // 86400}"
    concurrent_key = f"concurrent:firm:{current_user.firm_id}"

    usage_data = await auth_deps.redis_client.mget([minute_key, hour_key, day_key, concurrent_key])

    return {
        "current_usage": {
            "requests_this_minute": int(usage_data[0] or 0),
            "requests_this_hour": int(usage_data[1] or 0),
            "requests_today": int(usage_data[2] or 0),
            "concurrent_requests": int(usage_data[3] or 0),
        },
        "firm_id": str(current_user.firm_id),
        "user_id": str(current_user.user_id),
        "subscription_tier": current_user.subscription_tier.value,
    }


def _get_permission_description(permission: Permission) -> str:
    """Get human-readable description for permission."""
    descriptions = {
        Permission.RESEARCH_READ: "View research sessions and results",
        Permission.RESEARCH_WRITE: "Create and modify research sessions",
        Permission.RESEARCH_DELETE: "Delete research sessions",
        Permission.CASE_READ: "View case information",
        Permission.CASE_WRITE: "Create and modify case records",
        Permission.CASE_DELETE: "Delete case records",
        Permission.DOCUMENT_READ: "View documents and memos",
        Permission.DOCUMENT_WRITE: "Create and modify documents",
        Permission.DOCUMENT_DELETE: "Delete documents",
        Permission.DOCUMENT_EXPORT: "Export documents in various formats",
        Permission.FIRM_ADMIN: "Administer firm settings and users",
        Permission.USER_MANAGE: "Manage user accounts and permissions",
        Permission.BILLING_READ: "View billing and usage information",
        Permission.ANALYTICS_READ: "View analytics and reports",
        Permission.API_ACCESS: "Access REST API programmatically",
        Permission.MCP_ACCESS: "Use MCP server tools",
    }
    return descriptions.get(permission, "No description available")
