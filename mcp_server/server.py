#!/usr/bin/env python3
"""alligator.ai MCP Server - Legal Research Platform

Provides AI assistants with access to comprehensive legal research capabilities:
- Real legal case search across all U.S. jurisdictions via CourtListener API
- Semantic search with ChromaDB for case similarity analysis  
- Citation-driven case discovery and network expansion
- Research workflow orchestration with multi-agent AI
- Legal memo generation and precedent analysis
"""

import asyncio
import logging
import sys
import os
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
        Prompt,
        PromptMessage,
        UserMessage,
        AssistantMessage
    )
except ImportError:
    # Fallback for development - create mock types
    class Server:
        def __init__(self, name):
            self.name = name
            self._tools = []
            
        def list_tools(self):
            def decorator(func):
                self._list_tools_func = func
                return func
            return decorator
            
        def call_tool(self):
            def decorator(func):
                self._call_tool_func = func
                return func
            return decorator
            
        def list_resources(self):
            def decorator(func):
                self._list_resources_func = func
                return func
            return decorator
            
        def read_resource(self):
            def decorator(func):
                self._read_resource_func = func
                return func
            return decorator
            
        async def run(self, read_stream, write_stream, options):
            print("MCP Server running in development mode")
            await asyncio.sleep(3600)  # Keep running
    
    class Tool:
        def __init__(self, name, description, inputSchema):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, type, text):
            self.type = type
            self.text = text
    
    class Resource:
        def __init__(self, uri, name, description, mimeType):
            self.uri = uri
            self.name = name
            self.description = description
            self.mimeType = mimeType
    
    async def stdio_server():
        class MockStream:
            async def read(self):
                return b""
            async def write(self, data):
                pass
        yield MockStream(), MockStream()

