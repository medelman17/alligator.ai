"""
Case management endpoints for legal research platform.

Provides CRUD operations for legal cases, citations, and related entities.
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from api.dependencies import get_chroma_service, get_neo4j_service
from shared.models.legal_entities import (
    Case,
    CaseStatus,
    Citation,
    CourtLevel,
    PracticeArea,
)

router = APIRouter()


# Request/Response Models
class CaseCreateRequest(BaseModel):
    """Request model for creating a new case."""

    case_name: str = Field(..., min_length=1, max_length=500)
    citation: str = Field(..., min_length=1, max_length=100)
    court_id: str = Field(..., description="ID of the court")
    judge_id: Optional[str] = Field(None, description="ID of the judge")
    decision_date: date
    jurisdiction: str = Field(..., min_length=1, max_length=100)
    practice_areas: list[PracticeArea] = Field(default_factory=list)
    case_status: CaseStatus = Field(default=CaseStatus.GOOD_LAW)
    docket_number: Optional[str] = Field(None, max_length=100)
    case_text: Optional[str] = Field(None, description="Full text of the case")
    summary: Optional[str] = Field(None, max_length=2000)
    holding: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class CaseUpdateRequest(BaseModel):
    """Request model for updating a case."""

    case_name: Optional[str] = Field(None, min_length=1, max_length=500)
    case_status: Optional[CaseStatus] = None
    summary: Optional[str] = Field(None, max_length=2000)
    holding: Optional[str] = Field(None, max_length=1000)
    practice_areas: Optional[list[PracticeArea]] = None
    metadata: Optional[dict[str, Any]] = None


class CitationCreateRequest(BaseModel):
    """Request model for creating a citation relationship."""

    citing_case_id: str = Field(..., description="ID of the case that cites")
    cited_case_id: str = Field(..., description="ID of the case being cited")
    citation_text: str = Field(..., min_length=1, max_length=200)
    page_number: Optional[int] = Field(None, ge=1)
    context: Optional[str] = Field(None, max_length=1000, description="Context around the citation")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class CaseResponse(BaseModel):
    """Enhanced case response with additional computed fields."""

    case: Case
    authority_score: Optional[float] = None
    citation_count: Optional[int] = None
    citing_count: Optional[int] = None
    related_cases_count: Optional[int] = None
    good_law_verification: Optional[dict[str, Any]] = None
    treatment_analysis: Optional[dict[str, Any]] = None


class CaseListResponse(BaseModel):
    """Response model for case list operations."""

    cases: list[CaseResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


# Dependencies are now imported from api.dependencies


# Case CRUD Endpoints
@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str = Path(..., description="Case ID"),
    include_stats: bool = Query(True, description="Include citation statistics"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Get a specific case by ID with optional statistics.

    Returns case details along with computed metrics like authority score
    and citation counts if requested.
    """
    try:
        # Get the case
        case = await neo4j.get_case_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        response = CaseResponse(case=case)

        if include_stats:
            try:
                # Get enhanced authority score
                response.authority_score = await neo4j.calculate_authority_score(case_id)

                # Get citation counts
                citing_cases = await neo4j.get_citing_cases(case_id, limit=1000)
                cited_cases = await neo4j.get_cited_cases(case_id, limit=1000)

                response.citing_count = len(citing_cases)
                response.citation_count = len(cited_cases)
                response.related_cases_count = response.citing_count + response.citation_count

                # Get enhanced legal analysis if available
                try:
                    response.good_law_verification = await neo4j.verify_good_law_status(case_id)
                    response.treatment_analysis = await neo4j.analyze_citation_treatment(case_id)
                except Exception as e:
                    # Enhanced features may not be available in basic schema
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Enhanced analysis unavailable for {case_id}: {e}")
            except Exception as e:
                # If stats collection fails, log but don't fail the whole request
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Stats collection failed for {case_id}: {e}")
                response.authority_score = None

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case: {e!s}",
        )


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Cases per page"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    practice_area: Optional[PracticeArea] = Query(None, description="Filter by practice area"),
    court_level: Optional[CourtLevel] = Query(None, description="Filter by court level"),
    case_status: Optional[CaseStatus] = Query(None, description="Filter by case status"),
    date_from: Optional[date] = Query(None, description="Filter cases from this date"),
    date_to: Optional[date] = Query(None, description="Filter cases to this date"),
    neo4j=Depends(get_neo4j_service),
):
    """
    List cases with pagination and filtering options.

    Returns a paginated list of cases matching the specified criteria.
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Build filter criteria
        practice_areas = [practice_area] if practice_area else None

        # Get cases from Neo4j
        cases = await neo4j.find_cases_by_criteria(
            jurisdiction=jurisdiction,
            practice_areas=practice_areas,
            court_level=court_level,
            case_status=case_status,
            date_from=date_from,
            date_to=date_to,
            limit=page_size + 1,  # Get one extra to check if there are more
            offset=offset,
        )

        # Check if there are more pages
        has_next = len(cases) > page_size
        if has_next:
            cases = cases[:page_size]  # Remove the extra case

        # Build response cases with enhanced stats
        response_cases = []
        for case in cases:
            authority_score = await neo4j.calculate_authority_score(case.id)
            case_response = CaseResponse(case=case, authority_score=authority_score)

            # Add basic verification for list view (less expensive)
            try:
                good_law_status = await neo4j.verify_good_law_status(case.id)
                case_response.good_law_verification = {
                    "status": good_law_status.get("good_law_confidence", "unknown"),
                    "confidence": good_law_status.get("good_law_confidence", "unknown")
                }
            except Exception:
                pass  # Enhanced features may not be available

            response_cases.append(case_response)

        # Get total count (this is expensive, could be optimized)
        # TODO: Implement count-only query for better performance
        all_cases = await neo4j.find_cases_by_criteria(
            jurisdiction=jurisdiction,
            practice_areas=practice_areas,
            court_level=court_level,
            case_status=case_status,
            date_from=date_from,
            date_to=date_to,
            limit=10000,  # Large limit to get count
        )
        total_count = len(all_cases)

        return CaseListResponse(
            cases=response_cases,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list cases: {e!s}"
        )


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    request: CaseCreateRequest, neo4j=Depends(get_neo4j_service), chroma=Depends(get_chroma_service)
):
    """
    Create a new case.

    Creates a case in Neo4j and optionally indexes the text in ChromaDB.
    """
    try:
        # Create case object
        case = Case(
            case_name=request.case_name,
            citation=request.citation,
            court_id=request.court_id,
            judge_id=request.judge_id,
            decision_date=request.decision_date,
            jurisdiction=request.jurisdiction,
            practice_areas=request.practice_areas,
            case_status=request.case_status,
            docket_number=request.docket_number,
            summary=request.summary,
            holding=request.holding,
            metadata=request.metadata or {},
        )

        # Create case in Neo4j
        case_id = await neo4j.create_case(case)
        case.id = case_id

        # Index case text in ChromaDB if provided
        if request.case_text:
            await chroma.add_documents(
                collection_name="cases",
                documents=[request.case_text],
                metadatas=[
                    {
                        "case_id": case_id,
                        "case_name": request.case_name,
                        "citation": request.citation,
                        "jurisdiction": request.jurisdiction,
                        "decision_date": request.decision_date.isoformat(),
                        "practice_areas": [pa.value for pa in request.practice_areas],
                    }
                ],
                ids=[case_id],
            )

        # Calculate initial authority score
        authority_score = await neo4j.calculate_authority_score(case_id)

        return CaseResponse(
            case=case,
            authority_score=authority_score,
            citation_count=0,
            citing_count=0,
            related_cases_count=0,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {e!s}",
        )


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str = Path(..., description="Case ID"),
    request: CaseUpdateRequest = ...,
    neo4j=Depends(get_neo4j_service),
):
    """
    Update an existing case.

    Updates case fields in Neo4j. Only provided fields are updated.
    """
    try:
        # Check if case exists
        existing_case = await neo4j.get_case_by_id(case_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Build update data
        update_data = {}
        if request.case_name is not None:
            update_data["case_name"] = request.case_name
        if request.case_status is not None:
            update_data["case_status"] = request.case_status
        if request.summary is not None:
            update_data["summary"] = request.summary
        if request.holding is not None:
            update_data["holding"] = request.holding
        if request.practice_areas is not None:
            update_data["practice_areas"] = request.practice_areas
        if request.metadata is not None:
            update_data["metadata"] = request.metadata

        # Update case in Neo4j
        await neo4j.update_case(case_id, update_data)

        # Get updated case
        updated_case = await neo4j.get_case_by_id(case_id)
        authority_score = await neo4j.calculate_authority_score(case_id)

        return CaseResponse(case=updated_case, authority_score=authority_score)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update case: {e!s}",
        )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str = Path(..., description="Case ID"),
    neo4j=Depends(get_neo4j_service),
    chroma=Depends(get_chroma_service),
):
    """
    Delete a case.

    Removes case from both Neo4j and ChromaDB.
    """
    try:
        # Check if case exists
        existing_case = await neo4j.get_case_by_id(case_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Delete from Neo4j (this should also delete related citations)
        await neo4j.delete_case(case_id)

        # Delete from ChromaDB
        try:
            # Note: ChromaDB delete might fail if document doesn't exist, that's OK
            await chroma.delete_documents("cases", [case_id])
        except Exception:
            pass  # Ignore ChromaDB deletion errors

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete case: {e!s}",
        )


# Citation Endpoints
@router.get("/{case_id}/citations", response_model=list[Citation])
async def get_case_citations(
    case_id: str = Path(..., description="Case ID"),
    direction: str = Query(
        "both", pattern="^(citing|cited|both)$", description="Citation direction"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum citations to return"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Get citations for a specific case.

    Returns cases that cite this case, cases cited by this case, or both.
    """
    try:
        citations = []

        if direction in ["citing", "both"]:
            citing_cases = await neo4j.get_citing_cases(case_id, limit=limit)
            citations.extend([citation for _, citation in citing_cases])

        if direction in ["cited", "both"]:
            cited_cases = await neo4j.get_cited_cases(case_id, limit=limit)
            citations.extend([citation for _, citation in cited_cases])

        return citations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get citations: {e!s}",
        )


