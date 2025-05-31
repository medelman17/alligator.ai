"""
FastAPI application for alligator.ai legal research platform.

This module creates and configures the FastAPI application with all routes,
middleware, and dependencies for the legal research API.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from api.endpoints import search, cases, research
from api.middleware.logging import RequestLoggingMiddleware
from api.middleware.rate_limiting import RateLimitMiddleware
from shared.models.legal_entities import Case, Court, Judge, Citation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting alligator.ai API server...")
    
    # Initialize database connections and services
    # TODO: Add service initialization here when we implement dependency injection
    
    yield
    
    logger.info("Shutting down alligator.ai API server...")
    # Clean up resources
    # TODO: Add cleanup logic here


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="alligator.ai Legal Research API",
        description="AI-powered legal research platform for boutique litigation firms",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        # Custom OpenAPI schema
        openapi_tags=[
            {
                "name": "search",
                "description": "Legal document search and discovery operations"
            },
            {
                "name": "cases", 
                "description": "Case management and retrieval operations"
            },
            {
                "name": "research",
                "description": "AI-powered legal research workflows"
            },
            {
                "name": "health",
                "description": "System health and monitoring endpoints"
            }
        ]
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Include routers
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Frontend origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.alligator.ai"]
    )
    
    # Custom request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)


def setup_routes(app: FastAPI) -> None:
    """Configure application routes."""
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
    @app.get("/api/v1/health", tags=["health"])
    async def api_health_check():
        """Detailed API health check with service status."""
        # TODO: Add actual service health checks
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": {
                "neo4j": "healthy",  # TODO: Implement actual checks
                "chromadb": "healthy",
                "postgresql": "healthy", 
                "redis": "healthy"
            }
        }
    
    # Include API routers
    app.include_router(
        search.router,
        prefix="/api/v1/search",
        tags=["search"]
    )
    
    app.include_router(
        cases.router,
        prefix="/api/v1/cases", 
        tags=["cases"]
    )
    
    app.include_router(
        research.router,
        prefix="/api/v1/research",
        tags=["research"]
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "type": "InternalServerError"
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation error",
                "message": str(exc),
                "type": "ValidationError"
            }
        )


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )