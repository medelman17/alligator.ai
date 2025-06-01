"""
Integration tests for enhanced legal research API endpoints.

Tests the integration between enhanced Neo4j service capabilities and FastAPI endpoints,
focusing on DateTime serialization, enhanced legal analysis, and sophisticated research features.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from httpx import AsyncClient

from api.main import app
from services.graph.enhanced_neo4j_service import EnhancedNeo4jService

class TestEnhancedCasesAPI:
    """Integration tests for enhanced cases API endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def enhanced_service(self):
        """Enhanced Neo4j service fixture."""
        service = EnhancedNeo4jService(
            uri="bolt://localhost:7687",
            user="neo4j", 
            password="citation_graph_2024"
        )
        try:
            await service.connect()
            yield service
        except Exception as e:
            pytest.skip(f"Enhanced Neo4j service not available: {e}")
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    async def test_case_good_law_status_endpoint(self, client: AsyncClient):
        """Test good law status endpoint with DateTime serialization."""
        # Test with sample case that should exist
        response = await client.get("/api/v1/cases/brown-v-board-1954/good-law-status")
        
        if response.status_code == 404:
            pytest.skip("Sample legal data not available")
            
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "case_id" in data
        assert "current_status" in data
        assert "good_law_confidence" in data
        assert "last_verification" in data
        
        # Verify DateTime serialization (critical fix)
        if data["last_verification"]:
            # Should be ISO string, not Neo4j DateTime object
            assert isinstance(data["last_verification"], str)
            # Should be parseable as datetime
            datetime.fromisoformat(data["last_verification"].replace('Z', '+00:00'))
    
    @pytest.mark.asyncio
    async def test_case_treatment_analysis_endpoint(self, client: AsyncClient):
        """Test citation treatment analysis endpoint with DateTime serialization."""
        response = await client.get("/api/v1/cases/brown-v-board-1954/treatment-analysis")
        
        if response.status_code == 404:
            pytest.skip("Sample legal data not available")
            
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_citations" in data
        assert "positive_citations" in data
        assert "negative_citations" in data
        assert "weighted_authority_impact" in data
        assert "good_law_confidence" in data
        assert "recent_citations" in data
        
        # Verify DateTime serialization in nested data
        if data["recent_citations"]:
            for citation in data["recent_citations"]:
                if "decision_date" in citation and citation["decision_date"]:
                    assert isinstance(citation["decision_date"], str)
                    datetime.fromisoformat(citation["decision_date"].replace('Z', '+00:00'))
    
    @pytest.mark.asyncio
    async def test_case_authoritative_precedents_endpoint(self, client: AsyncClient):
        """Test authoritative precedents discovery endpoint."""
        response = await client.get("/api/v1/cases/brown-v-board-1954/authoritative-precedents")
        
        if response.status_code == 404:
            pytest.skip("Sample legal data not available")
            
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of authoritative precedents
        assert isinstance(data, list)
        
        # Verify precedent structure if any exist
        for precedent in data:
            assert "case_id" in precedent
            assert "authority_score" in precedent
            if "decision_date" in precedent and precedent["decision_date"]:
                assert isinstance(precedent["decision_date"], str)
    
    @pytest.mark.asyncio
    async def test_enhanced_case_stats_integration(self, client: AsyncClient):
        """Test case retrieval with enhanced stats integration."""
        response = await client.get("/api/v1/cases/miranda-v-arizona-1966?include_stats=true")
        
        if response.status_code == 404:
            pytest.skip("Sample legal data not available")
            
        assert response.status_code == 200
        data = response.json()
        
        # Verify enhanced stats are included
        assert "authority_score" in data
        assert "citing_count" in data
        assert "citation_count" in data
        
        # Verify DateTime fields are properly serialized
        date_fields = ["decision_date", "filing_date", "created_at", "updated_at"]
        for field in date_fields:
            if field in data and data[field]:
                assert isinstance(data[field], str)
                datetime.fromisoformat(data[field].replace('Z', '+00:00'))

