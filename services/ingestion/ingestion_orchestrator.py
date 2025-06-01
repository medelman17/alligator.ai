"""
New Jersey Legal Data Ingestion Orchestrator.

Integrates all ingestion components into a cohesive system:
- CourtListener API client for New Jersey case discovery
- Premium LLM processing pipeline for legal analysis
- Sophisticated legal document chunking
- New Jersey jurisdiction mapping and court hierarchy
- Enhanced Neo4j and ChromaDB storage integration

Implements the complete ingestion workflow from ADR-002, ADR-003, and ADR-006.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import json
import time

from .courtlistener_client import CourtListenerClient, CaseIngestionJob, NewJerseyCourtType
from .llm_processor import (
    ExcellenceFirstProcessor, LegalAnalysisResult, ProcessingComplexity, LLMProvider
)
from .legal_chunking import (
    LegalDocumentChunkingPipeline, LegalChunk, LegalSectionType
)
from .nj_jurisdiction_mapper import NewJerseyJurisdictionMapper, CourtHierarchyInfo

from shared.models.legal_entities import (
    Case, Court, Citation, CitationTreatment, PracticeArea, CaseStatus
)
from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
from services.vector.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class IngestionStatus(Enum):
    """Status values for ingestion jobs."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class IngestionPriority(Enum):
    """Priority levels for ingestion jobs."""
    CRITICAL = 10    # Supreme Court cases, highly cited cases
    HIGH = 8         # Appellate court cases, recent decisions
    MEDIUM = 6       # Trial court cases, standard processing
    LOW = 4          # Older cases, low citation impact
    BACKGROUND = 2   # Bulk processing, completeness


@dataclass
class IngestionJobStatus:
    """Detailed status information for an ingestion job."""
    job_id: str
    case_id: str
    status: IngestionStatus
    priority: IngestionPriority
    
    # Processing stages
    discovery_completed: bool = False
    api_retrieval_completed: bool = False
    llm_analysis_completed: bool = False
    chunking_completed: bool = False
    storage_completed: bool = False
    
    # Results and metadata
    llm_analysis_result: Optional[LegalAnalysisResult] = None
    chunks_created: List[LegalChunk] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    processing_cost: float = 0.0
    
    # Timing information
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def processing_time(self) -> Optional[float]:
        """Calculate total processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if all processing stages are complete."""
        return all([
            self.discovery_completed,
            self.api_retrieval_completed,
            self.llm_analysis_completed,
            self.chunking_completed,
            self.storage_completed
        ])


@dataclass
class IngestionMetrics:
    """Metrics for monitoring ingestion performance."""
    total_jobs_processed: int = 0
    successful_completions: int = 0
    failed_jobs: int = 0
    jobs_requiring_review: int = 0
    
    # Processing stage metrics
    api_retrieval_failures: int = 0
    llm_processing_failures: int = 0
    chunking_failures: int = 0
    storage_failures: int = 0
    
    # Performance metrics
    average_processing_time: float = 0.0
    total_processing_cost: float = 0.0
    cases_per_hour: float = 0.0
    
    # Quality metrics
    average_confidence_score: float = 0.0
    expert_review_rate: float = 0.0


