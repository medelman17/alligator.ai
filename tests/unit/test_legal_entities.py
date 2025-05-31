"""
Unit tests for legal entity models.
"""

import pytest
from datetime import datetime, timezone
from typing import List

from shared.models.legal_entities import (
    Case, Court, Judge, Citation, LegalConcept, Statute, ChromaDocument,
    CourtLevel, CaseStatus, CitationTreatment, PracticeArea
)


@pytest.mark.unit
class TestCase:
    """Test Case model."""
    
    def test_case_creation(self):
        """Test basic case creation."""
        case = Case(
            id="test-case-1",
            citation="123 U.S. 456",
            case_name="Test v. Example",
            full_name="Test Plaintiff v. Example Defendant",
            court_id="us-supreme-court",
            jurisdiction="US",
            decision_date=datetime(2020, 1, 15),
            judges=["Justice Test"],
            status=CaseStatus.GOOD_LAW,
            practice_areas=[PracticeArea.CONSTITUTIONAL],
            summary="A test case for constitutional law principles.",
            holding="The test holding establishes important precedent.",
            authority_score=9.2,
            citation_count=150
        )
        
        assert case.id == "test-case-1"
        assert case.citation == "123 U.S. 456"
        assert case.case_name == "Test v. Example"
        assert case.jurisdiction == "US"
        assert case.status == CaseStatus.GOOD_LAW
        assert PracticeArea.CONSTITUTIONAL in case.practice_areas
        assert case.authority_score == 9.2
        assert case.citation_count == 150
        assert isinstance(case.decision_date, datetime)
    
    def test_case_defaults(self):
        """Test case creation with default values."""
        case = Case(
            id="minimal-case",
            citation="456 U.S. 789",
            case_name="Minimal v. Case",
            full_name="Minimal v. Case",
            court_id="test-court",
            jurisdiction="US",
            decision_date=datetime.now()
        )
        
        assert case.status == CaseStatus.GOOD_LAW
        assert case.judges == []
        assert case.practice_areas == []
        assert case.authority_score == 0.0
        assert case.citation_count == 0
        assert case.overruling_cases == []
        assert case.metadata == {}
    
    def test_case_validation(self):
        """Test case validation requirements."""
        # Missing required fields should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            Case()
        
        with pytest.raises(Exception):
            Case(id="test", citation="123 U.S. 456")  # Missing other required fields


@pytest.mark.unit
class TestCourt:
    """Test Court model."""
    
    def test_court_creation(self):
        """Test court creation."""
        court = Court(
            id="test-court",
            name="Test Supreme Court",
            short_name="TSC",
            level=CourtLevel.SUPREME_COURT,
            jurisdiction="TEST",
            parent_court_id=None,
            authority_weight=10.0
        )
        
        assert court.id == "test-court"
        assert court.name == "Test Supreme Court"
        assert court.level == CourtLevel.SUPREME_COURT
        assert court.authority_weight == 10.0
    
    def test_court_hierarchy(self):
        """Test court hierarchy relationships."""
        supreme_court = Court(
            id="supreme",
            name="Supreme Court",
            short_name="SC",
            level=CourtLevel.SUPREME_COURT,
            jurisdiction="US",
            authority_weight=10.0
        )
        
        appellate_court = Court(
            id="appellate",
            name="Court of Appeals",
            short_name="CA",
            level=CourtLevel.APPELLATE,
            jurisdiction="US-9",
            parent_court_id="supreme",
            authority_weight=8.0
        )
        
        assert appellate_court.parent_court_id == supreme_court.id
        assert appellate_court.authority_weight < supreme_court.authority_weight


@pytest.mark.unit
class TestJudge:
    """Test Judge model."""
    
    def test_judge_creation(self):
        """Test judge creation."""
        judge = Judge(
            id="judge-test",
            name="Justice Test",
            courts=["us-supreme-court"],
            appointment_date=datetime(2000, 1, 1),
            tenure_start=datetime(2000, 1, 1),
            tenure_end=datetime(2020, 1, 1),
            appointing_authority="President Test",
            judicial_philosophy="moderate"
        )
        
        assert judge.name == "Justice Test"
        assert "us-supreme-court" in judge.courts
        assert judge.judicial_philosophy == "moderate"


