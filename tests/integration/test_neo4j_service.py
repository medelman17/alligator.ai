"""
Integration tests for Neo4j service.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import List

from shared.models.legal_entities import Case, Court, Judge, Citation, PracticeArea, CaseStatus, CitationTreatment, CourtLevel
from services.graph.neo4j_service import Neo4jService


@pytest.mark.integration
class TestNeo4jService:
    """Integration tests for Neo4j service operations."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_test_data(self, neo4j_service: Neo4jService, sample_cases: List[Case], sample_citations: List[Citation]):
        """Set up test data for each test."""
        self.service = neo4j_service
        
        # Create test courts first
        test_court = Court(
            id="us-supreme-court",
            name="Supreme Court of the United States",
            short_name="SCOTUS",
            level=CourtLevel.SUPREME_COURT,
            jurisdiction="US",
            authority_weight=10.0
        )
        await self.service.create_court(test_court)
        
        appellate_court = Court(
            id="us-ca-9",
            name="United States Court of Appeals for the Ninth Circuit",
            short_name="9th Cir.",
            level=CourtLevel.APPELLATE,
            jurisdiction="US-9",
            parent_court_id="us-supreme-court",
            authority_weight=8.0
        )
        await self.service.create_court(appellate_court)
        
        # Store sample data for tests
        self.sample_cases = sample_cases
        self.sample_citations = sample_citations
    
    async def test_create_and_find_case(self):
        """Test creating and finding a case."""
        # Create a case
        case = self.sample_cases[0]
        created_case = await self.service.create_case(case)
        
        assert created_case.id == case.id
        assert created_case.case_name == case.case_name
        
        # Find the case by citation
        found_case = await self.service.find_case_by_citation(case.citation)
        
        assert found_case is not None
        assert found_case.id == case.id
        assert found_case.citation == case.citation
        assert found_case.case_name == case.case_name
    
    async def test_case_not_found(self):
        """Test finding a non-existent case."""
        found_case = await self.service.find_case_by_citation("999 U.S. 999")
        assert found_case is None
    
    async def test_create_citation_relationship(self):
        """Test creating citation relationships between cases."""
        # Create both cases first
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        # Create citation relationship
        citation = self.sample_citations[0]
        created_citation = await self.service.create_citation(citation)
        
        assert created_citation.id == citation.id
        assert created_citation.citing_case_id == citation.citing_case_id
        assert created_citation.cited_case_id == citation.cited_case_id
        assert created_citation.treatment == citation.treatment
    
    async def test_get_citing_cases(self):
        """Test retrieving cases that cite a given case."""
        # Set up cases and citation
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        citation = self.sample_citations[0]
        await self.service.create_citation(citation)
        
        # Get citing cases
        citing_cases = await self.service.get_citing_cases(citation.cited_case_id)
        
        assert len(citing_cases) == 1
        citing_case, citation_rel = citing_cases[0]
        assert citing_case.id == citation.citing_case_id
        assert citation_rel.treatment == citation.treatment
    
    async def test_get_cited_cases(self):
        """Test retrieving cases cited by a given case."""
        # Set up cases and citation
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        citation = self.sample_citations[0]
        await self.service.create_citation(citation)
        
        # Get cited cases
        cited_cases = await self.service.get_cited_cases(citation.citing_case_id)
        
        assert len(cited_cases) == 1
        cited_case, citation_rel = cited_cases[0]
        assert cited_case.id == citation.cited_case_id
        assert citation_rel.treatment == citation.treatment
    
    async def test_find_cases_by_jurisdiction(self):
        """Test finding cases by jurisdiction."""
        # Create cases with different jurisdictions
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        # Find US jurisdiction cases
        us_cases = await self.service.find_cases_by_criteria(jurisdiction="US")
        
        assert len(us_cases) >= 1
        for case in us_cases:
            assert case.jurisdiction == "US"
    
    async def test_find_cases_by_practice_area(self):
        """Test finding cases by practice area."""
        # Create cases
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        # Find constitutional law cases
        constitutional_cases = await self.service.find_cases_by_criteria(
            practice_areas=["constitutional"]
        )
        
        assert len(constitutional_cases) >= 1
        for case in constitutional_cases:
            assert "constitutional" in [area.value for area in case.practice_areas]
    
    async def test_find_cases_by_date_range(self):
        """Test finding cases by date range."""
        # Create cases
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        # Find cases from 2020-2022
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2022, 12, 31)
        
        recent_cases = await self.service.find_cases_by_criteria(
            date_range=(start_date, end_date)
        )
        
        assert len(recent_cases) >= 1
        for case in recent_cases:
            assert start_date <= case.decision_date <= end_date
    
    async def test_traverse_citation_network(self):
        """Test citation network traversal."""
        # Create a chain of citations: case1 <- case2 <- case3
        case3 = Case(
            id="test-case-3",
            citation="789 U.S. 012",
            case_name="Third v. Case",
            full_name="Third v. Case",
            court_id="us-supreme-court",
            jurisdiction="US",
            decision_date=datetime(2022, 1, 1),
            practice_areas=[PracticeArea.CONSTITUTIONAL]
        )
        
        # Create all cases
        for case in self.sample_cases + [case3]:
            await self.service.create_case(case)
        
        # Create citations: case2 cites case1, case3 cites case2
        citation1 = self.sample_citations[0]  # case2 cites case1
        await self.service.create_citation(citation1)
        
        citation2 = Citation(
            id="citation-2",
            citing_case_id="test-case-3",
            cited_case_id="test-case-2",
            treatment=CitationTreatment.FOLLOWS,
            context="Following appellate decision",
            strength=0.7
        )
        await self.service.create_citation(citation2)
        
        # Traverse network from case1
        network_results = await self.service.traverse_citation_network(
            "test-case-1", max_depth=3, limit=10
        )
        
        assert len(network_results) >= 2
        
        # Check that we found the related cases
        found_case_ids = [result["case"].id for result in network_results]
        assert "test-case-2" in found_case_ids
        assert "test-case-3" in found_case_ids
    
    async def test_create_court(self):
        """Test creating court entities."""
        court = Court(
            id="test-district-court",
            name="Test District Court",
            short_name="TDC",
            level=CourtLevel.DISTRICT,
            jurisdiction="TEST",
            parent_court_id="us-supreme-court",
            authority_weight=6.0
        )
        
        created_court = await self.service.create_court(court)
        
        assert created_court.id == court.id
        assert created_court.name == court.name
        assert created_court.level == court.level
        assert created_court.authority_weight == court.authority_weight
    
    async def test_create_judge(self):
        """Test creating judge entities."""
        judge = Judge(
            id="test-judge-1",
            name="Justice Test",
            courts=["us-supreme-court"],
            appointment_date=datetime(2010, 1, 1),
            tenure_start=datetime(2010, 1, 1),
            appointing_authority="President Test",
            judicial_philosophy="moderate"
        )
        
        created_judge = await self.service.create_judge(judge)
        
        assert created_judge.id == judge.id
        assert created_judge.name == judge.name
        assert created_judge.judicial_philosophy == judge.judicial_philosophy
    
    async def test_health_check(self):
        """Test service health check."""
        is_healthy = await self.service.health_check()
        assert is_healthy is True
    
    async def test_multiple_citations_same_case(self):
        """Test handling multiple citations to the same case."""
        # Create cases
        for case in self.sample_cases:
            await self.service.create_case(case)
        
        # Create multiple citations from case2 to case1
        citation1 = Citation(
            id="citation-1a",
            citing_case_id="test-case-2",
            cited_case_id="test-case-1",
            treatment=CitationTreatment.FOLLOWS,
            context="Following constitutional holding",
            strength=0.9
        )
        
        citation2 = Citation(
            id="citation-1b", 
            citing_case_id="test-case-2",
            cited_case_id="test-case-1",
            treatment=CitationTreatment.EXPLAINS,
            context="Explaining rationale",
            strength=0.7
        )
        
        await self.service.create_citation(citation1)
        await self.service.create_citation(citation2)
        
        # Get citing relationships
        citing_cases = await self.service.get_citing_cases("test-case-1")
        
        # Should find both citations
        assert len(citing_cases) == 2
        
        treatments = [citation_rel.treatment for _, citation_rel in citing_cases]
        assert CitationTreatment.FOLLOWS in treatments
        assert CitationTreatment.EXPLAINS in treatments
    
    async def test_case_update(self):
        """Test updating an existing case."""
        # Create initial case
        case = self.sample_cases[0]
        await self.service.create_case(case)
        
        # Update the case with new information
        updated_case = Case(
            id=case.id,
            citation=case.citation,
            case_name=case.case_name,
            full_name=case.full_name,
            court_id=case.court_id,
            jurisdiction=case.jurisdiction,
            decision_date=case.decision_date,
            judges=case.judges,
            status=CaseStatus.QUESTIONED,  # Change status
            practice_areas=case.practice_areas,
            summary="Updated summary with new information",  # Update summary
            holding=case.holding,
            authority_score=7.5  # Lower authority score
        )
        
        # Create (update) the case again
        result = await self.service.create_case(updated_case)
        
        # Verify the case was updated
        found_case = await self.service.find_case_by_citation(case.citation)
        assert found_case.status == CaseStatus.QUESTIONED
        assert found_case.summary == "Updated summary with new information"
        assert found_case.authority_score == 7.5


