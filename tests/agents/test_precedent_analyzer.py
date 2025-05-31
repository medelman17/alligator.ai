"""
Tests for PrecedentAnalyzer agent workflows.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import List, Dict, Any

from shared.models.legal_entities import Case, Citation, PracticeArea, CaseStatus, CitationTreatment
from services.orchestration.agents.precedent_analyzer import PrecedentAnalyzer, PrecedentAnalysisState


@pytest.mark.agent
class TestPrecedentAnalyzer:
    """Test PrecedentAnalyzer agent workflows."""
    
    @pytest_asyncio.fixture
    async def mock_services(self):
        """Set up mock services for testing."""
        # Mock Neo4j service
        mock_neo4j = AsyncMock()
        mock_neo4j.get_citing_cases = AsyncMock(return_value=[])
        mock_neo4j.get_cited_cases = AsyncMock(return_value=[])
        mock_neo4j.find_cases_by_criteria = AsyncMock(return_value=[])
        mock_neo4j.traverse_citation_network = AsyncMock(return_value=[])
        
        # Mock ChromaDB service
        mock_chroma = AsyncMock()
        mock_chroma.semantic_search = AsyncMock(return_value=[])
        
        return mock_neo4j, mock_chroma
    
    @pytest_asyncio.fixture
    async def analyzer(self, mock_services):
        """Create PrecedentAnalyzer with mocked services."""
        mock_neo4j, mock_chroma = mock_services
        
        # Use a mock API key for testing
        analyzer = PrecedentAnalyzer(
            neo4j_service=mock_neo4j,
            chroma_service=mock_chroma,
            anthropic_api_key="test-api-key"
        )
        
        # Mock the LLM to avoid actual API calls
        mock_llm_response = MagicMock()
        mock_llm_response.content = """
        # Precedent Analysis Memo
        
        ## Executive Summary
        Based on the research query regarding qualified immunity, several key precedents establish the current legal framework.
        
        ## Key Precedents Analysis
        1. **Test v. Case (2020)** - Establishes constitutional framework
        2. **Another v. Test (2021)** - Follows established precedent
        
        ## Authority Assessment
        The cases found represent binding precedent with high authority scores.
        
        ## Current Legal Status
        The legal doctrine remains active and controlling.
        
        ## Recommendations for Legal Strategy
        Consider the established precedent when developing arguments.
        """
        
        analyzer.llm.ainvoke = AsyncMock(return_value=mock_llm_response)
        
        return analyzer
    
    async def test_analyze_precedents_basic(self, analyzer: PrecedentAnalyzer):
        """Test basic precedent analysis workflow."""
        result = await analyzer.analyze_precedents(
            query="qualified immunity for police officers",
            jurisdiction="US",
            practice_areas=["civil_rights"]
        )
        
        # Check that result has expected structure
        assert "precedent_memo" in result
        assert "relevant_precedents" in result
        assert "authority_analysis" in result
        assert "treatment_analysis" in result
        assert "confidence_score" in result
        
        # Check that memo was generated
        assert isinstance(result["precedent_memo"], str)
        assert len(result["precedent_memo"]) > 0
        assert "Precedent Analysis Memo" in result["precedent_memo"]
        
        # Check confidence score
        assert isinstance(result["confidence_score"], float)
        assert 0 <= result["confidence_score"] <= 1
    
    async def test_semantic_search_step(self, analyzer: PrecedentAnalyzer, mock_services):
        """Test the semantic search step of the workflow."""
        mock_neo4j, mock_chroma = mock_services
        
        # Set up mock semantic search results
        mock_semantic_results = [
            {
                "id": "doc_case_test-case-1",
                "content": "Constitutional law case about qualified immunity",
                "metadata": {
                    "source_id": "test-case-1",
                    "title": "Test v. Case",
                    "authority_score": 8.5,
                    "jurisdiction": "US"
                },
                "similarity_score": 0.92,
                "document_type": "case"
            },
            {
                "id": "doc_case_test-case-2", 
                "content": "Civil rights case involving police misconduct",
                "metadata": {
                    "source_id": "test-case-2",
                    "title": "Another v. Test",
                    "authority_score": 7.2,
                    "jurisdiction": "US-9"
                },
                "similarity_score": 0.87,
                "document_type": "case"
            }
        ]
        
        mock_chroma.semantic_search.return_value = mock_semantic_results
        
        # Run analysis
        result = await analyzer.analyze_precedents(
            query="qualified immunity constitutional law",
            jurisdiction="US",
            practice_areas=["civil_rights", "constitutional"]
        )
        
        # Verify semantic search was called correctly
        mock_chroma.semantic_search.assert_called_once()
        call_args = mock_chroma.semantic_search.call_args
        
        assert call_args[1]["query"] == "qualified immunity constitutional law"
        assert call_args[1]["document_types"] == ["case"]
        assert call_args[1]["jurisdiction"] == "US"
        assert call_args[1]["practice_areas"] == ["civil_rights", "constitutional"]
        assert call_args[1]["limit"] == 20
        
        # Check that semantic results were processed
        assert result["semantic_results_count"] == 2
    
    async def test_citation_analysis_with_target_case(self, analyzer: PrecedentAnalyzer, mock_services, sample_cases: List[Case], sample_citations: List[Citation]):
        """Test citation analysis when a target case is specified."""
        mock_neo4j, mock_chroma = mock_services
        
        # Set up mock citation network results
        citing_cases = [(sample_cases[1], sample_citations[0])]  # case-2 cites case-1
        cited_cases = []  # case-1 doesn't cite others in this test
        
        mock_neo4j.get_citing_cases.return_value = citing_cases
        mock_neo4j.get_cited_cases.return_value = cited_cases
        
        # Run analysis with target case
        result = await analyzer.analyze_precedents(
            query="constitutional law analysis",
            jurisdiction="US",
            target_case_id="test-case-1"
        )
        
        # Verify citation methods were called
        mock_neo4j.get_citing_cases.assert_called_once_with("test-case-1", limit=30)
        mock_neo4j.get_cited_cases.assert_called_once_with("test-case-1", limit=30)
        
        # Check that citation results were processed
        assert result["citation_results_count"] >= 1
    
    async def test_citation_analysis_without_target_case(self, analyzer: PrecedentAnalyzer, mock_services, sample_cases: List[Case]):
        """Test citation analysis when no target case is specified."""
        mock_neo4j, mock_chroma = mock_services
        
        # Set up mock results for criteria-based search
        mock_neo4j.find_cases_by_criteria.return_value = sample_cases[:2]
        
        # Run analysis without target case
        result = await analyzer.analyze_precedents(
            query="civil rights law",
            jurisdiction="US",
            practice_areas=["civil_rights"]
        )
        
        # Verify criteria-based search was called
        mock_neo4j.find_cases_by_criteria.assert_called_once()
        call_args = mock_neo4j.find_cases_by_criteria.call_args
        
        assert call_args[1]["jurisdiction"] == "US"
        assert call_args[1]["practice_areas"] == ["civil_rights"]
        assert call_args[1]["limit"] == 30
    
    async def test_authority_analysis(self, analyzer: PrecedentAnalyzer):
        """Test authority analysis of found precedents."""
        # Mock semantic results with different authority levels
        mock_semantic_results = [
            {
                "id": "supreme-case",
                "content": "Supreme Court case",
                "metadata": {
                    "source_id": "supreme-case-1",
                    "authority_score": 9.8,
                    "jurisdiction": "US",
                    "court_id": "us-supreme-court"
                },
                "similarity_score": 0.95,
                "document_type": "case"
            },
            {
                "id": "appellate-case",
                "content": "Appellate court case",
                "metadata": {
                    "source_id": "appellate-case-1", 
                    "authority_score": 7.5,
                    "jurisdiction": "US-9",
                    "court_id": "us-ca-9"
                },
                "similarity_score": 0.88,
                "document_type": "case"
            }
        ]
        
        # Patch the semantic search to return our mock results
        with patch.object(analyzer.chroma, 'semantic_search', return_value=mock_semantic_results):
            result = await analyzer.analyze_precedents(
                query="test authority analysis",
                jurisdiction="US"
            )
        
        authority_analysis = result["authority_analysis"]
        
        # Check authority analysis structure
        assert "supreme_court_cases" in authority_analysis
        assert "appellate_cases" in authority_analysis
        assert "binding_precedents" in authority_analysis
        assert "persuasive_precedents" in authority_analysis
        assert "average_authority_score" in authority_analysis
        
        # Check that cases were categorized correctly
        assert len(authority_analysis["supreme_court_cases"]) >= 1
        assert len(authority_analysis["binding_precedents"]) >= 1
    
    async def test_treatment_analysis(self, analyzer: PrecedentAnalyzer):
        """Test treatment analysis of precedents."""
        # Mock results with different case statuses
        mock_semantic_results = [
            {
                "id": "good-law-case",
                "content": "Good law case",
                "metadata": {
                    "source_id": "good-case-1",
                    "status": "good_law",
                    "decision_date": "2022-01-01T00:00:00Z"
                },
                "similarity_score": 0.9,
                "document_type": "case"
            },
            {
                "id": "questioned-case",
                "content": "Questioned case",
                "metadata": {
                    "source_id": "questioned-case-1",
                    "status": "questioned",
                    "decision_date": "2018-01-01T00:00:00Z"
                },
                "similarity_score": 0.8,
                "document_type": "case"
            }
        ]
        
        with patch.object(analyzer.chroma, 'semantic_search', return_value=mock_semantic_results):
            result = await analyzer.analyze_precedents(
                query="test treatment analysis"
            )
        
        treatment_analysis = result["treatment_analysis"]
        
        # Check treatment analysis structure
        assert "good_law_cases" in treatment_analysis
        assert "questioned_cases" in treatment_analysis
        assert "overruled_cases" in treatment_analysis
        assert "recent_developments" in treatment_analysis
        assert "trend_analysis" in treatment_analysis
        
        # Check that cases were categorized by status
        assert len(treatment_analysis["good_law_cases"]) >= 1
        assert len(treatment_analysis["questioned_cases"]) >= 1
        
        # Check for recent developments (cases from last 5 years)
        assert len(treatment_analysis["recent_developments"]) >= 1
    
    async def test_confidence_score_calculation(self, analyzer: PrecedentAnalyzer):
        """Test confidence score calculation."""
        # Mock high-quality results
        high_quality_results = [
            {
                "id": f"quality-case-{i}",
                "content": f"High quality case {i}",
                "metadata": {
                    "source_id": f"quality-case-{i}",
                    "authority_score": 9.0,
                    "status": "good_law",
                    "court_id": "us-supreme-court",
                    "jurisdiction": "US"
                },
                "similarity_score": 0.95,
                "document_type": "case"
            }
            for i in range(5)
        ]
        
        with patch.object(analyzer.chroma, 'semantic_search', return_value=high_quality_results):
            result = await analyzer.analyze_precedents(
                query="high quality precedent analysis",
                jurisdiction="US"
            )
        
        # Should have high confidence with many high-authority cases
        assert result["confidence_score"] >= 0.7
        
        # Test with low-quality results
        low_quality_results = [
            {
                "id": "low-case-1",
                "content": "Low quality case",
                "metadata": {
                    "source_id": "low-case-1",
                    "authority_score": 3.0,
                    "status": "questioned"
                },
                "similarity_score": 0.6,
                "document_type": "case"
            }
        ]
        
        with patch.object(analyzer.chroma, 'semantic_search', return_value=low_quality_results):
            result_low = await analyzer.analyze_precedents(
                query="low quality precedent analysis"
            )
        
        # Should have lower confidence
        assert result_low["confidence_score"] < result["confidence_score"]
    
    async def test_error_handling(self, analyzer: PrecedentAnalyzer, mock_services):
        """Test error handling in the workflow."""
        mock_neo4j, mock_chroma = mock_services
        
        # Make semantic search fail
        mock_chroma.semantic_search.side_effect = Exception("ChromaDB connection failed")
        
        result = await analyzer.analyze_precedents(
            query="test error handling"
        )
        
        # Should handle error gracefully
        assert "error" in result
        assert result["confidence_score"] == 0.0
        assert "Analysis failed" in result["precedent_memo"]
    
    async def test_memo_generation_quality(self, analyzer: PrecedentAnalyzer):
        """Test the quality and structure of generated memos."""
        # Mock comprehensive results
        comprehensive_results = [
            {
                "id": "comprehensive-case-1",
                "content": "Comprehensive constitutional law case about equal protection",
                "metadata": {
                    "source_id": "comprehensive-case-1",
                    "title": "Comprehensive v. Analysis",
                    "citation": "123 U.S. 456",
                    "authority_score": 9.5,
                    "status": "good_law",
                    "court_id": "us-supreme-court",
                    "jurisdiction": "US",
                    "summary": "Important constitutional case establishing precedent"
                },
                "similarity_score": 0.95,
                "document_type": "case"
            }
        ]
        
        with patch.object(analyzer.chroma, 'semantic_search', return_value=comprehensive_results):
            result = await analyzer.analyze_precedents(
                query="comprehensive constitutional analysis",
                jurisdiction="US",
                practice_areas=["constitutional", "civil_rights"]
            )
        
        memo = result["precedent_memo"]
        
        # Check memo structure and content
        assert "Executive Summary" in memo
        assert "Key Precedents" in memo
        assert "Authority Assessment" in memo
        assert "Current Legal Status" in memo
        assert "Recommendations" in memo
        
        # Check that specific case information is included
        assert "Comprehensive v. Analysis" in memo or "123 U.S. 456" in memo
        
        # Memo should be substantial
        assert len(memo) > 500  # Should be a comprehensive memo
    
    async def test_workflow_state_progression(self, analyzer: PrecedentAnalyzer):
        """Test that workflow state progresses correctly through all steps."""
        # We'll track the workflow by mocking each step and checking the state
        original_semantic_search = analyzer._semantic_search
        original_citation_analysis = analyzer._citation_analysis
        original_filter_relevance = analyzer._filter_relevance
        original_analyze_authority = analyzer._analyze_authority
        original_analyze_treatment = analyzer._analyze_treatment
        original_generate_memo = analyzer._generate_memo
        
        steps_executed = []
        
        async def track_semantic_search(state):
            steps_executed.append("semantic_search")
            state["current_step"] = "semantic_search"
            state["semantic_results"] = []
            return state
        
        async def track_citation_analysis(state):
            steps_executed.append("citation_analysis")
            state["current_step"] = "citation_analysis"
            state["citation_results"] = []
            return state
        
        async def track_filter_relevance(state):
            steps_executed.append("filter_relevance")
            state["current_step"] = "filter_relevance"
            state["relevant_precedents"] = []
            return state
        
        async def track_analyze_authority(state):
            steps_executed.append("analyze_authority")
            state["current_step"] = "analyze_authority"
            state["authority_analysis"] = {"supreme_court_cases": [], "appellate_cases": [], "binding_precedents": [], "persuasive_precedents": [], "average_authority_score": 0.0}
            return state
        
        async def track_analyze_treatment(state):
            steps_executed.append("analyze_treatment")
            state["current_step"] = "analyze_treatment"
            state["treatment_analysis"] = {"good_law_cases": [], "questioned_cases": [], "overruled_cases": [], "recent_developments": [], "trend_analysis": ""}
            return state
        
        async def track_generate_memo(state):
            steps_executed.append("generate_memo")
            state["current_step"] = "generate_memo"
            state["precedent_memo"] = "Test memo generated"
            state["confidence_score"] = 0.5
            return state
        
        # Patch all the workflow methods
        analyzer._semantic_search = track_semantic_search
        analyzer._citation_analysis = track_citation_analysis
        analyzer._filter_relevance = track_filter_relevance
        analyzer._analyze_authority = track_analyze_authority
        analyzer._analyze_treatment = track_analyze_treatment
        analyzer._generate_memo = track_generate_memo
        
        try:
            await analyzer.analyze_precedents("test workflow progression")
            
            # Check that all steps were executed in the correct order
            expected_steps = [
                "semantic_search",
                "citation_analysis", 
                "filter_relevance",
                "analyze_authority",
                "analyze_treatment",
                "generate_memo"
            ]
            
            assert steps_executed == expected_steps
            
        finally:
            # Restore original methods
            analyzer._semantic_search = original_semantic_search
            analyzer._citation_analysis = original_citation_analysis
            analyzer._filter_relevance = original_filter_relevance
            analyzer._analyze_authority = original_analyze_authority
            analyzer._analyze_treatment = original_analyze_treatment
            analyzer._generate_memo = original_generate_memo


@pytest.mark.agent
@pytest.mark.slow
class TestPrecedentAnalyzerPerformance:
    """Performance tests for PrecedentAnalyzer."""
    
    async def test_analysis_performance(self, mock_services):
        """Test that analysis completes within reasonable time."""
        import time
        
        mock_neo4j, mock_chroma = mock_services
        
        # Set up large mock result sets
        large_semantic_results = [
            {
                "id": f"perf-case-{i}",
                "content": f"Performance test case {i}",
                "metadata": {"source_id": f"perf-case-{i}", "authority_score": 8.0},
                "similarity_score": 0.8,
                "document_type": "case"
            }
            for i in range(50)
        ]
        
        mock_chroma.semantic_search.return_value = large_semantic_results[:20]  # Limit to 20 as per service
        mock_neo4j.find_cases_by_criteria.return_value = []
        
        analyzer = PrecedentAnalyzer(
            neo4j_service=mock_neo4j,
            chroma_service=mock_chroma,
            anthropic_api_key="test-key"
        )
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "Performance test memo generated quickly"
        analyzer.llm.ainvoke = AsyncMock(return_value=mock_response)
        
        start_time = time.time()
        
        result = await analyzer.analyze_precedents(
            query="performance test query with many results"
        )
        
        end_time = time.time()
        
        # Should complete within reasonable time even with many results
        assert (end_time - start_time) < 30.0  # 30 seconds max
        assert result["confidence_score"] >= 0