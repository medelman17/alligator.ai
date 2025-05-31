# Authentication System Design for alligator.ai

## Overview

This document outlines the comprehensive authentication and authorization system designed for the alligator.ai legal research platform. The system supports multi-tenant B2B SaaS architecture with firm-level billing, role-based access control, and sophisticated rate limiting.

## Architecture Components

### 1. Authentication Models (`/api/auth/models.py`)

**Core Entities:**
- **User**: Individual users within law firms (attorneys, paralegals, admins)
- **Firm**: Law firm organizations with subscription tiers
- **TokenData**: JWT token payload structure
- **APIKey**: Programmatic access credentials

**User Roles:**
- `ADMIN`: Full firm administration access
- `PARTNER`: Senior attorney with elevated permissions
- `ATTORNEY`: Standard legal practitioner
- `ASSOCIATE`: Junior attorney with limited permissions
- `PARALEGAL`: Legal support staff
- `GUEST`: Read-only access

**Subscription Tiers:**
- `BASIC`: 30 req/min, 500 req/hour, 2,000 req/day
- `PROFESSIONAL`: 100 req/min, 2,000 req/hour, 10,000 req/day
- `ENTERPRISE`: 500 req/min, 10,000 req/hour, 50,000 req/day

**Granular Permissions:**
```python
# Research permissions
RESEARCH_READ, RESEARCH_WRITE, RESEARCH_DELETE

# Case permissions  
CASE_READ, CASE_WRITE, CASE_DELETE

# Document permissions
DOCUMENT_READ, DOCUMENT_WRITE, DOCUMENT_DELETE, DOCUMENT_EXPORT

# Administrative permissions
FIRM_ADMIN, USER_MANAGE, BILLING_READ, ANALYTICS_READ

# API access permissions
API_ACCESS, MCP_ACCESS
```

### 2. Authentication Service (`/api/auth/service.py`)

**Core Functionality:**
- User authentication with bcrypt password hashing
- JWT token generation and validation (access + refresh tokens)
- API key creation and verification
- Permission management and validation
- Secure password reset and email verification

**Token Structure:**
```json
{
  "user_id": "uuid",
  "firm_id": "uuid", 
  "email": "user@firm.com",
  "role": "attorney",
  "permissions": ["research:read", "research:write"],
  "subscription_tier": "professional",
  "token_type": "access",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**API Key Format:**
- Prefix: `alg_` followed by secure random string
- SHA256 hashed for storage
- Configurable expiration (1 day to 10 years)
- Granular permission assignment

### 3. FastAPI Dependencies (`/api/auth/dependencies.py`)

**Dependency Injection Functions:**
- `get_current_user()`: Extract and validate JWT token
- `require_permissions(*permissions)`: Permission-based authorization
- `require_subscription_tier(tier)`: Subscription tier enforcement  
- `rate_limit_general()`: Standard rate limiting
- `rate_limit_llm()`: LLM-specific rate limiting

**Usage Example:**
```python
@router.post("/research/sessions")
async def create_research_session(
    request_data: dict,
    current_user: TokenData = Depends(get_current_user),
    _: TokenData = Depends(require_permissions(Permission.RESEARCH_WRITE)),
    __: TokenData = Depends(rate_limit_general)
):
    # Protected endpoint logic
    pass
```

### 4. Rate Limiting Middleware (`/api/middleware/rate_limiting.py`)

**Sophisticated Rate Limiting:**
- Firm-level rate limiting (not just IP-based)
- Multiple time windows (minute, hour, day)
- Concurrent request limits
- Subscription tier-aware limits
- Redis-backed for scalability

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1234567890
X-RateLimit-Tier: professional
```

## Database Schema

### Core Authentication Tables

