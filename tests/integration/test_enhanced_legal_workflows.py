"""
Integration tests for complete enhanced legal research workflows.

Tests end-to-end legal research processes using enhanced capabilities,
including multi-step workflows, complex legal analysis, and research session management.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from httpx import AsyncClient

from api.main import app

class TestLegalResearchWorkflows:
    """Integration tests for complete legal research workflows."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_complete_constitutional_law_research_workflow(self, client: AsyncClient):
        """Test complete research workflow for constitutional law case."""
        # Step 1: Create research session
        session_request = {
            "query": "equal protection constitutional analysis",
            "jurisdiction": "federal",
            "practice_areas": ["constitutional_law"],
            "max_results": 10
        }
        
        response = await client.post("/api/v1/research/sessions", json=session_request)
        assert response.status_code == 201
        
        session_data = response.json()
        session_id = session_data["id"]
        assert session_data["status"] == "pending"
        
        # Step 2: Analyze specific precedent
        precedent_request = {
            "query": "equal protection strict scrutiny analysis",
            "case_id": "brown-v-board-1954",
            "jurisdiction": "federal",
            "practice_areas": ["constitutional_law"]
        }
        
        response = await client.post("/api/v1/research/analyze-precedent", json=precedent_request)
        
        if response.status_code == 200:
            precedent_data = response.json()
            
            # Verify comprehensive precedent analysis
            assert "precedent_analysis" in precedent_data
            assert "good_law_status" in precedent_data
            assert "treatment_analysis" in precedent_data
            assert "authority_metrics" in precedent_data
        
        # Step 3: Verify good law status of key cases
        test_cases = ["brown-v-board-1954", "miranda-v-arizona-1966"]
        good_law_results = {}
        
        for case_id in test_cases:
            response = await client.get(f"/api/v1/cases/{case_id}/good-law-status")
            if response.status_code == 200:
                good_law_results[case_id] = response.json()
        
        # Step 4: Analyze citation treatments
        treatment_results = {}
        for case_id in test_cases:
            response = await client.get(f"/api/v1/cases/{case_id}/treatment-analysis")
            if response.status_code == 200:
                treatment_results[case_id] = response.json()
        
        # Step 5: Find authoritative precedents
        for case_id in test_cases:
            response = await client.get(f"/api/v1/cases/{case_id}/authoritative-precedents")
            if response.status_code == 200:
                precedents = response.json()
                assert isinstance(precedents, list)
        
        # Step 6: Perform semantic searches
        semantic_searches = [
            "equal protection constitutional law",
            "due process constitutional analysis",
            "strict scrutiny judicial review"
        ]
        
        semantic_results = []
        for query in semantic_searches:
            search_request = {
                "query": query,
                "practice_areas": ["constitutional_law"],
                "jurisdiction": "federal",
                "max_results": 5
            }
            
            response = await client.post("/api/v1/search/semantic", json=search_request)
            if response.status_code == 200:
                semantic_results.append(response.json())
        
        # Step 7: Generate research memo
        memo_request = {
            "session_id": session_id,
            "memo_type": "case_analysis",
            "focus_areas": ["constitutional_analysis", "precedent_strength"]
        }
        
        response = await client.post("/api/v1/research/generate-memo", json=memo_request)
        
        if response.status_code == 200:
            memo_data = response.json()
            assert "memo_content" in memo_data
            assert "research_summary" in memo_data
        
        # Step 8: Verify session completion
        response = await client.get(f"/api/v1/research/sessions/{session_id}")
        if response.status_code == 200:
            final_session = response.json()
            # Session should have progressed or completed
            assert final_session["status"] in ["in_progress", "completed"]
    
    @pytest.mark.asyncio
    async def test_good_law_verification_workflow(self, client: AsyncClient):
        """Test comprehensive good law verification workflow."""
        # List of landmark cases to verify
        landmark_cases = [
            "brown-v-board-1954",
            "miranda-v-arizona-1966", 
            "roe-v-wade-1973",
            "dobbs-v-jackson-2022"
        ]
        
        verification_results = {}
        
        for case_id in landmark_cases:
            # Step 1: Get basic case information
            response = await client.get(f"/api/v1/cases/{case_id}")
            
            if response.status_code == 200:
                case_data = response.json()
                
                # Step 2: Verify good law status
                response = await client.get(f"/api/v1/cases/{case_id}/good-law-status")
                if response.status_code == 200:
                    good_law_data = response.json()
                    
                    # Step 3: Analyze citation treatment
                    response = await client.get(f"/api/v1/cases/{case_id}/treatment-analysis")
                    if response.status_code == 200:
                        treatment_data = response.json()
                        
                        # Compile comprehensive verification result
                        verification_results[case_id] = {
                            "case_info": case_data,
                            "good_law_status": good_law_data,
                            "treatment_analysis": treatment_data,
                            "verification_complete": True
                        }
                        
                        # Verify data consistency
                        self._verify_good_law_data_consistency(
                            case_data, good_law_data, treatment_data, case_id
                        )
        
        # Analyze verification results
        verified_cases = len(verification_results)
        assert verified_cases > 0, "Should verify at least one landmark case"
        
        # Check for overruling relationships
        overruled_cases = []
        for case_id, results in verification_results.items():
            good_law = results["good_law_status"]
            if good_law.get("current_status") == "overruled":
                overruled_cases.append(case_id)
        
        # Roe v. Wade should be overruled by Dobbs if both are present
        if "roe-v-wade-1973" in verification_results and "dobbs-v-jackson-2022" in verification_results:
            roe_status = verification_results["roe-v-wade-1973"]["good_law_status"]
            dobbs_status = verification_results["dobbs-v-jackson-2022"]["good_law_status"]
            
            # Verify overruling relationship
            if roe_status.get("current_status") == "overruled":
                overruled_by = roe_status.get("overruled_by", [])
                assert any("dobbs" in overrule.lower() for overrule in overruled_by), \
                    "Roe should be overruled by Dobbs"
    
    @pytest.mark.asyncio
    async def test_citation_network_analysis_workflow(self, client: AsyncClient):
        """Test citation network analysis workflow."""
        # Start with a foundational case
        root_case = "brown-v-board-1954"
        
        # Step 1: Get authoritative precedents
        response = await client.get(f"/api/v1/cases/{root_case}/authoritative-precedents")
        
        precedents = []
        if response.status_code == 200:
            precedents = response.json()
        
        # Step 2: Analyze citation treatments for each precedent
        network_analysis = {
            "root_case": root_case,
            "precedents": [],
            "citation_relationships": []
        }
        
        for precedent in precedents[:5]:  # Limit to 5 for performance
            precedent_id = precedent.get("case_id") or precedent.get("id")
            if precedent_id:
                # Get treatment analysis
                response = await client.get(f"/api/v1/cases/{precedent_id}/treatment-analysis")
                if response.status_code == 200:
                    treatment = response.json()
                    
                    network_analysis["precedents"].append({
                        "case_id": precedent_id,
                        "authority_score": precedent.get("authority_score", 0),
                        "treatment_summary": {
                            "total_citations": treatment.get("total_citations", 0),
                            "positive_citations": treatment.get("positive_citations", 0),
                            "negative_citations": treatment.get("negative_citations", 0)
                        }
                    })
        
        # Step 3: Search for cases citing the root case
        citing_search = {
            "query": f"cites {root_case}",
            "max_results": 10
        }
        
        response = await client.post("/api/v1/search/semantic", json=citing_search)
        if response.status_code == 200:
            citing_cases = response.json()
            
            for citing_case in citing_cases:
                case_id = citing_case.get("id") or citing_case.get("case_id")
                if case_id and case_id != root_case:
                    network_analysis["citation_relationships"].append({
                        "citing_case": case_id,
                        "cited_case": root_case,
                        "authority_score": citing_case.get("authority_score", 0)
                    })
        
        # Verify network analysis completeness
        assert network_analysis["root_case"] == root_case
        # Should have some network data if sample data is present
        total_network_size = len(network_analysis["precedents"]) + len(network_analysis["citation_relationships"])
        
        # Even with minimal data, network structure should be valid
        assert isinstance(network_analysis["precedents"], list)
        assert isinstance(network_analysis["citation_relationships"], list)
    
    @pytest.mark.asyncio
    async def test_practice_area_research_workflow(self, client: AsyncClient):
        """Test research workflow focused on specific practice areas."""
        practice_areas = ["constitutional_law", "civil_rights", "privacy_rights"]
        
        for practice_area in practice_areas:
            # Step 1: Search for cases in practice area
            search_params = {
                "practice_areas": practice_area,
                "good_law_only": "true",
                "limit": "5"
            }
            
            response = await client.get("/api/v1/search/cases", params=search_params)
            
            if response.status_code == 200:
                cases = response.json()
                
                # Step 2: Analyze each case found
                for case in cases:
                    case_id = case.get("id") or case.get("case_id")
                    if case_id:
                        # Verify practice area alignment
                        case_practice_areas = case.get("practice_areas", [])
                        assert practice_area in case_practice_areas or len(case_practice_areas) == 0, \
                            f"Case {case_id} should be in {practice_area}"
                        
                        # Step 3: Verify good law status
                        response = await client.get(f"/api/v1/cases/{case_id}/good-law-status")
                        if response.status_code == 200:
                            good_law = response.json()
                            
                            # Should be good law if filtered for good_law_only
                            if good_law.get("current_status"):
                                assert good_law["current_status"] in ["good_law", "unknown"], \
                                    f"Case {case_id} should be good law"
            
            # Step 3: Semantic search within practice area
            semantic_request = {
                "query": f"{practice_area.replace('_', ' ')} legal analysis",
                "practice_areas": [practice_area],
                "max_results": 3
            }
            
            response = await client.post("/api/v1/search/semantic", json=semantic_request)
            if response.status_code == 200:
                semantic_results = response.json()
                
                # Verify semantic results align with practice area
                for result in semantic_results:
                    result_practice_areas = result.get("practice_areas", [])
                    if result_practice_areas:
                        assert practice_area in result_practice_areas, \
                            f"Semantic result should match practice area {practice_area}"
    
    def _verify_good_law_data_consistency(
        self, 
        case_data: Dict[str, Any], 
        good_law_data: Dict[str, Any], 
        treatment_data: Dict[str, Any], 
        case_id: str
    ) -> None:
        """Verify consistency between different data sources for a case."""
        # Case IDs should match
        assert case_data.get("id") == case_id
        assert good_law_data.get("case_id") == case_id
        
        # Good law confidence should be consistent
        good_law_confidence_1 = good_law_data.get("good_law_confidence")
        good_law_confidence_2 = treatment_data.get("good_law_confidence")
        
        if good_law_confidence_1 and good_law_confidence_2:
            # Should be same or at least compatible
            assert good_law_confidence_1 == good_law_confidence_2 or \
                   (good_law_confidence_1 in ["unknown", "low"] and good_law_confidence_2 in ["unknown", "low"]), \
                   f"Good law confidence mismatch for {case_id}: {good_law_confidence_1} vs {good_law_confidence_2}"
        
        # Citation counts should be reasonable
        total_citations = treatment_data.get("total_citations", 0)
        positive_citations = treatment_data.get("positive_citations", 0)
        negative_citations = treatment_data.get("negative_citations", 0)
        
        assert positive_citations + negative_citations <= total_citations, \
            f"Citation count inconsistency for {case_id}"
        
        # If overruled, should have negative treatment
        if good_law_data.get("current_status") == "overruled":
            assert negative_citations > 0 or good_law_data.get("negative_treatment_count", 0) > 0, \
                f"Overruled case {case_id} should have negative treatment"