@pytest.mark.integration
@pytest.mark.slow
class TestNeo4jPerformance:
    """Performance tests for Neo4j operations."""
    
    async def test_large_citation_network_traversal(self, neo4j_service: Neo4jService):
        """Test performance with larger citation networks."""
        # This would be expanded in a real test suite
        # For now, just ensure the basic operation works
        
        # Create a few cases
        cases = []
        for i in range(5):
            case = Case(
                id=f"perf-case-{i}",
                citation=f"{100 + i} Perf. {200 + i}",
                case_name=f"Performance Case {i}",
                full_name=f"Performance Case {i}",
                court_id="us-supreme-court",
                jurisdiction="US",
                decision_date=datetime(2020 + i, 1, 1),
                practice_areas=[PracticeArea.CONSTITUTIONAL]
            )
            cases.append(case)
            await neo4j_service.create_case(case)
        
        # Create citations between them
        for i in range(1, 5):
            citation = Citation(
                id=f"perf-citation-{i}",
                citing_case_id=f"perf-case-{i}",
                cited_case_id=f"perf-case-{i-1}",
                treatment=CitationTreatment.FOLLOWS,
                strength=0.8
            )
            await neo4j_service.create_citation(citation)
        
        # Test traversal performance
        import time
        start_time = time.time()
        
        results = await neo4j_service.traverse_citation_network(
            "perf-case-0", max_depth=3, limit=20
        )
        
        end_time = time.time()
        
        # Should complete reasonably quickly (under 1 second for small network)
        assert (end_time - start_time) < 1.0
        assert len(results) >= 4  # Should find the 4 related cases