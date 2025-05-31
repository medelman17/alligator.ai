"""
Example integration of authentication system with existing API endpoints.

Shows how to protect endpoints with authentication, authorization, and rate limiting.
"""

from fastapi import APIRouter, Depends, Request

from api.auth import (
    Permission,
    SubscriptionTier,
    get_current_user,
    require_permissions,
    require_subscription_tier,
    rate_limit_general,
    rate_limit_llm,
    TokenData
)
from api.dependencies import get_precedent_analyzer

# Example of protecting existing research endpoints
router = APIRouter()


@router.post("/research/sessions")
async def create_research_session_protected(
    request_data: dict,
    request: Request,
    # Authentication required
    current_user: TokenData = Depends(get_current_user),
    # Must have research write permission
    _: TokenData = Depends(require_permissions(Permission.RESEARCH_WRITE)),
    # Rate limit check
    __: TokenData = Depends(rate_limit_general),
    # Access to services
    analyzer = Depends(get_precedent_analyzer)
):
    """
    Create research session with full authentication and authorization.
    
    This endpoint demonstrates:
    - JWT token authentication
    - Permission-based authorization
    - Rate limiting based on subscription tier
    - Audit logging capabilities
    """
    # Log the authenticated request
    print(f"User {current_user.email} from firm {current_user.firm_id} created research session")
    
    # Business logic here...
    return {
        "message": "Research session created",
        "user_id": str(current_user.user_id),
        "firm_id": str(current_user.firm_id),
        "subscription_tier": current_user.subscription_tier.value
    }


@router.post("/research/ai-analysis")
async def ai_analysis_endpoint(
    query: str,
    request: Request,
    # Professional tier or higher required for AI features
    current_user: TokenData = Depends(require_subscription_tier(SubscriptionTier.PROFESSIONAL)),
    # LLM-specific rate limiting
    _: TokenData = Depends(rate_limit_llm),
    analyzer = Depends(get_precedent_analyzer)
):
    """
    AI-powered analysis endpoint with subscription tier requirement.
    
    Only available to Professional and Enterprise tiers.
    """
    # Business logic for AI analysis...
    return {
        "analysis": f"AI analysis for: {query}",
        "user_tier": current_user.subscription_tier.value,
        "user_id": str(current_user.user_id)
    }


@router.get("/research/admin/stats")
async def get_research_stats(
    current_user: TokenData = Depends(require_permissions(
        Permission.ANALYTICS_READ,
        Permission.FIRM_ADMIN
    ))
):
    """
    Admin endpoint requiring multiple permissions.
    
    Only accessible to users with both analytics read and firm admin permissions.
    """
    return {
        "message": "Research statistics",
        "admin_user": current_user.email,
        "firm_id": str(current_user.firm_id)
    }


@router.post("/documents/export")
async def export_document(
    document_id: str,
    format: str,
    current_user: TokenData = Depends(require_permissions(Permission.DOCUMENT_EXPORT)),
    _: TokenData = Depends(rate_limit_general)
):
    """
    Document export with permission check.
    
    Requires specific document export permission.
    """
    return {
        "message": f"Exporting document {document_id} as {format}",
        "user_id": str(current_user.user_id)
    }


# Example of API key authentication for programmatic access
@router.get("/api/cases/bulk")
async def bulk_case_access(
    limit: int = 100,
    # Uses API key authentication instead of JWT
    current_user: TokenData = Depends(get_current_user),
    _: TokenData = Depends(require_permissions(Permission.API_ACCESS))
):
    """
    Bulk API endpoint for programmatic access.
    
    Can be accessed with either JWT tokens or API keys.
    Token type is indicated in current_user.token_type.
    """
    return {
        "cases": f"Returning {limit} cases",
        "access_method": current_user.token_type,
        "user_id": str(current_user.user_id),
        "firm_id": str(current_user.firm_id)
    }


# Example of endpoint with complex authorization logic
@router.delete("/research/sessions/{session_id}")
async def delete_research_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete research session with custom authorization logic.
    
    Users can delete their own sessions, or admins can delete any session.
    """
    # Custom authorization logic
    if Permission.RESEARCH_DELETE not in current_user.permissions:
        # Check if user owns the session (simplified example)
        if not await _user_owns_session(session_id, current_user.user_id):
            if Permission.FIRM_ADMIN not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete sessions you don't own"
                )
    
    return {"message": f"Session {session_id} deleted"}


async def _user_owns_session(session_id: str, user_id: str) -> bool:
    """Check if user owns the research session."""
    # Implementation would check database
    return True  # Simplified for example


# Example showing different endpoints for different user roles
@router.get("/firm/users")
async def list_firm_users(
    current_user: TokenData = Depends(require_permissions(Permission.USER_MANAGE))
):
    """List users in the firm - admin only."""
    return {"users": "List of firm users", "admin": current_user.email}


@router.get("/billing/usage")
async def get_billing_usage(
    current_user: TokenData = Depends(require_permissions(Permission.BILLING_READ))
):
    """Get billing usage - admin/partners only."""
    return {
        "usage": "Billing usage data",
        "firm_id": str(current_user.firm_id)
    }


# Example of MCP server endpoint
@router.post("/mcp/tools/search-precedents")
async def mcp_search_precedents(
    query: str,
    jurisdiction: str = None,
    current_user: TokenData = Depends(require_permissions(Permission.MCP_ACCESS)),
    _: TokenData = Depends(rate_limit_llm)
):
    """
    MCP server tool endpoint.
    
    Requires MCP access permission and uses LLM rate limiting.
    """
    return {
        "tool": "search-precedents",
        "query": query,
        "jurisdiction": jurisdiction,
        "mcp_user": str(current_user.user_id)
    }


# Health check endpoints (no authentication required)
@router.get("/health/auth")
async def auth_health_check():
    """Health check for authentication system."""
    return {
        "status": "healthy",
        "component": "authentication",
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    # Example of how to use the authentication system
    print("Authentication Integration Examples")
    print("==================================")
    print()
    print("1. JWT Token Authentication:")
    print("   POST /auth/login with email/password")
    print("   Use returned access_token in Authorization: Bearer <token>")
    print()
    print("2. API Key Authentication:")
    print("   POST /auth/api-keys to create key")
    print("   Use API key in Authorization: Bearer <api_key>")
    print()
    print("3. Rate Limiting:")
    print("   - Basic: 30 req/min, 500 req/hour, 2000 req/day")
    print("   - Professional: 100 req/min, 2000 req/hour, 10000 req/day")
    print("   - Enterprise: 500 req/min, 10000 req/hour, 50000 req/day")
    print()
    print("4. Permissions:")
    print("   - research:read, research:write, research:delete")
    print("   - case:read, case:write, case:delete")
    print("   - document:read, document:write, document:delete, document:export")
    print("   - firm:admin, user:manage, billing:read, analytics:read")
    print("   - api:access, mcp:access")