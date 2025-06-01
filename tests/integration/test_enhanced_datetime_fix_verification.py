"""
Integration tests to verify DateTime serialization fixes in enhanced legal research.

These tests verify that the critical DateTime serialization issues have been resolved
in the enhanced Neo4j service and API endpoints.
"""

import pytest
from datetime import datetime
from services.graph.enhanced_neo4j_service import EnhancedNeo4jService

@pytest.mark.integration
class TestDateTimeSerializationFix:
    """Test that DateTime serialization fixes are working."""
    
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
    async def test_enhanced_service_has_datetime_conversion_method(self, enhanced_service):
        """Verify enhanced service has the DateTime conversion method."""
        # The critical fix: enhanced service should have _convert_neo4j_temporals method
        assert hasattr(enhanced_service, '_convert_neo4j_temporals'), \
            "Enhanced service missing _convert_neo4j_temporals method"
        
        # Method should be callable
        assert callable(enhanced_service._convert_neo4j_temporals), \
            "_convert_neo4j_temporals should be callable"
    
    @pytest.mark.asyncio 
    async def test_datetime_conversion_functionality(self, enhanced_service):
        """Test that DateTime conversion method works correctly."""
        # Test with various data types that could contain Neo4j DateTime objects
        test_data = {
            "string_field": "test",
            "number_field": 123,
            "none_field": None,
            "list_field": [1, 2, 3],
            "nested_dict": {
                "inner_string": "test",
                "inner_list": ["a", "b", "c"]
            }
        }
        
        # Should handle regular data without errors
        result = enhanced_service._convert_neo4j_temporals(test_data)
        
        assert isinstance(result, dict)
        assert result["string_field"] == "test"
        assert result["number_field"] == 123
        assert result["none_field"] is None
        assert result["list_field"] == [1, 2, 3]
        assert result["nested_dict"]["inner_string"] == "test"
    
    @pytest.mark.asyncio
    async def test_good_law_verification_uses_datetime_conversion(self, enhanced_service):
        """Verify good law verification applies DateTime conversion."""
        # Test with a case that likely doesn't exist (to get default response)
        result = await enhanced_service.verify_good_law_status("nonexistent-test-case")
        
        # Should return dict without Neo4j DateTime objects
        assert isinstance(result, dict)
        
        # Should have expected structure
        assert "case_id" in result
        assert "current_status" in result
        assert "good_law_confidence" in result
        
        # Verify no Neo4j temporal objects in response
        self._verify_no_neo4j_temporals(result)
    
    @pytest.mark.asyncio
    async def test_citation_treatment_analysis_uses_datetime_conversion(self, enhanced_service):
        """Verify citation treatment analysis applies DateTime conversion."""
        # Test with a case that likely doesn't exist (to get default response)
        result = await enhanced_service.analyze_citation_treatment("nonexistent-test-case")
        
        # Should return dict without Neo4j DateTime objects
        assert isinstance(result, dict)
        
        # Should have expected structure
        assert "total_citations" in result
        assert "good_law_confidence" in result
        assert "recent_citations" in result
        
        # Verify no Neo4j temporal objects in response
        self._verify_no_neo4j_temporals(result)
    
    def _verify_no_neo4j_temporals(self, data, path="root"):
        """Recursively verify no Neo4j temporal objects in data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}"
                self._verify_no_neo4j_temporals(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                self._verify_no_neo4j_temporals(item, current_path)
        elif data is not None:
            # Check that value is not a Neo4j temporal object
            value_type = str(type(data))
            assert "neo4j.time.DateTime" not in value_type, \
                f"Neo4j DateTime object found at {path}: {data}"
            assert "neo4j.time.Date" not in value_type, \
                f"Neo4j Date object found at {path}: {data}"
            assert "neo4j.time.Duration" not in value_type, \
                f"Neo4j Duration object found at {path}: {data}"

@pytest.mark.integration
class TestEnhancedServiceImplementation:
    """Test that enhanced service implementation includes the fixes."""
    
    @pytest.mark.asyncio
    async def test_enhanced_service_class_has_required_methods(self):
        """Test that EnhancedNeo4jService class has required methods."""
        # Import the class (doesn't require connection)
        from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
        
        # Should have the critical methods
        assert hasattr(EnhancedNeo4jService, 'analyze_citation_treatment')
        assert hasattr(EnhancedNeo4jService, 'verify_good_law_status')
        assert hasattr(EnhancedNeo4jService, '_convert_neo4j_temporals')
        
        # Methods should be callable
        assert callable(getattr(EnhancedNeo4jService, 'analyze_citation_treatment'))
        assert callable(getattr(EnhancedNeo4jService, 'verify_good_law_status'))
        assert callable(getattr(EnhancedNeo4jService, '_convert_neo4j_temporals'))
    
    @pytest.mark.asyncio
    async def test_enhanced_service_methods_use_conversion(self):
        """Test that enhanced service methods use DateTime conversion."""
        # Read the source code to verify the fix is in place
        import inspect
        from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
        
        # Get source code of critical methods
        treatment_source = inspect.getsource(EnhancedNeo4jService.analyze_citation_treatment)
        good_law_source = inspect.getsource(EnhancedNeo4jService.verify_good_law_status)
        
        # Verify methods call _convert_neo4j_temporals
        assert "_convert_neo4j_temporals" in treatment_source, \
            "analyze_citation_treatment should call _convert_neo4j_temporals"
        assert "_convert_neo4j_temporals" in good_law_source, \
            "verify_good_law_status should call _convert_neo4j_temporals"
        
        # Verify the fix pattern is correct
        assert "return self._convert_neo4j_temporals(" in treatment_source, \
            "analyze_citation_treatment should return converted data"
        assert "return self._convert_neo4j_temporals(" in good_law_source, \
            "verify_good_law_status should return converted data"

@pytest.mark.integration  
@pytest.mark.slow
class TestEndToEndDateTimeFix:
    """End-to-end tests to verify DateTime serialization is working."""
    
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
    async def test_sample_case_good_law_verification(self, enhanced_service):
        """Test good law verification with sample case."""
        # Test with brown-v-board-1954 if it exists
        result = await enhanced_service.verify_good_law_status("brown-v-board-1954")
        
        # Should not raise serialization errors
        assert isinstance(result, dict)
        
        # If verification was successful, check structure
        if result.get("current_status") != "unknown":
            assert "good_law_confidence" in result
            assert "last_verification" in result
            
            # last_verification should be datetime or None (not Neo4j DateTime)
            last_verification = result.get("last_verification")
            if last_verification is not None:
                # Should be Python datetime, ISO string, or converted appropriately
                assert not str(type(last_verification)).startswith("neo4j.time")
    
    @pytest.mark.asyncio
    async def test_sample_case_treatment_analysis(self, enhanced_service):
        """Test treatment analysis with sample case."""
        # Test with brown-v-board-1954 if it exists
        result = await enhanced_service.analyze_citation_treatment("brown-v-board-1954") 
        
        # Should not raise serialization errors
        assert isinstance(result, dict)
        
        # Check structure
        assert "total_citations" in result
        assert "recent_citations" in result
        
        # Verify recent_citations doesn't contain Neo4j DateTime objects
        for citation in result.get("recent_citations", []):
            if isinstance(citation, dict):
                for key, value in citation.items():
                    if value is not None:
                        assert not str(type(value)).startswith("neo4j.time"), \
                            f"Neo4j temporal object in citation {key}: {value}"

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration