# MCP Server Implementation Guide

## Project Structure

```
legal_research_mcp/
├── __init__.py
├── server.py              # Main MCP server
├── tools/                 # Tool implementations
│   ├── __init__.py
│   ├── search.py
│   ├── research.py
│   ├── analysis.py
│   └── generation.py
├── auth/                  # Authentication
│   ├── __init__.py
│   └── handler.py
├── models/                # Pydantic models
│   ├── __init__.py
│   └── schemas.py
├── config.py             # Configuration
└── requirements.txt      # Dependencies
```

## Core Implementation

### 1. Main Server (server.py)

```python
#!/usr/bin/env python3
"""alligator.ai MCP Server"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
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

from legal_research_mcp.tools import (
    SearchTools,
    ResearchTools,
    AnalysisTools,
    GenerationTools
)
from legal_research_mcp.auth import AuthHandler
from legal_research_mcp.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalResearchMCP:
    def __init__(self):
        self.server = Server("alligator-ai")
        self.auth_handler = AuthHandler(settings.SECRET_KEY)
        
        # Initialize tool handlers
        self.search_tools = SearchTools(settings)
        self.research_tools = ResearchTools(settings)
        self.analysis_tools = AnalysisTools(settings)
        self.generation_tools = GenerationTools(settings)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            tools = []
            
            # Search tools
            tools.extend([
                Tool(
                    name="search_precedents",
                    description="Search for relevant legal precedents using semantic search and citation analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Legal issue or fact pattern to search for"
                            },
                            "jurisdiction": {
                                "type": "string",
                                "description": "Jurisdiction (e.g., 'federal', 'NY', 'CA')"
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "format": "date"},
                                    "end": {"type": "string", "format": "date"}
                                }
                            },
                            "limit": {
                                "type": "integer",
                                "default": 20,
                                "description": "Maximum results"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="analyze_case_law",
                    description="Deep analysis of specific cases including citations and treatment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "case_citation": {
                                "type": "string",
                                "description": "Full case citation"
                            },
                            "analysis_type": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["citations", "treatment", "authority", "distinguishing"]
                                }
                            }
                        },
                        "required": ["case_citation"]
                    }
                )
            ])
            
            # Research tools
            tools.extend([
                Tool(
                    name="conduct_research",
                    description="Conduct comprehensive legal research investigation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "objective": {
                                "type": "string",
                                "description": "Research objective"
                            },
                            "case_facts": {
                                "type": "string",
                                "description": "Relevant case facts"
                            },
                            "jurisdiction": {
                                "type": "string"
                            },
                            "depth": {
                                "type": "string",
                                "enum": ["quick", "standard", "comprehensive"],
                                "default": "standard"
                            }
                        },
                        "required": ["objective"]
                    }
                )
            ])
            
            # Analysis tools
            tools.extend([
                Tool(
                    name="identify_opposing_arguments",
                    description="Identify potential opposing arguments",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "position": {
                                "type": "string",
                                "description": "Your legal position"
                            },
                            "case_type": {
                                "type": "string"
                            }
                        },
                        "required": ["position", "case_type"]
                    }
                )
            ])
            
            # Generation tools
            tools.extend([
                Tool(
                    name="generate_memo",
                    description="Generate legal research memorandum",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "research_id": {
                                "type": "string",
                                "description": "Research investigation ID"
                            },
                            "memo_type": {
                                "type": "string",
                                "enum": ["internal", "client", "court"],
                                "default": "internal"
                            }
                        },
                        "required": ["research_id"]
                    }
                )
            ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
            """Handle tool execution"""
            logger.info(f"Executing tool: {name} with arguments: {arguments}")
            
            try:
                # Route to appropriate handler
                if name == "search_precedents":
                    result = await self.search_tools.search_precedents(**arguments)
                elif name == "analyze_case_law":
                    result = await self.search_tools.analyze_case(**arguments)
                elif name == "conduct_research":
                    result = await self.research_tools.conduct_research(**arguments)
                elif name == "identify_opposing_arguments":
                    result = await self.analysis_tools.identify_opposition(**arguments)
                elif name == "generate_memo":
                    result = await self.generation_tools.generate_memo(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="research://recent",
                    name="Recent Research",
                    description="View recent research investigations",
                    mimeType="application/json"
                ),
                Resource(
                    uri="research://saved",
                    name="Saved Research",
                    description="Access saved research projects",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "research://recent":
                research = await self.research_tools.get_recent_research()
                return str(research)
            elif uri == "research://saved":
                saved = await self.research_tools.get_saved_research()
                return str(saved)
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="case_research",
                    description="Research a legal case comprehensively",
                    arguments=[
                        {
                            "name": "case_type",
                            "description": "Type of case",
                            "required": True
                        },
                        {
                            "name": "facts",
                            "description": "Case facts",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="brief_section",
                    description="Draft a section of a legal brief",
                    arguments=[
                        {
                            "name": "section",
                            "description": "Brief section to draft",
                            "required": True
                        }
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[Dict[str, str]]) -> Optional[List[PromptMessage]]:
            """Get prompt template"""
            if name == "case_research":
                return [
                    UserMessage(
                        content=f"I need comprehensive legal research for a {arguments.get('case_type')} case. "
                               f"The facts are: {arguments.get('facts')}. Please search for relevant precedents, "
                               f"analyze potential arguments, and identify any weaknesses."
                    )
                ]
            elif name == "brief_section":
                return [
                    UserMessage(
                        content=f"Please help me draft the {arguments.get('section')} section of a legal brief. "
                               f"Use proper legal citations and persuasive language."
                    )
                ]
            return None
    
    async def run(self):
        """Run the MCP server"""
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

async def main():
    """Main entry point"""
    server = LegalResearchMCP()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Search Tools (tools/search.py)

```python
"""Search tool implementations"""

