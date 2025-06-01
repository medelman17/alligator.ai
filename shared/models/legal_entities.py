"""
Core legal entity models for the citation graph platform.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class CourtLevel(str, Enum):
    """Court hierarchy levels for authority scoring."""
    SUPREME_COURT = "supreme_court"
    APPELLATE = "appellate"
    DISTRICT = "district"
    TRIAL = "trial"
    ADMINISTRATIVE = "administrative"


class CaseStatus(str, Enum):
    """Legal status of a case."""
    GOOD_LAW = "good_law"
    BAD_LAW = "bad_law"
    QUESTIONED = "questioned"
    LIMITED = "limited"
    SUPERSEDED = "superseded"
    OVERRULED = "overruled"


class CitationTreatment(str, Enum):
    """How one case treats another in citations."""
    FOLLOWS = "follows"
    DISTINGUISHES = "distinguishes"
    OVERRULES = "overrules"
    CRITICIZES = "criticizes"
    EXPLAINS = "explains"
    CITES = "cites"


class PracticeArea(str, Enum):
    """Legal practice areas."""
    CIVIL_RIGHTS = "civil_rights"
    EMPLOYMENT = "employment"
    CONSTITUTIONAL = "constitutional"
    CONSTITUTIONAL_LAW = "constitutional_law"  # Added for compatibility
    CRIMINAL = "criminal"
    CRIMINAL_LAW = "criminal_law"  # Added for compatibility
    CORPORATE = "corporate"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    LITIGATION = "litigation"
    REGULATORY = "regulatory"
    EDUCATION = "education"  # Added for compatibility
    PRIVACY_RIGHTS = "privacy_rights"  # Added for compatibility
    REPRODUCTIVE_RIGHTS = "reproductive_rights"  # Added for compatibility
    FEDERALISM = "federalism"  # Added for compatibility
    PROCEDURE = "procedure"  # Added for compatibility
    TRANSPORTATION = "transportation"  # Added for compatibility


class Case(BaseModel):
    """Legal case entity."""
    id: str = Field(..., description="Unique case identifier")
    citation: str = Field(..., description="Legal citation (e.g., '347 U.S. 483')")
    case_name: str = Field(..., description="Case name (e.g., 'Brown v. Board')")
    full_name: str = Field(..., description="Full case name with parties")
    court_id: str = Field(..., description="Court identifier")
    jurisdiction: str = Field(..., description="Jurisdiction code (e.g., 'US', 'CA-9')")
    decision_date: datetime = Field(..., description="Date case was decided")
    filing_date: Optional[datetime] = Field(None, description="Date case was filed")
    judges: List[str] = Field(default_factory=list, description="Judge names")
    status: CaseStatus = Field(default=CaseStatus.GOOD_LAW, description="Current legal status")
    practice_areas: List[PracticeArea] = Field(default_factory=list, description="Practice areas")
    summary: Optional[str] = Field(None, description="Case summary")
    holding: Optional[str] = Field(None, description="Legal holding")
    procedural_posture: Optional[str] = Field(None, description="Procedural context")
    disposition: Optional[str] = Field(None, description="Case outcome")
    authority_score: float = Field(default=0.0, description="PageRank authority score")
    citation_count: int = Field(default=0, description="Number of citing cases")
    overruling_cases: List[str] = Field(default_factory=list, description="Cases that overrule this one")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Court(BaseModel):
    """Court entity."""
    id: str = Field(..., description="Unique court identifier")
    name: str = Field(..., description="Court name")
    short_name: str = Field(..., description="Court abbreviation")
    level: CourtLevel = Field(..., description="Court level in hierarchy")
    jurisdiction: str = Field(..., description="Jurisdiction code")
    parent_court_id: Optional[str] = Field(None, description="Parent court in hierarchy")
    established_date: Optional[datetime] = Field(None, description="Court establishment date")
    authority_weight: float = Field(default=1.0, description="Weight for authority calculations")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Judge(BaseModel):
    """Judge entity."""
    id: str = Field(..., description="Unique judge identifier")
    name: str = Field(..., description="Judge full name")
    courts: List[str] = Field(default_factory=list, description="Court IDs where judge serves")
    appointment_date: Optional[datetime] = Field(None, description="Appointment date")
    tenure_start: Optional[datetime] = Field(None, description="Start of current position")
    tenure_end: Optional[datetime] = Field(None, description="End of position (if applicable)")
    appointing_authority: Optional[str] = Field(None, description="Who appointed the judge")
    judicial_philosophy: Optional[str] = Field(None, description="Known judicial leanings")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """Citation relationship between cases."""
    id: str = Field(..., description="Unique citation identifier")
    citing_case_id: str = Field(..., description="Case making the citation")
    cited_case_id: str = Field(..., description="Case being cited")
    treatment: CitationTreatment = Field(..., description="How the citing case treats the cited case")
    context: Optional[str] = Field(None, description="Context of the citation")
    page_references: List[str] = Field(default_factory=list, description="Specific page references")
    quotations: List[str] = Field(default_factory=list, description="Direct quotations")
    strength: float = Field(default=1.0, description="Citation strength/importance (0-1)")
    depth: int = Field(default=1, description="Citation depth (1=primary, 2=secondary, etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LegalConcept(BaseModel):
    """Legal concept or doctrine."""
    id: str = Field(..., description="Unique concept identifier")
    name: str = Field(..., description="Concept name")
    description: str = Field(..., description="Concept description")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    practice_areas: List[PracticeArea] = Field(default_factory=list, description="Related practice areas")
    key_cases: List[str] = Field(default_factory=list, description="Foundational case IDs")
    evolution_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="How concept evolved")
    current_status: str = Field(default="active", description="Current status of the concept")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Statute(BaseModel):
    """Statute or regulation."""
    id: str = Field(..., description="Unique statute identifier")
    title: str = Field(..., description="Statute title")
    citation: str = Field(..., description="Legal citation (e.g., '42 U.S.C. § 1983')")
    jurisdiction: str = Field(..., description="Jurisdiction code")
    effective_date: datetime = Field(..., description="Date statute became effective")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date if applicable")
    full_text: str = Field(..., description="Full text of the statute")
    summary: Optional[str] = Field(None, description="Summary of the statute")
    practice_areas: List[PracticeArea] = Field(default_factory=list, description="Related practice areas")
    related_cases: List[str] = Field(default_factory=list, description="Key interpreting cases")
    amendments: List[Dict[str, Any]] = Field(default_factory=list, description="Amendment history")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchQuery(BaseModel):
    """Research query entity."""
    id: str = Field(..., description="Unique query identifier")
    user_id: str = Field(..., description="User who made the query")
    query_text: str = Field(..., description="Natural language query")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction filter")
    practice_areas: List[PracticeArea] = Field(default_factory=list, description="Practice area filters")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")
    results_found: int = Field(default=0, description="Number of results returned")
    success_score: Optional[float] = Field(None, description="User-rated query success")
    execution_time: Optional[float] = Field(None, description="Query execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChromaDocument(BaseModel):
    """Document for ChromaDB storage."""
    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document text content")
    document_type: str = Field(..., description="Type of document (case, statute, brief, etc.)")
    title: str = Field(..., description="Document title")
    source_id: str = Field(..., description="ID of source entity (case_id, statute_id, etc.)")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction")
    practice_areas: List[str] = Field(default_factory=list, description="Practice areas")
    court_level: Optional[str] = Field(None, description="Court level if applicable")
    decision_date: Optional[datetime] = Field(None, description="Decision date if applicable")
    authority_score: float = Field(default=0.0, description="Authority/importance score")
    
    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to ChromaDB metadata format."""
        metadata = {
            "document_type": self.document_type,
            "title": self.title,
            "source_id": self.source_id,
            "authority_score": self.authority_score,
        }
        
        if self.jurisdiction:
            metadata["jurisdiction"] = self.jurisdiction
        if self.practice_areas:
            metadata["practice_areas"] = ",".join(self.practice_areas)
        if self.court_level:
            metadata["court_level"] = self.court_level
        if self.decision_date:
            metadata["decision_date"] = self.decision_date.isoformat()
            
        return metadata