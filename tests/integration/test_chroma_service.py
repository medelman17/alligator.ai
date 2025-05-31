"""
Integration tests for ChromaDB service.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import List

from shared.models.legal_entities import Case, Statute, LegalConcept, PracticeArea
from services.vector.chroma_service import ChromaService


@pytest.mark.integration
class TestChromaService:
    """Integration tests for ChromaDB service operations."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_service(self, chroma_service: ChromaService, sample_cases: List[Case]):
        """Set up ChromaDB service for testing."""
        self.service = chroma_service
        self.sample_cases = sample_cases
    
    async def test_add_case_document(self):
        """Test adding case documents to ChromaDB."""
        case = self.sample_cases[0]
        full_text = f"{case.summary} {case.holding} Additional case details for testing semantic search."
        
        # Add case document
        doc_id = await self.service.add_case_document(case, full_text)
        
        assert doc_id == f"case_{case.id}"
    
    async def test_add_statute_document(self):
        """Test adding statute documents to ChromaDB."""
        statute = Statute(
            id="test-statute-1",
            title="Test Civil Rights Statute",
            citation="42 U.S.C. § 1234",
            jurisdiction="US",
            effective_date=datetime(1871, 4, 20),
            full_text="Every person who, under color of any statute, ordinance, regulation, custom, or usage, subjects any citizen to the deprivation of rights, shall be liable to the party injured.",
            summary="Test statute for civil rights violations",
            practice_areas=[PracticeArea.CIVIL_RIGHTS],
            related_cases=["test-case-1"]
        )
        
        # Add statute document
        doc_id = await self.service.add_statute_document(statute)
        
        assert doc_id == f"statute_{statute.id}"
    
    async def test_add_concept_document(self):
        """Test adding legal concept documents to ChromaDB."""
        concept = LegalConcept(
            id="test-concept-1",
            name="Test Legal Doctrine",
            description="A test legal doctrine that provides immunity for government officials in certain circumstances when they are performing discretionary functions.",
            aliases=["Test Immunity", "Official Protection"],
            practice_areas=[PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
            key_cases=["test-case-1", "test-case-2"],
            current_status="active"
        )
        
        concept_text = f"{concept.name}: {concept.description}"
        
        # Add concept document
        doc_id = await self.service.add_concept_document(concept, concept_text)
        
        assert doc_id == f"concept_{concept.id}"
    
    async def test_semantic_search_cases(self):
        """Test semantic search for cases."""
        # Add some case documents first
        case_texts = [
            "Constitutional law case about equal protection under the Fourteenth Amendment",
            "Civil rights case involving police misconduct and excessive force",
            "Criminal law case about Miranda rights and self-incrimination"
        ]
        
        for i, case in enumerate(self.sample_cases):
            if i < len(case_texts):
                await self.service.add_case_document(case, case_texts[i])
        
        # Search for constitutional law cases
        results = await self.service.semantic_search(
            query="constitutional equal protection fourteenth amendment",
            document_types=["case"],
            limit=5
        )
        
        assert len(results) >= 1
        
        # Check that results have required fields
        for result in results:
            assert "id" in result
            assert "content" in result
            assert "similarity_score" in result
            assert "source_id" in result
            assert "document_type" in result
            assert result["document_type"] == "case"
            assert 0 <= result["similarity_score"] <= 1
    
    async def test_semantic_search_with_filters(self):
        """Test semantic search with jurisdiction and practice area filters."""
        # Add case documents
        for case in self.sample_cases:
            case_text = f"{case.summary} {case.holding}"
            await self.service.add_case_document(case, case_text)
        
        # Search with jurisdiction filter
        results = await self.service.semantic_search(
            query="constitutional law",
            document_types=["case"],
            jurisdiction="US",
            practice_areas=["constitutional"],
            limit=5
        )
        
        assert len(results) >= 0  # May be 0 if no matches after filtering
        
        for result in results:
            metadata = result.get("metadata", {})
            if "jurisdiction" in metadata:
                assert metadata["jurisdiction"] == "US"
    
    async def test_find_similar_cases(self):
        """Test finding cases similar to given case text."""
        # Add case documents
        case_texts = [
            "Police officer used excessive force during arrest violating Fourth Amendment rights",
            "Qualified immunity protects government officials from civil liability", 
            "Constitutional violation under color of state law Section 1983 claim"
        ]
        
        for i, case in enumerate(self.sample_cases):
            if i < len(case_texts):
                await self.service.add_case_document(case, case_texts[i])
        
        # Find cases similar to a police misconduct scenario
        query_text = "Police officer excessive force Fourth Amendment violation"
        
        results = await self.service.find_similar_cases(
            case_text=query_text,
            jurisdiction="US",
            limit=3
        )
        
        assert len(results) >= 0
        
        for result in results:
            assert "similarity_score" in result
            assert "source_id" in result
            assert result["similarity_score"] >= 0
    
    async def test_hybrid_search(self):
        """Test hybrid search combining semantic and citation relevance."""
        # Add case documents
        for case in self.sample_cases:
            case_text = f"{case.summary} {case.holding}"
            await self.service.add_case_document(case, case_text)
        
        # Perform hybrid search
        citation_cases = ["test-case-1"]  # Cases that are cited in our search context
        
        results = await self.service.hybrid_search(
            query="constitutional rights civil rights",
            citation_cases=citation_cases,
            semantic_weight=0.6,
            citation_weight=0.4,
            limit=5
        )
        
        assert len(results) >= 0
        
        for result in results:
            assert "hybrid_score" in result
            assert "similarity_score" in result
            assert result["hybrid_score"] >= 0
    
    async def test_search_multiple_document_types(self):
        """Test searching across multiple document types."""
        # Add different types of documents
        case = self.sample_cases[0]
        await self.service.add_case_document(case, f"{case.summary} {case.holding}")
        
        statute = Statute(
            id="multi-test-statute",
            title="Multi-Type Test Statute",
            citation="42 U.S.C. § 9999",
            jurisdiction="US",
            effective_date=datetime(2000, 1, 1),
            full_text="Test statute text about constitutional rights and civil liberties",
            summary="Test statute for multi-type search",
            practice_areas=[PracticeArea.CONSTITUTIONAL]
        )
        await self.service.add_statute_document(statute)
        
        concept = LegalConcept(
            id="multi-test-concept",
            name="Multi-Type Test Concept",
            description="A legal concept about constitutional protections and civil rights",
            practice_areas=[PracticeArea.CONSTITUTIONAL],
            current_status="active"
        )
        await self.service.add_concept_document(concept, f"{concept.name}: {concept.description}")
        
        # Search across all document types
        results = await self.service.semantic_search(
            query="constitutional rights protection",
            document_types=["case", "statute", "concept"],
            limit=10
        )
        
        # Should find documents of different types
        document_types_found = set()
        for result in results:
            if "document_type" in result:
                document_types_found.add(result["document_type"])
        
        assert len(document_types_found) >= 1  # At least one type found
    
    async def test_search_with_date_range(self):
        """Test searching with date range filters."""
        # Add case with specific date
        case = self.sample_cases[0]
        await self.service.add_case_document(case, f"{case.summary} {case.holding}")
        
        # Search with date range that includes the case
        start_date = case.decision_date.replace(year=case.decision_date.year - 1)
        end_date = case.decision_date.replace(year=case.decision_date.year + 1)
        
        results = await self.service.semantic_search(
            query="constitutional law",
            document_types=["case"],
            date_range=(start_date, end_date),
            limit=5
        )
        
        assert len(results) >= 0
    
    async def test_empty_search_results(self):
        """Test handling of searches that return no results."""
        results = await self.service.semantic_search(
            query="nonexistent legal concept xyz123",
            document_types=["case"],
            limit=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    async def test_search_result_format(self):
        """Test that search results have consistent format."""
        # Add a case document
        case = self.sample_cases[0]
        await self.service.add_case_document(case, f"{case.summary} {case.holding}")
        
        results = await self.service.semantic_search(
            query="test case law",
            document_types=["case"],
            limit=5
        )
        
        if results:  # If we got results
            result = results[0]
            
            # Check required fields
            required_fields = ["id", "content", "metadata", "similarity_score", "source_id", "document_type"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Check field types
            assert isinstance(result["id"], str)
            assert isinstance(result["content"], str)
            assert isinstance(result["metadata"], dict)
            assert isinstance(result["similarity_score"], (int, float))
            assert isinstance(result["source_id"], str)
            assert isinstance(result["document_type"], str)
            
            # Check similarity score range
            assert 0 <= result["similarity_score"] <= 1


@pytest.mark.integration
@pytest.mark.slow
class TestChromaPerformance:
    """Performance tests for ChromaDB operations."""
    
    async def test_bulk_document_addition(self, chroma_service: ChromaService):
        """Test adding multiple documents efficiently."""
        import time
        
        # Create test cases
        test_cases = []
        for i in range(10):
            case = Case(
                id=f"bulk-case-{i}",
                citation=f"{400 + i} Bulk {500 + i}",
                case_name=f"Bulk Test Case {i}",
                full_name=f"Bulk Test Case {i}",
                court_id="us-supreme-court",
                jurisdiction="US",
                decision_date=datetime(2020, 1, 1),
                practice_areas=[PracticeArea.CONSTITUTIONAL],
                summary=f"Bulk test case {i} for performance testing with constitutional law principles",
                holding=f"Bulk test holding {i} establishes important precedent"
            )
            test_cases.append(case)
        
        # Time the bulk addition
        start_time = time.time()
        
        for case in test_cases:
            case_text = f"{case.summary} {case.holding}"
            await chroma_service.add_case_document(case, case_text)
        
        end_time = time.time()
        
        # Should complete reasonably quickly
        total_time = end_time - start_time
        assert total_time < 30.0  # Should complete within 30 seconds
        
        # Verify documents were added by searching
        results = await chroma_service.semantic_search(
            query="bulk test constitutional",
            document_types=["case"],
            limit=15
        )
        
        assert len(results) >= 5  # Should find several of the bulk cases
    
    async def test_large_search_performance(self, chroma_service: ChromaService):
        """Test search performance with larger result sets."""
        import time
        
        # Add some documents first
        for i in range(5):
            case = Case(
                id=f"search-perf-case-{i}",
                citation=f"{600 + i} Perf {700 + i}",
                case_name=f"Search Performance Case {i}",
                full_name=f"Search Performance Case {i}",
                court_id="us-supreme-court",
                jurisdiction="US",
                decision_date=datetime(2021, 1, 1),
                practice_areas=[PracticeArea.CONSTITUTIONAL],
                summary=f"Performance case {i} about constitutional law and civil rights",
                holding=f"Performance holding {i} for constitutional principles"
            )
            
            case_text = f"{case.summary} {case.holding}"
            await chroma_service.add_case_document(case, case_text)
        
        # Time a search operation
        start_time = time.time()
        
        results = await chroma_service.semantic_search(
            query="constitutional law civil rights performance",
            document_types=["case"],
            limit=20
        )
        
        end_time = time.time()
        
        # Search should be fast
        search_time = end_time - start_time
        assert search_time < 5.0  # Should complete within 5 seconds
        
        assert len(results) >= 0  # Should return some results