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

# Run development server (API Gateway)
poetry run python start_api.py

# Alternative: Run with uvicorn directly
poetry run uvicorn api.main:app --reload --host 127.0.0.1 --port 8001

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_name.py::test_function

# Run test categories with custom script
python scripts/run_tests.py --unit          # Unit tests only
python scripts/run_tests.py --integration   # Integration tests  
python scripts/run_tests.py --agents        # Agent workflow tests
python scripts/run_tests.py --quick         # Fast unit tests, no coverage

# Test API endpoints
poetry run python test_api.py

# Lint and format
poetry run ruff check .
poetry run ruff format .

# Type checking
poetry run mypy .

# Security scanning
poetry run bandit -r shared services api mcp_server
poetry run safety check
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

5. **Document Ingestion Service** (`/services/ingestion/`)
   - Automated legal document acquisition from multiple sources
   - CourtListener, Justia, Google Scholar integration
   - Cost-controlled LLM processing with tiered analysis
   - Eventual consistency storage across databases

6. **API Gateway** (`/api/`) ✅ IMPLEMENTED
   - FastAPI-based REST API with comprehensive dependency injection
   - Service lifecycle management (startup/shutdown hooks)
   - Health checking and monitoring for all services
   - Request routing to microservices with proper error handling
   - Mock services for development/testing environments

7. **Authentication Service** (`/api/auth/`) ✅ IMPLEMENTED
   - JWT-based authentication with access and refresh tokens
   - Role-based access control (RBAC) with hierarchical permissions
   - API key management for programmatic access
   - Subscription tier-based rate limiting with Redis backing
   - Comprehensive audit logging and security monitoring
   - PostgreSQL-backed user and firm management

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

### ChromaDB Collections ✅ POPULATED WITH REAL DATA
- `legal_cases`: 9 landmark Supreme Court cases with full text and embeddings
  - Tennessee v. Garner (1985) - police use of deadly force
  - Graham v. Connor (1989) - excessive force objective reasonableness standard
  - Terry v. Ohio (1968) - stop and frisk authority
  - Miranda v. Arizona (1966) - police interrogation rights
  - Brown v. Board (1954) - constitutional civil rights
  - Roe v. Wade (1973) - privacy rights
  - Plus additional constitutional cases
- `legal_statutes`: Statutory text with semantic embeddings (planned)
- `research_briefs`: Historical brief embeddings for strategy analysis (planned)

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

**CI/CD Pipeline** (GitHub Actions) ✅ FULLY OPERATIONAL:
- Matrix testing across test categories (unit, integration, agents)
- Database service provisioning (Neo4j, ChromaDB, PostgreSQL, Redis)
- Automated security scanning (Bandit + Safety) with zero issues
- Coverage reporting to Codecov
- Performance regression detection
- Local testing support with `gh act` for faster iteration

**Test Database Setup**:
- Isolated test databases for each service
- Automatic test data cleanup
- Mock services for external dependencies
- Dockerized testing environment

## Important Development Notes

### Current Status ✅
- **Development Environment**: Fully operational with all services running
- **API Gateway**: Complete FastAPI implementation with dependency injection
- **Authentication System**: Full JWT/RBAC implementation with rate limiting
- **CI/CD Pipeline**: All tests and security scans passing  
- **Documentation**: Comprehensive architecture and implementation guides available
- **Code Quality**: Zero security issues, proper error handling implemented
- **Real Legal Data Integration**: ✅ OPERATIONAL
  - ChromaDB semantic search with 9 landmark Supreme Court cases
  - CourtListener API integration fetching real New Jersey cases
  - spaCy text processing for legal document analysis
  - Citation-driven case discovery and network expansion
  - Research API generating memos from real legal precedents

### Key Implementation Decisions
1. **Eventual Consistency**: Chose over distributed transactions for ingestion system
2. **Cost Controls**: Implemented tiered LLM processing with budget limits  
3. **MVP-First Approach**: CourtListener integration prioritized for Phase 1
4. **Batch Processing**: Gap detection runs on schedule vs real-time for performance

### Service Endpoints (Local Development)
- **API Gateway**: http://localhost:8001
  - **API Documentation**: http://localhost:8001/api/docs (Swagger UI)
  - **Alternative Docs**: http://localhost:8001/api/redoc (ReDoc)
  - **Health Check**: http://localhost:8001/health
  - **Detailed Health**: http://localhost:8001/api/v1/health
  - **Authentication**: http://localhost:8001/api/v1/auth/
- **Neo4j**: http://localhost:7474 (Bolt: 7687)
- **ChromaDB**: http://localhost:8000/api/v2/heartbeat  
- **PostgreSQL**: localhost:5432 (citation_user/citation_pass_2024)
- **Redis**: localhost:6379 (auth: citation_redis_2024)

### Real Legal Data Integration Status ✅ COMPLETED
1. ✅ **ChromaDB Semantic Search**: Working with 9 landmark Supreme Court cases
2. ✅ **CourtListener API Integration**: Fetching real New Jersey cases from API v4
3. ✅ **spaCy Text Processing**: Installed v3.7.5 with English language model
4. ✅ **Citation Network Discovery**: Automatically expanding case networks
5. ✅ **Research API Workflow**: End-to-end legal research with real data
6. ✅ **Legal Precision Validation**: Correct ranking (Graham v. Connor #1 for excessive force)

### Semantic Search Quality Examples
For query "police qualified immunity excessive force civil rights cases":
1. **Graham v. Connor** (1989) - excessive force objective reasonableness ✅ PERFECT
2. **Tennessee v. Garner** (1985) - police deadly force limitations ✅ PERFECT  
3. **Terry v. Ohio** (1968) - police stop and frisk authority ✅ PERFECT

### Next Implementation Priorities
1. ✅ ~~Start Phase 1 ingestion system (CourtListener MVP)~~ **COMPLETED**
2. ✅ ~~Implement core service classes (Neo4jService, ChromaService)~~ **COMPLETED**
3. ✅ ~~Add database schemas and sample data~~ **COMPLETED** 
4. ✅ ~~Build basic research agent workflows~~ **COMPLETED**
5. Scale ingestion to populate more legal cases from CourtListener
6. Implement Neo4j citation graph population from ChromaDB cases
7. Add LLM-powered case summarization and analysis