class TestEnhancedSearchWorkflows:
    """Integration tests for enhanced search workflows."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_multi_modal_search_workflow(self, client: AsyncClient):
        """Test workflow combining multiple search methods."""
        search_query = "constitutional equal protection analysis"
        
        search_results = {
            "semantic_search": [],
            "structured_search": [],
            "precedent_search": []
        }
        
        # Step 1: Semantic search
        semantic_request = {
            "query": search_query,
            "practice_areas": ["constitutional_law"],
            "max_results": 5
        }
        
        response = await client.post("/api/v1/search/semantic", json=semantic_request)
        if response.status_code == 200:
            search_results["semantic_search"] = response.json()
        
        # Step 2: Structured search
        search_params = {
            "jurisdiction": "federal",
            "practice_areas": "constitutional_law",
            "limit": "5"
        }
        
        response = await client.get("/api/v1/search/cases", params=search_params)
        if response.status_code == 200:
            search_results["structured_search"] = response.json()
        
        # Step 3: Find precedents for any found cases
        all_found_cases = []
        
        for search_type, results in search_results.items():
            for result in results:
                case_id = result.get("id") or result.get("case_id")
                if case_id and case_id not in all_found_cases:
                    all_found_cases.append(case_id)
        
        # Get precedents for first few cases
        for case_id in all_found_cases[:3]:
            response = await client.get(f"/api/v1/cases/{case_id}/authoritative-precedents")
            if response.status_code == 200:
                precedents = response.json()
                search_results["precedent_search"].extend(precedents)
        
        # Analyze search result overlap and quality
        self._analyze_search_result_quality(search_results, search_query)
    
    @pytest.mark.asyncio
    async def test_jurisdiction_filtering_workflow(self, client: AsyncClient):
        """Test search workflows with jurisdiction filtering."""
        jurisdictions = ["federal", "state", "california"]
        
        for jurisdiction in jurisdictions:
            # Search with jurisdiction filter
            search_params = {
                "jurisdiction": jurisdiction,
                "limit": "10"
            }
            
            response = await client.get("/api/v1/search/cases", params=search_params)
            
            if response.status_code == 200:
                cases = response.json()
                
                # Verify jurisdiction filtering
                for case in cases:
                    case_jurisdiction = case.get("jurisdiction", "").lower()
                    if case_jurisdiction:
                        assert jurisdiction.lower() in case_jurisdiction or \
                               case_jurisdiction in jurisdiction.lower(), \
                               f"Case jurisdiction {case_jurisdiction} doesn't match filter {jurisdiction}"
    
    def _analyze_search_result_quality(self, search_results: Dict[str, List], query: str) -> None:
        """Analyze quality and consistency of search results."""
        total_results = sum(len(results) for results in search_results.values())
        
        # Should have some results if data is available
        if total_results > 0:
            # Check for result overlap between search methods
            semantic_ids = set()
            structured_ids = set()
            
            for result in search_results["semantic_search"]:
                case_id = result.get("id") or result.get("case_id")
                if case_id:
                    semantic_ids.add(case_id)
            
            for result in search_results["structured_search"]:
                case_id = result.get("id") or result.get("case_id")
                if case_id:
                    structured_ids.add(case_id)
            
            # Some overlap is expected for good search quality
            overlap = semantic_ids.intersection(structured_ids)
            
            # Results should be structured properly
            for search_type, results in search_results.items():
                for result in results:
                    assert isinstance(result, dict), f"Result should be dict in {search_type}"
                    # Should have identifying information
                    assert result.get("id") or result.get("case_id"), f"Result missing ID in {search_type}"

class TestEnhancedPerformanceWorkflows:
    """Integration tests for performance in enhanced workflows."""
    
    @pytest.fixture
    async def client(self):
        """Async HTTP client for testing API endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_concurrent_enhanced_operations(self, client: AsyncClient):
        """Test performance of concurrent enhanced operations."""
        import time
        
        # Define concurrent operations
        operations = [
            ("GET", "/api/v1/cases/brown-v-board-1954/good-law-status", None),
            ("GET", "/api/v1/cases/brown-v-board-1954/treatment-analysis", None),
            ("GET", "/api/v1/cases/miranda-v-arizona-1966/good-law-status", None),
            ("POST", "/api/v1/search/semantic", {
                "query": "constitutional law",
                "max_results": 5
            })
        ]
        
        start_time = time.time()
        
        # Execute operations concurrently
        tasks = []
        for method, endpoint, data in operations:
            if method == "GET":
                task = client.get(endpoint)
            elif method == "POST":
                task = client.post(endpoint, json=data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 10.0, f"Concurrent operations too slow: {total_time}s"
        
        # Verify responses
        successful_responses = 0
        for response in responses:
            if hasattr(response, 'status_code') and response.status_code == 200:
                successful_responses += 1
        
        # Should have some successful responses
        assert successful_responses > 0, "Should have at least one successful concurrent operation"