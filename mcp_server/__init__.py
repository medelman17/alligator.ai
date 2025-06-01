"""
alligator.ai MCP Server - Legal Research Platform

Model Context Protocol (MCP) server providing AI assistants with access to:
- Comprehensive legal case search across all U.S. jurisdictions
- Real-time case discovery via CourtListener API
- Semantic similarity search using ChromaDB
- Citation-driven network analysis and expansion
- AI-powered legal research workflows
- Professional legal memo generation

Usage:
    # Run the MCP server
    python -m mcp_server.server
    
    # Or import and use programmatically
    from mcp_server import AlligatorAIMCP
    server = AlligatorAIMCP()
    await server.run()
"""

from .server import AlligatorAIMCP
from .config import settings, MCPServerSettings
from .tools import (
    CourtListenerTools,
    ResearchTools,
    AnalysisTools,
    get_available_tools,
    get_tools_by_category,
    get_tool_description,
    TOOL_CATEGORIES
)

__version__ = "1.0.0"
__author__ = "alligator.ai"
__email__ = "support@alligator.ai"

__all__ = [
    "AlligatorAIMCP",
    "settings",
    "MCPServerSettings",
    "CourtListenerTools",
    "ResearchTools", 
    "AnalysisTools",
    "get_available_tools",
    "get_tools_by_category",
    "get_tool_description"
]

# Server metadata
SERVER_INFO = {
    "name": "alligator-ai",
    "version": __version__,
    "description": "AI-powered legal research platform with comprehensive case search and analysis",
    "capabilities": [
        "Legal case search across all U.S. jurisdictions",
        "Real-time CourtListener API integration", 
        "Semantic case similarity analysis",
        "Citation network expansion and discovery",
        "AI-powered research workflows",
        "Legal authority and precedent analysis",
        "Professional memo generation"
    ],
    "supported_jurisdictions": [
        "Federal Courts (Supreme Court, Circuit Courts, District Courts)",
        "All 50 State Court Systems",
        "Specialized Federal Courts",
        "Administrative Courts"
    ],
    "data_sources": [
        "CourtListener API (350,000+ cases)",
        "ChromaDB semantic search (landmark cases)",
        "Neo4j citation networks",
        "Real-time case discovery"
    ]
}

def get_server_info():
    """Get server information and capabilities"""
    return SERVER_INFO

def get_tool_info():
    """Get information about available tools"""
    tools = get_available_tools()
    return {
        "total_tools": len(tools),
        "tool_categories": list(TOOL_CATEGORIES.keys()),
        "tools": {
            tool: get_tool_description(tool) 
            for tool in tools
        }
    }

# Configuration validation
def validate_server_setup():
    """Validate server setup and dependencies"""
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "dependencies": {}
    }
    
    # Check configuration
    config_validation = settings.validate_configuration()
    validation_results["valid"] = config_validation["valid"]
    validation_results["errors"].extend(config_validation["errors"])
    validation_results["warnings"].extend(config_validation["warnings"])
    
    # Check optional dependencies
    try:
        from mcp.server import Server
        validation_results["dependencies"]["mcp"] = "Available"
    except ImportError:
        validation_results["dependencies"]["mcp"] = "Missing (development mode)"
        validation_results["warnings"].append("MCP library not available - running in development mode")
    
    try:
        import httpx
        validation_results["dependencies"]["httpx"] = "Available"
    except ImportError:
        validation_results["dependencies"]["httpx"] = "Missing"
        validation_results["errors"].append("httpx library required for API calls")
        validation_results["valid"] = False
    
    try:
        from services.ingestion.courtlistener_client import CourtListenerClient
        validation_results["dependencies"]["courtlistener"] = "Available"
    except ImportError:
        validation_results["dependencies"]["courtlistener"] = "Missing"
        validation_results["errors"].append("CourtListener client not available")
        validation_results["valid"] = False
    
    try:
        from services.vector.chroma_service import ChromaService
        validation_results["dependencies"]["chroma"] = "Available"
    except ImportError:
        validation_results["dependencies"]["chroma"] = "Missing"
        validation_results["warnings"].append("ChromaDB service not available - semantic search limited")
    
    return validation_results