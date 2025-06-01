"""
CourtListener API client for ingesting New Jersey legal data.

Implements the architecture decisions from ADR-002, ADR-003, and ADR-006:
- Excellence-first processing with premium LLM models
- Intelligent rate limiting (4,000/hour target) 
- New Jersey jurisdiction focus for MVP
- Citation-driven case expansion workflow
- Legal-aware document chunking strategies
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import httpx
import json
from urllib.parse import urlencode

from shared.models.legal_entities import (
    Case, Court, Judge, Citation, CourtLevel, CaseStatus, 
    CitationTreatment, PracticeArea
)

logger = logging.getLogger(__name__)


class NewJerseyCourtType(Enum):
    """New Jersey court types for MVP scope."""
    SUPREME = "nj"  # New Jersey Supreme Court
    APPELLATE = "njsuperapp"  # New Jersey Superior Court, Appellate Division
    SUPERIOR = "njsuper"  # New Jersey Superior Court
    # Related Federal Courts
    DISTRICT_NJ = "njd"  # U.S. District Court for the District of New Jersey
    THIRD_CIRCUIT = "ca3"  # U.S. Court of Appeals for the Third Circuit (NJ cases)


@dataclass
class RateLimitInfo:
    """Track rate limit state for intelligent throttling."""
    requests_made: int = 0
    window_start: float = field(default_factory=time.time)
    max_requests_per_hour: int = 4000  # 80% of 5,000 limit for safety
    
    @property
    def requests_remaining(self) -> int:
        """Calculate remaining requests in current window."""
        current_time = time.time()
        # Reset window if hour has passed
        if current_time - self.window_start >= 3600:
            self.requests_made = 0
            self.window_start = current_time
        
        return max(0, self.max_requests_per_hour - self.requests_made)
    
    @property
    def can_make_request(self) -> bool:
        """Check if we can make another request."""
        return self.requests_remaining > 0
    
    def record_request(self):
        """Record that a request was made."""
        self.requests_made += 1


@dataclass
class CaseIngestionJob:
    """Represents a case ingestion job with priority and metadata."""
    case_id: str
    priority: int  # Higher = more important
    source_url: str
    ingestion_type: str  # "seed", "first_order", "second_order"
    discovered_from: Optional[str] = None  # Parent case that led to discovery
    metadata: Dict[str, Any] = field(default_factory=dict)


class CourtListenerClient:
    """
    CourtListener API client focused on New Jersey jurisdiction.
    
    Implements excellence-first processing strategy:
    - Premium LLM models for all legal analysis
    - Citation-driven case expansion
    - New Jersey court focus for MVP
    - Intelligent rate limiting and quality gates
    """
    
    BASE_URL = "https://www.courtlistener.com/api/rest/v3/"
    
    def __init__(self, api_token: str, timeout: int = 30):
        self.api_token = api_token
        self.timeout = timeout
        self.rate_limit = RateLimitInfo()
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Token {api_token}",
                "User-Agent": "alligator.ai-legal-research/1.0",
                "Accept": "application/json"
            },
            timeout=timeout
        )
        
        # Track ingestion state
        self.ingestion_queue: List[CaseIngestionJob] = []
        self.processed_cases: Set[str] = set()
        self.failed_cases: Set[str] = set()
        
        # New Jersey court mappings
        self.nj_courts = {
            court.value: court for court in NewJerseyCourtType
        }
        
        logger.info("CourtListener client initialized for New Jersey jurisdiction")
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make rate-limited request to CourtListener API.
        
        Implements intelligent throttling from ADR-002:
        - 4,000 requests/hour target (80% of limit)
        - Automatic backoff when approaching limits
        - Comprehensive error handling
        """
        # Check rate limits
        if not self.rate_limit.can_make_request:
            wait_time = 3600 - (time.time() - self.rate_limit.window_start)
            logger.warning(f"Rate limit reached. Waiting {wait_time:.0f} seconds.")
            await asyncio.sleep(wait_time)
        
        try:
            response = await self.client.get(endpoint, params=params)
            self.rate_limit.record_request()
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                logger.warning("Hit rate limit, backing off")
                await asyncio.sleep(60)  # Wait 1 minute
                return await self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def search_new_jersey_cases(
        self, 
        limit: int = 100,
        court_types: List[NewJerseyCourtType] = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for New Jersey cases using CourtListener API.
        
        Args:
            limit: Maximum number of cases to retrieve
            court_types: Specific NJ court types to search (defaults to all)
            date_range: (start_date, end_date) for filtering cases
        
        Returns:
            List of case data from CourtListener
        """
        if court_types is None:
            court_types = list(NewJerseyCourtType)
        
        all_cases = []
        
        for court_type in court_types:
            logger.info(f"Searching {court_type.name} court for cases")
            
            params = {
                "court": court_type.value,
                "ordering": "-date_filed",  # Most recent first
                "page_size": min(limit, 20)  # CourtListener max page size
            }
            
            if date_range:
                start_date, end_date = date_range
                params["date_filed__gte"] = start_date.strftime("%Y-%m-%d")
                params["date_filed__lte"] = end_date.strftime("%Y-%m-%d")
            
            try:
                cases = await self._paginated_search("clusters/", params, limit)
                all_cases.extend(cases)
                logger.info(f"Found {len(cases)} cases from {court_type.name}")
                
            except Exception as e:
                logger.error(f"Error searching {court_type.name}: {e}")
                continue
        
        # Sort by authority score (court hierarchy + recency)
        all_cases.sort(key=lambda c: self._calculate_authority_score(c), reverse=True)
        
        return all_cases[:limit]
    
    async def _paginated_search(
        self, 
        endpoint: str, 
        params: Dict[str, Any], 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Handle paginated search results."""
        all_results = []
        page = 1
        
        while len(all_results) < max_results:
            params["page"] = page
            
            try:
                response = await self._make_request(endpoint, params)
                results = response.get("results", [])
                
                if not results:
                    break
                
                all_results.extend(results)
                
                # Check if more pages available
                if not response.get("next"):
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error in paginated search page {page}: {e}")
                break
        
        return all_results[:max_results]
    
    def _calculate_authority_score(self, case_data: Dict[str, Any]) -> float:
        """
        Calculate authority score based on court hierarchy and recency.
        
        Implements prioritization algorithm from ADR-002:
        - Court authority weight (40%)
        - Recency score (30%) 
        - Citation impact (20%)
        - Practice area relevance (10%)
        """
        court_id = case_data.get("court", "")
        
        # Court authority weights
        court_weights = {
            "nj": 9.0,  # NJ Supreme Court
            "njsuperapp": 7.0,  # NJ Appellate
            "njsuper": 6.0,  # NJ Superior
            "ca3": 8.0,  # 3rd Circuit 
            "njd": 6.5,  # NJ District
        }
        
        court_weight = court_weights.get(court_id, 5.0) * 0.4
        
        # Recency score (newer cases get higher score)
        date_filed = case_data.get("date_filed")
        recency_score = 0.0
        if date_filed:
            try:
                case_date = datetime.fromisoformat(date_filed.replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - case_date).days
                # Score decreases with age, max score 1.0 for recent cases
                recency_score = max(0, 1.0 - (days_old / 3650)) * 0.3  # 10 year decay
            except Exception:
                recency_score = 0.1
        
        # Citation impact (from precedential value)
        precedential_status = case_data.get("precedential_status", "")
        citation_score = {
            "Published": 0.2,
            "Unpublished": 0.1,
            "Errata": 0.05,
            "Separate": 0.15,
            "In-chambers": 0.05,
            "Relating-to": 0.1,
            "Unknown": 0.1
        }.get(precedential_status, 0.1) * 0.2
        
        # Practice area relevance (basic scoring for now)
        practice_area_score = 0.1  # Placeholder
        
        total_score = court_weight + recency_score + citation_score + practice_area_score
        
        return min(10.0, total_score)  # Cap at 10.0
    
    async def get_case_details(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed case information including full text.
        
        Returns comprehensive case data for LLM processing.
        """
        try:
            # Get cluster details (case metadata)
            cluster_data = await self._make_request(f"clusters/{case_id}/")
            
            # Get opinions (full text)
            opinions = []
            if cluster_data.get("sub_opinions"):
                for opinion_url in cluster_data["sub_opinions"]:
                    opinion_id = opinion_url.split("/")[-2]  # Extract ID from URL
                    opinion_data = await self._make_request(f"opinions/{opinion_id}/")
                    opinions.append(opinion_data)
            
            # Combine cluster and opinion data
            full_case_data = {
                **cluster_data,
                "opinions": opinions,
                "full_text": self._extract_full_text(opinions)
            }
            
            return full_case_data
            
        except Exception as e:
            logger.error(f"Error getting case details for {case_id}: {e}")
            return None
    
    def _extract_full_text(self, opinions: List[Dict[str, Any]]) -> str:
        """Extract and combine full text from all opinions."""
        text_parts = []
        
        for opinion in opinions:
            # Try different text formats in order of preference
            text_content = (
                opinion.get("html_columbia") or 
                opinion.get("html_lawbox") or 
                opinion.get("html") or
                opinion.get("plain_text") or
                ""
            )
            
            if text_content:
                # Basic HTML cleaning if needed
                if text_content.startswith("<"):
                    text_content = self._clean_html(text_content)
                
                text_parts.append(text_content)
        
        return "\n\n".join(text_parts)
    
    def _clean_html(self, html_content: str) -> str:
        """Basic HTML cleaning for legal text."""
        # Remove HTML tags (basic implementation)
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        
        return clean_text.strip()
    
    async def extract_citations_from_case(self, case_data: Dict[str, Any]) -> List[str]:
        """
        Extract legal citations from case text.
        
        This is a preliminary implementation that will be enhanced
        with premium LLM models as per ADR-003.
        """
        full_text = case_data.get("full_text", "")
        
        if not full_text:
            return []
        
        # Legal citation patterns (basic implementation)
        citation_patterns = [
            # Federal cases: 123 F.3d 456, 123 F.Supp.2d 789
            r'\d+\s+F\.(?:2d|3d|Supp\.2?d?|App\'x)\s+\d+',
            # State cases: 123 N.J. 456, 123 A.2d 789
            r'\d+\s+N\.J\.(?:Super\.)?(?:\s+(?:App\.\s+Div\.)?)??\s+\d+',
            r'\d+\s+A\.(?:2d|3d)?\s+\d+',
            # U.S. Supreme Court: 123 U.S. 456
            r'\d+\s+U\.S\.\s+\d+',
            # Federal supplement: 123 F.Supp. 456
            r'\d+\s+F\.Supp\.(?:2d)?\s+\d+',
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            citations.extend(matches)
        
        # Remove duplicates and clean up
        unique_citations = list(set(citations))
        
        # Basic validation - ensure citations have proper format
        validated_citations = []
        for citation in unique_citations:
            if self._validate_citation_format(citation):
                validated_citations.append(citation.strip())
        
        logger.debug(f"Extracted {len(validated_citations)} citations from case")
        return validated_citations
    
    def _validate_citation_format(self, citation: str) -> bool:
        """Basic validation of citation format."""
        # Must have numbers, letters, and proper legal abbreviations
        if not re.search(r'\d+', citation):
            return False
        
        # Must contain recognized legal reporters
        legal_reporters = [
            "F.", "F.2d", "F.3d", "F.Supp", "F.Supp.2d",
            "U.S.", "S.Ct.", "L.Ed", "L.Ed.2d",
            "N.J.", "N.J.Super", "A.", "A.2d", "A.3d"
        ]
        
        return any(reporter in citation for reporter in legal_reporters)
    
    async def citation_driven_expansion(
        self, 
        seed_case_id: str, 
        max_first_order: int = 10,
        max_second_order: int = 50
    ) -> List[CaseIngestionJob]:
        """
        Implement citation-driven case expansion workflow from ADR-003.
        
        1. Extract citations from seed case
        2. Download and process first-order citations immediately
        3. Queue second-order citations for batch processing
        4. Return prioritized ingestion jobs
        """
        logger.info(f"Starting citation-driven expansion from case {seed_case_id}")
        
        # Get seed case details
        seed_case = await self.get_case_details(seed_case_id)
        if not seed_case:
            logger.error(f"Could not retrieve seed case {seed_case_id}")
            return []
        
        # Extract citations from seed case
        citations = await self.extract_citations_from_case(seed_case)
        logger.info(f"Found {len(citations)} citations in seed case")
        
        ingestion_jobs = []
        first_order_cases = []
        
        # Process first-order citations immediately (up to budget)
        processed_count = 0
        for citation in citations[:max_first_order]:
            if not self.rate_limit.can_make_request:
                logger.warning("Rate limit reached during first-order expansion")
                break
            
            try:
                # Search for cited case
                cited_cases = await self.search_cases_by_citation(citation)
                
                for cited_case in cited_cases[:1]:  # Take first match
                    case_id = str(cited_case.get("id", ""))
                    
                    if case_id not in self.processed_cases:
                        job = CaseIngestionJob(
                            case_id=case_id,
                            priority=8,  # High priority for first-order
                            source_url=f"clusters/{case_id}/",
                            ingestion_type="first_order",
                            discovered_from=seed_case_id,
                            metadata={"citation": citation}
                        )
                        ingestion_jobs.append(job)
                        first_order_cases.append(cited_case)
                        processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing citation {citation}: {e}")
                continue
        
        logger.info(f"Queued {processed_count} first-order cases for processing")
        
        # Process second-order citations (from first-order cases)
        second_order_count = 0
        for first_order_case in first_order_cases:
            if second_order_count >= max_second_order:
                break
            
            try:
                first_order_details = await self.get_case_details(str(first_order_case.get("id", "")))
                if first_order_details:
                    second_order_citations = await self.extract_citations_from_case(first_order_details)
                    
                    for citation in second_order_citations[:5]:  # Limit per case
                        if second_order_count >= max_second_order:
                            break
                        
                        cited_cases = await self.search_cases_by_citation(citation)
                        for cited_case in cited_cases[:1]:
                            case_id = str(cited_case.get("id", ""))
                            
                            if case_id not in self.processed_cases:
                                job = CaseIngestionJob(
                                    case_id=case_id,
                                    priority=5,  # Medium priority for second-order
                                    source_url=f"clusters/{case_id}/",
                                    ingestion_type="second_order",
                                    discovered_from=first_order_case.get("id", ""),
                                    metadata={"citation": citation}
                                )
                                ingestion_jobs.append(job)
                                second_order_count += 1
            
            except Exception as e:
                logger.error(f"Error processing second-order citations: {e}")
                continue
        
        logger.info(f"Queued {second_order_count} second-order cases for batch processing")
        
        # Sort jobs by priority
        ingestion_jobs.sort(key=lambda job: job.priority, reverse=True)
        
        return ingestion_jobs
    
    async def search_cases_by_citation(self, citation: str) -> List[Dict[str, Any]]:
        """Search for cases by citation string."""
        try:
            params = {
                "citation": citation,
                "page_size": 5  # Limit results
            }
            
            response = await self._make_request("clusters/", params)
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Error searching for citation {citation}: {e}")
            return []
    
    async def get_case_processing_stats(self) -> Dict[str, int]:
        """Get statistics about case processing."""
        return {
            "processed_cases": len(self.processed_cases),
            "failed_cases": len(self.failed_cases),
            "queued_jobs": len(self.ingestion_queue),
            "rate_limit_remaining": self.rate_limit.requests_remaining
        }


# Example usage and testing
async def main():
    """Example usage of CourtListener client for New Jersey cases."""
    import os
    
    # Get API token from environment
    api_token = os.getenv("COURTLISTENER_API_TOKEN")
    if not api_token:
        logger.error("COURTLISTENER_API_TOKEN environment variable required")
        return
    
    client = CourtListenerClient(api_token)
    
    try:
        # Search for recent New Jersey Supreme Court cases
        logger.info("Searching for New Jersey Supreme Court cases...")
        
        nj_cases = await client.search_new_jersey_cases(
            limit=5,
            court_types=[NewJerseyCourtType.SUPREME]
        )
        
        logger.info(f"Found {len(nj_cases)} New Jersey cases")
        
        for case in nj_cases:
            case_name = case.get("case_name", "Unknown")
            case_id = case.get("id", "Unknown")
            court = case.get("court", "Unknown")
            logger.info(f"  - {case_name} (ID: {case_id}, Court: {court})")
        
        # Test citation expansion on first case
        if nj_cases:
            first_case_id = str(nj_cases[0].get("id", ""))
            logger.info(f"Testing citation expansion on case {first_case_id}")
            
            expansion_jobs = await client.citation_driven_expansion(
                first_case_id, 
                max_first_order=3,
                max_second_order=5
            )
            
            logger.info(f"Citation expansion generated {len(expansion_jobs)} ingestion jobs")
            
            for job in expansion_jobs[:3]:  # Show first 3
                logger.info(f"  - Job: {job.case_id} (Priority: {job.priority}, Type: {job.ingestion_type})")
        
        # Show processing stats
        stats = await client.get_case_processing_stats()
        logger.info(f"Processing stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())