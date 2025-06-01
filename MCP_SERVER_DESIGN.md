# MCP Server Design for alligator.ai

## Overview

The Model Context Protocol (MCP) server exposes alligator.ai's capabilities as tools that can be used by Claude Desktop, AI coding assistants, and other MCP-compatible clients. This enables attorneys to access sophisticated legal research directly within their preferred AI interfaces.

✅ **IMPLEMENTATION STATUS: COMPLETE AND OPERATIONAL**
- All MCP tools implemented and tested
- Multi-jurisdiction CourtListener integration working
- Real legal data flowing through semantic search
- Full research workflows validated
- Professional memo generation functional

## Architecture

### MCP Server Components

```
┌─────────────────────┐
│   MCP Clients       │
│ (Claude Desktop,    │
│  VS Code, etc.)     │
└──────────┬──────────┘
           │ JSON-RPC
┌──────────▼──────────┐
│   MCP Server        │
│  (FastAPI + MCP)    │
├─────────────────────┤
│ Authentication      │
│ Rate Limiting       │
│ Tool Registry       │
└──────────┬──────────┘
           │ 
┌──────────▼──────────┐
│  Platform Services  │
├─────────────────────┤
│ • Research Agents   │
│ • Graph Database    │
│ • Vector Search     │
│ • Memory System     │
└─────────────────────┘
```

## Tool Definitions

### 1. Legal Research Tools

#### search_precedents
**Description**: Search for relevant legal precedents using semantic search and citation analysis
```typescript
{
  name: "search_precedents",
  description: "Search for legal precedents relevant to a case or legal issue",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Legal issue or fact pattern to search for"
      },
      jurisdiction: {
        type: "string",
        description: "Jurisdiction to search within (e.g., 'federal', 'NY', 'CA')"
      },
      date_range: {
        type: "object",
        properties: {
          start: { type: "string", format: "date" },
          end: { type: "string", format: "date" }
        }
      },
      limit: {
        type: "number",
        default: 20,
        description: "Maximum number of results to return"
      }
    },
    required: ["query"]
  }
}
```

#### analyze_case_law
**Description**: Deep analysis of specific cases including citations, treatment, and authority
```typescript
{
  name: "analyze_case_law",
  description: "Perform deep analysis of a specific case including its citation network",
  inputSchema: {
    type: "object",
    properties: {
      case_citation: {
        type: "string",
        description: "Full case citation (e.g., '123 F.3d 456')"
      },
      analysis_type: {
        type: "array",
        items: {
          type: "string",
          enum: ["citations", "treatment", "authority", "distinguishing"]
        }
      },
      include_related: {
        type: "boolean",
        default: true,
        description: "Include analysis of related cases"
      }
    },
    required: ["case_citation"]
  }
}
```

#### conduct_research_investigation
**Description**: Launch a comprehensive multi-agent research investigation
```typescript
{
  name: "conduct_research_investigation",
  description: "Conduct a comprehensive legal research investigation using AI agents",
  inputSchema: {
    type: "object",
    properties: {
      objective: {
        type: "string",
        description: "Research objective and legal questions to investigate"
      },
      case_facts: {
        type: "string",
        description: "Relevant facts of the case"
      },
      legal_theories: {
        type: "array",
        items: { type: "string" },
        description: "Legal theories to explore"
      },
      jurisdiction: {
        type: "string",
        description: "Primary jurisdiction for the case"
      },
      research_depth: {
        type: "string",
        enum: ["quick", "standard", "comprehensive"],
        default: "standard"
      },
      include_opposition: {
        type: "boolean",
        default: true,
        description: "Include opposition research and counter-arguments"
      }
    },
    required: ["objective"]
  }
}
```

### 2. Strategic Analysis Tools

#### identify_opposing_arguments
**Description**: Identify and analyze potential opposing arguments and adverse authorities
```typescript
{
  name: "identify_opposing_arguments",
  description: "Identify potential opposing arguments and adverse authorities",
  inputSchema: {
    type: "object",
    properties: {
      our_position: {
        type: "string",
        description: "Our legal position and arguments"
      },
      case_type: {
        type: "string",
        description: "Type of case (e.g., 'employment discrimination', 'breach of contract')"
      },
      opposing_counsel: {
        type: "string",
        description: "Optional: Name of opposing counsel or firm for pattern analysis"
      }
    },
    required: ["our_position", "case_type"]
  }
}
```

