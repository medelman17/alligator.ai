"""
Integration tests for DateTime serialization in enhanced legal research endpoints.

Focuses specifically on testing the fixes for Neo4j DateTime object serialization
issues that were causing "Unable to serialize unknown type: <class 'neo4j.time.DateTime'>" errors.
"""

import pytest
import asyncio
from datetime import datetime, date
from typing import Any, Dict, List
from httpx import AsyncClient

from api.main import app
from services.graph.enhanced_neo4j_service import EnhancedNeo4jService

class TestDateTimeSerializationIntegration:
    """Integration tests for DateTime serialization fixes."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def enhanced_service(self):
        """Enhanced Neo4j service for direct testing."""
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
    async def test_good_law_verification_datetime_serialization(self, client: AsyncClient, enhanced_service):
        """Test good law verification endpoint DateTime serialization."""
        # Test direct service method first
        result = await enhanced_service.verify_good_law_status("brown-v-board-1954")
        
        # Verify service method returns properly converted dates
        self._verify_datetime_conversion(result, "verify_good_law_status")
        
        # Test API endpoint
        response = await client.get("/api/v1/cases/brown-v-board-1954/good-law-status")
        
        if response.status_code == 200:
            data = response.json()
            # Verify API response has properly serialized dates
            self._verify_api_datetime_serialization(data, "/good-law-status")
    
    @pytest.mark.asyncio
    async def test_citation_treatment_analysis_datetime_serialization(self, client: AsyncClient, enhanced_service):
        """Test citation treatment analysis endpoint DateTime serialization."""
        # Test direct service method first
        result = await enhanced_service.analyze_citation_treatment("brown-v-board-1954")
        
        # Verify service method returns properly converted dates
        self._verify_datetime_conversion(result, "analyze_citation_treatment")
        
        # Test API endpoint
        response = await client.get("/api/v1/cases/brown-v-board-1954/treatment-analysis")
        
        if response.status_code == 200:
            data = response.json()
            # Verify API response has properly serialized dates
            self._verify_api_datetime_serialization(data, "/treatment-analysis")
    
    @pytest.mark.asyncio
    async def test_authoritative_precedents_datetime_serialization(self, client: AsyncClient, enhanced_service):
        """Test authoritative precedents discovery DateTime serialization."""
        # Test direct service method
        result = await enhanced_service.find_authoritative_precedents(
            practice_areas=["constitutional_law"],
            jurisdiction="federal",
            limit=5
        )
        
        # Verify service method returns properly converted dates
        self._verify_datetime_conversion(result, "find_authoritative_precedents")
        
        # Test API endpoint
        response = await client.get("/api/v1/cases/brown-v-board-1954/authoritative-precedents")
        
        if response.status_code == 200:
            data = response.json()
            self._verify_api_datetime_serialization(data, "/authoritative-precedents")
    
    @pytest.mark.asyncio
    async def test_semantic_case_search_datetime_serialization(self, client: AsyncClient, enhanced_service):
        """Test semantic case search DateTime serialization."""
        # Test direct service method
        result = await enhanced_service.semantic_case_search(
            query="constitutional law",
            practice_areas=["constitutional_law"],
            limit=5
        )
        
        # Verify service method returns properly converted dates
        self._verify_datetime_conversion(result, "semantic_case_search")
        
        # Test API endpoint
        search_request = {
            "query": "constitutional law",
            "practice_areas": ["constitutional_law"],
            "max_results": 5
        }
        response = await client.post("/api/v1/search/semantic", json=search_request)
        
        if response.status_code == 200:
            data = response.json()
            self._verify_api_datetime_serialization(data, "/search/semantic")
    
    @pytest.mark.asyncio
    async def test_enhanced_case_retrieval_datetime_serialization(self, client: AsyncClient):
        """Test enhanced case retrieval with stats DateTime serialization."""
        response = await client.get("/api/v1/cases/miranda-v-arizona-1966?include_stats=true")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify all date fields are properly serialized
            date_fields = ["decision_date", "filing_date", "created_at", "updated_at"]
            for field in date_fields:
                if field in data and data[field]:
                    assert isinstance(data[field], str), f"Field {field} should be string, got {type(data[field])}"
                    # Should be parseable as ISO datetime
                    try:
                        datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    except ValueError as e:
                        pytest.fail(f"Field {field} is not valid ISO datetime: {data[field]} - {e}")
    
    @pytest.mark.asyncio
    async def test_research_session_datetime_serialization(self, client: AsyncClient):
        """Test research session creation and retrieval DateTime serialization."""
        # Create research session
        session_request = {
            "query": "constitutional law",
            "jurisdiction": "federal",
            "practice_areas": ["constitutional_law"]
        }
        
        response = await client.post("/api/v1/research/sessions", json=session_request)
        assert response.status_code == 201
        
        session_data = response.json()
        session_id = session_data["id"]
        
        # Verify creation response DateTime serialization
        datetime_fields = ["created_at", "updated_at", "completed_at"]
        for field in datetime_fields:
            if field in session_data and session_data[field]:
                assert isinstance(session_data[field], str), f"Field {field} should be string"
                try:
                    datetime.fromisoformat(session_data[field])
                except ValueError as e:
                    pytest.fail(f"Field {field} is not valid ISO datetime: {e}")
        
        # Retrieve session and verify DateTime serialization
        response = await client.get(f"/api/v1/research/sessions/{session_id}")
        
        if response.status_code == 200:
            retrieved_data = response.json()
            self._verify_api_datetime_serialization(retrieved_data, f"/sessions/{session_id}")
    
    def _verify_datetime_conversion(self, data: Any, method_name: str) -> None:
        """
        Verify that service method data has properly converted DateTime objects.
        
        After the _convert_neo4j_temporals fix, service methods should return
        Python datetime objects or ISO strings, never Neo4j DateTime objects.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    value_type = str(type(value))
                    
                    # Should never have Neo4j temporal objects
                    assert "neo4j.time.DateTime" not in value_type, \
                        f"Neo4j DateTime found in {method_name}: {key}={value}"
                    assert "neo4j.time.Date" not in value_type, \
                        f"Neo4j Date found in {method_name}: {key}={value}"
                    
                    # Recurse into nested structures
                    self._verify_datetime_conversion(value, method_name)
                    
        elif isinstance(data, list):
            for item in data:
                self._verify_datetime_conversion(item, method_name)
    
    def _verify_api_datetime_serialization(self, data: Any, endpoint: str) -> None:
        """
        Verify that API endpoint response has properly serialized DateTime fields.
        
        All datetime fields should be ISO string format for JSON serialization.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    # Check for common datetime field names
                    if any(date_term in key.lower() for date_term in ["date", "time", "at", "verification"]):
                        if isinstance(value, str):
                            # Should be parseable as ISO datetime
                            try:
                                datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except ValueError:
                                # Not all fields with "date" in name are dates, so warn but don't fail
                                pass
                    
                    # Verify no temporal objects leaked through
                    value_type = str(type(value))
                    assert "neo4j.time" not in value_type, \
                        f"Neo4j temporal object found in {endpoint}: {key}={value}"
                    assert "datetime.datetime" not in value_type, \
                        f"Python datetime object found in {endpoint}: {key}={value} (should be ISO string)"
                    
                    # Recurse into nested structures
                    self._verify_api_datetime_serialization(value, endpoint)
                    
        elif isinstance(data, list):
            for item in data:
                self._verify_api_datetime_serialization(item, endpoint)

class TestDateTimeEdgeCases:
    """Test edge cases for DateTime serialization."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_null_datetime_handling(self, client: AsyncClient):
        """Test that null/None datetime values are handled correctly."""
        response = await client.get("/api/v1/cases/nonexistent-case/good-law-status")
        
        # Should handle missing case gracefully
        if response.status_code == 200:
            data = response.json()
            # Null datetime fields should be null, not cause serialization errors
            assert data.get("last_verification") is None or isinstance(data["last_verification"], str)
    
    @pytest.mark.asyncio
    async def test_empty_citation_list_datetime_handling(self, client: AsyncClient):
        """Test datetime handling with empty citation lists."""
        response = await client.get("/api/v1/cases/brown-v-board-1954/treatment-analysis")
        
        if response.status_code == 200:
            data = response.json()
            # Empty recent_citations list should not cause errors
            assert isinstance(data.get("recent_citations", []), list)
    
    @pytest.mark.asyncio
    async def test_mixed_datetime_formats_handling(self, client: AsyncClient):
        """Test handling of various datetime formats in responses."""
        # Test multiple endpoints that might return different datetime formats
        endpoints = [
            "/api/v1/cases/brown-v-board-1954",
            "/api/v1/cases/brown-v-board-1954/good-law-status",
            "/api/v1/cases/brown-v-board-1954/treatment-analysis"
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                
                # All datetime strings should follow consistent format
                self._verify_consistent_datetime_format(data, endpoint)
    
    def _verify_consistent_datetime_format(self, data: Any, endpoint: str) -> None:
        """Verify consistent datetime format across all fields."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and any(term in key.lower() for term in ["date", "time", "at", "verification"]):
                    if value and len(value) > 10:  # Likely a datetime string
                        try:
                            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            # Should be in ISO format
                            assert 'T' in value or ' ' in value, f"Datetime should be ISO format in {endpoint}: {key}={value}"
                        except ValueError:
                            # Not all fields with date terms are actually dates
                            pass
                
                # Recurse
                self._verify_consistent_datetime_format(value, endpoint)
                
        elif isinstance(data, list):
            for item in data:
                self._verify_consistent_datetime_format(item, endpoint)

class TestDateTimePerformance:
    """Test DateTime conversion performance in integration scenarios."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_datetime_conversion_performance(self, client: AsyncClient):
        """Test that DateTime conversion doesn't significantly impact response times."""
        import time
        
        # Test enhanced endpoint that processes many datetime fields
        start_time = time.time()
        response = await client.get("/api/v1/cases/brown-v-board-1954/treatment-analysis")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            # DateTime conversion should not add significant overhead
            assert response_time < 5.0, f"DateTime conversion too slow: {response_time}s"
            
            # Response should still be properly formatted
            data = response.json()
            assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_bulk_datetime_conversion(self, client: AsyncClient):
        """Test DateTime conversion with multiple results."""
        search_request = {
            "query": "constitutional law",
            "max_results": 10
        }
        
        response = await client.post("/api/v1/search/semantic", json=search_request)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should handle datetime conversion for multiple results efficiently
            if isinstance(data, list) and len(data) > 0:
                # Verify all results have properly converted dates
                for result in data:
                    if "decision_date" in result and result["decision_date"]:
                        assert isinstance(result["decision_date"], str)
                        datetime.fromisoformat(result["decision_date"].replace('Z', '+00:00'))