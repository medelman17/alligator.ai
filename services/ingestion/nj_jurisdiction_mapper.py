"""
New Jersey Jurisdiction Mapping and Court Hierarchy Integration.

Implements comprehensive mapping of New Jersey court system for MVP scope:
- New Jersey Supreme Court (highest state court)
- New Jersey Superior Court, Appellate Division (intermediate appellate)
- New Jersey Superior Court (trial level - various divisions)
- Related Federal Courts (U.S. District Court for D.N.J., Third Circuit)

Provides authority weighting, precedential relationships, and jurisdiction-specific processing.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import re

from shared.models.legal_entities import Court, CourtLevel

logger = logging.getLogger(__name__)


class NewJerseyCourtType(Enum):
    """New Jersey court types with CourtListener IDs."""
    # State Courts
    NJ_SUPREME = "nj"                    # New Jersey Supreme Court
    NJ_APPELLATE = "njsuperapp"         # Superior Court, Appellate Division  
    NJ_SUPERIOR = "njsuper"             # Superior Court (trial level)
    NJ_TAX = "njtaxct"                  # Tax Court of New Jersey
    
    # Related Federal Courts
    DISTRICT_NJ = "njd"                 # U.S. District Court for the District of New Jersey
    THIRD_CIRCUIT = "ca3"               # U.S. Court of Appeals for the Third Circuit
    
    # Federal Supreme Court (for completeness)
    US_SUPREME = "scotus"               # Supreme Court of the United States


class NewJerseyVenue(Enum):
    """New Jersey Superior Court venues/counties."""
    ATLANTIC = "atlantic"
    BERGEN = "bergen" 
    BURLINGTON = "burlington"
    CAMDEN = "camden"
    CAPE_MAY = "cape_may"
    CUMBERLAND = "cumberland"
    ESSEX = "essex"
    GLOUCESTER = "gloucester"
    HUDSON = "hudson"
    HUNTERDON = "hunterdon"
    MERCER = "mercer"
    MIDDLESEX = "middlesex"
    MONMOUTH = "monmouth"
    MORRIS = "morris"
    OCEAN = "ocean"
    PASSAIC = "passaic"
    SALEM = "salem"
    SOMERSET = "somerset"
    SUSSEX = "sussex"
    UNION = "union"
    WARREN = "warren"


class FederalDistrict(Enum):
    """Federal districts covering New Jersey."""
    DISTRICT_NJ = "njd"                 # District of New Jersey
    THIRD_CIRCUIT = "ca3"               # Third Circuit (covers NJ, PA, DE, VI)


@dataclass
class CourtHierarchyInfo:
    """Information about a court's position in the legal hierarchy."""
    court_id: str
    court_type: NewJerseyCourtType
    level: CourtLevel
    authority_weight: float
    jurisdiction_scope: str
    
    # Hierarchical relationships
    parent_courts: List[str] = field(default_factory=list)
    child_courts: List[str] = field(default_factory=list)
    
    # Binding/persuasive authority
    binding_over: List[str] = field(default_factory=list)
    bound_by: List[str] = field(default_factory=list)
    persuasive_for: List[str] = field(default_factory=list)
    
    # Geographic scope
    geographic_jurisdiction: List[str] = field(default_factory=list)
    venue_restrictions: Optional[List[NewJerseyVenue]] = None
    
    # Special characteristics
    specialized_subject_matter: List[str] = field(default_factory=list)
    appeals_to: Optional[str] = None
    appeals_from: List[str] = field(default_factory=list)


@dataclass
class JurisdictionRule:
    """Rules for determining which court has jurisdiction."""
    rule_type: str  # "subject_matter", "geographic", "amount_in_controversy", etc.
    conditions: Dict[str, Any]
    applicable_courts: List[NewJerseyCourtType]
    precedence: int  # Higher number = higher precedence


