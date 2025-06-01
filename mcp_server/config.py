"""
Configuration settings for alligator.ai MCP Server.

Manages environment variables and settings for:
- API connections and authentication
- Service endpoints and timeouts
- Rate limiting and performance settings
- Debug and logging configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class MCPServerSettings(BaseSettings):
    """Settings for alligator.ai MCP Server"""
    
    # MCP Server Configuration
    MCP_SERVER_NAME: str = "alligator-ai"
    MCP_SERVER_VERSION: str = "1.0.0"
    MCP_DEBUG: bool = False
    
    # API Configuration - alligator.ai platform
    API_BASE_URL: str = "http://localhost:8001"
    API_KEY: Optional[str] = None
    API_TIMEOUT: int = 120  # seconds
    
    # CourtListener API Configuration
    COURTLISTENER_API_TOKEN: Optional[str] = None
    COURTLISTENER_BASE_URL: str = "https://www.courtlistener.com/api/rest/v4/"
    COURTLISTENER_TIMEOUT: int = 30
    COURTLISTENER_RATE_LIMIT: int = 4000  # requests per hour
    
    # Database Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "citation_graph_2024"
    NEO4J_TIMEOUT: int = 30
    
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_TIMEOUT: int = 30
    
    POSTGRES_URL: str = "postgresql://citation_user:citation_pass_2024@localhost:5432/citation_graph"
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = "citation_redis_2024"
    
    # AI/LLM Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "anthropic"
    LLM_TIMEOUT: int = 60
    
    # Performance and Rate Limiting
    MAX_CONCURRENT_REQUESTS: int = 10
    DEFAULT_REQUEST_TIMEOUT: int = 30
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # MCP Tool Configuration
    MAX_SEARCH_RESULTS: int = 100
    DEFAULT_SEARCH_LIMIT: int = 20
    MAX_CITATION_EXPANSION_DEPTH: int = 3
    MAX_CITATION_EXPANSION_CASES: int = 200
    
    # Semantic Search Configuration
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.5
    SEMANTIC_SEARCH_MAX_RESULTS: int = 50
    
    # Research Configuration
    RESEARCH_SESSION_TIMEOUT: int = 300  # 5 minutes
    MAX_RESEARCH_CASES: int = 50
    MEMO_GENERATION_TIMEOUT: int = 120  # 2 minutes
    
    # Security Configuration
    ENABLE_AUTH: bool = False  # Set to True in production
    SECRET_KEY: str = "mcp-server-secret-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ENABLE_REQUEST_LOGGING: bool = True
    
    # Development Configuration
    DEVELOPMENT_MODE: bool = True
    MOCK_SERVICES: bool = False  # Set to True to use mock services
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables
    
    def get_api_headers(self) -> dict:
        """Get headers for API requests"""
        headers = {
            "User-Agent": f"alligator-ai-mcp/{self.MCP_SERVER_VERSION}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.API_KEY:
            headers["Authorization"] = f"Bearer {self.API_KEY}"
        
        return headers
    
    def get_courtlistener_headers(self) -> dict:
        """Get headers for CourtListener API requests"""
        headers = {
            "User-Agent": f"alligator-ai-mcp/{self.MCP_SERVER_VERSION}",
            "Accept": "application/json"
        }
        
        if self.COURTLISTENER_API_TOKEN:
            headers["Authorization"] = f"Token {self.COURTLISTENER_API_TOKEN}"
        
        return headers
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEVELOPMENT_MODE and self.ENABLE_AUTH
    
    def get_neo4j_config(self) -> dict:
        """Get Neo4j connection configuration"""
        return {
            "uri": self.NEO4J_URI,
            "user": self.NEO4J_USER,
            "password": self.NEO4J_PASSWORD,
            "timeout": self.NEO4J_TIMEOUT
        }
    
    def get_chroma_config(self) -> dict:
        """Get ChromaDB configuration"""
        return {
            "host": self.CHROMA_HOST,
            "port": self.CHROMA_PORT,
            "timeout": self.CHROMA_TIMEOUT
        }
    
    def validate_configuration(self) -> dict:
        """Validate configuration and return status"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check required API endpoints
        if not self.API_BASE_URL:
            validation_results["errors"].append("API_BASE_URL is required")
            validation_results["valid"] = False
        
        # Check authentication in production
        if self.is_production() and not self.API_KEY:
            validation_results["warnings"].append("API_KEY should be set in production")
        
        # Check CourtListener configuration
        if not self.COURTLISTENER_API_TOKEN:
            validation_results["warnings"].append("COURTLISTENER_API_TOKEN not set - using anonymous access with rate limits")
        
        # Check LLM API keys
        if not self.ANTHROPIC_API_KEY and not self.OPENAI_API_KEY:
            validation_results["warnings"].append("No LLM API keys configured - some features may be limited")
        
        # Check database connections
        database_warnings = []
        if "localhost" in self.NEO4J_URI:
            database_warnings.append("Neo4j")
        if self.CHROMA_HOST == "localhost":
            database_warnings.append("ChromaDB")
        if "localhost" in self.POSTGRES_URL:
            database_warnings.append("PostgreSQL")
        
        if database_warnings:
            validation_results["warnings"].append(f"Using localhost for: {', '.join(database_warnings)}")
        
        return validation_results