@pytest.mark.unit
class TestCitation:
    """Test Citation model."""
    
    def test_citation_creation(self):
        """Test citation relationship creation."""
        citation = Citation(
            id="citation-1",
            citing_case_id="case-a",
            cited_case_id="case-b",
            treatment=CitationTreatment.FOLLOWS,
            context="Following established precedent in constitutional law",
            page_references=["123", "124-125"],
            quotations=["The court held that..."],
            strength=0.9,
            depth=1
        )
        
        assert citation.citing_case_id == "case-a"
        assert citation.cited_case_id == "case-b"
        assert citation.treatment == CitationTreatment.FOLLOWS
        assert citation.strength == 0.9
        assert "123" in citation.page_references
    
    def test_citation_treatments(self):
        """Test different citation treatments."""
        treatments = [
            CitationTreatment.FOLLOWS,
            CitationTreatment.DISTINGUISHES,
            CitationTreatment.OVERRULES,
            CitationTreatment.CRITICIZES,
            CitationTreatment.EXPLAINS,
            CitationTreatment.CITES
        ]
        
        for treatment in treatments:
            citation = Citation(
                id=f"citation-{treatment.value}",
                citing_case_id="case-a",
                cited_case_id="case-b",
                treatment=treatment
            )
            assert citation.treatment == treatment


