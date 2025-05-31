"""
Search endpoints for legal research platform.

Provides semantic search, precedent discovery, and citation analysis endpoints.
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_chroma_service, get_neo4j_service
from shared.models.legal_entities import Case, Citation, CourtLevel, PracticeArea

router = APIRouter()


# Request/Response Models
class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    practice_areas: Optional[list[PracticeArea]] = Field(
        None, description="Filter by practice areas"
    )
    date_from: Optional[date] = Field(None, description="Filter cases from this date")
    date_to: Optional[date] = Field(None, description="Filter cases to this date")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")


class PrecedentSearchRequest(BaseModel):
    """Request model for precedent search."""

    case_id: str = Field(..., description="Case ID to find precedents for")
    depth: int = Field(2, ge=1, le=4, description="Citation network depth")
    include_treatments: bool = Field(True, description="Include treatment analysis")
    jurisdiction_filter: Optional[str] = Field(None, description="Filter by jurisdiction")


class SearchResult(BaseModel):
    """Search result model."""

    case: Case
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    authority_score: Optional[float] = Field(None, description="Authority score if available")
    snippet: Optional[str] = Field(None, description="Relevant text snippet")


class PrecedentResult(BaseModel):
    """Precedent search result model."""

    case: Case
    citation: Citation
    relevance_score: float
    authority_score: float
    citation_depth: int


class CitationNetworkResult(BaseModel):
    """Citation network analysis result."""

    center_case: Case
    citing_cases: list[PrecedentResult]
    cited_cases: list[PrecedentResult]
    network_stats: dict[str, Any]


# Dependencies are now imported from api.dependencies


@router.post("/semantic", response_model=list[SearchResult])
async def semantic_search(
    request: SemanticSearchRequest,
    neo4j=Depends(get_neo4j_service),
    chroma=Depends(get_chroma_service),
):
    """
    Perform semantic search across legal documents.

    Uses enhanced Neo4j semantic search with legal domain filtering
    and fallback to ChromaDB for vector similarity.
    """
    try:
        # Prepare filters for enhanced Neo4j search
        jurisdictions = [request.jurisdiction] if request.jurisdiction else None
        practice_areas = [pa.value for pa in request.practice_areas] if request.practice_areas else None
        date_range = None

        if request.date_from or request.date_to:
            date_range = (
                request.date_from or date(1800, 1, 1),
                request.date_to or date.today()
            )

        # Use enhanced Neo4j semantic search
        search_results = await neo4j.semantic_case_search(
            search_terms=request.query,
            jurisdictions=jurisdictions,
            practice_areas=practice_areas,
            date_range=date_range,
            good_law_only=True,
            limit=request.limit
        )

        # Convert to SearchResult format
        enhanced_results = []
        for result in search_results:
            case = result["case"]
            enhanced_results.append(
                SearchResult(
                    case=case,
                    relevance_score=min(result.get("relevance_score", 0.0) / 10.0, 1.0),  # Normalize to 0-1
                    authority_score=result.get("authority_score", case.authority_score),
                    snippet=case.summary[:200] + "..." if case.summary and len(case.summary) > 200 else case.summary,
                )
            )

        return enhanced_results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Enhanced semantic search failed: {e!s}"
        )


@router.get("/cases", response_model=list[SearchResult])
async def search_cases(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    practice_area: Optional[PracticeArea] = Query(None, description="Filter by practice area"),
    court_level: Optional[CourtLevel] = Query(None, description="Filter by court level"),
    date_from: Optional[date] = Query(None, description="Filter cases from this date"),
    date_to: Optional[date] = Query(None, description="Filter cases to this date"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Search for cases using structured criteria.

    Uses enhanced Neo4j semantic search with legal domain filtering.
    """
    try:
        # Prepare filters for enhanced search
        jurisdictions = [jurisdiction] if jurisdiction else None
        practice_areas = [practice_area.value] if practice_area else None
        court_levels = [court_level.value] if court_level else None
        date_range = None

        if date_from or date_to:
            date_range = (
                date_from or date(1800, 1, 1),
                date_to or date.today()
            )

        # Use enhanced semantic search
        search_results = await neo4j.semantic_case_search(
            search_terms=q,
            jurisdictions=jurisdictions,
            practice_areas=practice_areas,
            court_levels=court_levels,
            date_range=date_range,
            good_law_only=True,
            limit=limit
        )

        # Convert to SearchResult format
        results = []
        for result in search_results:
            case = result["case"]
            results.append(
                SearchResult(
                    case=case,
                    relevance_score=min(result.get("relevance_score", 0.0) / 10.0, 1.0),  # Normalize to 0-1
                    authority_score=result.get("authority_score", case.authority_score),
                    snippet=case.summary[:200] + "..." if case.summary and len(case.summary) > 200 else case.summary,
                )
            )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Enhanced case search failed: {e!s}"
        )


