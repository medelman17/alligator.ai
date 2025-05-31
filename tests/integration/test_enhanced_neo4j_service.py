"""
Integration tests for enhanced Neo4j service with legal research capabilities.

Tests the sophisticated legal research features including:
- Enhanced schema initialization
- Authoritative precedent discovery 
- Citation treatment analysis
- Good law verification
- Legal authority PageRank calculations
- Semantic case search
"""

import pytest
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any

from services.graph.neo4j_service import Neo4jService
from shared.models.legal_entities import Case, Court

# Test configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "citation_graph_2024"

class TestEnhancedNeo4jService:
    """Test suite for enhanced Neo4j service legal research capabilities."""
    
    @pytest.fixture
    async def neo4j_service(self):
        """Fixture providing a connected Neo4j service instance."""
        service = Neo4jService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            await service.connect()
            yield service
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    async def test_enhanced_schema_initialization(self, neo4j_service):
        """Test that enhanced schema is properly initialized."""
        # Check if enhanced schema was initialized
        assert hasattr(neo4j_service, 'enhanced_schema_available')
        
        # Test health check with enhanced features
        is_healthy = await neo4j_service.health_check()
        assert is_healthy, "Neo4j service should be healthy"
    
    @pytest.mark.asyncio
    async def test_find_authoritative_precedents(self, neo4j_service):
        """Test finding authoritative precedents with multi-factor scoring."""
        if not neo4j_service.enhanced_schema_available:
            pytest.skip("Enhanced schema not available")
        
        # Test with sample constitutional law case
        precedents = await neo4j_service.find_authoritative_precedents(
            case_id="brown-v-board-1954",
            target_jurisdictions=["US", "US-9"],
            practice_areas=["constitutional_law", "civil_rights"],
            primary_jurisdiction="US",
            limit=10
        )
        
        # Should return precedents with relevance scoring
        assert isinstance(precedents, list)
        
        if precedents:
            precedent = precedents[0]
            assert "case" in precedent
            assert "relevance_score" in precedent
            assert "authority_factors" in precedent
            
            # Check authority factors structure
            factors = precedent["authority_factors"]
            assert "authority_score" in factors
            assert "jurisdiction" in factors
            assert "practice_areas" in factors
    
    @pytest.mark.asyncio
    async def test_citation_treatment_analysis(self, neo4j_service):
        """Test comprehensive citation treatment analysis."""
        if not neo4j_service.enhanced_schema_available:
            pytest.skip("Enhanced schema not available")
        
        # Test with landmark case that should have citations
        treatment = await neo4j_service.analyze_citation_treatment("brown-v-board-1954")
        
        assert isinstance(treatment, dict)
        assert "total_citations" in treatment
        assert "positive_citations" in treatment
        assert "negative_citations" in treatment
        assert "neutral_citations" in treatment
        assert "good_law_confidence" in treatment
        assert "recent_citations" in treatment
        
        # Good law confidence should be a valid value
        confidence = treatment["good_law_confidence"]
        assert confidence in ["strong", "moderate", "questionable", "unknown"]
    
    @pytest.mark.asyncio
    async def test_good_law_verification(self, neo4j_service):
        """Test good law status verification."""
        if not neo4j_service.enhanced_schema_available:
            pytest.skip("Enhanced schema not available")
        
        # Test with Brown v. Board (should be good law)
        verification = await neo4j_service.verify_good_law_status("brown-v-board-1954")
        
        assert isinstance(verification, dict)
        assert "case_id" in verification
        assert "good_law_confidence" in verification
        assert "overruled_by" in verification
        assert "negative_treatment_count" in verification
        assert "positive_treatment_count" in verification
        
        assert verification["case_id"] == "brown-v-board-1954"
    
    @pytest.mark.asyncio 
    async def test_legal_authority_pagerank(self, neo4j_service):
        """Test PageRank calculation with legal domain weighting."""
        if not neo4j_service.enhanced_schema_available:
            pytest.skip("Enhanced schema not available")
        
        # Calculate PageRank scores
        pagerank_result = await neo4j_service.calculate_legal_authority_pagerank()
        
        assert isinstance(pagerank_result, dict)
        
        # Should either succeed or fail gracefully
        if "error" not in pagerank_result:
            assert "nodes_updated" in pagerank_result
            assert "algorithm" in pagerank_result
            assert pagerank_result["algorithm"] == "legal_authority_pagerank"
    
    @pytest.mark.asyncio
    async def test_semantic_case_search(self, neo4j_service):
        """Test enhanced semantic search with legal filtering."""
        # Test basic semantic search
        results = await neo4j_service.semantic_case_search(
            search_terms="constitutional equal protection",
            jurisdictions=["US"],
            practice_areas=["constitutional_law"],
            good_law_only=True,
            limit=5
        )
        
        assert isinstance(results, list)
        
        if results:
            result = results[0]
            assert "case" in result
            assert "relevance_score" in result
            assert "authority_score" in result
            
            # Case should match search criteria
            case = result["case"]
            assert case.jurisdiction == "US"
            
            # Should have practice area overlap
            if hasattr(case, 'practice_areas') and case.practice_areas:
                assert "constitutional_law" in case.practice_areas
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_date_range(self, neo4j_service):
        """Test semantic search with date range filtering."""
        # Search for cases from 1950-1960 (should include Brown v. Board)
        results = await neo4j_service.semantic_case_search(
            search_terms="education segregation",
            jurisdictions=["US"],
            date_range=(date(1950, 1, 1), date(1960, 12, 31)),
            limit=10
        )
        
        assert isinstance(results, list)
        
        # Check date filtering works
        for result in results:
            case = result["case"]
            if hasattr(case, 'decision_date') and case.decision_date:
                case_date = case.decision_date.date() if isinstance(case.decision_date, datetime) else case.decision_date
                assert date(1950, 1, 1) <= case_date <= date(1960, 12, 31)
    
    @pytest.mark.asyncio
    async def test_fallback_functionality(self, neo4j_service):
        """Test that service gracefully falls back when enhanced features unavailable."""
        # Temporarily disable enhanced schema to test fallback
        original_enhanced = neo4j_service.enhanced_schema_available
        neo4j_service.enhanced_schema_available = False
        
        try:
            # Test precedent search fallback
            precedents = await neo4j_service.find_authoritative_precedents(
                case_id="brown-v-board-1954",
                target_jurisdictions=["US"],
                practice_areas=["constitutional_law"],
                limit=5
            )
            assert isinstance(precedents, list)
            
            # Test citation analysis fallback
            treatment = await neo4j_service.analyze_citation_treatment("brown-v-board-1954")
            assert isinstance(treatment, dict)
            assert "good_law_confidence" in treatment
            
            # Test good law verification fallback
            verification = await neo4j_service.verify_good_law_status("brown-v-board-1954")
            assert isinstance(verification, dict)
            assert "good_law_confidence" in verification
            
        finally:
            # Restore original state
            neo4j_service.enhanced_schema_available = original_enhanced
    
    @pytest.mark.asyncio
    async def test_legacy_compatibility(self, neo4j_service):
        """Test that legacy API methods still work with enhanced service."""
        # Test legacy case retrieval
        case = await neo4j_service.get_case_by_id("brown-v-board-1954")
        if case:
            assert hasattr(case, 'case_name')
            assert hasattr(case, 'jurisdiction')
        
        # Test legacy case search
        cases = await neo4j_service.find_cases_by_criteria(
            jurisdiction="US",
            practice_areas=["constitutional_law"],
            limit=5
        )
        assert isinstance(cases, list)
        
        # Test legacy authority score calculation
        authority_score = await neo4j_service.calculate_authority_score("brown-v-board-1954")
        assert isinstance(authority_score, (int, float))
        assert authority_score >= 0.0
    
    @pytest.mark.asyncio
    async def test_enhanced_vs_basic_schema_behavior(self, neo4j_service):
        """Test behavior differences between enhanced and basic schemas."""
        # This test documents the differences in behavior
        
        if neo4j_service.enhanced_schema_available:
            # Enhanced schema should provide detailed treatment analysis
            treatment = await neo4j_service.analyze_citation_treatment("brown-v-board-1954")
            
            # Enhanced schema has more detailed fields
            expected_fields = [
                "total_citations", "positive_citations", "negative_citations",
                "weighted_authority_impact", "good_law_confidence", "recent_citations"
            ]
            
            for field in expected_fields:
                assert field in treatment, f"Enhanced schema should include {field}"
        
        else:
            # Basic schema provides simpler analysis
            treatment = await neo4j_service.analyze_citation_treatment("brown-v-board-1954")
            
            # Basic schema has core fields
            basic_fields = ["total_citations", "good_law_confidence"]
            for field in basic_fields:
                assert field in treatment, f"Basic schema should include {field}"


