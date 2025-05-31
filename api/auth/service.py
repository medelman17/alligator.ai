"""
Authentication service for user management and token operations.

Handles user authentication, JWT token generation/validation, and API key management.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from api.auth.models import (
    ROLE_PERMISSIONS,
    APIKey,
    APIKeyRequest,
    Firm,
    LoginRequest,
    LoginResponse,
    Permission,
    TokenData,
    User,
    UserRole,
)


class AuthService:
    """Authentication service for the platform."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 30,
    ):
        self.db_pool = db_pool
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        async with self.db_pool.acquire() as conn:
            # Get user with hashed password
            user_row = await conn.fetchrow(
                """
                SELECT u.*, f.subscription_tier, f.name as firm_name
                FROM users u
                JOIN firms f ON u.firm_id = f.id
                WHERE u.email = $1 AND u.is_active = true
            """,
                email,
            )

            if not user_row:
                return None

            # Verify password
            stored_password = user_row["password_hash"]
            if not self.verify_password(password, stored_password):
                return None

            # Update last login
            await conn.execute(
                """
                UPDATE users SET last_login = NOW() WHERE id = $1
            """,
                user_row["id"],
            )

            # Convert to User model
            return self._row_to_user(user_row)

    async def login(self, request: LoginRequest) -> LoginResponse:
        """Authenticate user and return tokens."""
        user = await self.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get firm information
        firm = await self.get_firm_by_id(user.firm_id)
        if not firm:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Firm not found"
            )

        # Create tokens
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=self.refresh_token_expire_days)

        access_token = await self.create_access_token(
            user=user, firm=firm, expires_delta=access_token_expires
        )
        refresh_token = await self.create_refresh_token(
            user=user, firm=firm, expires_delta=refresh_token_expires
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=user,
            firm=firm,
        )

    async def create_access_token(
        self, user: User, firm: Firm, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        # Get user permissions
        permissions = self.get_user_permissions(user.role, user.permissions)

        token_data = TokenData(
            user_id=user.id,
            firm_id=user.firm_id,
            email=user.email,
            role=user.role,
            permissions=permissions,
            subscription_tier=firm.subscription_tier,
            token_type="access",
        )

        payload = {
            **token_data.dict(),
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(user.id),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def create_refresh_token(
        self, user: User, firm: Firm, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)

        payload = {
            "user_id": str(user.id),
            "firm_id": str(user.firm_id),
            "token_type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": str(user.id),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("token_type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
                )

            # Create TokenData from payload
            token_data = TokenData(
                user_id=UUID(payload["user_id"]),
                firm_id=UUID(payload["firm_id"]),
                email=payload["email"],
                role=UserRole(payload["role"]),
                permissions=[Permission(p) for p in payload["permissions"]],
                subscription_tier=payload["subscription_tier"],
                token_type=payload["token_type"],
            )

            return token_data

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("token_type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
                )

            user_id = UUID(payload["user_id"])

            # Get current user and firm data
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
                )

            firm = await self.get_firm_by_id(user.firm_id)
            if not firm:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Firm not found"
                )

            # Create new access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            return await self.create_access_token(user, firm, access_token_expires)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

    async def create_api_key(self, user_id: UUID, request: APIKeyRequest) -> tuple[APIKey, str]:
        """Create a new API key for programmatic access."""
        # Generate secure API key
        api_key = self._generate_api_key()
        api_key_hash = self._hash_api_key(api_key)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        async with self.db_pool.acquire() as conn:
            # Insert API key record
            api_key_id = await conn.fetchval(
                """
                INSERT INTO api_keys (
                    user_id, firm_id, name, description, key_hash,
                    permissions, expires_at, created_at
                )
                SELECT
                    $1, u.firm_id, $2, $3, $4, $5, $6, NOW()
                FROM users u WHERE u.id = $1
                RETURNING id
            """,
                user_id,
                request.name,
                request.description,
                api_key_hash,
                [p.value for p in request.permissions],
                expires_at,
            )

            # Get the created API key
            api_key_row = await conn.fetchrow(
                """
                SELECT * FROM api_keys WHERE id = $1
            """,
                api_key_id,
            )

        api_key_obj = self._row_to_api_key(api_key_row)
        return api_key_obj, api_key

    async def verify_api_key(self, api_key: str) -> TokenData:
        """Verify API key and return token data."""
        api_key_hash = self._hash_api_key(api_key)

        async with self.db_pool.acquire() as conn:
            # Get API key with user and firm data
            row = await conn.fetchrow(
                """
                SELECT
                    ak.*, u.email, u.role, u.firm_id,
                    f.subscription_tier
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                JOIN firms f ON u.firm_id = f.id
                WHERE ak.key_hash = $1
                    AND ak.is_active = true
                    AND ak.expires_at > NOW()
                    AND u.is_active = true
            """,
                api_key_hash,
            )

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key"
                )

            # Update last used timestamp
            await conn.execute(
                """
                UPDATE api_keys SET last_used = NOW() WHERE id = $1
            """,
                row["id"],
            )

        # Create token data for API key
        permissions = [Permission(p) for p in row["permissions"]]
        return TokenData(
            user_id=row["user_id"],
            firm_id=row["firm_id"],
            email=row["email"],
            role=UserRole(row["role"]),
            permissions=permissions,
            subscription_tier=row["subscription_tier"],
            token_type="api_key",
        )

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT u.*, f.subscription_tier
                FROM users u
                JOIN firms f ON u.firm_id = f.id
                WHERE u.id = $1
            """,
                user_id,
            )

            if row:
                return self._row_to_user(row)
            return None

    async def get_firm_by_id(self, firm_id: UUID) -> Optional[Firm]:
        """Get firm by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM firms WHERE id = $1", firm_id)
            if row:
                return self._row_to_firm(row)
            return None

    def get_user_permissions(
        self, role: UserRole, custom_permissions: list[Permission] = None
    ) -> list[Permission]:
        """Get effective permissions for a user."""
        # Start with role-based permissions
        permissions = set(ROLE_PERMISSIONS.get(role, []))

        # Add any custom permissions
        if custom_permissions:
            permissions.update(custom_permissions)

        return list(permissions)

    def has_permission(
        self, user_permissions: list[Permission], required_permission: Permission
    ) -> bool:
        """Check if user has required permission."""
        return required_permission in user_permissions

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password."""
        return self.pwd_context.hash(password)

    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        # Format: alg_<random_32_chars>
        random_part = secrets.token_urlsafe(24)
        return f"alg_{random_part}"

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _row_to_user(self, row) -> User:
        """Convert database row to User model."""
        return User(
            id=row["id"],
            firm_id=row["firm_id"],
            email=row["email"],
            full_name=row["full_name"],
            role=UserRole(row["role"]),
            bar_number=row.get("bar_number"),
            practice_areas=row.get("practice_areas", []),
            permissions=[Permission(p) for p in row.get("permissions", {}).get("custom", [])],
            preferences=row.get("preferences", {}),
            last_login=row.get("last_login"),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_firm(self, row) -> Firm:
        """Convert database row to Firm model."""
        return Firm(
            id=row["id"],
            name=row["name"],
            short_name=row["short_name"],
            bar_number=row.get("bar_number"),
            jurisdiction=row["jurisdiction"],
            practice_areas=row.get("practice_areas", []),
            subscription_tier=row["subscription_tier"],
            settings=row.get("settings", {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_api_key(self, row) -> APIKey:
        """Convert database row to APIKey model."""
        return APIKey(
            id=row["id"],
            user_id=row["user_id"],
            firm_id=row["firm_id"],
            name=row["name"],
            description=row.get("description"),
            key_hash=row["key_hash"],
            permissions=[Permission(p) for p in row["permissions"]],
            last_used=row.get("last_used"),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            is_active=row["is_active"],
        )