@pytest.mark.unit
class TestLegalConcept:
    """Test LegalConcept model."""
    
    def test_concept_creation(self):
        """Test legal concept creation."""
        concept = LegalConcept(
            id="qualified-immunity",
            name="Qualified Immunity",
            description="Legal doctrine protecting government officials",
            aliases=["QI", "Official Immunity"],
            practice_areas=[PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
            key_cases=["case-1", "case-2"],
            current_status="active"
        )
        
        assert concept.name == "Qualified Immunity"
        assert "QI" in concept.aliases
        assert PracticeArea.CIVIL_RIGHTS in concept.practice_areas
        assert concept.current_status == "active"


@pytest.mark.unit
class TestStatute:
    """Test Statute model."""
    
    def test_statute_creation(self):
        """Test statute creation."""
        statute = Statute(
            id="42-usc-1983",
            title="Civil Action for Deprivation of Rights",
            citation="42 U.S.C. § 1983",
            jurisdiction="US",
            effective_date=datetime(1871, 4, 20),
            full_text="Every person who, under color of any statute...",
            summary="Federal civil rights statute",
            practice_areas=[PracticeArea.CIVIL_RIGHTS],
            related_cases=["monroe-v-pape"]
        )
        
        assert statute.citation == "42 U.S.C. § 1983"
        assert statute.jurisdiction == "US"
        assert PracticeArea.CIVIL_RIGHTS in statute.practice_areas
        assert "monroe-v-pape" in statute.related_cases


@pytest.mark.unit
class TestChromaDocument:
    """Test ChromaDocument model."""
    
    def test_chroma_document_creation(self):
        """Test ChromaDB document creation."""
        doc = ChromaDocument(
            id="doc-1",
            content="This is the full text of a legal case...",
            document_type="case",
            title="Test v. Case",
            source_id="case-1",
            jurisdiction="US",
            practice_areas=["constitutional"],
            court_level="supreme_court",
            decision_date=datetime(2020, 1, 1),
            authority_score=9.0
        )
        
        assert doc.document_type == "case"
        assert doc.jurisdiction == "US"
        assert "constitutional" in doc.practice_areas
        assert doc.authority_score == 9.0
    
    def test_chroma_metadata_conversion(self):
        """Test conversion to ChromaDB metadata format."""
        doc = ChromaDocument(
            id="doc-1",
            content="Legal document content",
            document_type="case",
            title="Test Case",
            source_id="case-1",
            jurisdiction="US",
            practice_areas=["civil_rights", "constitutional"],
            court_level="supreme_court",
            decision_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            authority_score=8.5
        )
        
        metadata = doc.to_chroma_metadata()
        
        assert metadata["document_type"] == "case"
        assert metadata["title"] == "Test Case"
        assert metadata["source_id"] == "case-1"
        assert metadata["jurisdiction"] == "US"
        assert metadata["practice_areas"] == "civil_rights,constitutional"
        assert metadata["court_level"] == "supreme_court"
        assert metadata["authority_score"] == 8.5
        assert "decision_date" in metadata
        assert metadata["decision_date"] == "2020-01-01T00:00:00+00:00"


@pytest.mark.unit
class TestEnumValidation:
    """Test enum validation and usage."""
    
    def test_court_levels(self):
        """Test court level enum values."""
        levels = [
            CourtLevel.SUPREME_COURT,
            CourtLevel.APPELLATE,
            CourtLevel.DISTRICT,
            CourtLevel.TRIAL,
            CourtLevel.ADMINISTRATIVE
        ]
        
        for level in levels:
            court = Court(
                id=f"court-{level.value}",
                name=f"Test {level.value} Court",
                short_name=f"T{level.value[0].upper()}C",
                level=level,
                jurisdiction="TEST"
            )
            assert court.level == level
    
    def test_case_statuses(self):
        """Test case status enum values."""
        statuses = [
            CaseStatus.GOOD_LAW,
            CaseStatus.BAD_LAW,
            CaseStatus.QUESTIONED,
            CaseStatus.LIMITED,
            CaseStatus.SUPERSEDED,
            CaseStatus.OVERRULED
        ]
        
        for status in statuses:
            case = Case(
                id=f"case-{status.value}",
                citation=f"123 Test {status.value}",
                case_name=f"Test {status.value} Case",
                full_name=f"Test {status.value} Case",
                court_id="test-court",
                jurisdiction="TEST",
                decision_date=datetime.now(),
                status=status
            )
            assert case.status == status
    
    def test_practice_areas(self):
        """Test practice area enum values."""
        areas = [
            PracticeArea.CIVIL_RIGHTS,
            PracticeArea.EMPLOYMENT,
            PracticeArea.CONSTITUTIONAL,
            PracticeArea.CRIMINAL,
            PracticeArea.CORPORATE,
            PracticeArea.INTELLECTUAL_PROPERTY,
            PracticeArea.LITIGATION,
            PracticeArea.REGULATORY
        ]
        
        for area in areas:
            case = Case(
                id=f"case-{area.value}",
                citation=f"123 {area.value} 456",
                case_name=f"{area.value} Test Case",
                full_name=f"{area.value} Test Case",
                court_id="test-court", 
                jurisdiction="TEST",
                decision_date=datetime.now(),
                practice_areas=[area]
            )
            assert area in case.practice_areas


@pytest.mark.unit
class TestModelIntegration:
    """Test integration between different models."""
    
    def test_case_with_all_relationships(self):
        """Test case model with complete relationship data."""
        case = Case(
            id="complex-case",
            citation="555 U.S. 123",
            case_name="Complex v. Case",
            full_name="Complex Plaintiff v. Case Defendant",
            court_id="us-supreme-court",
            jurisdiction="US",
            decision_date=datetime(2021, 5, 15),
            judges=["Chief Justice", "Associate Justice"],
            status=CaseStatus.GOOD_LAW,
            practice_areas=[
                PracticeArea.CONSTITUTIONAL,
                PracticeArea.CIVIL_RIGHTS,
                PracticeArea.LITIGATION
            ],
            summary="Complex case involving multiple legal issues",
            holding="Establishes multi-part legal standard",
            authority_score=9.8,
            citation_count=750,
            overruling_cases=[],
            metadata={
                "impact": "high",
                "complexity": "complex",
                "citations_per_year": 50
            }
        )
        
        # Test all fields are properly set
        assert len(case.judges) == 2
        assert len(case.practice_areas) == 3
        assert case.metadata["impact"] == "high"
        assert case.overruling_cases == []
        
        # Test the case can be used in citations
        citation = Citation(
            id="citation-to-complex",
            citing_case_id="other-case",
            cited_case_id=case.id,
            treatment=CitationTreatment.FOLLOWS,
            context="Following the multi-part standard",
            strength=0.95
        )
        
        assert citation.cited_case_id == case.id
        assert citation.strength == 0.95