class TestEnhancedSearchAPI:
    """Integration tests for enhanced search API endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_enhanced_semantic_search(self, client: AsyncClient):
        """Test semantic search using enhanced Neo4j service."""
        search_request = {
            "query": "constitutional equal protection analysis",
            "jurisdiction": "federal",
            "practice_areas": ["constitutional_law"],
            "max_results": 5
        }
        
        response = await client.post("/api/v1/search/semantic", json=search_request)
        
        # May return empty results if no data, but should not error
        assert response.status_code in [200, 204]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Verify DateTime serialization in search results
            for result in data:
                if "decision_date" in result and result["decision_date"]:
                    assert isinstance(result["decision_date"], str)
    
    @pytest.mark.asyncio
    async def test_enhanced_case_search(self, client: AsyncClient):
        """Test structured case search with enhanced filtering."""
        search_params = {
            "jurisdiction": "federal",
            "practice_areas": "constitutional_law",
            "good_law_only": "true",
            "limit": "10"
        }
        
        response = await client.get("/api/v1/search/cases", params=search_params)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify enhanced filtering worked
        for case in data:
            if "jurisdiction" in case:
                # Should match filter if jurisdiction is present
                assert case.get("jurisdiction") in ["federal", None]

class TestEnhancedResearchAPI:
    """Integration tests for enhanced research workflow endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_research_session_with_enhanced_analysis(self, client: AsyncClient):
        """Test research session creation using enhanced capabilities."""
        session_request = {
            "query": "constitutional law equal protection",
            "jurisdiction": "federal", 
            "practice_areas": ["constitutional_law"],
            "max_results": 5
        }
        
        response = await client.post("/api/v1/research/sessions", json=session_request)
        assert response.status_code == 201
        
        session_data = response.json()
        assert "id" in session_data
        assert session_data["status"] == "pending"
        
        # Verify DateTime serialization
        assert isinstance(session_data["created_at"], str)
        datetime.fromisoformat(session_data["created_at"])
    
    @pytest.mark.asyncio
    async def test_precedent_analysis_with_enhanced_features(self, client: AsyncClient):
        """Test precedent analysis using enhanced legal research capabilities."""
        analysis_request = {
            "query": "constitutional equal protection analysis",
            "case_id": "brown-v-board-1954",
            "jurisdiction": "federal",
            "practice_areas": ["constitutional_law"]
        }
        
        response = await client.post("/api/v1/research/analyze-precedent", json=analysis_request)
        
        # May fail if case doesn't exist, but should not have serialization errors
        if response.status_code == 200:
            data = response.json()
            
            # Verify enhanced analysis fields
            if "good_law_status" in data and data["good_law_status"]:
                assert "current_status" in data["good_law_status"]
                assert "good_law_confidence" in data["good_law_status"]
                
                # Verify DateTime serialization
                if "last_verification" in data["good_law_status"]:
                    last_verification = data["good_law_status"]["last_verification"]
                    if last_verification:
                        assert isinstance(last_verification, str)

class TestEnhancedErrorHandling:
    """Integration tests for enhanced service error handling."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_enhanced_endpoint_with_nonexistent_case(self, client: AsyncClient):
        """Test enhanced endpoints gracefully handle missing cases."""
        response = await client.get("/api/v1/cases/nonexistent-case-id/good-law-status")
        
        # Should return 404 or empty result, not serialization error
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            data = response.json()
            # Should have default structure
            assert "case_id" in data
            assert "current_status" in data
    
    @pytest.mark.asyncio
    async def test_enhanced_endpoint_datetime_consistency(self, client: AsyncClient):
        """Test that all enhanced endpoints consistently serialize DateTime objects."""
        # Test multiple enhanced endpoints for consistent DateTime handling
        test_cases = [
            "/api/v1/cases/brown-v-board-1954/good-law-status",
            "/api/v1/cases/brown-v-board-1954/treatment-analysis"
        ]
        
        for endpoint in test_cases:
            response = await client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # Recursively check for DateTime objects
                self._verify_no_datetime_objects(data, endpoint)
    
    def _verify_no_datetime_objects(self, data: Any, endpoint: str) -> None:
        """Recursively verify no Neo4j DateTime objects in response data."""
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    # Check for Neo4j DateTime object indicators
                    value_type = str(type(value))
                    assert "neo4j.time.DateTime" not in value_type, f"DateTime object found in {endpoint}: {key}={value}"
                    assert "neo4j.time.Date" not in value_type, f"Date object found in {endpoint}: {key}={value}"
                    
                    # Recurse into nested structures
                    self._verify_no_datetime_objects(value, endpoint)
        elif isinstance(data, list):
            for item in data:
                self._verify_no_datetime_objects(item, endpoint)

class TestEnhancedServiceIntegration:
    """Integration tests for enhanced service lifecycle and dependency injection."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_enhanced_service_health_integration(self, client: AsyncClient):
        """Test enhanced service health through API health endpoint."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify service health includes enhanced capabilities
        assert "services" in data
        if "neo4j" in data["services"]:
            neo4j_status = data["services"]["neo4j"]
            # Should indicate if enhanced schema is available
            assert "enhanced_schema" in neo4j_status
    
    @pytest.mark.asyncio
    async def test_enhanced_service_dependency_injection(self, client: AsyncClient):
        """Test that enhanced service is properly injected into endpoints."""
        # Test an endpoint that requires enhanced Neo4j service
        response = await client.get("/api/v1/cases/brown-v-board-1954/good-law-status")
        
        # Should not fail with dependency injection errors
        assert response.status_code != 500
        
        # If it returns 200, the enhanced service was successfully injected
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)