# Performance and stress tests
class TestEnhancedNeo4jPerformance:
    """Performance tests for enhanced Neo4j service."""
    
    @pytest.fixture
    async def neo4j_service(self):
        """Fixture providing a connected Neo4j service instance."""
        service = Neo4jService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            await service.connect()
            yield service
        except Exception as e:
            pytest.skip(f"Neo4j not available: {e}")
        finally:
            await service.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, neo4j_service):
        """Test concurrent legal research queries."""
        if not neo4j_service.enhanced_schema_available:
            pytest.skip("Enhanced schema not available")
        
        # Run multiple queries concurrently
        tasks = [
            neo4j_service.find_authoritative_precedents(
                "brown-v-board-1954", ["US"], ["constitutional_law"], limit=5
            ),
            neo4j_service.analyze_citation_treatment("brown-v-board-1954"),
            neo4j_service.verify_good_law_status("brown-v-board-1954"),
            neo4j_service.semantic_case_search("equal protection", ["US"], limit=5)
        ]
        
        # All tasks should complete successfully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Task {i} failed: {result}"
    
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, neo4j_service):
        """Test handling of large result sets."""
        # Test with larger limits
        results = await neo4j_service.semantic_case_search(
            search_terms="law",  # Broad search term
            limit=100
        )
        
        assert isinstance(results, list)
        assert len(results) <= 100  # Should respect limit
    
    @pytest.mark.asyncio
    async def test_query_performance_logging(self, neo4j_service, caplog):
        """Test that query performance is tracked."""
        import time
        
        start_time = time.time()
        
        # Run a complex query
        await neo4j_service.find_authoritative_precedents(
            "brown-v-board-1954", 
            ["US", "US-1", "US-2", "US-3"], 
            ["constitutional_law", "civil_rights"],
            limit=25
        )
        
        elapsed_time = time.time() - start_time
        
        # Query should complete in reasonable time (less than 5 seconds)
        assert elapsed_time < 5.0, f"Query took too long: {elapsed_time:.2f}s"


if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])