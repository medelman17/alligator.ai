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

### 🔐 Enterprise Authentication
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC) with hierarchical permissions
- API key management for programmatic access
- Subscription tier-based rate limiting
- Comprehensive audit logging and security monitoring

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
│  🔐 JWT Auth  │  📊 Rate Limiting  │  🛣️ Routing   │
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
# Services: Neo4j (ports 7474/7687), ChromaDB (port 8000), 
#          PostgreSQL (port 5432), Redis (port 6379)
```

You can verify services are working:
```bash
# Test Neo4j
curl http://localhost:7474

# Test ChromaDB
curl http://localhost:8000/api/v2/heartbeat

# Test PostgreSQL
PGPASSWORD=citation_pass_2024 psql -h localhost -U citation_user -d citation_graph -c "SELECT 1;"

# Test Redis
redis-cli -a citation_redis_2024 ping
```

6. Run database migrations (once PostgreSQL is ready):
```bash
poetry run alembic upgrade head
```

7. Run the API Gateway:
```bash
# Start the API server
poetry run python start_api.py

# Alternative: Run with uvicorn directly
poetry run uvicorn api.main:app --reload --host 127.0.0.1 --port 8001
```

The API will be available at:
- **Main API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/api/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8001/api/redoc (ReDoc) 
- **Health Check**: http://localhost:8001/health
- **Detailed Health**: http://localhost:8001/api/v1/health

8. Test the API endpoints:
```bash
# Test with the included test script
poetry run python test_api.py
```

### Project Structure

```
citation_graph/
├── api/                  # ✅ FastAPI Gateway (IMPLEMENTED)
│   ├── main.py           # FastAPI app with lifecycle management
│   ├── dependencies.py   # Dependency injection system
│   ├── auth/             # ✅ Authentication system (JWT, RBAC, API keys)
│   ├── endpoints/        # REST API endpoints
│   └── middleware/       # CORS, logging, rate limiting
├── services/             # Microservices 
│   ├── orchestration/    # LangGraph multi-agent orchestration
│   ├── graph/           # ✅ Enhanced Neo4j legal research service
│   ├── vector/          # ✅ ChromaDB semantic search
│   ├── llm/             # LLM provider abstraction
│   └── memory/          # Multi-tier memory system
├── shared/              # ✅ Shared utilities and models
├── mcp_server/          # MCP server for AI assistants
├── tests/               # ✅ Comprehensive test suite
├── scripts/             # ✅ Utility scripts
├── start_api.py         # ✅ API server startup script
├── test_api.py          # ✅ API testing script
└── docker/              # Docker configurations
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

## Enhanced Legal Research Features

### 🏛️ **Sophisticated Citation Network Analysis**

alligator.ai includes a comprehensive Neo4j service with advanced legal research capabilities that transform basic citation networks into sophisticated legal intelligence.

#### **Core Legal Research Methods**

```python
# Find authoritative precedents with multi-factor scoring
precedents = await neo4j_service.find_authoritative_precedents(
    case_id="brown-v-board-1954",
    target_jurisdictions=["US", "US-9"],
    practice_areas=["constitutional_law", "civil_rights"],
    primary_jurisdiction="US"
)

# Analyze citation treatment (positive/negative/neutral)
treatment = await neo4j_service.analyze_citation_treatment("roe-v-wade-1973")

# Verify good law status with confidence assessment
verification = await neo4j_service.verify_good_law_status("miranda-v-arizona-1966")

# Calculate legal authority with PageRank + domain factors
pagerank = await neo4j_service.calculate_legal_authority_pagerank()

# Enhanced semantic search with legal filtering
results = await neo4j_service.semantic_case_search(
    search_terms="equal protection constitutional",
    jurisdictions=["US"],
    practice_areas=["constitutional_law"],
    good_law_only=True
)
```

#### **Legal Citation Treatment Analysis**

The system recognizes 15+ legal citation treatment types with sophisticated scoring:

**Positive Treatments** (strengthen authority):
- `follows` (1.0) - Directly follows precedent
- `affirmed` (1.0) - Appellate affirmance  
- `explained` (0.8) - Clarifies holding
- `expanded` (0.9) - Extends holding to new facts

**Negative Treatments** (weaken authority):
- `distinguished` (-0.3) - Limited to specific facts
- `questioned` (-0.5) - Casts doubt on reasoning
- `criticized` (-0.7) - Direct criticism
- `overruled` (-1.0) - Explicitly overturned

**Authority Calculation Factors**:
- Court hierarchy weighting (Supreme Court: 10.0, Appellate: 8.0, District: 6.0)
- Jurisdictional authority (binding vs. persuasive)
- Temporal relevance (authority decay over time)
- Citation strength and treatment type

#### **Legal Sample Data**

The system includes real constitutional law landmark cases:

```cypher
// Brown v. Board overrules Plessy v. Ferguson
(brown:Case {citation: "347 U.S. 483 (1954)"})
-[CITES {treatment: "overruled", strength: 1.0}]->
(plessy:Case {citation: "163 U.S. 537 (1896)"})

// Dobbs v. Jackson overrules Roe v. Wade  
(dobbs:Case {citation: "597 U.S. ___ (2022)"})
-[CITES {treatment: "overruled", strength: 1.0}]->
(roe:Case {citation: "410 U.S. 113 (1973)"})
```

#### **Court Hierarchy with Real Authority Data**

```python
# All 13 federal circuit courts with real metrics
courts = {
    "us-ca-9": {  # 9th Circuit
        "authority_weight": 8.0,
        "reversal_rate": 0.78,      # Highest SCOTUS reversal rate
        "conservative_score": 0.31,  # Most liberal circuit
        "geographic_scope": ["CA", "OR", "WA", "AK", "HI", "NV", "ID", "MT", "AZ"]
    },
    "us-ca-5": {  # 5th Circuit  
        "authority_weight": 8.0,
        "reversal_rate": 0.09,      # Lowest SCOTUS reversal rate
        "conservative_score": 0.71,  # Most conservative circuit
        "geographic_scope": ["LA", "MS", "TX"]
    }
}
```

