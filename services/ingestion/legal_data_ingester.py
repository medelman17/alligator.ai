"""
Legal data ingestion service for populating Neo4j and ChromaDB.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
import re
import uuid

from shared.models.legal_entities import (
    Case, Court, Judge, Citation, LegalConcept, Statute, 
    CourtLevel, CaseStatus, CitationTreatment, PracticeArea
)
from services.graph.neo4j_service import Neo4jService
from services.vector.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class LegalDataIngester:
    """Service for ingesting legal data from various sources."""
    
    def __init__(self, neo4j_service: Neo4jService, chroma_service: ChromaService):
        self.neo4j = neo4j_service
        self.chroma = chroma_service
    
    async def ingest_sample_data(self):
        """Ingest sample legal data for development and testing."""
        logger.info("Starting sample data ingestion...")
        
        # Create courts first
        courts = await self._create_sample_courts()
        logger.info(f"Created {len(courts)} courts")
        
        # Create judges
        judges = await self._create_sample_judges()
        logger.info(f"Created {len(judges)} judges")
        
        # Create landmark cases
        cases = await self._create_sample_cases()
        logger.info(f"Created {len(cases)} cases")
        
        # Create citations between cases
        citations = await self._create_sample_citations(cases)
        logger.info(f"Created {len(citations)} citations")
        
        # Create legal concepts
        concepts = await self._create_sample_concepts()
        logger.info(f"Created {len(concepts)} legal concepts")
        
        # Create sample statutes
        statutes = await self._create_sample_statutes()
        logger.info(f"Created {len(statutes)} statutes")
        
        logger.info("Sample data ingestion completed successfully")
    
    async def _create_sample_courts(self) -> List[Court]:
        """Create sample courts."""
        courts_data = [
            {
                "id": "us-supreme-court",
                "name": "Supreme Court of the United States",
                "short_name": "SCOTUS",
                "level": CourtLevel.SUPREME_COURT,
                "jurisdiction": "US",
                "authority_weight": 10.0
            },
            {
                "id": "us-ca-9",
                "name": "United States Court of Appeals for the Ninth Circuit",
                "short_name": "9th Cir.",
                "level": CourtLevel.APPELLATE,
                "jurisdiction": "US-9",
                "parent_court_id": "us-supreme-court",
                "authority_weight": 8.0
            },
            {
                "id": "ca-supreme",
                "name": "Supreme Court of California",
                "short_name": "Cal. Sup. Ct.",
                "level": CourtLevel.SUPREME_COURT,
                "jurisdiction": "CA",
                "authority_weight": 9.0
            },
            {
                "id": "us-dc-district",
                "name": "United States District Court for the District of Columbia",
                "short_name": "D.D.C.",
                "level": CourtLevel.DISTRICT,
                "jurisdiction": "US-DC",
                "authority_weight": 6.0
            }
        ]
        
        courts = []
        for court_data in courts_data:
            court = Court(**court_data)
            await self.neo4j.create_court(court)
            courts.append(court)
        
        return courts
    
    async def _create_sample_judges(self) -> List[Judge]:
        """Create sample judges."""
        judges_data = [
            {
                "id": "warren-earl",
                "name": "Earl Warren",
                "courts": ["us-supreme-court"],
                "appointment_date": datetime(1953, 10, 5),
                "tenure_start": datetime(1953, 10, 5),
                "tenure_end": datetime(1969, 6, 23),
                "appointing_authority": "President Eisenhower",
                "judicial_philosophy": "liberal"
            },
            {
                "id": "marshall-thurgood",
                "name": "Thurgood Marshall",
                "courts": ["us-supreme-court"],
                "appointment_date": datetime(1967, 8, 30),
                "tenure_start": datetime(1967, 10, 2),
                "tenure_end": datetime(1991, 10, 1),
                "appointing_authority": "President Johnson",
                "judicial_philosophy": "liberal"
            },
            {
                "id": "scalia-antonin",
                "name": "Antonin Scalia",
                "courts": ["us-supreme-court"],
                "appointment_date": datetime(1986, 9, 26),
                "tenure_start": datetime(1986, 9, 26),
                "tenure_end": datetime(2016, 2, 13),
                "appointing_authority": "President Reagan",
                "judicial_philosophy": "conservative"
            }
        ]
        
        judges = []
        for judge_data in judges_data:
            judge = Judge(**judge_data)
            await self.neo4j.create_judge(judge)
            judges.append(judge)
        
        return judges
    
    async def _create_sample_cases(self) -> List[Case]:
        """Create landmark legal cases."""
        cases_data = [
            {
                "id": "brown-v-board-1954",
                "citation": "347 U.S. 483",
                "case_name": "Brown v. Board of Education",
                "full_name": "Brown v. Board of Education of Topeka",
                "court_id": "us-supreme-court",
                "jurisdiction": "US",
                "decision_date": datetime(1954, 5, 17),
                "judges": ["warren-earl"],
                "status": CaseStatus.GOOD_LAW,
                "practice_areas": [PracticeArea.CONSTITUTIONAL, PracticeArea.CIVIL_RIGHTS],
                "summary": "Declared state laws establishing separate public schools for black and white students to be unconstitutional, overturning Plessy v. Ferguson.",
                "holding": "Separate educational facilities are inherently unequal and violate the Equal Protection Clause of the Fourteenth Amendment.",
                "procedural_posture": "Appeal from District Court",
                "disposition": "Reversed",
                "authority_score": 9.8,
                "citation_count": 4500
            },
            {
                "id": "miranda-v-arizona-1966",
                "citation": "384 U.S. 436",
                "case_name": "Miranda v. Arizona",
                "full_name": "Miranda v. Arizona",
                "court_id": "us-supreme-court",
                "jurisdiction": "US",
                "decision_date": datetime(1966, 6, 13),
                "judges": ["warren-earl"],
                "status": CaseStatus.GOOD_LAW,
                "practice_areas": [PracticeArea.CRIMINAL, PracticeArea.CONSTITUTIONAL],
                "summary": "Established that defendants must be informed of their rights before police interrogation.",
                "holding": "The prosecution may not use statements made by a defendant while in custody unless the defendant was informed of constitutional rights.",
                "procedural_posture": "Appeal from Supreme Court of Arizona",
                "disposition": "Reversed",
                "authority_score": 9.5,
                "citation_count": 3200
            },
            {
                "id": "monroe-v-pape-1961",
                "citation": "365 U.S. 167",
                "case_name": "Monroe v. Pape",
                "full_name": "Monroe v. Pape",
                "court_id": "us-supreme-court",
                "jurisdiction": "US",
                "decision_date": datetime(1961, 2, 20),
                "judges": ["warren-earl"],
                "status": CaseStatus.QUESTIONED,
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "summary": "Established that Section 1983 provides a federal cause of action against state officials acting under color of law.",
                "holding": "42 U.S.C. § 1983 applies to actions by state officials even when those actions violate state law.",
                "procedural_posture": "Appeal from Court of Appeals for the Seventh Circuit",
                "disposition": "Reversed",
                "authority_score": 8.2,
                "citation_count": 2800
            },
            {
                "id": "monell-v-dept-social-services-1978",
                "citation": "436 U.S. 658",
                "case_name": "Monell v. Department of Social Services",
                "full_name": "Monell v. Department of Social Services of the City of New York",
                "court_id": "us-supreme-court",
                "jurisdiction": "US",
                "decision_date": datetime(1978, 6, 6),
                "judges": ["marshall-thurgood"],
                "status": CaseStatus.GOOD_LAW,
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "summary": "Established that municipalities can be sued under Section 1983 for constitutional violations.",
                "holding": "Local governments can be sued directly under § 1983 for monetary, declaratory, or injunctive relief where the action that is alleged to be unconstitutional implements or executes a policy statement, ordinance, regulation, or decision officially adopted and promulgated by that body's officers.",
                "procedural_posture": "Appeal from Court of Appeals for the Second Circuit",
                "disposition": "Reversed",
                "authority_score": 9.1,
                "citation_count": 2100
            },
            {
                "id": "pearson-v-callahan-2009",
                "citation": "555 U.S. 223",
                "case_name": "Pearson v. Callahan",
                "full_name": "Pearson v. Callahan",
                "court_id": "us-supreme-court",
                "jurisdiction": "US",
                "decision_date": datetime(2009, 1, 21),
                "judges": ["scalia-antonin"],
                "status": CaseStatus.GOOD_LAW,
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "summary": "Modified the rigid two-step qualified immunity analysis established in Saucier v. Katz.",
                "holding": "Courts have discretion to decide which of the two prongs of qualified immunity analysis to address first.",
                "procedural_posture": "Appeal from Court of Appeals for the Tenth Circuit",
                "disposition": "Reversed",
                "authority_score": 8.7,
                "citation_count": 1800
            }
        ]
        
        cases = []
        for case_data in cases_data:
            case = Case(**case_data)
            await self.neo4j.create_case(case)
            
            # Add case text to ChromaDB
            case_text = f"{case.summary} {case.holding}"
            await self.chroma.add_case_document(case, case_text)
            
            cases.append(case)
        
        return cases
    
    async def _create_sample_citations(self, cases: List[Case]) -> List[Citation]:
        """Create citation relationships between cases."""
        citations_data = [
            # Monell cites Monroe
            {
                "citing_case": "monell-v-dept-social-services-1978",
                "cited_case": "monroe-v-pape-1961",
                "treatment": CitationTreatment.EXPLAINS,
                "context": "Discussing the scope of Section 1983 liability",
                "strength": 0.9
            },
            # Pearson cites Monroe
            {
                "citing_case": "pearson-v-callahan-2009", 
                "cited_case": "monroe-v-pape-1961",
                "treatment": CitationTreatment.FOLLOWS,
                "context": "Following Monroe's interpretation of Section 1983",
                "strength": 0.8
            },
            # Pearson cites Monell
            {
                "citing_case": "pearson-v-callahan-2009",
                "cited_case": "monell-v-dept-social-services-1978",
                "treatment": CitationTreatment.FOLLOWS,
                "context": "Municipal liability under Section 1983",
                "strength": 0.7
            },
            # Cases citing Brown v. Board
            {
                "citing_case": "monroe-v-pape-1961",
                "cited_case": "brown-v-board-1954",
                "treatment": CitationTreatment.CITES,
                "context": "Equal protection principles",
                "strength": 0.6
            }
        ]
        
        citations = []
        case_lookup = {case.id: case for case in cases}
        
        for citation_data in citations_data:
            citing_case_id = citation_data["citing_case"]
            cited_case_id = citation_data["cited_case"]
            
            if citing_case_id in case_lookup and cited_case_id in case_lookup:
                citation = Citation(
                    id=str(uuid.uuid4()),
                    citing_case_id=citing_case_id,
                    cited_case_id=cited_case_id,
                    treatment=citation_data["treatment"],
                    context=citation_data["context"],
                    strength=citation_data["strength"]
                )
                
                await self.neo4j.create_citation(citation)
                citations.append(citation)
        
        return citations
    
    async def _create_sample_concepts(self) -> List[LegalConcept]:
        """Create legal concepts and doctrines."""
        concepts_data = [
            {
                "id": "qualified-immunity",
                "name": "Qualified Immunity",
                "description": "A legal doctrine that shields government officials from liability for civil damages insofar as their conduct does not violate clearly established statutory or constitutional rights.",
                "aliases": ["QI", "Official Immunity"],
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "key_cases": ["pearson-v-callahan-2009", "monroe-v-pape-1961"],
                "current_status": "active"
            },
            {
                "id": "section-1983",
                "name": "42 U.S.C. § 1983",
                "description": "Federal civil rights statute that provides a cause of action for the deprivation of rights under color of state law.",
                "aliases": ["Section 1983", "Civil Rights Act"],
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "key_cases": ["monroe-v-pape-1961", "monell-v-dept-social-services-1978"],
                "current_status": "active"
            },
            {
                "id": "equal-protection",
                "name": "Equal Protection Clause",
                "description": "Constitutional principle requiring that all persons be treated equally under the law.",
                "aliases": ["Fourteenth Amendment Equal Protection", "Equal Protection"],
                "practice_areas": [PracticeArea.CONSTITUTIONAL, PracticeArea.CIVIL_RIGHTS],
                "key_cases": ["brown-v-board-1954"],
                "current_status": "active"
            },
            {
                "id": "miranda-rights",
                "name": "Miranda Rights",
                "description": "Constitutional rights that must be read to suspects before custodial interrogation.",
                "aliases": ["Miranda Warning", "Miranda Rule"],
                "practice_areas": [PracticeArea.CRIMINAL, PracticeArea.CONSTITUTIONAL],
                "key_cases": ["miranda-v-arizona-1966"],
                "current_status": "active"
            }
        ]
        
        concepts = []
        for concept_data in concepts_data:
            concept = LegalConcept(**concept_data)
            
            # Add to ChromaDB
            concept_text = f"{concept.name}: {concept.description}"
            await self.chroma.add_concept_document(concept, concept_text)
            
            concepts.append(concept)
        
        return concepts
    
    async def _create_sample_statutes(self) -> List[Statute]:
        """Create sample statutes."""
        statutes_data = [
            {
                "id": "42-usc-1983",
                "title": "Civil Action for Deprivation of Rights",
                "citation": "42 U.S.C. § 1983",
                "jurisdiction": "US",
                "effective_date": datetime(1871, 4, 20),
                "full_text": "Every person who, under color of any statute, ordinance, regulation, custom, or usage, of any State or Territory or the District of Columbia, subjects, or causes to be subjected, any citizen of the United States or other person within the jurisdiction thereof to the deprivation of any rights, privileges, or immunities secured by the Constitution and laws, shall be liable to the party injured in an action at law, suit in equity, or other proper proceeding for redress.",
                "summary": "Provides federal civil rights cause of action against state actors",
                "practice_areas": [PracticeArea.CIVIL_RIGHTS, PracticeArea.CONSTITUTIONAL],
                "related_cases": ["monroe-v-pape-1961", "monell-v-dept-social-services-1978"]
            },
            {
                "id": "14th-amendment",
                "title": "Fourteenth Amendment to the United States Constitution",
                "citation": "U.S. Const. amend. XIV",
                "jurisdiction": "US",
                "effective_date": datetime(1868, 7, 9),
                "full_text": "All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws.",
                "summary": "Constitutional amendment establishing citizenship and equal protection rights",
                "practice_areas": [PracticeArea.CONSTITUTIONAL, PracticeArea.CIVIL_RIGHTS],
                "related_cases": ["brown-v-board-1954"]
            }
        ]
        
        statutes = []
        for statute_data in statutes_data:
            statute = Statute(**statute_data)
            
            # Add to ChromaDB
            await self.chroma.add_statute_document(statute)
            
            statutes.append(statute)
        
        return statutes
    
    async def ingest_from_json_file(self, file_path: str, data_type: str):
        """Ingest legal data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if data_type == "cases":
                await self._ingest_cases_from_data(data)
            elif data_type == "citations":
                await self._ingest_citations_from_data(data)
            elif data_type == "courts":
                await self._ingest_courts_from_data(data)
            elif data_type == "statutes":
                await self._ingest_statutes_from_data(data)
            else:
                raise ValueError(f"Unknown data type: {data_type}")
                
            logger.info(f"Successfully ingested {len(data)} {data_type} from {file_path}")
            
        except Exception as e:
            logger.error(f"Error ingesting data from {file_path}: {e}")
            raise
    
    async def _ingest_cases_from_data(self, cases_data: List[Dict[str, Any]]):
        """Ingest cases from structured data."""
        for case_data in cases_data:
            try:
                # Parse and validate case data
                case_data = self._normalize_case_data(case_data)
                case = Case(**case_data)
                
                # Store in Neo4j
                await self.neo4j.create_case(case)
                
                # Extract full text and store in ChromaDB
                full_text = self._extract_case_text(case_data)
                if full_text:
                    await self.chroma.add_case_document(case, full_text)
                
                logger.debug(f"Ingested case: {case.case_name}")
                
            except Exception as e:
                logger.error(f"Error ingesting case {case_data.get('case_name', 'Unknown')}: {e}")
                continue
    
    def _normalize_case_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate case data."""
        normalized = {}
        
        # Required fields
        normalized["id"] = raw_data.get("id") or self._generate_case_id(raw_data)
        normalized["citation"] = raw_data["citation"]
        normalized["case_name"] = raw_data["case_name"]
        normalized["full_name"] = raw_data.get("full_name", raw_data["case_name"])
        normalized["court_id"] = raw_data["court_id"]
        normalized["jurisdiction"] = raw_data["jurisdiction"]
        
        # Parse decision date
        decision_date = raw_data["decision_date"]
        if isinstance(decision_date, str):
            normalized["decision_date"] = datetime.fromisoformat(decision_date)
        else:
            normalized["decision_date"] = decision_date
        
        # Optional fields with defaults
        normalized["judges"] = raw_data.get("judges", [])
        normalized["status"] = CaseStatus(raw_data.get("status", "good_law"))
        normalized["practice_areas"] = [
            PracticeArea(area) for area in raw_data.get("practice_areas", [])
        ]
        normalized["summary"] = raw_data.get("summary")
        normalized["holding"] = raw_data.get("holding")
        normalized["authority_score"] = raw_data.get("authority_score", 0.0)
        normalized["citation_count"] = raw_data.get("citation_count", 0)
        
        return normalized
    
    def _generate_case_id(self, case_data: Dict[str, Any]) -> str:
        """Generate a unique case ID from case data."""
        case_name = case_data.get("case_name", "unknown")
        year = "unknown"
        
        if "decision_date" in case_data:
            try:
                if isinstance(case_data["decision_date"], str):
                    date = datetime.fromisoformat(case_data["decision_date"])
                else:
                    date = case_data["decision_date"]
                year = str(date.year)
            except:
                pass
        
        # Create slug from case name
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', case_name.lower())
        slug = re.sub(r'\s+', '-', slug)
        
        return f"{slug}-{year}"
    
    def _extract_case_text(self, case_data: Dict[str, Any]) -> str:
        """Extract full text content from case data for vector storage."""
        text_parts = []
        
        # Add case name
        text_parts.append(case_data.get("case_name", ""))
        
        # Add summary
        if case_data.get("summary"):
            text_parts.append(case_data["summary"])
        
        # Add holding
        if case_data.get("holding"):
            text_parts.append(case_data["holding"])
        
        # Add full opinion text if available
        if case_data.get("opinion_text"):
            text_parts.append(case_data["opinion_text"])
        
        return " ".join(text_parts).strip()


# Example usage and testing
async def main():
    """Example usage of the legal data ingester."""
    # Initialize services (would come from dependency injection in real app)
    neo4j_service = Neo4jService("bolt://localhost:7687", "neo4j", "citation_graph_2024")
    chroma_service = ChromaService()
    
    ingester = LegalDataIngester(neo4j_service, chroma_service)
    
    try:
        await neo4j_service.connect()
        await ingester.ingest_sample_data()
        logger.info("Sample data ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
    finally:
        await neo4j_service.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())