#### evaluate_case_strength
**Description**: Evaluate the strength of legal arguments and predict likely outcomes
```typescript
{
  name: "evaluate_case_strength",
  description: "Evaluate case strength and predict likely outcomes",
  inputSchema: {
    type: "object",
    properties: {
      case_summary: {
        type: "string",
        description: "Summary of case facts and legal issues"
      },
      supporting_precedents: {
        type: "array",
        items: { type: "string" },
        description: "List of supporting case citations"
      },
      adverse_precedents: {
        type: "array",
        items: { type: "string" },
        description: "List of adverse case citations"
      },
      judge: {
        type: "string",
        description: "Optional: Judge name for judge-specific analysis"
      }
    },
    required: ["case_summary"]
  }
}
```

### 3. Document Generation Tools

#### generate_research_memo
**Description**: Generate a professional legal research memorandum
```typescript
{
  name: "generate_research_memo",
  description: "Generate a professional legal research memorandum",
  inputSchema: {
    type: "object",
    properties: {
      research_id: {
        type: "string",
        description: "ID of completed research investigation"
      },
      memo_type: {
        type: "string",
        enum: ["internal", "client", "court"],
        default: "internal"
      },
      sections: {
        type: "array",
        items: {
          type: "string",
          enum: ["summary", "facts", "issues", "analysis", "conclusion", "recommendations"]
        },
        default: ["summary", "facts", "issues", "analysis", "conclusion"]
      },
      style_preferences: {
        type: "object",
        properties: {
          tone: { type: "string", enum: ["formal", "conversational"] },
          length: { type: "string", enum: ["concise", "detailed"] }
        }
      }
    },
    required: ["research_id"]
  }
}
```

#### draft_brief_section
**Description**: Draft specific sections of legal briefs with proper citations
```typescript
{
  name: "draft_brief_section",
  description: "Draft sections of legal briefs with proper citations",
  inputSchema: {
    type: "object",
    properties: {
      section_type: {
        type: "string",
        enum: ["statement_of_facts", "legal_standard", "argument", "conclusion"]
      },
      content_outline: {
        type: "string",
        description: "Outline or key points to cover"
      },
      supporting_cases: {
        type: "array",
        items: { type: "string" },
        description: "Case citations to incorporate"
      },
      citation_format: {
        type: "string",
        enum: ["bluebook", "alwd"],
        default: "bluebook"
      }
    },
    required: ["section_type", "content_outline"]
  }
}
```

### 4. Knowledge Graph Tools

#### explore_legal_concept
**Description**: Explore legal concepts and their relationships in the knowledge graph
```typescript
{
  name: "explore_legal_concept",
  description: "Explore legal concepts and doctrinal relationships",
  inputSchema: {
    type: "object",
    properties: {
      concept: {
        type: "string",
        description: "Legal concept to explore (e.g., 'qualified immunity')"
      },
      relationship_depth: {
        type: "number",
        default: 2,
        description: "How many relationship levels to traverse"
      },
      include_evolution: {
        type: "boolean",
        default: false,
        description: "Include historical evolution of the concept"
      }
    },
    required: ["concept"]
  }
}
```

## Implementation

### MCP Server Structure

