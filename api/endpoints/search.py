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

    Uses vector embeddings to find semantically similar cases based on the query.
    Can be filtered by jurisdiction, practice areas, and date ranges.
    """
    try:
        # Prepare search filters
        search_filters = {}
        if request.jurisdiction:
            search_filters["jurisdiction"] = request.jurisdiction
        if request.practice_areas:
            search_filters["practice_areas"] = [pa.value for pa in request.practice_areas]
        if request.date_from:
            search_filters["date_from"] = request.date_from.isoformat()
        if request.date_to:
            search_filters["date_to"] = request.date_to.isoformat()

        # Perform semantic search using ChromaDB
        search_results = await chroma.semantic_search(
            query=request.query, collection_name="cases", limit=request.limit, **search_filters
        )

        # Enhance results with Neo4j data
        enhanced_results = []
        for result in search_results:
            case_id = result.get("metadata", {}).get("case_id")
            if case_id:
                # Get case details from Neo4j
                case = await neo4j.get_case_by_id(case_id)
                if case:
                    # Get authority score
                    authority_score = await neo4j.calculate_authority_score(case_id)

                    enhanced_results.append(
                        SearchResult(
                            case=case,
                            relevance_score=result.get("distance", 0.0),
                            authority_score=authority_score,
                            snippet=result.get("document", "")[:200] + "..."
                            if result.get("document")
                            else None,
                        )
                    )

        return enhanced_results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {e!s}"
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

    Performs graph-based search using Neo4j with filtering capabilities.
    """
    try:
        # Build search criteria
        practice_areas = [practice_area] if practice_area else None

        # Perform Neo4j search
        cases = await neo4j.find_cases_by_criteria(
            jurisdiction=jurisdiction,
            practice_areas=practice_areas,
            court_level=court_level,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        # Calculate authority scores and build results
        results = []
        for case in cases:
            authority_score = await neo4j.calculate_authority_score(case.id)

            # Simple text matching for relevance (could be enhanced)
            relevance_score = 0.5  # TODO: Implement proper relevance scoring

            results.append(
                SearchResult(
                    case=case, relevance_score=relevance_score, authority_score=authority_score
                )
            )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Case search failed: {e!s}"
        )


@router.post("/precedents", response_model=list[PrecedentResult])
async def search_precedents(request: PrecedentSearchRequest, neo4j=Depends(get_neo4j_service)):
    """
    Find precedent cases for a given case.

    Analyzes citation networks to find related cases that may serve as precedents.
    """
    try:
        # Get citing cases (cases that cite this one)
        citing_cases = await neo4j.get_citing_cases(
            case_id=request.case_id,
            limit=50,  # Get more initially, then filter
        )

        # Get cited cases (cases this one cites)
        cited_cases = await neo4j.get_cited_cases(case_id=request.case_id, limit=50)

        precedent_results = []

        # Process citing cases
        for case, citation in citing_cases:
            if request.jurisdiction_filter and case.jurisdiction != request.jurisdiction_filter:
                continue

            authority_score = await neo4j.calculate_authority_score(case.id)

            precedent_results.append(
                PrecedentResult(
                    case=case,
                    citation=citation,
                    relevance_score=0.8,  # TODO: Implement relevance scoring
                    authority_score=authority_score,
                    citation_depth=1,
                )
            )

        # Process cited cases
        for case, citation in cited_cases:
            if request.jurisdiction_filter and case.jurisdiction != request.jurisdiction_filter:
                continue

            authority_score = await neo4j.calculate_authority_score(case.id)

            precedent_results.append(
                PrecedentResult(
                    case=case,
                    citation=citation,
                    relevance_score=0.7,  # Cited cases slightly lower relevance
                    authority_score=authority_score,
                    citation_depth=1,
                )
            )

        # Sort by authority score and relevance
        precedent_results.sort(key=lambda x: (x.authority_score, x.relevance_score), reverse=True)

        return precedent_results[:20]  # Return top 20 precedents

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Precedent search failed: {e!s}",
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