class NewJerseyJurisdictionMapper:
    """
    Comprehensive mapping of New Jersey court system and jurisdiction rules.
    
    Provides authoritative information about court hierarchy, precedential
    relationships, and jurisdiction-specific processing rules.
    """
    
    def __init__(self):
        self.court_hierarchy = self._build_court_hierarchy()
        self.jurisdiction_rules = self._build_jurisdiction_rules()
        self.court_name_mappings = self._build_court_name_mappings()
        self.citation_patterns = self._build_nj_citation_patterns()
        
        logger.info("New Jersey jurisdiction mapper initialized")
    
    def _build_court_hierarchy(self) -> Dict[str, CourtHierarchyInfo]:
        """Build comprehensive New Jersey court hierarchy."""
        
        hierarchy = {}
        
        # U.S. Supreme Court (apex of all law)
        hierarchy["scotus"] = CourtHierarchyInfo(
            court_id="scotus",
            court_type=NewJerseyCourtType.US_SUPREME,
            level=CourtLevel.SUPREME_COURT,
            authority_weight=10.0,
            jurisdiction_scope="national",
            binding_over=["ca3", "njd", "nj", "njsuperapp", "njsuper", "njtaxct"],
            geographic_jurisdiction=["US"]
        )
        
        # New Jersey Supreme Court (highest state court)
        hierarchy["nj"] = CourtHierarchyInfo(
            court_id="nj",
            court_type=NewJerseyCourtType.NJ_SUPREME,
            level=CourtLevel.SUPREME_COURT,
            authority_weight=9.5,
            jurisdiction_scope="new_jersey_state",
            parent_courts=["scotus"],
            child_courts=["njsuperapp", "njsuper", "njtaxct"],
            bound_by=["scotus"],
            binding_over=["njsuperapp", "njsuper", "njtaxct"],
            persuasive_for=["ca3", "njd"],  # State supreme court persuasive for federal courts
            geographic_jurisdiction=["NJ"],
            appeals_from=["njsuperapp", "njtaxct"]
        )
        
        # U.S. Court of Appeals, Third Circuit
        hierarchy["ca3"] = CourtHierarchyInfo(
            court_id="ca3",
            court_type=NewJerseyCourtType.THIRD_CIRCUIT,
            level=CourtLevel.APPELLATE,
            authority_weight=8.5,
            jurisdiction_scope="third_circuit_federal",
            parent_courts=["scotus"],
            child_courts=["njd"],
            bound_by=["scotus"],
            binding_over=["njd"],
            persuasive_for=["nj", "njsuperapp", "njsuper"],  # Federal circuit persuasive for state courts
            geographic_jurisdiction=["NJ", "PA", "DE", "VI"],
            appeals_from=["njd"]
        )
        
        # New Jersey Superior Court, Appellate Division
        hierarchy["njsuperapp"] = CourtHierarchyInfo(
            court_id="njsuperapp",
            court_type=NewJerseyCourtType.NJ_APPELLATE,
            level=CourtLevel.APPELLATE,
            authority_weight=8.0,
            jurisdiction_scope="new_jersey_appellate",
            parent_courts=["nj"],
            child_courts=["njsuper"],
            bound_by=["scotus", "nj"],
            binding_over=["njsuper"],
            geographic_jurisdiction=["NJ"],
            appeals_to="nj",
            appeals_from=["njsuper"]
        )
        
        # U.S. District Court for the District of New Jersey
        hierarchy["njd"] = CourtHierarchyInfo(
            court_id="njd",
            court_type=NewJerseyCourtType.DISTRICT_NJ,
            level=CourtLevel.DISTRICT,
            authority_weight=7.0,
            jurisdiction_scope="new_jersey_federal",
            parent_courts=["ca3"],
            bound_by=["scotus", "ca3"],
            persuasive_for=["njsuper"],  # Federal district persuasive for state trial courts
            geographic_jurisdiction=["NJ"],
            appeals_to="ca3",
            specialized_subject_matter=["federal_law", "diversity", "federal_question"]
        )
        
        # New Jersey Superior Court (trial level)
        hierarchy["njsuper"] = CourtHierarchyInfo(
            court_id="njsuper",
            court_type=NewJerseyCourtType.NJ_SUPERIOR,
            level=CourtLevel.TRIAL,
            authority_weight=6.0,
            jurisdiction_scope="new_jersey_trial",
            parent_courts=["njsuperapp"],
            bound_by=["scotus", "nj", "njsuperapp"],
            geographic_jurisdiction=["NJ"],
            appeals_to="njsuperapp",
            venue_restrictions=list(NewJerseyVenue),
            specialized_subject_matter=["civil", "criminal", "family", "probate"]
        )
        
        # New Jersey Tax Court
        hierarchy["njtaxct"] = CourtHierarchyInfo(
            court_id="njtaxct",
            court_type=NewJerseyCourtType.NJ_TAX,
            level=CourtLevel.TRIAL,
            authority_weight=6.5,  # Specialized court with higher weight
            jurisdiction_scope="new_jersey_tax",
            parent_courts=["nj"],  # Appeals directly to NJ Supreme Court
            bound_by=["scotus", "nj"],
            geographic_jurisdiction=["NJ"],
            appeals_to="nj",
            specialized_subject_matter=["tax_law", "administrative_law"]
        )
        
        return hierarchy
    
    def _build_jurisdiction_rules(self) -> List[JurisdictionRule]:
        """Build rules for determining court jurisdiction."""
        
        rules = []
        
        # Federal question jurisdiction
        rules.append(JurisdictionRule(
            rule_type="subject_matter",
            conditions={
                "federal_law": True,
                "constitutional_claims": True,
                "federal_statutes": True
            },
            applicable_courts=[NewJerseyCourtType.DISTRICT_NJ],
            precedence=10
        ))
        
        # Diversity jurisdiction
        rules.append(JurisdictionRule(
            rule_type="diversity",
            conditions={
                "amount_in_controversy": {"min": 75000},
                "diverse_citizenship": True
            },
            applicable_courts=[NewJerseyCourtType.DISTRICT_NJ],
            precedence=9
        ))
        
        # State law matters
        rules.append(JurisdictionRule(
            rule_type="subject_matter",
            conditions={
                "state_law": True,
                "local_matters": True
            },
            applicable_courts=[
                NewJerseyCourtType.NJ_SUPERIOR,
                NewJerseyCourtType.NJ_APPELLATE,
                NewJerseyCourtType.NJ_SUPREME
            ],
            precedence=8
        ))
        
        # Tax matters
        rules.append(JurisdictionRule(
            rule_type="subject_matter",
            conditions={
                "tax_dispute": True,
                "administrative_appeal": True
            },
            applicable_courts=[NewJerseyCourtType.NJ_TAX],
            precedence=9
        ))
        
        # Appeals
        rules.append(JurisdictionRule(
            rule_type="procedural",
            conditions={
                "appeal_from_trial_court": True,
                "state_court_appeal": True
            },
            applicable_courts=[NewJerseyCourtType.NJ_APPELLATE],
            precedence=10
        ))
        
        return rules
    
    def _build_court_name_mappings(self) -> Dict[str, str]:
        """Build mappings between various court name formats."""
        
        return {
            # New Jersey Supreme Court variations
            "Supreme Court of New Jersey": "nj",
            "N.J. Sup. Ct.": "nj",
            "N.J.": "nj",
            "New Jersey Supreme Court": "nj",
            
            # Superior Court Appellate Division
            "Superior Court of New Jersey, Appellate Division": "njsuperapp",
            "N.J. Super. Ct. App. Div.": "njsuperapp",
            "N.J. Super. App. Div.": "njsuperapp",
            "New Jersey Appellate Division": "njsuperapp",
            
            # Superior Court
            "Superior Court of New Jersey": "njsuper",
            "N.J. Super. Ct.": "njsuper",
            "N.J. Super.": "njsuper",
            "New Jersey Superior Court": "njsuper",
            
            # Tax Court
            "Tax Court of New Jersey": "njtaxct",
            "N.J. Tax Ct.": "njtaxct",
            "New Jersey Tax Court": "njtaxct",
            
            # Federal Courts
            "United States District Court for the District of New Jersey": "njd",
            "U.S. District Court for the District of New Jersey": "njd",
            "D.N.J.": "njd",
            "District of New Jersey": "njd",
            
            "United States Court of Appeals for the Third Circuit": "ca3",
            "U.S. Court of Appeals for the Third Circuit": "ca3",
            "Third Circuit": "ca3",
            "3d Cir.": "ca3",
            "3rd Cir.": "ca3",
            
            "Supreme Court of the United States": "scotus",
            "U.S.": "scotus",
            "SCOTUS": "scotus"
        }
    
    def _build_nj_citation_patterns(self) -> Dict[str, List[str]]:
        """Build citation patterns specific to New Jersey courts."""
        
        return {
            "nj": [
                r'\d+\s+N\.J\.\s+\d+',           # 123 N.J. 456
                r'\d+\s+A\.(?:2d|3d)\s+\d+'     # 123 A.2d 789 (also used)
            ],
            "njsuperapp": [
                r'\d+\s+N\.J\.\s*Super\.\s*(?:App\.\s*Div\.)?\s*\d+',  # 123 N.J. Super. App. Div. 456
                r'\d+\s+A\.(?:2d|3d)\s+\d+'     # 123 A.2d 789
            ],
            "njsuper": [
                r'\d+\s+N\.J\.\s*Super\.\s+\d+', # 123 N.J. Super. 456
                r'\d+\s+A\.(?:2d|3d)\s+\d+'      # 123 A.2d 789
            ],
            "njtaxct": [
                r'\d+\s+N\.J\.\s*Tax\s+\d+',     # 123 N.J. Tax 456
                r'\d+\s+A\.(?:2d|3d)\s+\d+'      # 123 A.2d 789
            ],
            "njd": [
                r'\d+\s+F\.Supp\.(?:2d|3d)?\s+\d+', # Federal district court
                r'\d+\s+F\.R\.D\.\s+\d+'            # Federal Rules Decisions
            ],
            "ca3": [
                r'\d+\s+F\.(?:2d|3d)\s+\d+',     # 123 F.3d 456
                r'\d+\s+F\.App\'x\s+\d+'         # 123 F.App'x 456 (unpublished)
            ],
            "scotus": [
                r'\d+\s+U\.S\.\s+\d+',           # 123 U.S. 456
                r'\d+\s+S\.Ct\.\s+\d+',          # 123 S.Ct. 456
                r'\d+\s+L\.Ed\.(?:2d)?\s+\d+'    # 123 L.Ed.2d 456
            ]
        }
    
    def get_court_info(self, court_id: str) -> Optional[CourtHierarchyInfo]:
        """Get comprehensive information about a specific court."""
        return self.court_hierarchy.get(court_id)
    
    def get_authority_weight(self, court_id: str) -> float:
        """Get the authority weight for a court."""
        court_info = self.get_court_info(court_id)
        return court_info.authority_weight if court_info else 0.0
    
    def is_binding_precedent(self, citing_court: str, cited_court: str) -> bool:
        """Determine if cited court's decisions are binding on citing court."""
        
        citing_info = self.get_court_info(citing_court)
        cited_info = self.get_court_info(cited_court)
        
        if not citing_info or not cited_info:
            return False
        
        return cited_court in citing_info.bound_by
    
    def is_persuasive_precedent(self, citing_court: str, cited_court: str) -> bool:
        """Determine if cited court's decisions are persuasive for citing court."""
        
        citing_info = self.get_court_info(citing_court)
        cited_info = self.get_court_info(cited_court)
        
        if not citing_info or not cited_info:
            return False
        
        return citing_court in cited_info.persuasive_for
    
    def get_precedential_relationship(self, citing_court: str, cited_court: str) -> str:
        """Get the precedential relationship between two courts."""
        
        if self.is_binding_precedent(citing_court, cited_court):
            return "binding"
        elif self.is_persuasive_precedent(citing_court, cited_court):
            return "persuasive"
        elif citing_court == cited_court:
            return "same_court"
        else:
            return "no_precedential_value"
    
    def map_court_name_to_id(self, court_name: str) -> Optional[str]:
        """Map various court name formats to standard court ID."""
        
        # Direct lookup first
        if court_name in self.court_name_mappings:
            return self.court_name_mappings[court_name]
        
        # Fuzzy matching for variations
        court_name_clean = court_name.strip().replace("  ", " ")
        
        for known_name, court_id in self.court_name_mappings.items():
            if self._fuzzy_court_match(court_name_clean, known_name):
                return court_id
        
        return None
    
    def _fuzzy_court_match(self, court_name: str, known_name: str) -> bool:
        """Fuzzy matching for court names."""
        
        # Normalize both names
        name1 = re.sub(r'[^\w\s]', '', court_name.lower())
        name2 = re.sub(r'[^\w\s]', '', known_name.lower())
        
        # Check for key words match
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Must have significant overlap
        overlap = len(words1 & words2)
        min_words = min(len(words1), len(words2))
        
        return overlap / max(min_words, 1) >= 0.7  # 70% word overlap
    
    def identify_court_from_citation(self, citation: str) -> Optional[str]:
        """Identify court from citation format."""
        
        for court_id, patterns in self.citation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    return court_id
        
        return None
    
    def get_appeals_chain(self, court_id: str) -> List[str]:
        """Get the chain of courts for appeals from given court."""
        
        chain = [court_id]
        current_court = court_id
        
        while current_court:
            court_info = self.get_court_info(current_court)
            if court_info and court_info.appeals_to:
                chain.append(court_info.appeals_to)
                current_court = court_info.appeals_to
            else:
                break
        
        return chain
    
    def get_jurisdiction_for_case(self, case_data: Dict[str, Any]) -> List[NewJerseyCourtType]:
        """Determine which courts have jurisdiction over a case."""
        
        applicable_courts = []
        
        for rule in sorted(self.jurisdiction_rules, key=lambda r: r.precedence, reverse=True):
            if self._case_matches_rule(case_data, rule):
                applicable_courts.extend(rule.applicable_courts)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_courts = []
        for court in applicable_courts:
            if court not in seen:
                seen.add(court)
                unique_courts.append(court)
        
        return unique_courts
    
    def _case_matches_rule(self, case_data: Dict[str, Any], rule: JurisdictionRule) -> bool:
        """Check if a case matches a jurisdiction rule."""
        
        for condition, value in rule.conditions.items():
            case_value = case_data.get(condition)
            
            if isinstance(value, dict):
                # Range or complex condition
                if "min" in value and case_value and case_value < value["min"]:
                    return False
                if "max" in value and case_value and case_value > value["max"]:
                    return False
            elif isinstance(value, bool):
                # Boolean condition
                if bool(case_value) != value:
                    return False
            elif case_value != value:
                # Exact match condition
                return False
        
        return True
    
    def get_related_federal_courts(self) -> List[str]:
        """Get federal courts that handle cases related to New Jersey."""
        return ["njd", "ca3", "scotus"]
    
    def get_related_state_courts(self) -> List[str]:
        """Get New Jersey state courts."""
        return ["nj", "njsuperapp", "njsuper", "njtaxct"]
    
    def calculate_case_authority_score(
        self, 
        court_id: str, 
        case_date: datetime,
        precedential_status: str = "Published"
    ) -> float:
        """
        Calculate comprehensive authority score for a case.
        
        Factors:
        - Court hierarchy weight (40%)
        - Precedential status (25%)
        - Recency (20%)
        - Publication status (15%)
        """
        
        court_info = self.get_court_info(court_id)
        if not court_info:
            return 0.0
        
        # Base authority from court hierarchy
        base_authority = court_info.authority_weight * 0.4
        
        # Precedential status weight
        status_weights = {
            "Published": 0.25,
            "Unpublished": 0.15,
            "Per Curiam": 0.20,
            "Memorandum": 0.10,
            "Errata": 0.05,
            "Unknown": 0.10
        }
        precedential_weight = status_weights.get(precedential_status, 0.10) * 10  # Scale to match other factors
        
        # Recency factor (cases lose authority over time)
        days_old = (datetime.now() - case_date).days
        recency_factor = max(0.1, 1.0 - (days_old / 7300))  # 20-year decay, min 10%
        recency_weight = recency_factor * 2.0  # Scale to 0-2 range
        
        # Publication status (similar to precedential but for accessibility)
        publication_weight = 1.5 if precedential_status == "Published" else 1.0
        
        total_score = base_authority + precedential_weight + recency_weight + publication_weight
        
        # Cap at 10.0
        return min(10.0, total_score)
    
    def get_mvp_court_priorities(self) -> Dict[str, int]:
        """Get priority rankings for MVP scope courts."""
        
        return {
            "nj": 1,          # Highest priority - NJ Supreme Court
            "njsuperapp": 2,  # Second priority - NJ Appellate
            "njsuper": 3,     # Third priority - NJ Superior
            "ca3": 4,         # Fourth priority - Third Circuit (NJ cases)
            "njd": 5,         # Fifth priority - NJ Federal District
            "njtaxct": 6,     # Sixth priority - NJ Tax Court
            "scotus": 7       # Seventh priority - US Supreme Court (selective)
        }
    
    def is_mvp_scope_court(self, court_id: str) -> bool:
        """Check if court is within MVP scope."""
        mvp_courts = self.get_mvp_court_priorities()
        return court_id in mvp_courts
    
    def get_court_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the jurisdiction mapping."""
        
        total_courts = len(self.court_hierarchy)
        state_courts = len([c for c in self.court_hierarchy.values() 
                           if "nj" in c.court_id and c.court_id != "njd"])
        federal_courts = len([c for c in self.court_hierarchy.values() 
                             if c.court_id in ["njd", "ca3", "scotus"]])
        
        return {
            "total_courts_mapped": total_courts,
            "state_courts": state_courts,
            "federal_courts": federal_courts,
            "jurisdiction_rules": len(self.jurisdiction_rules),
            "court_name_mappings": len(self.court_name_mappings),
            "citation_patterns": sum(len(patterns) for patterns in self.citation_patterns.values()),
            "mvp_scope_courts": len(self.get_mvp_court_priorities())
        }


# Example usage and testing
def main():
    """Example usage of New Jersey jurisdiction mapper."""
    
    mapper = NewJerseyJurisdictionMapper()
    
    print("=== New Jersey Jurisdiction Mapping ===")
    print(f"Summary: {mapper.get_court_summary_stats()}")
    
    print("\n=== Court Hierarchy ===")
    for court_id, info in mapper.court_hierarchy.items():
        print(f"{court_id}: {info.court_type.value} (Authority: {info.authority_weight})")
        if info.bound_by:
            print(f"  Bound by: {info.bound_by}")
        if info.binding_over:
            print(f"  Binding over: {info.binding_over}")
    
    print("\n=== Precedential Relationships ===")
    test_relationships = [
        ("njsuper", "njsuperapp"),  # Trial court citing appellate
        ("njsuperapp", "nj"),       # Appellate citing supreme
        ("njd", "ca3"),             # District citing circuit
        ("nj", "scotus"),           # State supreme citing US Supreme
    ]
    
    for citing, cited in test_relationships:
        relationship = mapper.get_precedential_relationship(citing, cited)
        print(f"{citing} → {cited}: {relationship}")
    
    print("\n=== Court Name Mapping ===")
    test_names = [
        "Supreme Court of New Jersey",
        "N.J. Super. Ct. App. Div.",
        "U.S. District Court for the District of New Jersey",
        "Third Circuit"
    ]
    
    for name in test_names:
        court_id = mapper.map_court_name_to_id(name)
        print(f"'{name}' → {court_id}")
    
    print("\n=== Citation Pattern Recognition ===")
    test_citations = [
        "123 N.J. 456",
        "456 N.J. Super. App. Div. 789",
        "789 F.3d 123",
        "321 U.S. 654"
    ]
    
    for citation in test_citations:
        court_id = mapper.identify_court_from_citation(citation)
        print(f"'{citation}' → {court_id}")
    
    print("\n=== Appeals Chain ===")
    for court_id in ["njsuper", "njd", "njtaxct"]:
        chain = mapper.get_appeals_chain(court_id)
        print(f"{court_id} appeals chain: {' → '.join(chain)}")
    
    print("\n=== Authority Scoring ===")
    test_date = datetime(2023, 1, 15)
    for court_id in ["nj", "njsuperapp", "njsuper", "ca3", "njd"]:
        score = mapper.calculate_case_authority_score(court_id, test_date, "Published")
        print(f"{court_id} authority score: {score:.2f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()