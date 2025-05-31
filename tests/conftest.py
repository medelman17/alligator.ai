"""
Pytest configuration and shared fixtures for legal research platform tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
import tempfile
import os
from pathlib import Path

# Test database configurations
TEST_NEO4J_URI = "bolt://localhost:7687"
TEST_NEO4J_USER = "neo4j"
TEST_NEO4J_PASSWORD = "citation_graph_2024"
TEST_CHROMA_HOST = "localhost"
TEST_CHROMA_PORT = 8000
TEST_POSTGRES_URL = "postgresql://citation_user:citation_pass_2024@localhost/citation_graph_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def neo4j_service():
    """Provide a Neo4j service instance for testing."""
    from services.graph.neo4j_service import Neo4jService
    
    service = Neo4jService(TEST_NEO4J_URI, TEST_NEO4J_USER, TEST_NEO4J_PASSWORD)
    await service.connect()
    
    # Clean up test data before tests
    await cleanup_neo4j_test_data(service)
    
    yield service
    
    # Clean up test data after tests
    await cleanup_neo4j_test_data(service)
    await service.close()


@pytest_asyncio.fixture(scope="session")
async def chroma_service():
    """Provide a ChromaDB service instance for testing."""
    from services.vector.chroma_service import ChromaService
    
    service = ChromaService()
    yield service
    
    # Clean up test collections
    await cleanup_chroma_test_data()


@pytest_asyncio.fixture
async def sample_cases():
    """Provide sample case data for testing."""
    from shared.models.legal_entities import Case, PracticeArea, CaseStatus
    from datetime import datetime
    
    return [
        Case(
            id="test-case-1",
            citation="123 U.S. 456",
            case_name="Test v. Case",
            full_name="Test v. Case One",
            court_id="us-supreme-court",
            jurisdiction="US",
            decision_date=datetime(2020, 1, 15),
            judges=["Test Judge"],
            status=CaseStatus.GOOD_LAW,
            practice_areas=[PracticeArea.CONSTITUTIONAL],
            summary="Test case for constitutional law",
            holding="Test holding for case law",
            authority_score=8.5
        ),
        Case(
            id="test-case-2", 
            citation="456 U.S. 789",
            case_name="Another v. Test",
            full_name="Another v. Test Case",
            court_id="us-ca-9",
            jurisdiction="US-9",
            decision_date=datetime(2021, 6, 10),
            judges=["Another Judge"],
            status=CaseStatus.GOOD_LAW,
            practice_areas=[PracticeArea.CIVIL_RIGHTS],
            summary="Test case for civil rights",
            holding="Test holding for civil rights",
            authority_score=7.2
        )
    ]


@pytest_asyncio.fixture
async def sample_citations():
    """Provide sample citation data for testing."""
    from shared.models.legal_entities import Citation, CitationTreatment
    import uuid
    
    return [
        Citation(
            id=str(uuid.uuid4()),
            citing_case_id="test-case-2",
            cited_case_id="test-case-1", 
            treatment=CitationTreatment.FOLLOWS,
            context="Following constitutional principles",
            strength=0.8
        )
    ]


@pytest.fixture
def sample_legal_query():
    """Provide sample legal research query."""
    return {
        "query": "qualified immunity for police officers",
        "jurisdiction": "US",
        "practice_areas": ["civil_rights", "constitutional"],
        "date_range": None
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock response from Anthropic Claude API."""
    return """
    # Precedent Analysis Memo
    
    ## Executive Summary
    The research query regarding qualified immunity for police officers reveals several key precedents that establish the current legal framework.
    
    ## Key Precedents
    1. **Pearson v. Callahan (2009)** - Modified the rigid two-step analysis
    2. **Monroe v. Pape (1961)** - Established Section 1983 framework
    
    ## Authority Assessment
    These cases represent binding precedent from the Supreme Court with high authority scores.
    
    ## Current Legal Status
    The doctrine remains active but has evolved significantly since Monroe.
    
    ## Recommendations
    Consider recent circuit court developments when applying qualified immunity analysis.
    """


async def cleanup_neo4j_test_data(service):
    """Clean up Neo4j test data."""
    async with service.driver.session() as session:
        # Delete test nodes and relationships
        await session.run("MATCH (n) WHERE n.id STARTS WITH 'test-' DETACH DELETE n")
        await session.run("MATCH (n:Case) WHERE n.citation CONTAINS 'TEST' DETACH DELETE n")


async def cleanup_chroma_test_data():
    """Clean up ChromaDB test collections."""
    try:
        # Note: In a real implementation, we would clean up test collections
        # For now, we'll rely on test isolation
        pass
    except Exception:
        pass


# Markers for different test categories
pytest.register_assert_rewrite("tests.utils.assertions")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require database connections"
    )
    config.addinivalue_line(
        "markers", "agent: Tests for AI agent workflows"
    )
    config.addinivalue_line(
        "markers", "accuracy: Tests for legal research accuracy"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )


# Skip integration tests if databases aren't available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle database availability."""
    import socket
    
    # Check if Neo4j is available
    neo4j_available = check_service_available("localhost", 7687)
    chroma_available = check_service_available("localhost", 8000)
    
    skip_neo4j = pytest.mark.skip(reason="Neo4j not available")
    skip_chroma = pytest.mark.skip(reason="ChromaDB not available")
    
    for item in items:
        # Only skip integration tests, not unit tests
        if ("neo4j_service" in item.nodeid.lower() or 
            ("neo4j" in item.nodeid.lower() and "integration" in item.nodeid.lower())):
            if not neo4j_available:
                item.add_marker(skip_neo4j)
        if ("chroma_service" in item.nodeid.lower() or 
            ("chroma" in item.nodeid.lower() and "integration" in item.nodeid.lower())):
            if not chroma_available:
                item.add_marker(skip_chroma)


def check_service_available(host: str, port: int) -> bool:
    """Check if a service is available on host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False