#### **Performance Optimization**

**Composite Indexes** for legal research patterns:
```cypher
// Multi-dimensional legal research optimization
CREATE INDEX case_research_composite 
FOR (c:Case) ON (c.jurisdiction, c.practice_areas, c.authority_score, c.decision_date)

CREATE INDEX citation_authority_composite 
FOR ()-[r:CITES]-() ON (r.treatment, r.calculated_authority, r.binding_precedent)
```

**Graph Algorithm Projections** for authority calculations:
```cypher
// Legal authority network with weighted relationships
CALL gds.graph.project(
  'legal-authority-network',
  'Case',
  'CITES',
  {relationshipProperties: ['calculated_authority', 'temporal_weight']}
)
```

#### **API Integration Examples**

```bash
# Find precedents for constitutional privacy cases
curl -X POST "http://localhost:8001/api/v1/search/precedents" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "case_id": "roe-v-wade-1973",
    "jurisdictions": ["US"],
    "practice_areas": ["constitutional_law", "privacy_rights"]
  }'

# Analyze citation treatment
curl -X GET "http://localhost:8001/api/v1/cases/brown-v-board-1954/treatment-analysis" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Verify good law status
curl -X GET "http://localhost:8001/api/v1/cases/miranda-v-arizona-1966/good-law-status" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

#### **Enhanced vs. Basic Schema**

The service automatically detects schema capabilities and provides:

**Enhanced Schema Features**:
- 15+ citation treatment types with confidence scoring
- Multi-factor authority calculations
- Full-text search with legal metadata filtering
- Good law verification with overruling detection
- Temporal and jurisdictional relevance scoring

**Basic Schema Fallback**:
- Simple citation relationships
- Basic authority scoring
- Text-based case search
- Graceful degradation of advanced features

#### **Legal Research Query Examples**

```python
# Complex precedent analysis
precedents = await service.find_authoritative_precedents(
    case_id="citizens-united-2010",
    target_jurisdictions=["US", "US-DC"],
    practice_areas=["constitutional_law", "campaign_finance"],
    primary_jurisdiction="US"
)

# Citation network traversal with legal filtering
network = await service.traverse_citation_network(
    case_id="brown-v-board-1954",
    max_depth=3,
    treatment_filter=["follows", "explained", "expanded"]
)

# Temporal doctrine evolution analysis  
evolution = await service.track_doctrine_evolution(
    doctrine_tags=["equal_protection", "due_process"],
    time_range=(date(1950, 1, 1), date(2024, 1, 1))
)
```

This sophisticated legal research infrastructure enables alligator.ai to provide enterprise-grade legal intelligence that rivals traditional legal research platforms like Westlaw and LexisNexis.

## Documentation

- [Product Requirements Document](PRD.md) - Detailed product vision and requirements
- [Development Guide](CLAUDE.md) - Architecture and development guidelines
- [Memory Architecture](MEMORY_ARCHITECTURE.md) - Memory system design
- [Memory Implementation](MEMORY_IMPLEMENTATION.md) - Memory system implementation details
- [MCP Server Design](MCP_SERVER_DESIGN.md) - MCP integration details
- [MCP Implementation](MCP_IMPLEMENTATION.md) - MCP server implementation guide
- [Ingestion Architecture](INGESTION_ARCHITECTURE.md) - Automated document ingestion system
- [Ingestion Implementation](INGESTION_IMPLEMENTATION.md) - Practical ingestion implementation plan
- [Graphiti Architecture](GRAPHITI_ARCHITECTURE.md) - Temporal knowledge evolution system
- [Graphiti Implementation](GRAPHITI_IMPLEMENTATION.md) - Graphiti integration details

## Development

### Testing

We have comprehensive test coverage with multiple test categories:

```bash
# Run all tests with coverage
poetry run pytest

# Quick development cycle (unit tests only, no coverage)
python scripts/run_tests.py --quick

# Run specific test categories
python scripts/run_tests.py --unit          # Unit tests (fast, no external deps)
python scripts/run_tests.py --integration   # Integration tests (require databases)
python scripts/run_tests.py --agents        # AI agent workflow tests
python scripts/run_tests.py --performance   # Performance benchmarks
python scripts/run_tests.py --accuracy      # Legal research accuracy validation

# Test API endpoints
poetry run python test_api.py               # Test API Gateway endpoints

# Generate detailed coverage report
python scripts/run_tests.py --coverage

# Check if databases are available for testing
python scripts/run_tests.py --check-db
```

**Current Test Coverage:**
- **Unit Tests**: 16 tests with 100% coverage on legal entity models
- **Integration Tests**: Database operations and service interactions
- **Agent Tests**: LangGraph workflow validation and AI agent behavior
- **Performance Tests**: Load testing and benchmark validation

### Code Quality & Security
```bash
# Run all quality checks
python scripts/run_tests.py --lint

# Security scanning
poetry run bandit -r shared services api mcp_server    # Security vulnerability scanning
poetry run safety check                                # Dependency vulnerability check

# Or run individually
poetry run ruff check .      # Linting
poetry run ruff format .     # Code formatting
poetry run mypy .            # Static type checking
```

### Local GitHub Actions Testing
```bash
# Test GitHub Actions workflows locally using act
gh act --job security                    # Test security scanning
gh act --job test                       # Test full test suite
gh act --list                          # List available workflows

# Dry run (validate without executing)
gh act --job security --dryrun
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