from mcp_server.tools.courtlistener import CourtListenerTools
from mcp_server.tools.research import ResearchTools
from mcp_server.tools.analysis import AnalysisTools
from mcp_server.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlligatorAIMCP:
    """alligator.ai MCP Server for Legal Research"""
    
    def __init__(self):
        self.server = Server("alligator-ai")
        
        # Initialize tool handlers
        self.courtlistener_tools = CourtListenerTools(settings)
        self.research_tools = ResearchTools(settings)
        self.analysis_tools = AnalysisTools(settings)
        
        # Register handlers
        self._register_handlers()
        
        logger.info("alligator.ai MCP Server initialized")
    
    def _register_handlers(self):
        """Register all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available legal research tools"""
            tools = []
            
            # CourtListener legal case search tools
            tools.extend([
                Tool(
                    name="search_legal_cases",
                    description="Search for legal cases across all U.S. jurisdictions using CourtListener API. Supports federal courts, state courts, and specialized courts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for legal cases (case name, legal issue, keywords)"
                            },
                            "jurisdiction": {
                                "type": "string",
                                "description": "Jurisdiction code (e.g., 'scotus', 'ca9', 'nj', 'ny', 'ca'). Leave empty for all jurisdictions"
                            },
                            "court_type": {
                                "type": "string",
                                "enum": ["federal", "state", "appellate", "trial", "supreme"],
                                "description": "Type of court to search"
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "format": "date", "description": "Start date (YYYY-MM-DD)"},
                                    "end": {"type": "string", "format": "date", "description": "End date (YYYY-MM-DD)"}
                                },
                                "description": "Date range for case decisions"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100,
                                "description": "Maximum number of results"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_case_details",
                    description="Get detailed information about a specific legal case including full text, citations, and metadata",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "case_id": {
                                "type": "string",
                                "description": "CourtListener case ID or citation"
                            },
                            "include_full_text": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include full case text in response"
                            },
                            "include_citations": {
                                "type": "boolean", 
                                "default": True,
                                "description": "Extract and include legal citations"
                            }
                        },
                        "required": ["case_id"]
                    }
                ),
                Tool(
                    name="citation_network_expansion",
                    description="Discover related cases through citation analysis. Expands legal research by following case citations to build comprehensive case networks.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "seed_case_id": {
                                "type": "string",
                                "description": "Starting case ID for citation expansion"
                            },
                            "expansion_depth": {
                                "type": "integer",
                                "default": 2,
                                "minimum": 1,
                                "maximum": 3,
                                "description": "How many citation levels to expand (1=direct citations, 2=citations of citations, etc.)"
                            },
                            "max_cases": {
                                "type": "integer", 
                                "default": 50,
                                "minimum": 10,
                                "maximum": 200,
                                "description": "Maximum total cases to discover"
                            },
                            "jurisdiction_filter": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Limit expansion to specific jurisdictions"
                            }
                        },
                        "required": ["seed_case_id"]
                    }
                )
            ])
            
            # Research workflow tools  
            tools.extend([
                Tool(
                    name="conduct_legal_research",
                    description="Conduct comprehensive legal research using AI agents. Combines semantic search, citation analysis, and legal reasoning.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "research_question": {
                                "type": "string",
                                "description": "Legal research question or issue to investigate"
                            },
                            "case_facts": {
                                "type": "string",
                                "description": "Relevant facts of your case or situation"
                            },
                            "jurisdiction": {
                                "type": "string",
                                "description": "Primary jurisdiction for research"
                            },
                            "practice_areas": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["constitutional", "criminal", "civil_rights", "contract", "tort", "employment", "environmental", "corporate", "tax", "family", "immigration", "intellectual_property"]
                                },
                                "description": "Relevant practice areas"
                            },
                            "research_depth": {
                                "type": "string",
                                "enum": ["quick", "standard", "comprehensive"],
                                "default": "standard",
                                "description": "Depth of research analysis"
                            }
                        },
                        "required": ["research_question"]
                    }
                ),
                Tool(
                    name="semantic_case_search",
                    description="Find legally similar cases using semantic search. Uses AI embeddings to find cases with similar legal concepts and fact patterns.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Description of legal issue or fact pattern"
                            },
                            "jurisdiction": {
                                "type": "string",
                                "description": "Jurisdiction to search within"
                            },
                            "practice_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Relevant practice areas to filter by"
                            },
                            "similarity_threshold": {
                                "type": "number",
                                "default": 0.7,
                                "minimum": 0.5,
                                "maximum": 1.0,
                                "description": "Minimum similarity score (0.5-1.0)"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50,
                                "description": "Maximum results to return"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ])
            
            # Legal analysis tools
            tools.extend([
                Tool(
                    name="analyze_case_authority",
                    description="Analyze the legal authority and precedential value of cases using citation networks and court hierarchy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "case_id": {
                                "type": "string",
                                "description": "Case ID or citation to analyze"
                            },
                            "target_jurisdiction": {
                                "type": "string",
                                "description": "Jurisdiction where authority will be evaluated"
                            },
                            "analysis_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["authority_score", "citation_treatment", "good_law_status", "binding_precedent"]
                                },
                                "default": ["authority_score", "good_law_status"],
                                "description": "Types of authority analysis to perform"
                            }
                        },
                        "required": ["case_id"]
                    }
                ),
                Tool(
                    name="generate_legal_memo",
                    description="Generate a professional legal research memorandum based on research results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "research_session_id": {
                                "type": "string",
                                "description": "Research session ID from conduct_legal_research"
                            },
                            "memo_type": {
                                "type": "string",
                                "enum": ["research_memo", "case_brief", "authority_analysis", "client_advisory"],
                                "default": "research_memo",
                                "description": "Type of legal document to generate"
                            },
                            "audience": {
                                "type": "string",
                                "enum": ["internal", "client", "court"],
                                "default": "internal",
                                "description": "Intended audience for the memo"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["markdown", "html", "text"],
                                "default": "markdown",
                                "description": "Output format"
                            }
                        },
                        "required": ["research_session_id"]
                    }
                )
            ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
            """Handle tool execution"""
            logger.info(f"Executing tool: {name}")
            
            try:
                # Route to appropriate handler
                if name == "search_legal_cases":
                    result = await self.courtlistener_tools.search_cases(**arguments)
                elif name == "get_case_details":
                    result = await self.courtlistener_tools.get_case_details(**arguments)
                elif name == "citation_network_expansion":
                    result = await self.courtlistener_tools.citation_expansion(**arguments)
                elif name == "conduct_legal_research":
                    result = await self.research_tools.conduct_research(**arguments)
                elif name == "semantic_case_search":
                    result = await self.research_tools.semantic_search(**arguments)
                elif name == "analyze_case_authority":
                    result = await self.analysis_tools.analyze_authority(**arguments)
                elif name == "generate_legal_memo":
                    result = await self.research_tools.generate_memo(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Format result as JSON string for MCP
                import json
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available legal research resources"""
            return [
                Resource(
                    uri="legal://recent-research",
                    name="Recent Legal Research",
                    description="View recently conducted legal research sessions",
                    mimeType="application/json"
                ),
                Resource(
                    uri="legal://court-hierarchy",
                    name="U.S. Court Hierarchy",
                    description="Reference guide to U.S. federal and state court systems",
                    mimeType="application/json"
                ),
                Resource(
                    uri="legal://jurisdiction-guide",
                    name="Jurisdiction Reference",
                    description="Guide to court jurisdiction codes and coverage",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "legal://recent-research":
                research = await self.research_tools.get_recent_sessions()
                return str(research)
            elif uri == "legal://court-hierarchy":
                hierarchy = await self.courtlistener_tools.get_court_hierarchy()
                return str(hierarchy)
            elif uri == "legal://jurisdiction-guide":
                guide = await self.courtlistener_tools.get_jurisdiction_guide()
                return str(guide)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def run(self):
        """Run the MCP server"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="alligator-ai",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Server failed to run: {e}")
            # In development mode, keep server alive
            if hasattr(self.server, '_list_tools_func'):
                logger.info("Running in development mode")
                await asyncio.sleep(3600)


async def main():
    """Main entry point"""
    server = AlligatorAIMCP()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())