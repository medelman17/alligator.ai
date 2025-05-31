# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

alligator.ai is an AI-powered legal research platform for boutique litigation firms that combines:
- Multi-agent AI orchestration (LangGraph) for conducting research workflows
- Graph database (Neo4j) for analyzing legal citation relationships
- Vector search (ChromaDB) for semantic case similarity
- LLM integration (Claude/GPT-4) for analysis and memo generation

## Development Commands

### Python Backend
```bash
# Install dependencies
poetry install

# Run development server
poetry run python -m uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_name.py::test_function

# Lint and format
poetry run ruff check .
poetry run ruff format .

# Type checking
poetry run mypy .
```

### Frontend (if applicable)
```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Run tests
pnpm test

# Lint
pnpm lint
```

### Infrastructure
```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d neo4j

# View logs
docker compose logs -f [service_name]

# Stop all services
docker compose down
```

## Architecture Overview

### Phased Development Approach

**Phase 1 (Foundation)**: Core legal research platform with:
- Neo4j citation graph analysis
- ChromaDB semantic search  
- LangGraph multi-agent orchestration
- Basic memory systems (Redis, PostgreSQL)

**Phase 2 (Temporal Enhancement)**: Integration of Graphiti for temporal knowledge evolution:
- Research pattern learning and adaptation
- Case law treatment tracking over time
- Judge-specific strategy optimization
- User/firm preference personalization

See `GRAPHITI_ARCHITECTURE.md` and `GRAPHITI_IMPLEMENTATION.md` for temporal enhancement details.

### Memory Architecture

The platform includes a sophisticated memory system to enhance agent capabilities:

1. **Working Memory** (Redis): Session-based context and caching
2. **Episodic Memory** (PostgreSQL + ChromaDB): Historical research patterns and outcomes
3. **Semantic Memory** (Neo4j + ChromaDB): Evolving legal knowledge graph
4. **Personalization Memory** (PostgreSQL): User and firm preferences
5. **Temporal Memory** (Graphiti - Phase 2): Time-aware knowledge evolution and learning

See `MEMORY_ARCHITECTURE.md` and `MEMORY_IMPLEMENTATION.md` for detailed design and implementation patterns.

### MCP Server Integration

The platform includes an MCP (Model Context Protocol) server that exposes research capabilities as tools for AI assistants:

1. **Available Tools**: search_precedents, analyze_case_law, conduct_research, generate_memo
2. **Authentication**: JWT-based security with firm-level rate limiting
3. **Deployment**: Docker container or integrated with API gateway

See `MCP_SERVER_DESIGN.md` and `MCP_IMPLEMENTATION.md` for implementation details.

### Core Services (Microservices Architecture)

1. **Research Orchestration Service** (`/services/orchestration/`)
   - LangGraph-based multi-agent system
   - Manages complex research workflows with specialized agents
   - State management for multi-step investigations

2. **Graph Database Service** (`/services/graph/`)
   - Neo4j integration for citation network analysis
   - PageRank algorithm for authority scoring
   - Jurisdiction and temporal relevance calculations

3. **Vector Search Service** (`/services/vector/`)
   - ChromaDB for semantic case similarity
   - Legal domain-specific embeddings
   - Hybrid search combining semantic and citation relevance

4. **LLM Integration Service** (`/services/llm/`)
   - Abstraction layer for multiple LLM providers
   - Structured output parsing and function calling
   - Cost optimization and rate limiting

5. **API Gateway** (`/api/`)
   - FastAPI-based REST API
   - Authentication and authorization
   - Request routing to microservices

### Key Design Patterns

1. **Agent Orchestration**: Uses LangGraph for complex multi-agent workflows where agents have specialized roles (precedent analysis, opposition research, memo generation)

2. **Hybrid Search**: Combines vector similarity (ChromaDB) with graph traversal (Neo4j) to find both semantically similar and legally authoritative cases

3. **Authority Ranking**: Custom PageRank implementation on citation graph, weighted by court hierarchy and temporal factors

## Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Databases**: Neo4j (graph), ChromaDB (vector), PostgreSQL (relational)
- **AI/ML**: LangGraph, LangChain, Claude/GPT-4 APIs
- **Infrastructure**: Docker Compose (dev), AWS/Kubernetes (prod)
- **Package Management**: Poetry (Python), pnpm (JavaScript)

## Database Schemas

### Neo4j Graph Structure
- Nodes: Case, Court, Judge, Attorney
- Relationships: CITES, OVERRULES, DISTINGUISHES, FOLLOWS
- Properties: date, jurisdiction, authority_score, treatment_type

### ChromaDB Collections
- `cases`: Full text and embeddings of case law
- `statutes`: Statutory text with semantic embeddings
- `briefs`: Historical brief embeddings for strategy analysis

## Development Guidelines

1. **Dependency Management**:
   - Always use `poetry` for Python dependencies
   - Always use `pnpm` for JavaScript dependencies

2. **AI Agent Development**:
   - Each agent should have a single, well-defined responsibility
   - Use LangGraph's state management for complex workflows
   - Implement retry logic and error handling for LLM calls

3. **Graph Queries**:
   - Optimize Cypher queries for large citation networks
   - Use indexes on frequently queried properties
   - Implement query result caching for expensive operations

4. **Vector Search**:
   - Batch embed new documents for efficiency
   - Maintain separate collections for different document types
   - Use metadata filtering to improve search relevance

## Environment Variables

```bash
# LLM Configuration
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Database Connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=
CHROMA_HOST=localhost
CHROMA_PORT=8000
DATABASE_URL=postgresql://user:pass@localhost/citation_graph

# Service Configuration
API_PORT=8000
REDIS_URL=redis://localhost:6379
```

## Testing Strategy

### Comprehensive Test Coverage ✅ IMPLEMENTED

**Testing Framework**: pytest with async support, coverage reporting, and CI/CD integration

**Test Categories**:
- **Unit Tests** (`tests/unit/`): Data models, service logic, utilities (Target: 90%+ coverage)
- **Integration Tests** (`tests/integration/`): Database operations, service interactions
- **Agent Tests** (`tests/agents/`): LangGraph workflow testing, agent behavior validation
- **Performance Tests**: Load testing, citation network traversal, search benchmarks
- **Legal Accuracy Tests**: Validation of legal research quality and correctness
- **Security Tests**: Bandit security scanning, dependency vulnerability checks

**Test Commands**:
```bash
# Run all tests with coverage
poetry run pytest

# Run specific test categories
python scripts/run_tests.py --unit          # Unit tests only
python scripts/run_tests.py --integration   # Integration tests
python scripts/run_tests.py --agents        # Agent workflow tests
python scripts/run_tests.py --performance   # Performance benchmarks
python scripts/run_tests.py --accuracy      # Legal accuracy validation

# Quick development cycle
python scripts/run_tests.py --quick         # Fast unit tests, no coverage

# Generate coverage report
python scripts/run_tests.py --coverage      # HTML + XML coverage reports

# Check code quality
python scripts/run_tests.py --lint          # Ruff linting + mypy type checking
```

**CI/CD Pipeline** (GitHub Actions):
- Matrix testing across test categories
- Database service provisioning (Neo4j, ChromaDB, PostgreSQL, Redis)
- Automated security scanning
- Coverage reporting to Codecov
- Performance regression detection

**Test Database Setup**:
- Isolated test databases for each service
- Automatic test data cleanup
- Mock services for external dependencies
- Dockerized testing environment