```sql
-- Law firms
CREATE TABLE firms (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    settings JSONB DEFAULT '{}'
);

-- Users within firms
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firm_id UUID REFERENCES firms(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'attorney',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

-- API keys for programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    firm_id UUID REFERENCES firms(id),
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions TEXT[] NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Security audit trail
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    firm_id UUID REFERENCES firms(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### Authentication Endpoints (`/api/auth/endpoints.py`)

```
POST /auth/login                    # User login with email/password
POST /auth/refresh                  # Refresh access token
POST /auth/logout                   # Logout (blacklist token)
GET  /auth/me                      # Get current user profile
POST /auth/api-keys               # Create API key
GET  /auth/api-keys               # List user's API keys
DELETE /auth/api-keys/{id}        # Revoke API key
GET  /auth/permissions            # List available permissions
GET  /auth/rate-limits            # Get rate limit information
GET  /auth/usage                  # Get current usage statistics
```

### Example Usage

**Login:**
```bash
curl -X POST /auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "attorney@firm.com", "password": "secure_password"}'
```

**Protected Request:**
```bash
curl -X GET /api/v1/research/sessions \
  -H "Authorization: Bearer <jwt_token>"
```

**API Key Request:**
```bash
curl -X GET /api/v1/cases/bulk \
  -H "Authorization: Bearer alg_secure_api_key_here"
