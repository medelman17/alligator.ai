"""
Research workflow endpoints for AI-powered legal research.

Provides endpoints for conducting legal research, precedent analysis, and memo generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_chroma_service, get_neo4j_service, get_precedent_analyzer
from shared.models.legal_entities import PracticeArea

router = APIRouter()

# Enums
class ResearchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    PRECEDENT_ANALYSIS = "precedent_analysis"
    OPPOSITION_RESEARCH = "opposition_research"
    AUTHORITY_ANALYSIS = "authority_analysis"
    TREATMENT_ANALYSIS = "treatment_analysis"


# Request/Response Models
class ResearchRequest(BaseModel):
    """Request model for conducting legal research."""
    query: str = Field(..., min_length=1, max_length=2000, description="Research question or topic")
    jurisdiction: Optional[str] = Field(None, description="Target jurisdiction")
    practice_areas: Optional[list[PracticeArea]] = Field(None, description="Relevant practice areas")
    case_ids: Optional[list[str]] = Field(None, description="Specific cases to analyze")
    analysis_types: list[AnalysisType] = Field(default=[AnalysisType.PRECEDENT_ANALYSIS], description="Types of analysis to perform")
    max_cases: int = Field(20, ge=1, le=100, description="Maximum cases to analyze")
    include_memo: bool = Field(True, description="Generate research memo")


class ResearchSession(BaseModel):
    """Research session model."""
    id: str
    query: str
    status: ResearchStatus
    analysis_types: list[AnalysisType]
    jurisdiction: Optional[str] = None
    practice_areas: Optional[list[PracticeArea]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[dict[str, Any]] = None
    memo: Optional[str] = None
    error_message: Optional[str] = None


class PrecedentAnalysisRequest(BaseModel):
    """Request for precedent analysis."""
    case_id: str = Field(..., description="Case ID to analyze")
    depth: int = Field(2, ge=1, le=4, description="Analysis depth")
    include_treatments: bool = Field(True, description="Include treatment analysis")
    jurisdiction_filter: Optional[str] = Field(None, description="Filter by jurisdiction")


class PrecedentAnalysisResult(BaseModel):
    """Result of precedent analysis."""
    case_id: str
    analysis_summary: str
    key_precedents: list[dict[str, Any]]
    authority_analysis: dict[str, Any]
    treatment_analysis: Optional[dict[str, Any]] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    supporting_cases: list[str]
    distinguishing_cases: list[str]
    recommendations: list[str]


class MemoGenerationRequest(BaseModel):
    """Request for memo generation."""
    research_session_id: str = Field(..., description="Research session ID")
    memo_type: str = Field("research_memo", description="Type of memo to generate")
    include_citations: bool = Field(True, description="Include case citations")
    format: str = Field("markdown", pattern="^(markdown|html|text)$", description="Output format")


class MemoResponse(BaseModel):
    """Generated memo response."""
    memo_content: str
    format: str
    citations_count: int
    generated_at: datetime
    research_session_id: str


# Dependencies are now imported from api.dependencies


# In-memory storage for demo (replace with proper database in production)
research_sessions: dict[str, ResearchSession] = {}


def generate_session_id() -> str:
    """Generate a unique session ID."""
    import uuid
    return str(uuid.uuid4())


@router.post("/sessions", response_model=ResearchSession, status_code=status.HTTP_201_CREATED)
async def create_research_session(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    neo4j = Depends(get_neo4j_service),
    chroma = Depends(get_chroma_service),
    analyzer = Depends(get_precedent_analyzer)
):
    """
    Create a new research session and start background analysis.

    Initiates AI-powered legal research based on the provided query and parameters.
    """
    try:
        # Create research session
        session_id = generate_session_id()
        session = ResearchSession(
            id=session_id,
            query=request.query,
            status=ResearchStatus.PENDING,
            analysis_types=request.analysis_types,
            jurisdiction=request.jurisdiction,
            practice_areas=request.practice_areas,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        research_sessions[session_id] = session

        # Start background research task
        background_tasks.add_task(
            conduct_research_background,
            session_id,
            request,
            neo4j,
            chroma,
            analyzer
        )

        return session

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research session: {e!s}"
        )


async def conduct_research_background(
    session_id: str,
    request: ResearchRequest,
    neo4j,
    chroma,
    analyzer
):
    """Background task to conduct legal research."""
    try:
        session = research_sessions[session_id]
        session.status = ResearchStatus.IN_PROGRESS
        session.updated_at = datetime.utcnow()

        results = {}

        # Perform different types of analysis
        for analysis_type in request.analysis_types:
            if analysis_type == AnalysisType.PRECEDENT_ANALYSIS:
                # Use semantic search to find relevant cases
                search_results = await chroma.semantic_search(
                    query=request.query,
                    collection_name="cases",
                    limit=request.max_cases,
                    jurisdiction=request.jurisdiction
                )

                # Analyze each case
                precedent_results = []
                for result in search_results[:10]:  # Limit for performance
                    case_id = result.get("metadata", {}).get("case_id")
                    if case_id:
                        # Run precedent analysis
                        analysis_result = await analyzer.analyze_precedent(
                            case_id=case_id,
                            query=request.query,
                            jurisdiction=request.jurisdiction
                        )
                        if analysis_result:
                            precedent_results.append(analysis_result)

                results["precedent_analysis"] = {
                    "cases_analyzed": len(precedent_results),
                    "results": precedent_results[:5],  # Top 5 results
                    "summary": f"Analyzed {len(precedent_results)} relevant precedents"
                }

        # Generate memo if requested
        memo_content = None
        if request.include_memo and results:
            memo_content = await generate_research_memo(
                query=request.query,
                results=results,
                jurisdiction=request.jurisdiction
            )

        # Update session with results
        session.results = results
        session.memo = memo_content
        session.status = ResearchStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()

    except Exception as e:
        # Update session with error
        session = research_sessions.get(session_id)
        if session:
            session.status = ResearchStatus.FAILED
            session.error_message = str(e)
            session.updated_at = datetime.utcnow()


async def generate_research_memo(
    query: str,
    results: dict[str, Any],
    jurisdiction: Optional[str] = None
) -> str:
    """Generate a research memo from analysis results."""
    # Simple memo generation (could be enhanced with LLM)
    memo_lines = [
        "# Legal Research Memo",
        "",
        f"**Research Query:** {query}",
        f"**Jurisdiction:** {jurisdiction or 'Not specified'}",
        f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d')}",
        "",
        "## Executive Summary",
        ""
    ]

    # Add precedent analysis if available
    if "precedent_analysis" in results:
        precedent_data = results["precedent_analysis"]
        memo_lines.extend([
            "## Precedent Analysis",
            "",
            f"Analyzed {precedent_data['cases_analyzed']} relevant precedents.",
            precedent_data["summary"],
            ""
        ])

        # Add top cases
        if precedent_data.get("results"):
            memo_lines.append("### Key Precedents")
            memo_lines.append("")
            for i, result in enumerate(precedent_data["results"][:3], 1):
                memo_lines.append(f"{i}. Case ID: {result.get('case_id', 'Unknown')}")
                memo_lines.append(f"   Summary: {result.get('analysis_summary', 'No summary available')}")
                memo_lines.append("")

    memo_lines.extend([
        "## Recommendations",
        "",
        "- Review the identified precedents for applicability to your case",
        "- Consider jurisdiction-specific factors in your analysis",
        "- Consult with legal counsel for case-specific advice",
        "",
        "---",
        "*This memo was generated by alligator.ai legal research platform.*"
    ])

    return "\n".join(memo_lines)


@router.get("/sessions/{session_id}", response_model=ResearchSession)
async def get_research_session(session_id: str):
    """
    Get research session status and results.

    Returns the current state of a research session including any results.
    """
    session = research_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {session_id} not found"
        )

    return session


@router.get("/sessions", response_model=list[ResearchSession])
async def list_research_sessions(
    status_filter: Optional[ResearchStatus] = None,
    limit: int = 20
):
    """
    List research sessions with optional status filtering.

    Returns a list of research sessions, optionally filtered by status.
    """
    sessions = list(research_sessions.values())

    if status_filter:
        sessions = [s for s in sessions if s.status == status_filter]

    # Sort by creation date (newest first)
    sessions.sort(key=lambda x: x.created_at, reverse=True)

    return sessions[:limit]


@router.post("/analyze-precedent", response_model=PrecedentAnalysisResult)
async def analyze_precedent(
    request: PrecedentAnalysisRequest,
    analyzer = Depends(get_precedent_analyzer),
    neo4j = Depends(get_neo4j_service)
):
    """
    Perform detailed precedent analysis for a specific case.

    Analyzes citation networks, authority, and treatment of a specific case.
    """
    try:
        # Check if case exists
        case = await neo4j.get_case_by_id(request.case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {request.case_id} not found"
            )

        # Perform precedent analysis
        analysis_result = await analyzer.analyze_precedent(
            case_id=request.case_id,
            query=f"Analysis of {case.case_name}",
            jurisdiction=request.jurisdiction_filter,
            depth=request.depth,
            include_treatments=request.include_treatments
        )

        if not analysis_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Precedent analysis failed"
            )

        return PrecedentAnalysisResult(
            case_id=request.case_id,
            analysis_summary=analysis_result.get("summary", "No summary available"),
            key_precedents=analysis_result.get("precedents", []),
            authority_analysis=analysis_result.get("authority_analysis", {}),
            treatment_analysis=analysis_result.get("treatment_analysis") if request.include_treatments else None,
            confidence_score=analysis_result.get("confidence_score", 0.5),
            supporting_cases=analysis_result.get("supporting_cases", []),
            distinguishing_cases=analysis_result.get("distinguishing_cases", []),
            recommendations=analysis_result.get("recommendations", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Precedent analysis failed: {e!s}"
        )


@router.post("/generate-memo", response_model=MemoResponse)
async def generate_memo(request: MemoGenerationRequest):
    """
    Generate a legal research memo from session results.

    Creates a formatted legal memo based on research session data.
    """
    try:
        # Get research session
        session = research_sessions.get(request.research_session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research session {request.research_session_id} not found"
            )

        if not session.results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Research session has no results to generate memo from"
            )

        # Generate memo content
        memo_content = await generate_research_memo(
            query=session.query,
            results=session.results,
            jurisdiction=session.jurisdiction
        )

        # Convert format if needed
        if request.format == "html":
            # Simple markdown to HTML conversion
            import re
            memo_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', memo_content, flags=re.MULTILINE)
            memo_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', memo_content, flags=re.MULTILINE)
            memo_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', memo_content, flags=re.MULTILINE)
            memo_content = memo_content.replace('\n\n', '</p><p>').replace('\n', '<br>')
            memo_content = f"<div>{memo_content}</div>"
        elif request.format == "text":
            # Strip markdown formatting
            import re
            memo_content = re.sub(r'^#+\s+', '', memo_content, flags=re.MULTILINE)
            memo_content = re.sub(r'\*\*(.+?)\*\*', r'\1', memo_content)
            memo_content = re.sub(r'\*(.+?)\*', r'\1', memo_content)

        # Count citations (simple heuristic)
        citation_count = memo_content.count("Case ID:") + memo_content.count("v.")

        return MemoResponse(
            memo_content=memo_content,
            format=request.format,
            citations_count=citation_count,
            generated_at=datetime.utcnow(),
            research_session_id=request.research_session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memo generation failed: {e!s}"
        )