```python
# mcp_server/server.py
from fastapi import FastAPI, Depends
from mcp import Server, Tool, Resource
from typing import Dict, Any, List
import asyncio

class LegalResearchMCPServer:
    def __init__(self, platform_config: Dict[str, Any]):
        self.app = FastAPI()
        self.mcp_server = Server(
            name="alligator-ai",
            version="1.0.0"
        )
        self.platform_config = platform_config
        self._setup_tools()
        self._setup_resources()
        
    def _setup_tools(self):
        """Register all MCP tools"""
        
        @self.mcp_server.tool()
        async def search_precedents(
            query: str,
            jurisdiction: str = None,
            date_range: Dict = None,
            limit: int = 20
        ) -> Dict[str, Any]:
            """Search for relevant legal precedents"""
            # Call platform's search service
            results = await self.platform_services.search_precedents(
                query=query,
                jurisdiction=jurisdiction,
                date_range=date_range,
                limit=limit
            )
            
            return {
                "precedents": results.cases,
                "total_found": results.total,
                "relevance_scores": results.scores,
                "search_metadata": results.metadata
            }
        
        @self.mcp_server.tool()
        async def conduct_research_investigation(
            objective: str,
            case_facts: str = None,
            legal_theories: List[str] = None,
            jurisdiction: str = None,
            research_depth: str = "standard",
            include_opposition: bool = True
        ) -> Dict[str, Any]:
            """Launch comprehensive research investigation"""
            # Initialize research workflow
            research_id = await self.orchestration_service.start_research(
                objective=objective,
                facts=case_facts,
                theories=legal_theories,
                jurisdiction=jurisdiction,
                depth=research_depth
            )
            
            # Monitor progress
            async for update in self.orchestration_service.get_updates(research_id):
                if update.type == "progress":
                    yield {"progress": update.data}
                elif update.type == "finding":
                    yield {"finding": update.data}
            
            # Return final results
            results = await self.orchestration_service.get_results(research_id)
            return {
                "research_id": research_id,
                "findings": results.findings,
                "recommendations": results.recommendations,
                "memo_preview": results.memo_preview
            }
        
        @self.mcp_server.tool()
        async def generate_research_memo(
            research_id: str,
            memo_type: str = "internal",
            sections: List[str] = None,
            style_preferences: Dict = None
        ) -> Dict[str, Any]:
            """Generate professional research memo"""
            memo = await self.document_service.generate_memo(
                research_id=research_id,
                memo_type=memo_type,
                sections=sections or ["summary", "facts", "issues", "analysis", "conclusion"],
                style=style_preferences
            )
            
            return {
                "memo_id": memo.id,
                "content": memo.content,
                "citations": memo.citations,
                "word_count": memo.word_count,
                "download_url": memo.download_url
            }
    
    def _setup_resources(self):
        """Register MCP resources"""
        
        @self.mcp_server.resource("research/{research_id}")
        async def get_research(research_id: str) -> Dict[str, Any]:
            """Get detailed research results"""
            return await self.storage.get_research(research_id)
        
        @self.mcp_server.resource("memo/{memo_id}")
        async def get_memo(memo_id: str) -> Dict[str, Any]:
            """Get generated memo content"""
            return await self.storage.get_memo(memo_id)
```

### Authentication & Security

```python
# mcp_server/auth.py
from typing import Optional
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class MCPAuthHandler:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.security = HTTPBearer()
    
    def create_token(self, user_id: str, firm_id: str) -> str:
        """Create JWT token for MCP client"""
        payload = {
            "user_id": user_id,
            "firm_id": firm_id,
            "permissions": ["research", "memo_generation"],
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        token = credentials.credentials
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp/tool/search_precedents")
@limiter.limit("100/hour")
async def search_precedents_endpoint(
    request: SearchRequest,
    auth: Dict = Depends(auth_handler.verify_token)
):
    # Apply firm-specific rate limits
    firm_limits = await get_firm_limits(auth["firm_id"])
    if not within_limits(auth["firm_id"], "search", firm_limits):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return await mcp_server.search_precedents(**request.dict())
```

### Client Configuration

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "legal-research": {
      "command": "docker",
      "args": ["run", "-p", "8000:8000", "alligator-ai-mcp:latest"],
      "env": {
        "MCP_AUTH_TOKEN": "${LEGAL_RESEARCH_TOKEN}"
      }
    }
  }
}
```

```json
// Alternative: Direct Python execution
{
  "mcpServers": {
    "legal-research": {
      "command": "python",
      "args": ["-m", "legal_research_mcp.server"],
      "env": {
        "LEGAL_RESEARCH_API_KEY": "${LEGAL_RESEARCH_API_KEY}",
        "LEGAL_RESEARCH_API_URL": "https://api.alligator.ai"
      }
    }
  }
}
```

## Deployment Options

### 1. Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy MCP server code
COPY mcp_server/ ./mcp_server/

# Expose MCP port
EXPOSE 8000

# Run MCP server
CMD ["python", "-m", "mcp_server.server"]
```

### 2. Standalone Service
```yaml
# docker-compose.yml addition
services:
  mcp-server:
    build:
      context: .
      dockerfile: mcp_server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PLATFORM_API_URL=http://api-gateway:8080
      - NEO4J_URI=bolt://neo4j:7687
      - CHROMA_HOST=chroma
      - REDIS_URL=redis://redis:6379
    depends_on:
      - api-gateway
      - neo4j
      - chroma
      - redis
```

### 3. Integrated with API Gateway
```python
# api/main.py
from mcp_server import LegalResearchMCPServer

# Add MCP endpoint to existing API
app.mount("/mcp", mcp_server.app)
```

## Usage Examples

### Claude Desktop Usage
```
Human: Search for recent employment discrimination cases in California involving wrongful termination and retaliation.