```

## Rate Limiting Strategy

### Firm-Level vs User-Level

**Firm-Level Rate Limiting** (Primary):
- Shared quotas across all firm users
- Subscription tier-based limits
- Prevents one firm from overwhelming system
- Aligns with B2B billing model

**User-Level Rate Limiting** (Secondary):
- Individual user quotas for fairness within firm
- Prevents single user abuse
- Admin override capabilities

### Implementation Details

**Redis Keys Structure:**
```
rate_limit:firm:{firm_id}:minute:{timestamp}
rate_limit:firm:{firm_id}:hour:{timestamp}  
rate_limit:firm:{firm_id}:day:{timestamp}
concurrent:firm:{firm_id}
```

**LLM-Specific Limits:**
```
rate_limit:firm:{firm_id}:llm:minute:{timestamp}
rate_limit:firm:{firm_id}:llm:day:{timestamp}
```

## Role-Based Access Control (RBAC)

### Permission Matrix

| Role      | Research | Cases | Documents | Admin | API | MCP |
|-----------|----------|-------|-----------|-------|-----|-----|
| Guest     | Read     | Read  | Read      | -     | -   | -   |
| Paralegal | Read     | Read  | Read+Write| -     | -   | -   |
| Associate | Read+Write| Read+Write| Read+Write| -  | Yes | -   |
| Attorney  | Read+Write| Read+Write| Read+Write+Export| - | Yes | Yes |
| Partner   | Full     | Full  | Full      | Analytics| Yes| Yes |
| Admin     | Full     | Full  | Full      | Full  | Yes | Yes |

### Custom Permissions

Users can have custom permissions beyond their role defaults:
```json
{
  "custom": ["document:delete", "analytics:read"],
  "restrictions": ["research:delete"]
}
```

## API Key Management

### Security Features

**Key Generation:**
- Format: `alg_` + 24 character URL-safe random string
- SHA256 hashed for database storage
- Never stored in plaintext

**Permission Control:**
- Users can only grant permissions they possess
- Granular permission selection
- Expiration date enforcement (1 day to 10 years)

**Audit Trail:**
- Creation, usage, and revocation logged
- Last used timestamp tracking
- Automatic cleanup of expired keys

### Usage Patterns

**Bulk Data Access:**
```python
# Long-lived API key for data exports
api_key = create_api_key(
    name="Monthly Case Export",
    permissions=[Permission.API_ACCESS, Permission.CASE_READ],
    expires_in_days=365
)
```

**Integration Services:**
```python  
# Limited scope for external integration
api_key = create_api_key(
    name="Document Sync Service",
    permissions=[Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE],
    expires_in_days=30
)
```

## MCP Server Integration

### Authentication for MCP Tools

**JWT Token Method:**
```json
{
  "mcpServers": {
    "legal-research": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "LEGAL_RESEARCH_TOKEN": "${JWT_TOKEN}"
      }
    }
  }
}
```

**API Key Method:**
```json
{
  "mcpServers": {
    "legal-research": {
      "command": "python", 
      "args": ["-m", "mcp_server.server"],
      "env": {
        "LEGAL_RESEARCH_API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### MCP-Specific Rate Limits

- Separate LLM call quotas for MCP usage
- Tool-specific rate limiting
- Session-based usage tracking

## Security Features

### Password Security
- bcrypt hashing with salt rounds
- Minimum password complexity requirements
- Password change tracking
- Secure reset token generation

### Token Security
- Short-lived access tokens (30 minutes)
- Long-lived refresh tokens (30 days)
- Token blacklisting for logout
- Automatic token rotation

### Audit Logging
```sql
INSERT INTO security_audit_log (
    user_id, firm_id, event_type, event_data, 
    ip_address, success, created_at
) VALUES (
    $1, $2, 'login_attempt', 
    '{"method": "password", "user_agent": "..."}',
    $3, $4, NOW()
);
```

**Logged Events:**
- Login/logout attempts
- Password changes
- API key creation/revocation
- Permission changes
- Rate limit violations
- Failed authentication attempts

## Integration with Existing System

### FastAPI Dependencies Integration

The authentication system integrates seamlessly with the existing FastAPI dependency injection:

```python
# Before (unprotected)
@router.post("/research/sessions")
async def create_research_session(
    request: ResearchRequest,
    analyzer = Depends(get_precedent_analyzer)
):
    pass

# After (protected)
@router.post("/research/sessions") 
async def create_research_session(
    request: ResearchRequest,
    current_user: TokenData = Depends(get_current_user),
    _: TokenData = Depends(require_permissions(Permission.RESEARCH_WRITE)),
    analyzer = Depends(get_precedent_analyzer)
):
    pass
```

### Middleware Stack Integration

```python
# Enhanced middleware stack
app.add_middleware(
    AuthenticatedRateLimitMiddleware,
    redis_client=redis_client,
    secret_key=settings.SECRET_KEY
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CORSMiddleware, ...)
```

### Service Layer Integration

```python
# Enhanced service manager with auth
class ServiceManager:
    def __init__(self):
        self.auth_service = AuthService(...)
        self.neo4j_service = Neo4jService(...)
        self.chroma_service = ChromaService(...)
```

## Configuration and Deployment

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-256-bit-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=postgresql://user:pass@localhost/citation_graph
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=0

# Security
PASSWORD_MIN_LENGTH=8
API_KEY_DEFAULT_EXPIRE_DAYS=365
```

### Production Considerations

**Scalability:**
- Redis Cluster for rate limiting
- Database connection pooling
- Horizontal scaling support

**Security:**
- HTTPS enforcement
- Secure cookie settings
- Regular security audits
- Penetration testing

**Monitoring:**
- Authentication metrics
- Rate limit metrics
- Security event alerting
- Performance monitoring

## Testing Strategy

### Unit Tests
- Password hashing/verification
- Token generation/validation
- Permission checking logic
- Rate limit calculations

### Integration Tests
- End-to-end authentication flow
- Database operations
- Redis rate limiting
- API endpoint protection

### Security Tests
- Token tampering attempts
- Permission escalation tests
- Rate limit bypass attempts
- SQL injection prevention

## Migration and Rollout Plan

### Phase 1: Core Authentication
1. Deploy database schema updates
2. Implement basic JWT authentication
3. Add authentication to critical endpoints
4. Test with limited user base

### Phase 2: Advanced Features
1. Implement API key management
2. Add sophisticated rate limiting
3. Deploy audit logging
4. Full role-based permissions

### Phase 3: MCP Integration
1. Integrate authentication with MCP server
2. Add MCP-specific rate limiting
3. Tool-level permission controls
4. Production deployment

### Backward Compatibility
- Gradual endpoint migration
- Optional authentication headers
- Soft rate limit enforcement initially
- Clear deprecation timelines

## Conclusion

This authentication system provides enterprise-grade security and access control for the alligator.ai platform while maintaining the flexibility needed for a B2B SaaS legal research platform. The design supports the existing FastAPI architecture and provides clear integration points for all platform services.

The system addresses the specific needs of law firms including:
- Multi-user firm environments
- Secure access to sensitive legal data
- Compliance with legal industry standards
- Flexible billing and usage models
- Integration with external AI tools and services