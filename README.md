# alligator.ai 🐊

AI-powered legal research platform that revolutionizes how boutique litigation firms conduct case analysis and develop winning strategies.

## Overview

alligator.ai combines cutting-edge AI technology with deep legal expertise to deliver:

- **Multi-Agent Research**: Orchestrated AI agents that conduct research like senior attorneys
- **Citation Graph Analysis**: Neo4j-powered precedent relationship mapping
- **Semantic Search**: Advanced vector search for finding conceptually similar cases
- **Strategic Intelligence**: Opposition research and argument strength evaluation
- **Automated Memo Generation**: Professional research memoranda in minutes, not hours

## Key Features

### 🔍 Intelligent Legal Research
- Semantic case law search with citation network analysis
- Automated precedent authority ranking using custom PageRank
- Jurisdiction-specific legal interpretation tracking
- Temporal relevance scoring for case law currency

### 🤖 AI Agent Orchestration
- Specialized agents for different research tasks
- LangGraph-based workflow management
- Iterative research refinement
- Quality assessment and validation

### 💾 Advanced Memory System
- Working memory for session context
- Episodic memory for learning from past research
- Semantic memory for evolving legal knowledge
- Personalization for attorney and firm preferences

### 🔌 MCP Integration
- Use alligator.ai directly in Claude Desktop
- VS Code extension support
- Secure API access with JWT authentication
- Rate-limited access controls

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Web Interface     │     │    MCP Clients      │
│   (React + TypeScript)     │   (Claude Desktop)   │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────┐
│              API Gateway (FastAPI)               │
├─────────────────────────────────────────────────┤
│  Auth  │  Rate Limiting  │  Request Routing     │
└─────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│            Microservices Architecture            │
├─────────────────┬───────────────┬───────────────┤
│   Orchestration │  Graph DB     │ Vector Search │
│   (LangGraph)   │  (Neo4j)      │ (ChromaDB)    │
├─────────────────┴───────────────┴───────────────┤
│        Memory System (Redis + PostgreSQL)        │
└─────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, LangGraph, LangChain
- **Databases**: Neo4j (graph), ChromaDB (vector), PostgreSQL (relational), Redis (cache)
- **AI/ML**: Claude 3.5 Sonnet, GPT-4, custom legal embeddings
- **Infrastructure**: Docker, Kubernetes, AWS
- **Package Management**: Poetry (Python), pnpm (JavaScript)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (if building frontend)
- Docker and Docker Compose
- Poetry for Python dependency management
- pnpm for JavaScript dependency management (if building frontend)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/citation_graph.git
cd citation_graph
```

2. Install backend dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Start the infrastructure services:
```bash
docker compose up -d
```

5. Wait for services to be healthy:
```bash
docker compose ps
# All services should show as "healthy"
```

6. Run database migrations (once PostgreSQL is ready):
```bash
poetry run alembic upgrade head
```

7. Run the development server:
```bash
poetry run python -m uvicorn api.main:app --reload --port 8001
```

The API will be available at http://localhost:8001

### Project Structure

```
citation_graph/
├── services/              # Microservices
│   ├── orchestration/     # LangGraph multi-agent orchestration
│   ├── graph/            # Neo4j citation network analysis
│   ├── vector/           # ChromaDB semantic search
│   ├── llm/              # LLM provider abstraction
│   └── memory/           # Multi-tier memory system
├── api/                  # FastAPI gateway
├── mcp_server/           # MCP server for AI assistants
├── shared/               # Shared utilities and models
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── docker/               # Docker configurations
```

### Using the MCP Server

1. Build the MCP Docker image:
```bash
docker build -t alligator-ai-mcp:latest -f mcp_server/Dockerfile .
```

2. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "alligator-ai": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--env-file", ".env", "alligator-ai-mcp:latest"]
    }
  }
}
```

## Documentation

- [Product Requirements Document](PRD.md) - Detailed product vision and requirements
- [Development Guide](CLAUDE.md) - Architecture and development guidelines
- [Memory Architecture](MEMORY_ARCHITECTURE.md) - Memory system design
- [MCP Server Design](MCP_SERVER_DESIGN.md) - MCP integration details

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy .
```

### Building for Production
```bash
docker compose -f docker-compose.prod.yml build
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

Copyright © 2024 alligator.ai. All rights reserved.

## Support

For questions or support, please contact: support@alligator.ai

---

Built with 🐊 by the alligator.ai team