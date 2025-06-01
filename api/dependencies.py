"""
Dependency injection for FastAPI application.

Manages service instances and database connections with proper lifecycle management.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from api.auth.dependencies import AuthDependencies
from api.auth.service import AuthService
from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
from services.orchestration.agents.precedent_analyzer import PrecedentAnalyzer
from services.vector.chroma_service import ChromaService

logger = logging.getLogger(__name__)

# Global service instances (will be initialized at startup)
_neo4j_service: Optional[EnhancedNeo4jService] = None
_chroma_service: Optional[ChromaService] = None
_precedent_analyzer: Optional[PrecedentAnalyzer] = None
_auth_service: Optional[AuthService] = None
_auth_dependencies: Optional[AuthDependencies] = None


class ServiceManager:
    """Manages service lifecycle and configuration."""

    def __init__(self):
        self.neo4j_service: Optional[EnhancedNeo4jService] = None
        self.chroma_service: Optional[ChromaService] = None
        self.precedent_analyzer: Optional[PrecedentAnalyzer] = None
        self.auth_service: Optional[AuthService] = None
        self.auth_dependencies: Optional[AuthDependencies] = None
        self._initialized = False

    async def initialize(self):
        """Initialize all services with proper configuration."""
        if self._initialized:
            return

        logger.info("Initializing services...")

        try:
            # Initialize Neo4j service
            await self._initialize_neo4j()

            # Initialize ChromaDB service
            await self._initialize_chroma()

            # Initialize AI agents
            await self._initialize_agents()

            # Initialize authentication system
            await self._initialize_auth()

            self._initialized = True
            logger.info("✅ All services initialized successfully")

        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            raise

    async def _initialize_neo4j(self):
        """Initialize Neo4j service with configuration."""
        try:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "citation_graph_2024")

            self.neo4j_service = EnhancedNeo4jService(
                uri=neo4j_uri, user=neo4j_user, password=neo4j_password
            )

            # Test connection
            await self.neo4j_service.connect()
            logger.info("✅ Neo4j service initialized")

        except Exception as e:
            logger.warning(f"⚠️ Neo4j initialization failed: {e}")
            # Create mock service for development
            self.neo4j_service = MockNeo4jService()
            logger.info("📝 Using mock Neo4j service")

    async def _initialize_chroma(self):
        """Initialize ChromaDB service with configuration."""
        try:
            chroma_host = os.getenv("CHROMA_HOST", "localhost")
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

            self.chroma_service = ChromaService()

            # Test connection
            await self.chroma_service.initialize()
            logger.info("✅ ChromaDB service initialized")

        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
            # Create mock service for development
            self.chroma_service = MockChromaService()
            logger.info("📝 Using mock ChromaDB service")

    async def _initialize_agents(self):
        """Initialize AI agents and orchestration."""
        try:
            # Get Anthropic API key
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            # Initialize precedent analyzer with services
            self.precedent_analyzer = PrecedentAnalyzer(
                neo4j_service=self.neo4j_service,
                chroma_service=self.chroma_service,
                anthropic_api_key=anthropic_api_key,
            )

            logger.info("✅ AI agents initialized")

        except Exception as e:
            logger.warning(f"⚠️ Agent initialization failed: {e}")
            # Create mock agent for development
            self.precedent_analyzer = MockPrecedentAnalyzer()
            logger.info("📝 Using mock precedent analyzer")

    async def _initialize_auth(self):
        """Initialize authentication system."""
        try:
            # PostgreSQL connection pool for auth service
            import asyncpg

            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                # Use default values for development
                database_url = (
                    "postgresql://citation_user:citation_pass_2024@localhost:5432/citation_graph"
                )

            # Create connection pool
            db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)

            # JWT configuration
            jwt_secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
            jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

            # Initialize auth service
            self.auth_service = AuthService(
                db_pool=db_pool,
                secret_key=jwt_secret,
                algorithm=jwt_algorithm,
                access_token_expire_minutes=access_token_expire_minutes,
            )

            # Initialize Redis for auth dependencies (rate limiting, token blacklist)
            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL", "redis://:citation_redis_2024@localhost:6379/0")
            redis_client = redis.from_url(redis_url)

            # Initialize auth dependencies
            self.auth_dependencies = AuthDependencies(
                auth_service=self.auth_service, redis_client=redis_client
            )

            # Set global auth dependencies for convenience functions
            import api.auth.dependencies as auth_deps_module

            auth_deps_module.auth_deps = self.auth_dependencies

            logger.info("✅ Authentication system initialized")

        except Exception as e:
            logger.warning(f"⚠️ Authentication initialization failed: {e}")
            # For development, we can continue without auth
            logger.info("📝 Continuing without authentication (development mode)")

    async def cleanup(self):
        """Clean up service connections."""
        logger.info("Cleaning up services...")

        try:
            if self.neo4j_service:
                await self.neo4j_service.close()

            if self.chroma_service:
                # ChromaDB doesn't require explicit cleanup
                pass

            logger.info("✅ Services cleaned up")

        except Exception as e:
            logger.error(f"❌ Service cleanup failed: {e}")

    async def health_check(self) -> dict:
        """Check health of all services."""
        health_status = {
            "neo4j": "unknown",
            "chromadb": "unknown",
            "agents": "unknown",
            "auth": "unknown",
        }

        # Check Neo4j
        try:
            if self.neo4j_service:
                await self.neo4j_service.health_check()
                health_status["neo4j"] = "healthy"
        except Exception:
            health_status["neo4j"] = "unhealthy"

        # Check ChromaDB
        try:
            if self.chroma_service:
                await self.chroma_service.get_collection_stats("cases")
                health_status["chromadb"] = "healthy"
        except Exception:
            health_status["chromadb"] = "unhealthy"

        # Check agents
        try:
            if self.precedent_analyzer:
                health_status["agents"] = "healthy"
        except Exception:
            health_status["agents"] = "unhealthy"

        # Check authentication system
        try:
            if self.auth_service and self.auth_dependencies:
                # Test database connection
                async with self.auth_service.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                # Test Redis connection
                await self.auth_dependencies.redis_client.ping()
                health_status["auth"] = "healthy"
        except Exception:
            health_status["auth"] = "unhealthy"

        return health_status


# Global service manager instance
service_manager = ServiceManager()


# Mock services for development/testing
class MockNeo4jService:
    """Mock Neo4j service for development."""

    async def connect(self):
        pass

    async def close(self):
        pass

    async def health_check(self):
        return True

    async def get_case_by_id(self, case_id: str):
        return None

    async def find_cases_by_criteria(self, **kwargs):
        return []

    async def create_case(self, case):
        return "mock_case_id"

    async def update_case(self, case_id: str, update_data: dict):
        pass

    async def delete_case(self, case_id: str):
        pass

    async def get_citing_cases(self, case_id: str, limit: int = 10):
        return []

    async def get_cited_cases(self, case_id: str, limit: int = 10):
        return []

    async def calculate_authority_score(self, case_id: str):
        return 0.5

    async def get_citation_network(self, case_id: str, depth: int = 2):
        return {"citing_cases": [], "cited_cases": []}

    async def create_citation(self, citation):
        return "mock_citation_id"


class MockChromaService:
    """Mock ChromaDB service for development."""

    async def initialize(self):
        pass

    async def get_collection_info(self, collection_name: str):
        return {"name": collection_name, "count": 0}

    async def semantic_search(
        self, query: str, collection_name: str = "cases", limit: int = 10, **filters
    ):
        return []

    async def add_documents(
        self, collection_name: str, documents: list, metadatas: list, ids: list
    ):
        pass

    async def delete_documents(self, collection_name: str, ids: list):
        pass

    async def get_collection_stats(self, collection_name: str):
        return {"document_count": 0, "collection_name": collection_name}


class MockPrecedentAnalyzer:
    """Mock precedent analyzer for development."""

    async def analyze_precedent(self, case_id: str, query: str, **kwargs):
        return {
            "case_id": case_id,
            "summary": "Mock precedent analysis",
            "precedents": [],
            "authority_analysis": {},
            "confidence_score": 0.5,
            "supporting_cases": [],
            "distinguishing_cases": [],
            "recommendations": ["Mock recommendation"],
        }


# Dependency functions for FastAPI
async def get_neo4j_service() -> EnhancedNeo4jService:
    """Get Neo4j service instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager.neo4j_service


async def get_chroma_service() -> ChromaService:
    """Get ChromaDB service instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager.chroma_service


async def get_precedent_analyzer() -> PrecedentAnalyzer:
    """Get precedent analyzer instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager.precedent_analyzer


async def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager.auth_service


async def get_auth_dependencies() -> AuthDependencies:
    """Get authentication dependencies instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager.auth_dependencies


async def get_service_manager() -> ServiceManager:
    """Get service manager instance."""
    if not service_manager._initialized:
        await service_manager.initialize()
    return service_manager


# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan_manager(app):
    """Manage application lifespan with proper service initialization and cleanup."""
    # Startup
    logger.info("🚀 Starting alligator.ai API server...")
    await service_manager.initialize()

    yield

    # Shutdown
    logger.info("🛑 Shutting down alligator.ai API server...")
    await service_manager.cleanup()
