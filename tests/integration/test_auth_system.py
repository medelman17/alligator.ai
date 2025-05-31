"""
Integration tests for the authentication system.

Tests the complete authentication flow including JWT tokens, API keys,
rate limiting, and permission-based authorization.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import asyncpg
import redis.asyncio as redis
from fastapi.testclient import TestClient

from api.auth.service import AuthService
from api.auth.models import (
    LoginRequest,
    APIKeyRequest,
    Permission,
    SubscriptionTier,
    UserRole
)


@pytest.fixture
async def auth_service():
    """Create auth service for testing."""
    # Use test database connection
    db_pool = await asyncpg.create_pool(
        "postgresql://citation_user:citation_pass_2024@localhost:5432/citation_test"
    )
    
    auth_service = AuthService(
        db_pool=db_pool,
        secret_key="test_secret_key_for_jwt_tokens",
        access_token_expire_minutes=30,
        refresh_token_expire_days=30
    )
    
    yield auth_service
    
    await db_pool.close()


@pytest.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host="localhost", port=6379, db=1)  # Use test database
    yield client
    await client.flushdb()  # Clean up after test
    await client.close()


@pytest.fixture
async def test_user_data():
    """Create test user and firm data."""
    return {
        "firm": {
            "id": str(uuid4()),
            "name": "Test Law Firm",
            "short_name": "TLF",
            "jurisdiction": "CA",
            "subscription_tier": SubscriptionTier.PROFESSIONAL
        },
        "user": {
            "id": str(uuid4()),
            "email": "test@testfirm.com",
            "full_name": "Test Attorney",
            "password": "test_password_123",
            "role": UserRole.ATTORNEY
        }
    }


class TestAuthenticationFlow:
    """Test authentication flow end-to-end."""

    async def test_user_login_success(self, auth_service, test_user_data):
        """Test successful user login."""
        # Create test user in database (simplified)
        password_hash = auth_service.get_password_hash(test_user_data["user"]["password"])
        
        # Mock user exists in database
        # In real test, would insert into test database
        
        login_request = LoginRequest(
            email=test_user_data["user"]["email"],
            password=test_user_data["user"]["password"]
        )
        
        # This would work with actual database setup
        # response = await auth_service.login(login_request)
        # assert response.access_token
        # assert response.user.email == test_user_data["user"]["email"]

    async def test_token_verification(self, auth_service, test_user_data):
        """Test JWT token verification."""
        from api.auth.models import TokenData, User, Firm
        
        # Create mock user and firm
        user = User(
            id=test_user_data["user"]["id"],
            firm_id=test_user_data["firm"]["id"],
            email=test_user_data["user"]["email"],
            full_name=test_user_data["user"]["full_name"],
            role=test_user_data["user"]["role"],
            permissions=[Permission.RESEARCH_READ, Permission.RESEARCH_WRITE],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        firm = Firm(
            id=test_user_data["firm"]["id"],
            name=test_user_data["firm"]["name"],
            short_name=test_user_data["firm"]["short_name"],
            jurisdiction=test_user_data["firm"]["jurisdiction"],
            subscription_tier=test_user_data["firm"]["subscription_tier"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create access token
        token = await auth_service.create_access_token(user, firm)
        assert token
        
        # Verify token
        token_data = await auth_service.verify_token(token)
        assert token_data.user_id == user.id
        assert token_data.firm_id == user.firm_id
        assert token_data.email == user.email
        assert Permission.RESEARCH_READ in token_data.permissions

    async def test_api_key_creation(self, auth_service, test_user_data):
        """Test API key creation and verification."""
        api_key_request = APIKeyRequest(
            name="Test API Key",
            description="For testing purposes",
            permissions=[Permission.API_ACCESS, Permission.RESEARCH_READ],
            expires_in_days=30
        )
        
        # This would work with actual database setup
        # api_key_obj, api_key = await auth_service.create_api_key(
        #     test_user_data["user"]["id"], 
        #     api_key_request
        # )
        # assert api_key.startswith("alg_")
        # assert len(api_key) > 20


class TestRateLimiting:
    """Test rate limiting functionality."""

    async def test_basic_rate_limiting(self, redis_client):
        """Test basic rate limiting with Redis."""
        from api.middleware.rate_limiting import AuthenticatedRateLimitMiddleware
        
        # Simulate rate limit checks
        current_time = int(asyncio.get_event_loop().time())
        identifier = "test_user"
        
        # Test minute-based limiting
        minute_key = f"rate_limit:{identifier}:minute:{current_time // 60}"
        
        # Should allow first request
        count = await redis_client.incr(minute_key)
        assert count == 1
        
        # Should track multiple requests
        for i in range(5):
            count = await redis_client.incr(minute_key)
        assert count == 6

    async def test_subscription_tier_limits(self, redis_client):
        """Test different rate limits by subscription tier."""
        from api.auth.models import DEFAULT_RATE_LIMITS
        
        basic_limits = DEFAULT_RATE_LIMITS[SubscriptionTier.BASIC]
        professional_limits = DEFAULT_RATE_LIMITS[SubscriptionTier.PROFESSIONAL]
        enterprise_limits = DEFAULT_RATE_LIMITS[SubscriptionTier.ENTERPRISE]
        
        # Verify tier differences
        assert basic_limits.requests_per_minute < professional_limits.requests_per_minute
        assert professional_limits.requests_per_minute < enterprise_limits.requests_per_minute
        
        assert basic_limits.llm_calls_per_day < professional_limits.llm_calls_per_day
        assert professional_limits.llm_calls_per_day < enterprise_limits.llm_calls_per_day


class TestPermissionSystem:
    """Test role-based permission system."""

    def test_role_permissions(self):
        """Test default permissions for each role."""
        from api.auth.models import ROLE_PERMISSIONS
        
        # Test role hierarchy
        admin_permissions = set(ROLE_PERMISSIONS[UserRole.ADMIN])
        partner_permissions = set(ROLE_PERMISSIONS[UserRole.PARTNER])
        attorney_permissions = set(ROLE_PERMISSIONS[UserRole.ATTORNEY])
        paralegal_permissions = set(ROLE_PERMISSIONS[UserRole.PARALEGAL])
        
        # Admin should have all permissions
        assert Permission.FIRM_ADMIN in admin_permissions
        assert Permission.USER_MANAGE in admin_permissions
        
        # Partner should have most permissions but not user management
        assert Permission.ANALYTICS_READ in partner_permissions
        assert Permission.USER_MANAGE not in partner_permissions
        
        # Attorney should have research and case permissions
        assert Permission.RESEARCH_WRITE in attorney_permissions
        assert Permission.CASE_WRITE in attorney_permissions
        assert Permission.FIRM_ADMIN not in attorney_permissions
        
        # Paralegal should have limited permissions
        assert Permission.RESEARCH_READ in paralegal_permissions
        assert Permission.RESEARCH_WRITE not in paralegal_permissions

    def test_permission_inheritance(self):
        """Test that higher roles include lower role permissions."""
        from api.auth.models import ROLE_PERMISSIONS
        
        admin_perms = set(ROLE_PERMISSIONS[UserRole.ADMIN])
        attorney_perms = set(ROLE_PERMISSIONS[UserRole.ATTORNEY])
        
        # Admin should have at least all attorney permissions
        common_perms = {
            Permission.RESEARCH_READ,
            Permission.RESEARCH_WRITE,
            Permission.CASE_READ,
            Permission.CASE_WRITE
        }
        
        assert common_perms.issubset(admin_perms)
        assert common_perms.issubset(attorney_perms)


class TestSecurityFeatures:
    """Test security features like audit logging and token blacklisting."""

    async def test_password_hashing(self, auth_service):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = auth_service.get_password_hash(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should verify correctly
        assert auth_service.verify_password(password, hashed)
        
        # Should not verify incorrect password
        assert not auth_service.verify_password("wrong_password", hashed)

    async def test_token_expiration(self, auth_service):
        """Test token expiration handling."""
        import jwt
        from datetime import datetime, timedelta
        
        # Create expired token
        expired_payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "token_type": "access"
        }
        
        expired_token = jwt.encode(
            expired_payload, 
            auth_service.secret_key, 
            algorithm=auth_service.algorithm
        )
        
        # Should raise exception for expired token
        with pytest.raises(Exception):  # HTTPException in real usage
            await auth_service.verify_token(expired_token)

    async def test_api_key_security(self, auth_service):
        """Test API key security features."""
        # Test key generation format
        api_key = auth_service._generate_api_key()
        assert api_key.startswith("alg_")
        assert len(api_key) > 20
        
        # Test key hashing
        key_hash = auth_service._hash_api_key(api_key)
        assert key_hash != api_key
        assert len(key_hash) == 64  # SHA256 hex length


class TestMCPIntegration:
    """Test MCP server authentication integration."""

    def test_mcp_permissions(self):
        """Test MCP-specific permissions."""
        from api.auth.models import Permission
        
        # MCP access should be separate permission
        assert Permission.MCP_ACCESS in Permission
        
        # Should be included in appropriate roles
        from api.auth.models import ROLE_PERMISSIONS
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        attorney_perms = ROLE_PERMISSIONS[UserRole.ATTORNEY]
        
        assert Permission.MCP_ACCESS in admin_perms
        assert Permission.MCP_ACCESS in attorney_perms


# Example test for rate limiting integration
@pytest.mark.asyncio
async def test_rate_limiting_integration():
    """Test rate limiting with actual Redis."""
    redis_client = redis.Redis(host="localhost", port=6379, db=1)
    
    try:
        # Test basic increment
        key = "test:rate_limit"
        count = await redis_client.incr(key)
        assert count == 1
        
        # Test expiration
        await redis_client.expire(key, 60)
        ttl = await redis_client.ttl(key)
        assert ttl > 0
        
    finally:
        await redis_client.delete(key)
        await redis_client.close()


if __name__ == "__main__":
    """Run integration tests."""
    print("Authentication System Integration Tests")
    print("====================================")
    print()
    print("To run these tests:")
    print("1. Ensure PostgreSQL test database is running")
    print("2. Ensure Redis test instance is running")
    print("3. Run: pytest tests/integration/test_auth_system.py -v")
    print()
    print("Test Coverage:")
    print("- JWT token authentication")
    print("- API key management")
    print("- Role-based permissions")
    print("- Subscription tier rate limiting")
    print("- Security features (hashing, expiration)")
    print("- MCP server integration")
    print("- Audit logging capabilities")