class NewJerseyIngestionOrchestrator:
    """
    Main orchestrator for New Jersey legal data ingestion.
    
    Implements the complete excellence-first ingestion workflow:
    1. Discovery: Find New Jersey cases via CourtListener API
    2. Retrieval: Get full case details and metadata
    3. Analysis: Premium LLM processing for legal analysis
    4. Chunking: Sophisticated legal document chunking
    5. Storage: Enhanced storage in Neo4j and ChromaDB
    6. Citation Expansion: Citation-driven case discovery
    """
    
    def __init__(
        self,
        courtlistener_api_token: str,
        openai_api_key: str = None,
        anthropic_api_key: str = None,
        neo4j_service: EnhancedNeo4jService = None,
        chroma_service: ChromaService = None
    ):
        # Initialize core components
        self.courtlistener_client = CourtListenerClient(courtlistener_api_token)
        self.llm_processor = ExcellenceFirstProcessor(openai_api_key, anthropic_api_key)
        self.chunking_pipeline = LegalDocumentChunkingPipeline()
        self.jurisdiction_mapper = NewJerseyJurisdictionMapper()
        
        # Storage services
        self.neo4j_service = neo4j_service
        self.chroma_service = chroma_service
        
        # Orchestrator state
        self.active_jobs: Dict[str, IngestionJobStatus] = {}
        self.completed_jobs: Dict[str, IngestionJobStatus] = {}
        self.processing_queue: List[CaseIngestionJob] = []
        self.processed_case_ids: Set[str] = set()
        
        # Performance tracking
        self.metrics = IngestionMetrics()
        self.start_time = datetime.now()
        
        logger.info("New Jersey ingestion orchestrator initialized")
    
    async def start_mvp_ingestion(
        self,
        max_cases: int = 100,
        court_types: List[NewJerseyCourtType] = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """
        Start MVP ingestion workflow for New Jersey courts.
        
        Args:
            max_cases: Maximum number of cases to process
            court_types: Specific NJ court types (defaults to MVP scope)
            date_range: Date range for case filtering
        
        Returns:
            Summary of ingestion results
        """
        
        if court_types is None:
            # Default MVP scope: NJ Supreme, Appellate, Superior + related federal
            court_types = [
                NewJerseyCourtType.NJ_SUPREME,
                NewJerseyCourtType.NJ_APPELLATE,
                NewJerseyCourtType.NJ_SUPERIOR,
                NewJerseyCourtType.DISTRICT_NJ,
                NewJerseyCourtType.THIRD_CIRCUIT
            ]
        
        logger.info(f"Starting MVP ingestion for {len(court_types)} court types, max {max_cases} cases")
        
        try:
            # Stage 1: Discovery
            logger.info("Stage 1: Discovering New Jersey cases")
            discovered_cases = await self._discover_nj_cases(max_cases, court_types, date_range)
            logger.info(f"Discovered {len(discovered_cases)} cases")
            
            # Stage 2: Create ingestion jobs with priority ranking
            logger.info("Stage 2: Creating prioritized ingestion jobs")
            ingestion_jobs = await self._create_prioritized_jobs(discovered_cases)
            logger.info(f"Created {len(ingestion_jobs)} ingestion jobs")
            
            # Stage 3: Process jobs in priority order
            logger.info("Stage 3: Processing ingestion jobs")
            processing_results = await self._process_ingestion_jobs(ingestion_jobs)
            
            # Stage 4: Citation-driven expansion
            logger.info("Stage 4: Citation-driven case expansion")
            expansion_results = await self._citation_expansion_workflow(processing_results)
            
            # Stage 5: Generate summary report
            summary = self._generate_ingestion_summary()
            
            logger.info("MVP ingestion workflow completed")
            return summary
            
        except Exception as e:
            logger.error(f"Error in MVP ingestion workflow: {e}")
            raise
    
    async def _discover_nj_cases(
        self,
        max_cases: int,
        court_types: List[NewJerseyCourtType],
        date_range: Tuple[datetime, datetime] = None
    ) -> List[Dict[str, Any]]:
        """Discover New Jersey cases using CourtListener API."""
        
        cases_per_court = max_cases // len(court_types)
        all_cases = []
        
        for court_type in court_types:
            try:
                court_cases = await self.courtlistener_client.search_new_jersey_cases(
                    limit=cases_per_court,
                    court_types=[court_type],
                    date_range=date_range
                )
                
                # Enhance cases with jurisdiction information
                for case in court_cases:
                    case["jurisdiction_info"] = self.jurisdiction_mapper.get_court_info(court_type.value)
                    case["authority_score"] = self._calculate_enhanced_authority_score(case)
                
                all_cases.extend(court_cases)
                logger.info(f"Found {len(court_cases)} cases from {court_type.value}")
                
            except Exception as e:
                logger.error(f"Error discovering cases from {court_type.value}: {e}")
                continue
        
        # Sort by authority score and return top cases
        all_cases.sort(key=lambda c: c.get("authority_score", 0), reverse=True)
        return all_cases[:max_cases]
    
    async def _create_prioritized_jobs(self, discovered_cases: List[Dict[str, Any]]) -> List[CaseIngestionJob]:
        """Create prioritized ingestion jobs from discovered cases."""
        
        jobs = []
        
        for case in discovered_cases:
            case_id = str(case.get("id", ""))
            court_id = case.get("court", "")
            authority_score = case.get("authority_score", 0.0)
            
            # Determine priority based on court hierarchy and authority
            priority = self._determine_ingestion_priority(court_id, authority_score, case)
            
            job = CaseIngestionJob(
                case_id=case_id,
                priority=priority.value,
                source_url=f"clusters/{case_id}/",
                ingestion_type="seed",
                metadata={
                    "court_id": court_id,
                    "authority_score": authority_score,
                    "case_name": case.get("case_name", ""),
                    "decision_date": case.get("date_filed", ""),
                    "precedential_status": case.get("precedential_status", "")
                }
            )
            jobs.append(job)
        
        # Sort by priority
        jobs.sort(key=lambda j: j.priority, reverse=True)
        
        return jobs
    
    def _determine_ingestion_priority(
        self,
        court_id: str,
        authority_score: float,
        case_data: Dict[str, Any]
    ) -> IngestionPriority:
        """Determine ingestion priority based on case characteristics."""
        
        # High priority courts
        if court_id in ["nj", "scotus"]:  # NJ Supreme Court, US Supreme Court
            return IngestionPriority.CRITICAL
        
        # Circuit courts and recent appellate decisions
        if court_id in ["ca3", "njsuperapp"]:
            return IngestionPriority.HIGH
        
        # High authority score cases
        if authority_score >= 8.0:
            return IngestionPriority.HIGH
        
        # Recent decisions (within last 2 years)
        decision_date = case_data.get("date_filed")
        if decision_date:
            try:
                case_date = datetime.fromisoformat(decision_date.replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - case_date).days
                if days_old <= 730:  # 2 years
                    return IngestionPriority.HIGH
            except Exception:
                pass
        
        # Published precedential decisions
        if case_data.get("precedential_status") == "Published":
            return IngestionPriority.MEDIUM
        
        # Default priority
        return IngestionPriority.LOW
    
    def _calculate_enhanced_authority_score(self, case_data: Dict[str, Any]) -> float:
        """Calculate enhanced authority score using jurisdiction mapper."""
        
        court_id = case_data.get("court", "")
        
        # Get base authority from jurisdiction mapper
        base_authority = self.jurisdiction_mapper.get_authority_weight(court_id)
        
        # Parse decision date
        decision_date = None
        if case_data.get("date_filed"):
            try:
                decision_date = datetime.fromisoformat(case_data["date_filed"].replace("Z", "+00:00"))
            except Exception:
                decision_date = datetime.now()
        
        if decision_date:
            precedential_status = case_data.get("precedential_status", "Unknown")
            enhanced_score = self.jurisdiction_mapper.calculate_case_authority_score(
                court_id, decision_date, precedential_status
            )
            return enhanced_score
        
        return base_authority
    
    async def _process_ingestion_jobs(self, jobs: List[CaseIngestionJob]) -> Dict[str, IngestionJobStatus]:
        """Process ingestion jobs with complete workflow."""
        
        completed_jobs = {}
        
        for i, job in enumerate(jobs):
            logger.info(f"Processing job {i+1}/{len(jobs)}: {job.case_id} (priority: {job.priority})")
            
            job_status = IngestionJobStatus(
                job_id=f"job_{int(time.time())}_{i}",
                case_id=job.case_id,
                status=IngestionStatus.PROCESSING,
                priority=IngestionPriority(job.priority),
                started_at=datetime.now()
            )
            
            try:
                # Stage 1: Retrieve case details
                case_data = await self._retrieve_case_details(job, job_status)
                if not case_data:
                    job_status.status = IngestionStatus.FAILED
                    job_status.error_messages.append("Failed to retrieve case details")
                    continue
                
                # Stage 2: LLM analysis
                analysis_result = await self._perform_llm_analysis(case_data, job_status)
                if not analysis_result:
                    job_status.status = IngestionStatus.FAILED
                    job_status.error_messages.append("LLM analysis failed")
                    continue
                
                job_status.llm_analysis_result = analysis_result
                
                # Stage 3: Legal document chunking
                chunks = await self._perform_legal_chunking(case_data, job_status)
                job_status.chunks_created = chunks
                
                # Stage 4: Store in databases
                await self._store_case_data(case_data, analysis_result, chunks, job_status)
                
                # Mark as completed or requiring review
                if analysis_result.requires_expert_review:
                    job_status.status = IngestionStatus.REQUIRES_REVIEW
                    self.metrics.jobs_requiring_review += 1
                else:
                    job_status.status = IngestionStatus.COMPLETED
                    self.metrics.successful_completions += 1
                
                job_status.completed_at = datetime.now()
                self.processed_case_ids.add(job.case_id)
                
            except Exception as e:
                logger.error(f"Error processing job {job.case_id}: {e}")
                job_status.status = IngestionStatus.FAILED
                job_status.error_messages.append(str(e))
                job_status.completed_at = datetime.now()
                self.metrics.failed_jobs += 1
            
            completed_jobs[job_status.job_id] = job_status
            self.metrics.total_jobs_processed += 1
        
        return completed_jobs
    
    async def _retrieve_case_details(
        self,
        job: CaseIngestionJob,
        job_status: IngestionJobStatus
    ) -> Optional[Dict[str, Any]]:
        """Retrieve detailed case information from CourtListener."""
        
        try:
            case_data = await self.courtlistener_client.get_case_details(job.case_id)
            
            if case_data:
                job_status.api_retrieval_completed = True
                return case_data
            else:
                job_status.error_messages.append("No case data returned from API")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving case {job.case_id}: {e}")
            job_status.error_messages.append(f"API retrieval error: {str(e)}")
            self.metrics.api_retrieval_failures += 1
            return None
    
    async def _perform_llm_analysis(
        self,
        case_data: Dict[str, Any],
        job_status: IngestionJobStatus
    ) -> Optional[LegalAnalysisResult]:
        """Perform comprehensive LLM analysis on case data."""
        
        try:
            # Determine processing complexity based on court and case characteristics
            court_id = case_data.get("court", "")
            complexity = self._determine_processing_complexity(court_id, case_data)
            
            # Run premium LLM analysis
            analysis_result = await self.llm_processor.process_case_comprehensive(
                case_data, complexity
            )
            
            job_status.llm_analysis_completed = True
            job_status.processing_cost += analysis_result.processing_cost
            self.metrics.total_processing_cost += analysis_result.processing_cost
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in LLM analysis for case {job_status.case_id}: {e}")
            job_status.error_messages.append(f"LLM analysis error: {str(e)}")
            self.metrics.llm_processing_failures += 1
            return None
    
    def _determine_processing_complexity(
        self,
        court_id: str,
        case_data: Dict[str, Any]
    ) -> ProcessingComplexity:
        """Determine LLM processing complexity based on case characteristics."""
        
        if court_id in ["nj", "scotus"]:  # Supreme courts
            return ProcessingComplexity.SUPREME_COURT
        elif court_id in ["ca3", "njsuperapp"]:  # Appellate courts
            return ProcessingComplexity.CIRCUIT_COURT
        else:  # Trial courts
            return ProcessingComplexity.DISTRICT_COURT
    
    async def _perform_legal_chunking(
        self,
        case_data: Dict[str, Any],
        job_status: IngestionJobStatus
    ) -> List[LegalChunk]:
        """Perform sophisticated legal document chunking."""
        
        try:
            full_text = case_data.get("full_text", "")
            if not full_text:
                logger.warning(f"No full text available for case {job_status.case_id}")
                return []
            
            # Determine document type for chunking strategy
            court_id = case_data.get("court", "")
            if court_id in ["nj", "scotus"]:
                document_type = "supreme_court_opinion"
            elif court_id in ["ca3", "njsuperapp"]:
                document_type = "circuit_opinion"
            else:
                document_type = "district_opinion"
            
            # Perform chunking
            chunks = self.chunking_pipeline.chunk_legal_document(
                document=full_text,
                document_type=document_type,
                complexity_level="high",
                metadata=case_data
            )
            
            job_status.chunking_completed = True
            return chunks
            
        except Exception as e:
            logger.error(f"Error in legal chunking for case {job_status.case_id}: {e}")
            job_status.error_messages.append(f"Chunking error: {str(e)}")
            self.metrics.chunking_failures += 1
            return []
    
    async def _store_case_data(
        self,
        case_data: Dict[str, Any],
        analysis_result: LegalAnalysisResult,
        chunks: List[LegalChunk],
        job_status: IngestionJobStatus
    ) -> bool:
        """Store processed case data in Neo4j and ChromaDB."""
        
        try:
            if not self.neo4j_service or not self.chroma_service:
                logger.warning("Storage services not available - skipping storage")
                job_status.storage_completed = True
                return True
            
            # Create enhanced Case entity
            case_entity = self._create_case_entity(case_data, analysis_result)
            
            # Store in Neo4j
            await self.neo4j_service.create_enhanced_case(case_entity)
            
            # Store citations in Neo4j
            for citation_data in analysis_result.extracted_citations:
                citation_entity = self._create_citation_entity(citation_data, case_entity.id)
                await self.neo4j_service.create_citation(citation_entity)
            
            # Store chunks in ChromaDB
            for chunk in chunks:
                await self.chroma_service.add_case_document(
                    case_entity,
                    chunk.content,
                    metadata={
                        "chunk_index": chunk.chunk_index,
                        "section_type": chunk.section_type.value,
                        "legal_context": chunk.legal_context
                    }
                )
            
            job_status.storage_completed = True
            return True
            
        except Exception as e:
            logger.error(f"Error storing case data for {job_status.case_id}: {e}")
            job_status.error_messages.append(f"Storage error: {str(e)}")
            self.metrics.storage_failures += 1
            return False
    
    def _create_case_entity(
        self,
        case_data: Dict[str, Any],
        analysis_result: LegalAnalysisResult
    ) -> Case:
        """Create Case entity from case data and analysis results."""
        
        case_id = str(case_data.get("id", ""))
        
        # Parse decision date
        decision_date = None
        if case_data.get("date_filed"):
            try:
                decision_date = datetime.fromisoformat(case_data["date_filed"].replace("Z", "+00:00"))
            except Exception:
                decision_date = datetime.now()
        
        case = Case(
            id=f"cl_{case_id}",  # Prefix with CourtListener source
            citation=case_data.get("citation", ""),
            case_name=case_data.get("case_name", ""),
            full_name=case_data.get("case_name_full", case_data.get("case_name", "")),
            court_id=case_data.get("court", ""),
            jurisdiction=case_data.get("court", ""),  # Use court ID as jurisdiction
            decision_date=decision_date,
            judges=[],  # Would be populated from opinion data
            status=CaseStatus.GOOD_LAW,  # Default, would be determined by analysis
            practice_areas=analysis_result.practice_areas,
            summary=case_data.get("summary", ""),
            holding=analysis_result.legal_holdings[0] if analysis_result.legal_holdings else "",
            procedural_posture=case_data.get("procedural_history", ""),
            disposition=case_data.get("disposition", ""),
            authority_score=analysis_result.authority_score,
            citation_count=len(analysis_result.extracted_citations)
        )
        
        return case
    
    def _create_citation_entity(self, citation_data: Dict[str, Any], citing_case_id: str) -> Citation:
        """Create Citation entity from citation analysis data."""
        
        return Citation(
            id=f"cite_{int(time.time())}_{hash(citation_data.get('citation', ''))}",
            citing_case_id=citing_case_id,
            cited_case_id=citation_data.get("case_name", ""),  # Would need resolution to actual case ID
            treatment=CitationTreatment.CITES,  # Default, would be determined from analysis
            context=citation_data.get("context", ""),
            strength=citation_data.get("strength", 0.5)
        )
    
    async def _citation_expansion_workflow(
        self,
        processing_results: Dict[str, IngestionJobStatus]
    ) -> Dict[str, Any]:
        """Implement citation-driven case expansion on successfully processed cases."""
        
        expansion_results = {
            "expansion_jobs_created": 0,
            "second_order_cases_discovered": 0,
            "expansion_errors": []
        }
        
        # Select high-quality completed cases for expansion
        expansion_candidates = []
        for job_status in processing_results.values():
            if (job_status.status == IngestionStatus.COMPLETED and 
                job_status.llm_analysis_result and
                job_status.llm_analysis_result.overall_confidence >= 0.90):
                expansion_candidates.append(job_status)
        
        logger.info(f"Running citation expansion on {len(expansion_candidates)} high-quality cases")
        
        for job_status in expansion_candidates[:5]:  # Limit to top 5 for MVP
            try:
                expansion_jobs = await self.courtlistener_client.citation_driven_expansion(
                    job_status.case_id,
                    max_first_order=3,  # Conservative for MVP
                    max_second_order=10
                )
                
                expansion_results["expansion_jobs_created"] += len(expansion_jobs)
                
                # Process a subset of expansion jobs
                for exp_job in expansion_jobs[:2]:  # Process top 2 from each expansion
                    if exp_job.case_id not in self.processed_case_ids:
                        # Add to processing queue (would be processed in next iteration)
                        self.processing_queue.append(exp_job)
                        expansion_results["second_order_cases_discovered"] += 1
                
            except Exception as e:
                logger.error(f"Error in citation expansion for {job_status.case_id}: {e}")
                expansion_results["expansion_errors"].append(str(e))
        
        return expansion_results
    
    def _generate_ingestion_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary of ingestion results."""
        
        processing_time = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate performance metrics
        if processing_time > 0:
            self.metrics.cases_per_hour = (self.metrics.total_jobs_processed / processing_time) * 3600
        
        if self.metrics.total_jobs_processed > 0:
            self.metrics.expert_review_rate = (
                self.metrics.jobs_requiring_review / self.metrics.total_jobs_processed
            )
        
        # Calculate average confidence score
        confidence_scores = []
        for job_status in self.completed_jobs.values():
            if (job_status.llm_analysis_result and 
                job_status.llm_analysis_result.overall_confidence > 0):
                confidence_scores.append(job_status.llm_analysis_result.overall_confidence)
        
        if confidence_scores:
            self.metrics.average_confidence_score = sum(confidence_scores) / len(confidence_scores)
        
        summary = {
            "ingestion_summary": {
                "total_processing_time_seconds": processing_time,
                "cases_processed": self.metrics.total_jobs_processed,
                "success_rate": (
                    self.metrics.successful_completions / max(self.metrics.total_jobs_processed, 1)
                ),
                "cases_per_hour": self.metrics.cases_per_hour,
                "total_cost": self.metrics.total_processing_cost
            },
            "quality_metrics": {
                "average_confidence_score": self.metrics.average_confidence_score,
                "expert_review_rate": self.metrics.expert_review_rate,
                "jobs_requiring_review": self.metrics.jobs_requiring_review
            },
            "processing_breakdown": {
                "successful_completions": self.metrics.successful_completions,
                "failed_jobs": self.metrics.failed_jobs,
                "api_retrieval_failures": self.metrics.api_retrieval_failures,
                "llm_processing_failures": self.metrics.llm_processing_failures,
                "chunking_failures": self.metrics.chunking_failures,
                "storage_failures": self.metrics.storage_failures
            },
            "system_status": {
                "processed_case_ids": len(self.processed_case_ids),
                "pending_jobs_in_queue": len(self.processing_queue),
                "jurisdiction_mapper_stats": self.jurisdiction_mapper.get_court_summary_stats()
            }
        }
        
        return summary
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and metrics."""
        
        active_job_count = len([j for j in self.active_jobs.values() 
                               if j.status == IngestionStatus.PROCESSING])
        
        return {
            "active_jobs": active_job_count,
            "completed_jobs": len(self.completed_jobs),
            "processed_cases": len(self.processed_case_ids),
            "pending_queue": len(self.processing_queue),
            "current_metrics": self.metrics.__dict__,
            "rate_limit_status": await self.courtlistener_client.get_case_processing_stats()
        }
    
    async def close(self):
        """Clean up resources."""
        await self.courtlistener_client.close()
        logger.info("Ingestion orchestrator closed")


# Example usage and testing
async def main():
    """Example usage of the ingestion orchestrator."""
    import os
    
    # Get API keys from environment
    courtlistener_token = os.getenv("COURTLISTENER_API_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not courtlistener_token:
        logger.error("COURTLISTENER_API_TOKEN environment variable required")
        return
    
    # Initialize orchestrator
    orchestrator = NewJerseyIngestionOrchestrator(
        courtlistener_api_token=courtlistener_token,
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key
        # Note: Neo4j and Chroma services would be injected in real application
    )
    
    try:
        logger.info("Starting MVP ingestion workflow")
        
        # Run MVP ingestion with limited scope for testing
        summary = await orchestrator.start_mvp_ingestion(
            max_cases=5,  # Small test run
            court_types=[NewJerseyCourtType.NJ_SUPREME]  # Just NJ Supreme Court
        )
        
        logger.info("Ingestion completed successfully")
        logger.info(f"Summary: {json.dumps(summary, indent=2, default=str)}")
        
        # Show processing status
        status = await orchestrator.get_processing_status()
        logger.info(f"Final status: {json.dumps(status, indent=2, default=str)}")
        
    except Exception as e:
        logger.error(f"Error in ingestion workflow: {e}")
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())