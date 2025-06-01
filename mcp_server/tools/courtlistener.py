"""
CourtListener API tools for MCP server.

Provides comprehensive legal case search and citation analysis across all U.S. jurisdictions.
Supports federal courts, state courts, and specialized courts through CourtListener API.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import json

from services.ingestion.courtlistener_client import CourtListenerClient, NewJerseyCourtType

logger = logging.getLogger(__name__)


class CourtListenerTools:
    """CourtListener API integration for MCP server"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        
        # Expanded court mappings for all U.S. jurisdictions
        self.court_mappings = {
            # Federal Courts
            "scotus": "Supreme Court of the United States",
            "ca1": "U.S. Court of Appeals for the 1st Circuit",
            "ca2": "U.S. Court of Appeals for the 2nd Circuit", 
            "ca3": "U.S. Court of Appeals for the 3rd Circuit",
            "ca4": "U.S. Court of Appeals for the 4th Circuit",
            "ca5": "U.S. Court of Appeals for the 5th Circuit",
            "ca6": "U.S. Court of Appeals for the 6th Circuit",
            "ca7": "U.S. Court of Appeals for the 7th Circuit",
            "ca8": "U.S. Court of Appeals for the 8th Circuit",
            "ca9": "U.S. Court of Appeals for the 9th Circuit",
            "ca10": "U.S. Court of Appeals for the 10th Circuit",
            "ca11": "U.S. Court of Appeals for the 11th Circuit",
            "cadc": "U.S. Court of Appeals for the D.C. Circuit",
            "cafc": "U.S. Court of Appeals for the Federal Circuit",
            
            # Federal District Courts (sample)
            "nynd": "U.S. District Court for Northern District of New York",
            "nysd": "U.S. District Court for Southern District of New York",
            "nyed": "U.S. District Court for Eastern District of New York",
            "nywd": "U.S. District Court for Western District of New York",
            "njd": "U.S. District Court for District of New Jersey",
            "cand": "U.S. District Court for Northern District of California",
            "cacd": "U.S. District Court for Central District of California",
            "caed": "U.S. District Court for Eastern District of California",
            "casd": "U.S. District Court for Southern District of California",
            
            # State Supreme Courts
            "cal": "California Supreme Court",
            "ny": "New York Court of Appeals",
            "nj": "New Jersey Supreme Court",
            "tex": "Texas Supreme Court",
            "fla": "Florida Supreme Court",
            "ill": "Illinois Supreme Court",
            "pa": "Pennsylvania Supreme Court",
            "ohio": "Ohio Supreme Court",
            "mich": "Michigan Supreme Court",
            "ga": "Georgia Supreme Court",
            "nc": "North Carolina Supreme Court",
            "va": "Virginia Supreme Court",
            "wash": "Washington Supreme Court",
            "mass": "Massachusetts Supreme Judicial Court",
            "md": "Maryland Court of Appeals",
            
            # State Appellate Courts (sample)
            "calctapp": "California Court of Appeal",
            "nyappterm": "New York Appellate Term",
            "njsuperapp": "New Jersey Superior Court, Appellate Division",
            "texapp": "Texas Court of Appeals",
            "flaapp": "Florida District Court of Appeal"
        }
        
        # Jurisdiction hierarchy for authority scoring
        self.jurisdiction_hierarchy = {
            "federal": {
                "scotus": 10.0,
                "ca1": 8.0, "ca2": 8.0, "ca3": 8.0, "ca4": 8.0, "ca5": 8.0,
                "ca6": 8.0, "ca7": 8.0, "ca8": 8.0, "ca9": 8.0, "ca10": 8.0,
                "ca11": 8.0, "cadc": 8.0, "cafc": 8.0,
                "district": 6.0
            },
            "state": {
                "supreme": 8.0,
                "appellate": 6.0,
                "trial": 4.0
            }
        }
    
    async def _get_client(self) -> CourtListenerClient:
        """Get initialized CourtListener client"""
        if self.client is None:
            # Use API token from settings if available, otherwise anonymous access
            api_token = getattr(self.settings, 'COURTLISTENER_API_TOKEN', None)
            self.client = CourtListenerClient(api_token=api_token)
        return self.client
    
    async def search_cases(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        court_type: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for legal cases across all U.S. jurisdictions.
        
        Args:
            query: Search query for legal cases
            jurisdiction: Jurisdiction code (e.g., 'scotus', 'ca9', 'nj')
            court_type: Type of court ('federal', 'state', 'appellate', 'trial', 'supreme')
            date_range: Date range with 'start' and 'end' keys
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            client = await self._get_client()
            
            # Convert broad search to specific CourtListener API parameters
            search_params = {
                "limit": min(limit, 100),
                "ordering": "-date_filed"  # Most recent first
            }
            
            # Handle jurisdiction filtering
            if jurisdiction:
                # Map jurisdiction codes to CourtListener court IDs
                if jurisdiction in self.court_mappings:
                    search_params["court"] = jurisdiction
                else:
                    # Try to find partial matches for state abbreviations
                    matching_courts = [
                        court_id for court_id in self.court_mappings.keys()
                        if jurisdiction.lower() in court_id.lower()
                    ]
                    if matching_courts:
                        search_params["court__in"] = ",".join(matching_courts[:10])  # Limit to 10 courts
            
            # Handle court type filtering
            if court_type:
                if court_type == "federal":
                    federal_courts = [k for k in self.court_mappings.keys() 
                                    if k.startswith(('ca', 'scotus')) or 'd' in k]
                    search_params["court__in"] = ",".join(federal_courts[:20])
                elif court_type == "supreme":
                    supreme_courts = ["scotus"] + [k for k in self.court_mappings.keys() 
                                                  if not k.startswith('ca') and not 'd' in k and not 'app' in k]
                    search_params["court__in"] = ",".join(supreme_courts[:10])
                elif court_type == "appellate":
                    appellate_courts = [k for k in self.court_mappings.keys() 
                                      if k.startswith('ca') or 'app' in k]
                    search_params["court__in"] = ",".join(appellate_courts[:15])
            
            # Handle date range
            if date_range:
                if date_range.get("start"):
                    search_params["date_filed__gte"] = date_range["start"]
                if date_range.get("end"):
                    search_params["date_filed__lte"] = date_range["end"]
            
            # Perform search using CourtListener API
            # For now, adapt the New Jersey search method for broader use
            if jurisdiction and jurisdiction in ["nj", "njd", "njsuperapp", "njsuper"]:
                # Use existing New Jersey client for NJ courts
                nj_court_types = []
                if jurisdiction == "nj":
                    nj_court_types = [NewJerseyCourtType.SUPREME]
                elif jurisdiction == "njsuperapp":
                    nj_court_types = [NewJerseyCourtType.APPELLATE]
                elif jurisdiction == "njsuper":
                    nj_court_types = [NewJerseyCourtType.SUPERIOR]
                elif jurisdiction == "njd":
                    nj_court_types = [NewJerseyCourtType.DISTRICT_NJ]
                
                # Convert date range to datetime objects
                date_range_obj = None
                if date_range:
                    start_date = datetime.fromisoformat(date_range["start"]) if date_range.get("start") else datetime.now() - timedelta(days=365*2)
                    end_date = datetime.fromisoformat(date_range["end"]) if date_range.get("end") else datetime.now()
                    date_range_obj = (start_date, end_date)
                
                results = await client.search_new_jersey_cases(
                    limit=limit,
                    court_types=nj_court_types,
                    date_range=date_range_obj
                )
            else:
                # For non-NJ jurisdictions, use direct API search
                results = await self._generic_case_search(client, query, search_params)
            
            # Format results for MCP response
            formatted_results = {
                "query": query,
                "jurisdiction": jurisdiction,
                "court_type": court_type,
                "total_results": len(results),
                "search_metadata": {
                    "date_range": date_range,
                    "limit": limit,
                    "courts_searched": self._get_courts_searched(jurisdiction, court_type)
                },
                "cases": []
            }
            
            for case in results[:limit]:
                case_data = {
                    "id": str(case.get("id", "")),
                    "citation": case.get("citation", ""),
                    "case_name": case.get("case_name", "Unknown Case"),
                    "court": {
                        "id": case.get("court", ""),
                        "name": self.court_mappings.get(case.get("court", ""), "Unknown Court")
                    },
                    "date_filed": case.get("date_filed", ""),
                    "precedential_status": case.get("precedential_status", ""),
                    "authority_score": self._calculate_case_authority(case),
                    "summary": case.get("summary", ""),
                    "practice_areas": self._extract_practice_areas(case),
                    "url": f"https://www.courtlistener.com/opinion/{case.get('id', '')}/",
                    "api_url": f"{client.BASE_URL}clusters/{case.get('id', '')}/"
                }
                formatted_results["cases"].append(case_data)
            
            logger.info(f"Found {len(formatted_results['cases'])} cases for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Case search failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "total_results": 0,
                "cases": []
            }
    
    async def _generic_case_search(self, client: CourtListenerClient, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform generic case search for non-NJ jurisdictions"""
        try:
            # Use the client's paginated search method
            endpoint = "clusters/"
            
            # Add text search if query provided
            if query:
                params["q"] = query
            
            results = await client._paginated_search(endpoint, params, params.get("limit", 20))
            return results
            
        except Exception as e:
            logger.error(f"Generic case search failed: {e}")
            return []
    
    async def get_case_details(
        self,
        case_id: str,
        include_full_text: bool = True,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific legal case.
        
        Args:
            case_id: CourtListener case ID or citation
            include_full_text: Include full case text
            include_citations: Extract legal citations
            
        Returns:
            Detailed case information
        """
        try:
            client = await self._get_client()
            
            # Get case details using existing client method
            case_details = await client.get_case_details(case_id)
            
            if not case_details:
                return {
                    "error": f"Case not found: {case_id}",
                    "case_id": case_id
                }
            
            # Format detailed response
            result = {
                "case_id": case_id,
                "basic_info": {
                    "citation": case_details.get("citation", ""),
                    "case_name": case_details.get("case_name", ""),
                    "court": {
                        "id": case_details.get("court", ""),
                        "name": self.court_mappings.get(case_details.get("court", ""), "Unknown Court")
                    },
                    "date_filed": case_details.get("date_filed", ""),
                    "precedential_status": case_details.get("precedential_status", ""),
                    "judges": case_details.get("judges", ""),
                    "nature_of_suit": case_details.get("nature_of_suit", "")
                },
                "authority_analysis": {
                    "authority_score": self._calculate_case_authority(case_details),
                    "court_level": self._get_court_level(case_details.get("court", "")),
                    "precedential_value": case_details.get("precedential_status", "")
                }
            }
            
            # Add full text if requested
            if include_full_text:
                result["full_text"] = case_details.get("full_text", "")
                result["word_count"] = len(case_details.get("full_text", "").split()) if case_details.get("full_text") else 0
            
            # Extract citations if requested
            if include_citations:
                citations = await client.extract_citations_from_case(case_details)
                result["citations"] = {
                    "total_count": len(citations),
                    "citations": citations[:50],  # Limit to first 50 citations
                    "citation_types": self._categorize_citations(citations)
                }
            
            # Add opinion information
            if case_details.get("opinions"):
                result["opinions"] = [
                    {
                        "type": opinion.get("type", ""),
                        "author": opinion.get("author", ""),
                        "per_curiam": opinion.get("per_curiam", False),
                        "word_count": len(opinion.get("plain_text", "").split()) if opinion.get("plain_text") else 0
                    }
                    for opinion in case_details["opinions"][:5]  # Limit to 5 opinions
                ]
            
            logger.info(f"Retrieved detailed case information for: {case_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get case details for {case_id}: {e}")
            return {
                "error": str(e),
                "case_id": case_id
            }
    
    async def citation_expansion(
        self,
        seed_case_id: str,
        expansion_depth: int = 2,
        max_cases: int = 50,
        jurisdiction_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Discover related cases through citation analysis.
        
        Args:
            seed_case_id: Starting case ID for expansion
            expansion_depth: How many citation levels to expand
            max_cases: Maximum total cases to discover
            jurisdiction_filter: Limit to specific jurisdictions
            
        Returns:
            Citation network expansion results
        """
        try:
            client = await self._get_client()
            
            # Use existing citation-driven expansion
            expansion_jobs = await client.citation_driven_expansion(
                seed_case_id=seed_case_id,
                max_first_order=min(max_cases // 2, 25),
                max_second_order=min(max_cases, 50)
            )
            
            # Filter by jurisdiction if specified
            if jurisdiction_filter:
                filtered_jobs = []
                for job in expansion_jobs:
                    # This would require additional API calls to check jurisdiction
                    # For now, include all jobs
                    filtered_jobs.append(job)
                expansion_jobs = filtered_jobs
            
            # Format results
            result = {
                "seed_case_id": seed_case_id,
                "expansion_depth": expansion_depth,
                "max_cases": max_cases,
                "jurisdiction_filter": jurisdiction_filter,
                "discovered_cases": {
                    "total": len(expansion_jobs),
                    "by_priority": {}
                },
                "citation_network": []
            }
            
            # Group by priority/type
            priority_groups = {}
            for job in expansion_jobs:
                priority = job.priority
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(job)
            
            result["discovered_cases"]["by_priority"] = {
                str(priority): len(jobs) for priority, jobs in priority_groups.items()
            }
            
            # Add detailed case information for top results
            for job in expansion_jobs[:20]:  # Limit to top 20 for detailed info
                case_info = {
                    "case_id": job.case_id,
                    "priority": job.priority,
                    "ingestion_type": job.ingestion_type,
                    "discovered_from": job.discovered_from,
                    "metadata": job.metadata,
                    "source_url": job.source_url
                }
                result["citation_network"].append(case_info)
            
            logger.info(f"Citation expansion from {seed_case_id} found {len(expansion_jobs)} related cases")
            return result
            
        except Exception as e:
            logger.error(f"Citation expansion failed for {seed_case_id}: {e}")
            return {
                "error": str(e),
                "seed_case_id": seed_case_id,
                "discovered_cases": {"total": 0},
                "citation_network": []
            }
    
    def _calculate_case_authority(self, case_data: Dict[str, Any]) -> float:
        """Calculate authority score for a case"""
        court_id = case_data.get("court", "")
        
        # Federal court scoring
        if court_id in self.jurisdiction_hierarchy["federal"]:
            court_score = self.jurisdiction_hierarchy["federal"].get(court_id, 6.0)
        else:
            # State court scoring
            if court_id in ["nj", "ny", "cal", "tex", "fla", "ill", "pa", "ohio", "mich", "ga", "nc", "va", "wash", "mass", "md"]:
                court_score = self.jurisdiction_hierarchy["state"]["supreme"]
            elif "app" in court_id or "appellate" in court_id.lower():
                court_score = self.jurisdiction_hierarchy["state"]["appellate"]
            else:
                court_score = self.jurisdiction_hierarchy["state"]["trial"]
        
        # Adjust for precedential status
        precedential_multiplier = {
            "Published": 1.0,
            "Unpublished": 0.7,
            "Errata": 0.5,
            "Separate": 0.8,
            "In-chambers": 0.4,
            "Unknown": 0.6
        }.get(case_data.get("precedential_status", "Unknown"), 0.6)
        
        # Adjust for recency (cases lose authority over time)
        date_filed = case_data.get("date_filed")
        recency_multiplier = 1.0
        if date_filed:
            try:
                case_date = datetime.fromisoformat(date_filed.replace("Z", "+00:00"))
                years_old = (datetime.now(timezone.utc) - case_date).days / 365.25
                recency_multiplier = max(0.3, 1.0 - (years_old * 0.02))  # 2% decay per year, min 0.3
            except:
                pass
        
        return min(10.0, court_score * precedential_multiplier * recency_multiplier)
    
    def _get_court_level(self, court_id: str) -> str:
        """Determine court level for authority analysis"""
        if court_id == "scotus":
            return "Supreme Court"
        elif court_id.startswith("ca"):
            return "Federal Appellate"
        elif "d" in court_id and len(court_id) <= 4:
            return "Federal District"
        elif court_id in ["nj", "ny", "cal", "tex", "fla", "ill", "pa", "ohio", "mich", "ga", "nc", "va", "wash", "mass", "md"]:
            return "State Supreme"
        elif "app" in court_id:
            return "State Appellate"
        else:
            return "State Trial"
    
    def _get_courts_searched(self, jurisdiction: Optional[str], court_type: Optional[str]) -> List[str]:
        """Get list of courts searched for metadata"""
        if jurisdiction and jurisdiction in self.court_mappings:
            return [self.court_mappings[jurisdiction]]
        
        if court_type == "federal":
            return ["All Federal Courts"]
        elif court_type == "state":
            return ["All State Courts"]
        elif court_type == "supreme":
            return ["Supreme Courts"]
        elif court_type == "appellate":
            return ["Appellate Courts"]
        else:
            return ["All U.S. Courts"]
    
    def _extract_practice_areas(self, case_data: Dict[str, Any]) -> List[str]:
        """Extract practice areas from case data"""
        # This is a simplified implementation
        # In a full system, this would use NLP to analyze case content
        nature_of_suit = case_data.get("nature_of_suit", "").lower()
        case_name = case_data.get("case_name", "").lower()
        
        practice_areas = []
        
        # Criminal law indicators
        if any(term in nature_of_suit or term in case_name for term in ["criminal", "prosecution", "defendant", "murder", "theft", "drug"]):
            practice_areas.append("criminal")
        
        # Civil rights indicators  
        if any(term in nature_of_suit or term in case_name for term in ["civil rights", "discrimination", "equal protection", "due process"]):
            practice_areas.append("civil_rights")
        
        # Employment indicators
        if any(term in nature_of_suit or term in case_name for term in ["employment", "labor", "workplace", "termination", "harassment"]):
            practice_areas.append("employment")
        
        # Contract indicators
        if any(term in nature_of_suit or term in case_name for term in ["contract", "breach", "agreement", "commercial"]):
            practice_areas.append("contract")
        
        # Constitutional indicators
        if any(term in nature_of_suit or term in case_name for term in ["constitutional", "amendment", "first amendment", "fourth amendment"]):
            practice_areas.append("constitutional")
        
        return practice_areas if practice_areas else ["general"]
    
    def _categorize_citations(self, citations: List[str]) -> Dict[str, int]:
        """Categorize citations by type"""
        categories = {
            "federal_appellate": 0,
            "federal_district": 0,
            "supreme_court": 0,
            "state_courts": 0,
            "other": 0
        }
        
        for citation in citations:
            if "U.S." in citation:
                categories["supreme_court"] += 1
            elif "F.2d" in citation or "F.3d" in citation:
                categories["federal_appellate"] += 1
            elif "F.Supp" in citation:
                categories["federal_district"] += 1
            elif any(state in citation for state in ["N.J.", "N.Y.", "Cal.", "Tex.", "Fla."]):
                categories["state_courts"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    async def get_court_hierarchy(self) -> Dict[str, Any]:
        """Get U.S. court hierarchy information"""
        return {
            "federal_system": {
                "supreme_court": {
                    "name": "Supreme Court of the United States", 
                    "code": "scotus",
                    "authority_score": 10.0,
                    "description": "Highest court in the United States"
                },
                "circuit_courts": [
                    {"name": self.court_mappings[code], "code": code, "authority_score": 8.0}
                    for code in self.court_mappings.keys() if code.startswith("ca")
                ],
                "district_courts": {
                    "description": "94 federal judicial districts",
                    "authority_score": 6.0
                }
            },
            "state_systems": {
                "supreme_courts": [
                    {"name": self.court_mappings[code], "code": code, "authority_score": 8.0}
                    for code in ["nj", "ny", "cal", "tex", "fla", "ill", "pa", "ohio", "mich", "ga", "nc", "va", "wash", "mass", "md"]
                ],
                "appellate_courts": {
                    "description": "Intermediate appellate courts in most states",
                    "authority_score": 6.0
                },
                "trial_courts": {
                    "description": "State trial courts of general jurisdiction",
                    "authority_score": 4.0
                }
            }
        }
    
    async def get_jurisdiction_guide(self) -> Dict[str, Any]:
        """Get jurisdiction codes and coverage guide"""
        return {
            "federal_courts": {
                court_code: court_name for court_code, court_name in self.court_mappings.items()
                if court_code.startswith(("ca", "scotus")) or "d" in court_code
            },
            "state_courts": {
                court_code: court_name for court_code, court_name in self.court_mappings.items()
                if not court_code.startswith(("ca", "scotus")) and "d" not in court_code
            },
            "usage_examples": {
                "search_supreme_court": "jurisdiction: 'scotus'",
                "search_ninth_circuit": "jurisdiction: 'ca9'",
                "search_new_jersey": "jurisdiction: 'nj'",
                "search_federal_courts": "court_type: 'federal'",
                "search_all_appellate": "court_type: 'appellate'"
            },
            "authority_hierarchy": self.jurisdiction_hierarchy
        }