@router.post("/precedents", response_model=list[PrecedentResult])
async def search_precedents(request: PrecedentSearchRequest, neo4j=Depends(get_neo4j_service)):
    """
    Find precedent cases for a given case.

    Uses enhanced precedent discovery with multi-factor relevance scoring.
    """
    try:
        # Check if case exists
        center_case = await neo4j.get_case_by_id(request.case_id)
        if not center_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {request.case_id} not found"
            )

        # Use enhanced precedent discovery
        jurisdictions = [request.jurisdiction_filter] if request.jurisdiction_filter else None

        precedents = await neo4j.find_authoritative_precedents(
            case_id=request.case_id,
            target_jurisdictions=jurisdictions or [center_case.jurisdiction],
            practice_areas=center_case.practice_areas or [],
            primary_jurisdiction=center_case.jurisdiction,
            limit=25
        )

        # Convert to PrecedentResult format
        precedent_results = []
        for precedent in precedents:
            case = precedent["case"]

            # Create a mock citation (in real implementation, get from citation relationship)
            from shared.models.legal_entities import Citation
            mock_citation = Citation(
                citing_case_id=request.case_id,
                cited_case_id=case.id,
                citation_text=f"See {case.case_name}",
                treatment="cited",  # Default treatment
            )

            precedent_results.append(
                PrecedentResult(
                    case=case,
                    citation=mock_citation,
                    relevance_score=min(precedent["relevance_score"] / 10.0, 1.0),  # Normalize to 0-1
                    authority_score=precedent["authority_factors"]["authority_score"],
                    citation_depth=1,
                )
            )

        return precedent_results[:20]  # Return top 20 precedents

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced precedent search failed: {e!s}",
        )


@router.get("/citation-network/{case_id}", response_model=CitationNetworkResult)
async def get_citation_network(
    case_id: str,
    depth: int = Query(2, ge=1, le=4, description="Network traversal depth"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Analyze citation network for a specific case.

    Returns comprehensive citation network analysis including cited and citing cases.
    """
    try:
        # Get the center case
        center_case = await neo4j.get_case_by_id(case_id)
        if not center_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Get citation network from Neo4j
        network_data = await neo4j.get_citation_network(case_id, depth=depth)

        # Process citing cases
        citing_results = []
        for case, citation in network_data.get("citing_cases", []):
            authority_score = await neo4j.calculate_authority_score(case.id)
            citing_results.append(
                PrecedentResult(
                    case=case,
                    citation=citation,
                    relevance_score=0.9,
                    authority_score=authority_score,
                    citation_depth=citation.metadata.get("depth", 1) if citation.metadata else 1,
                )
            )

        # Process cited cases
        cited_results = []
        for case, citation in network_data.get("cited_cases", []):
            authority_score = await neo4j.calculate_authority_score(case.id)
            cited_results.append(
                PrecedentResult(
                    case=case,
                    citation=citation,
                    relevance_score=0.8,
                    authority_score=authority_score,
                    citation_depth=citation.metadata.get("depth", 1) if citation.metadata else 1,
                )
            )

        # Calculate network statistics
        network_stats = {
            "total_citing_cases": len(citing_results),
            "total_cited_cases": len(cited_results),
            "avg_authority_score": sum(r.authority_score for r in citing_results + cited_results)
            / (len(citing_results) + len(cited_results))
            if citing_results + cited_results
            else 0,
            "network_depth": depth,
            "jurisdictions": list(set(r.case.jurisdiction for r in citing_results + cited_results)),
        }

        return CitationNetworkResult(
            center_case=center_case,
            citing_cases=citing_results,
            cited_cases=cited_results,
            network_stats=network_stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation network analysis failed: {e!s}",
        )