# Global settings instance
settings = MCPServerSettings()


# Configuration validation on import
def validate_and_log_config():
    """Validate configuration and log results"""
    import logging
    
    # Configure logging based on settings
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT
    )
    
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    validation = settings.validate_configuration()
    
    if validation["valid"]:
        logger.info("MCP Server configuration validated successfully")
    else:
        logger.error("MCP Server configuration validation failed")
        for error in validation["errors"]:
            logger.error(f"Configuration error: {error}")
    
    # Log warnings
    for warning in validation["warnings"]:
        logger.warning(f"Configuration warning: {warning}")
    
    # Log key configuration details
    logger.info(f"MCP Server: {settings.MCP_SERVER_NAME} v{settings.MCP_SERVER_VERSION}")
    logger.info(f"API Base URL: {settings.API_BASE_URL}")
    logger.info(f"Development Mode: {settings.DEVELOPMENT_MODE}")
    logger.info(f"Authentication Enabled: {settings.ENABLE_AUTH}")
    
    if settings.COURTLISTENER_API_TOKEN:
        logger.info("CourtListener API: Authenticated access")
    else:
        logger.info("CourtListener API: Anonymous access (rate limited)")
    
    return validation


# Environment-specific configurations
def get_development_config() -> MCPServerSettings:
    """Get development configuration"""
    config = MCPServerSettings()
    config.DEVELOPMENT_MODE = True
    config.ENABLE_AUTH = False
    config.LOG_LEVEL = "DEBUG"
    config.MCP_DEBUG = True
    return config


def get_production_config() -> MCPServerSettings:
    """Get production configuration"""
    config = MCPServerSettings()
    config.DEVELOPMENT_MODE = False
    config.ENABLE_AUTH = True
    config.LOG_LEVEL = "INFO"
    config.MCP_DEBUG = False
    
    # Production-specific validation
    required_production_vars = [
        "API_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_production_vars:
        if not getattr(config, var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Production configuration missing required variables: {missing_vars}")
    
    return config


def get_testing_config() -> MCPServerSettings:
    """Get testing configuration"""
    config = MCPServerSettings()
    config.DEVELOPMENT_MODE = True
    config.MOCK_SERVICES = True
    config.LOG_LEVEL = "WARNING"
    config.API_BASE_URL = "http://localhost:8001"
    config.NEO4J_URI = "bolt://localhost:7687"
    return config


# Validate configuration on import
if __name__ != "__main__":
    validate_and_log_config()