import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class SearchTools:
    def __init__(self, settings):
        self.api_base = settings.PLATFORM_API_URL
        self.api_key = settings.PLATFORM_API_KEY
        
    async def search_precedents(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search for legal precedents"""
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            params = {
                "q": query,
                "limit": limit
            }
            
            if jurisdiction:
                params["jurisdiction"] = jurisdiction
            
            if date_range:
                params["date_start"] = date_range.get("start")
                params["date_end"] = date_range.get("end")
            
            async with session.get(
                f"{self.api_base}/api/v1/search/precedents",
                headers=headers,
                params=params
            ) as response:
                data = await response.json()
                
                # Format results for MCP response
                results = {
                    "query": query,
                    "total_results": data["total"],
                    "precedents": []
                }
                
                for case in data["results"]:
                    results["precedents"].append({
                        "citation": case["citation"],
                        "name": case["name"],
                        "court": case["court"],
                        "date": case["date"],
                        "relevance_score": case["score"],
                        "summary": case["summary"],
                        "key_holdings": case.get("holdings", []),
                        "url": f"{self.api_base}/cases/{case['id']}"
                    })
                
                return results
    
    async def analyze_case(
        self,
        case_citation: str,
        analysis_type: List[str] = ["citations", "treatment"]
    ) -> Dict[str, Any]:
        """Analyze specific case law"""
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            data = {
                "citation": case_citation,
                "analysis_types": analysis_type
            }
            
            async with session.post(
                f"{self.api_base}/api/v1/analyze/case",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                
                analysis = {
                    "case": {
                        "citation": result["citation"],
                        "name": result["name"],
                        "court": result["court"],
                        "date": result["date"]
                    },
                    "analysis": {}
                }
                
                if "citations" in analysis_type:
                    analysis["analysis"]["citations"] = {
                        "total": result["citations"]["total"],
                        "binding": result["citations"]["binding"],
                        "persuasive": result["citations"]["persuasive"],
                        "key_citations": result["citations"]["key_citations"]
                    }
                
                if "treatment" in analysis_type:
                    analysis["analysis"]["treatment"] = {
                        "positive": result["treatment"]["positive"],
                        "negative": result["treatment"]["negative"],
                        "distinguished": result["treatment"]["distinguished"],
                        "overruled": result["treatment"].get("overruled", False)
                    }
                
                if "authority" in analysis_type:
                    analysis["analysis"]["authority"] = {
                        "score": result["authority"]["score"],
                        "rank": result["authority"]["rank"],
                        "strength": result["authority"]["strength"]
                    }
                
                return analysis
```

### 3. Research Tools (tools/research.py)

```python
"""Research orchestration tools"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import uuid4
import json

class ResearchTools:
    def __init__(self, settings):
        self.api_base = settings.PLATFORM_API_URL
        self.api_key = settings.PLATFORM_API_KEY
        self.research_cache = {}
    
    async def conduct_research(
        self,
        objective: str,
        case_facts: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """Conduct comprehensive research investigation"""
        
        research_id = str(uuid4())
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Start research investigation
            data = {
                "objective": objective,
                "facts": case_facts,
                "jurisdiction": jurisdiction,
                "depth": depth
            }
            
            async with session.post(
                f"{self.api_base}/api/v1/research/investigate",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                research_id = result["research_id"]
            
            # Poll for results (in real implementation, use websockets)
            max_attempts = 60  # 5 minutes max
            for attempt in range(max_attempts):
                async with session.get(
                    f"{self.api_base}/api/v1/research/{research_id}/status",
                    headers=headers
                ) as response:
                    status = await response.json()
                    
                    if status["status"] == "completed":
                        break
                    elif status["status"] == "failed":
                        raise Exception(f"Research failed: {status.get('error')}")
                    
                    await asyncio.sleep(5)  # Poll every 5 seconds
            
            # Get final results
            async with session.get(
                f"{self.api_base}/api/v1/research/{research_id}/results",
                headers=headers
            ) as response:
                results = await response.json()
            
            # Cache results
            self.research_cache[research_id] = results
            
            return {
                "research_id": research_id,
                "objective": objective,
                "status": "completed",
                "findings": {
                    "relevant_cases": results["cases"],
                    "key_authorities": results["authorities"],
                    "legal_principles": results["principles"],
                    "potential_arguments": results["arguments"]
                },
                "analysis": {
                    "strengths": results["analysis"]["strengths"],
                    "weaknesses": results["analysis"]["weaknesses"],
                    "opportunities": results["analysis"]["opportunities"],
                    "risks": results["analysis"]["risks"]
                },
                "recommendations": results["recommendations"],
                "next_steps": results["next_steps"],
                "estimated_success": results.get("success_probability", "Not calculated")
            }
    
    async def get_recent_research(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent research investigations"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with session.get(
                f"{self.api_base}/api/v1/research/recent",
                headers=headers,
                params={"limit": limit}
            ) as response:
                data = await response.json()
                return data["research_projects"]
```

### 4. Package Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    PLATFORM_API_URL: str = "http://localhost:8080"
    PLATFORM_API_KEY: str
    
    # MCP Server Configuration
    MCP_SERVER_NAME: str = "legal-research-platform"
    MCP_SERVER_VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 5. Installation Script

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="alligator-ai-mcp",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "mcp>=0.9.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "asyncio>=3.4.3"
    ],
    entry_points={
        "console_scripts": [
            "alligator-ai-mcp=alligator_ai_mcp.server:main",
        ],
    },
    python_requires=">=3.11",
)
```

### 6. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alligator_ai_mcp/ ./alligator_ai_mcp/
COPY setup.py .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Run the MCP server
CMD ["alligator-ai-mcp"]
```

### 7. Client Configuration Examples

#### Claude Desktop
```json
{
  "mcpServers": {
    "legal-research": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file", ".env",
        "legal-research-mcp:latest"
      ]
    }
  }
}
```

#### VS Code
```json
{
  "mcp.servers": {
    "legal-research": {
      "command": "alligator-ai-mcp",
      "env": {
        "PLATFORM_API_KEY": "${env:LEGAL_RESEARCH_API_KEY}"
      }
    }
  }
}
```

## Usage Examples

### Example 1: Basic Precedent Search
```
User: Search for recent employment discrimination cases involving retaliation in California