@router.post("/{case_id}/citations", response_model=Citation, status_code=status.HTTP_201_CREATED)
async def create_citation(
    case_id: str = Path(..., description="Citing case ID"),
    request: CitationCreateRequest = ...,
    neo4j=Depends(get_neo4j_service),
):
    """
    Create a citation relationship between two cases.

    Creates a citation edge in the Neo4j graph.
    """
    try:
        # Validate that both cases exist
        citing_case = await neo4j.get_case_by_id(request.citing_case_id)
        cited_case = await neo4j.get_case_by_id(request.cited_case_id)

        if not citing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Citing case {request.citing_case_id} not found",
            )

        if not cited_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cited case {request.cited_case_id} not found",
            )

        # Create citation object
        citation = Citation(
            citing_case_id=request.citing_case_id,
            cited_case_id=request.cited_case_id,
            citation_text=request.citation_text,
            page_number=request.page_number,
            context=request.context,
            metadata=request.metadata or {},
        )

        # Create citation in Neo4j
        citation_id = await neo4j.create_citation(citation)
        citation.id = citation_id

        return citation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create citation: {e!s}",
        )


# Enhanced Legal Analysis Endpoints
@router.get("/{case_id}/treatment-analysis", response_model=dict[str, Any])
async def get_treatment_analysis(
    case_id: str = Path(..., description="Case ID"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Get comprehensive citation treatment analysis for a case.

    Analyzes how the case has been treated by subsequent courts
    with sophisticated scoring and confidence assessment.
    """
    try:
        # Check if case exists
        case = await neo4j.get_case_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Get enhanced treatment analysis
        treatment_analysis = await neo4j.analyze_citation_treatment(case_id)

        return treatment_analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Treatment analysis failed: {e!s}",
        )


@router.get("/{case_id}/good-law-status", response_model=dict[str, Any])
async def get_good_law_status(
    case_id: str = Path(..., description="Case ID"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Verify if a case is still good law.

    Provides confidence assessment based on citation analysis
    and identifies any overruling cases.
    """
    try:
        # Check if case exists
        case = await neo4j.get_case_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Get good law verification
        verification = await neo4j.verify_good_law_status(case_id)

        return verification

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Good law verification failed: {e!s}",
        )


@router.get("/{case_id}/authoritative-precedents", response_model=list[dict[str, Any]])
async def get_authoritative_precedents(
    case_id: str = Path(..., description="Case ID"),
    target_jurisdictions: Optional[str] = Query(None, description="Comma-separated jurisdictions"),
    practice_areas: Optional[str] = Query(None, description="Comma-separated practice areas"),
    limit: int = Query(10, ge=1, le=50, description="Maximum precedents to return"),
    neo4j=Depends(get_neo4j_service),
):
    """
    Find authoritative precedents for a case.

    Uses sophisticated multi-factor scoring to identify the most
    relevant and authoritative precedents.
    """
    try:
        # Check if case exists
        case = await neo4j.get_case_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found"
            )

        # Parse query parameters
        jurisdictions = []
        if target_jurisdictions:
            jurisdictions = [j.strip() for j in target_jurisdictions.split(",")]
        if not jurisdictions:
            jurisdictions = [case.jurisdiction]  # Default to case's jurisdiction

        areas = []
        if practice_areas:
            areas = [a.strip() for a in practice_areas.split(",")]
        if not areas and case.practice_areas:
            areas = case.practice_areas  # Default to case's practice areas

        # Get authoritative precedents
        precedents = await neo4j.find_authoritative_precedents(
            case_id=case_id,
            target_jurisdictions=jurisdictions,
            practice_areas=areas,
            primary_jurisdiction=case.jurisdiction,
            limit=limit
        )

        return precedents

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Precedent analysis failed: {e!s}",
        )
