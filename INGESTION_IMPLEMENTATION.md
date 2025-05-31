# Legal Document Ingestion Implementation Plan

## Executive Summary

This document outlines a practical, phased implementation of the automated legal document ingestion system. The approach prioritizes MVP delivery, cost efficiency, and integration with existing platform components while providing a clear path to the full architecture described in `INGESTION_ARCHITECTURE_PROPOSAL.md`.

## Implementation Philosophy

### MVP-First Approach
- Start with CourtListener integration (highest ROI)
- Batch processing over real-time (cost efficiency)
- Eventual consistency over distributed transactions
- Manual triggers before automatic gap detection

### Cost-Conscious Design
- LLM usage optimization and budgeting
- Efficient caching and deduplication
- Rate limit coordination across sources
- Incremental processing with checkpoints

## Phase 1: MVP Implementation (Weeks 1-4)

### Core Components

#### 1. Basic Ingestion Service (`services/ingestion/`)

```python
# services/ingestion/core_ingester.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

class IngestionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class IngestionJob:
    id: str
    citation: str
    source: str
    priority: int
    status: IngestionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_msg: Optional[str] = None
    metadata: Dict = None

class CoreIngester:
    """MVP ingestion service focusing on CourtListener"""
    
    def __init__(self):
        self.court_listener = CourtListenerClient()
        self.neo4j_service = Neo4jService()
        self.chroma_service = ChromaService()
        self.job_queue = IngestionQueue()
        self.cost_tracker = CostTracker()
        
    async def process_batch(self, citations: List[str]) -> List[IngestionJob]:
        """Process a batch of citations with cost controls"""
        jobs = []
        
        for citation in citations:
            # Check if already exists
            if await self._document_exists(citation):
                jobs.append(IngestionJob(
                    id=generate_id(),
                    citation=citation,
                    source="skip",
                    priority=0,
                    status=IngestionStatus.SKIPPED
                ))
                continue
                
            # Check daily cost budget
            if not await self.cost_tracker.within_budget():
                logging.warning("Daily cost budget exceeded, queuing for tomorrow")
                break
                
            job = await self._process_single_document(citation)
            jobs.append(job)
            
        return jobs
        
    async def _process_single_document(self, citation: str) -> IngestionJob:
        """Process single document with error handling"""
        job = IngestionJob(
            id=generate_id(),
            citation=citation,
            source="courtlistener",
            priority=1,
            status=IngestionStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        
        try:
            # 1. Fetch from CourtListener
            document = await self.court_listener.fetch_by_citation(citation)
            if not document:
                job.status = IngestionStatus.FAILED
                job.error_msg = "Document not found"
                return job
                
            # 2. Extract basic metadata (no LLM yet)
            metadata = self._extract_basic_metadata(document)
            
            # 3. Update databases with eventual consistency
            await self._store_with_eventual_consistency(document, metadata)
            
            job.status = IngestionStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = IngestionStatus.FAILED
            job.error_msg = str(e)
            logging.error(f"Failed to process {citation}: {e}")
            
        return job
```

#### 2. CourtListener Integration

```python
# services/ingestion/sources/court_listener.py
import aiohttp
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class CourtListenerDocument:
    id: str
    citation: str
    case_name: str
    court: str
    date_filed: str
    text: str
    metadata: Dict

class CourtListenerClient:
    """MVP CourtListener integration with rate limiting"""
    
    def __init__(self):
        self.base_url = "https://www.courtlistener.com/api/rest/v3"
        self.rate_limiter = RateLimiter(30, 60)  # 30 requests per minute
        self.session = None
        
    async def fetch_by_citation(self, citation: str) -> Optional[CourtListenerDocument]:
        """Fetch document by citation with rate limiting"""
        await self.rate_limiter.acquire()
        
        try:
            # Search for the case
            search_url = f"{self.base_url}/search/"
            params = {
                "type": "o",  # opinions
                "q": citation,
                "format": "json"
            }
            
            async with self._get_session().get(search_url, params=params) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                results = data.get("results", [])
                
                if not results:
                    return None
                    
                # Get the first result
                opinion = results[0]
                
                # Fetch full text
                text = await self._fetch_opinion_text(opinion["resource_uri"])
                
                return CourtListenerDocument(
                    id=str(opinion["id"]),
                    citation=citation,
                    case_name=opinion.get("case_name", ""),
                    court=opinion.get("court", ""),
                    date_filed=opinion.get("date_filed", ""),
                    text=text,
                    metadata=opinion
                )
                
        except Exception as e:
            logging.error(f"CourtListener fetch failed for {citation}: {e}")
            return None
            
    async def _fetch_opinion_text(self, resource_uri: str) -> str:
        """Fetch full opinion text"""
        await self.rate_limiter.acquire()
        
        try:
            async with self._get_session().get(resource_uri) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("plain_text", data.get("html", ""))
                return ""
        except Exception:
            return ""
```

#### 3. Eventual Consistency Storage

```python
# services/ingestion/storage/eventual_consistency.py
import asyncio
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class StorageResult:
    service: str
    success: bool
    error: Optional[str] = None
    retry_count: int = 0

class EventualConsistencyStore:
    """Store documents across databases with eventual consistency"""
    
    def __init__(self):
        self.neo4j_service = Neo4jService()
        self.chroma_service = ChromaService()
        self.retry_queue = RetryQueue()
        
    async def store_document(self, document: CourtListenerDocument) -> List[StorageResult]:
        """Store document with eventual consistency guarantees"""
        results = []
        
        # Attempt all storage operations in parallel
        tasks = [
            self._store_in_neo4j(document),
            self._store_in_chroma(document)
        ]
        
        storage_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(storage_results):
            service = ["neo4j", "chroma"][i]
            
            if isinstance(result, Exception):
                # Schedule for retry
                await self._schedule_retry(service, document, str(result))
                results.append(StorageResult(service, False, str(result)))
            else:
                results.append(StorageResult(service, True))
                
        return results
        
    async def _store_in_neo4j(self, document: CourtListenerDocument):
        """Store case and citation relationships in Neo4j"""
        query = """
        MERGE (c:Case {id: $id})
        SET c.citation = $citation,
            c.case_name = $case_name,
            c.court = $court,
            c.date_filed = $date_filed,
            c.updated_at = datetime()
        """
        
        await self.neo4j_service.run_query(query, {
            "id": document.id,
            "citation": document.citation,
            "case_name": document.case_name,
            "court": document.court,
            "date_filed": document.date_filed
        })
        
    async def _store_in_chroma(self, document: CourtListenerDocument):
        """Store document text in ChromaDB for semantic search"""
        # Chunk the document for better search
        chunks = self._chunk_document(document.text)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "citation": document.citation,
                "case_name": document.case_name,
                "court": document.court,
                "date_filed": document.date_filed,
                "chunk_index": i
            })
            ids.append(f"{document.id}_{i}")
            
        await self.chroma_service.add_documents(
            collection_name="cases",
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
```

#### 4. Cost Tracking and Budget Controls

```python
# services/ingestion/cost_tracker.py
from datetime import datetime, date
from typing import Dict
import asyncio

class CostTracker:
    """Track and limit ingestion costs"""
    
    def __init__(self):
        self.daily_budget = 50.0  # $50/day
        self.cost_per_document = 0.10  # Estimated cost
        self.redis = Redis()
        
    async def within_budget(self) -> bool:
        """Check if we're within daily budget"""
        today = date.today().isoformat()
        spent_key = f"ingestion:cost:{today}"
        
        spent_today = float(await self.redis.get(spent_key) or 0)
        return spent_today < self.daily_budget
        
    async def record_cost(self, amount: float):
        """Record cost for today"""
        today = date.today().isoformat()
        spent_key = f"ingestion:cost:{today}"
        
        await self.redis.incrbyfloat(spent_key, amount)
        await self.redis.expire(spent_key, 86400)  # 24 hours
        
    async def get_daily_stats(self) -> Dict:
        """Get daily cost statistics"""
        today = date.today().isoformat()
        spent_key = f"ingestion:cost:{today}"
        count_key = f"ingestion:count:{today}"
        
        spent = float(await self.redis.get(spent_key) or 0)
        count = int(await self.redis.get(count_key) or 0)
        
        return {
            "date": today,
            "spent": spent,
            "budget": self.daily_budget,
            "remaining": self.daily_budget - spent,
            "documents_processed": count,
            "avg_cost_per_doc": spent / count if count > 0 else 0
        }
```

### Integration Points

#### 1. Manual Trigger API

```python
# api/endpoints/ingestion.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])

class IngestionRequest(BaseModel):
    citations: List[str]
    priority: int = 1

@router.post("/trigger")
async def trigger_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks
):
    """Manually trigger document ingestion"""
    if len(request.citations) > 100:
        raise HTTPException(400, "Maximum 100 citations per request")
        
    ingester = CoreIngester()
    
    # Start background processing
    background_tasks.add_task(
        ingester.process_batch,
        request.citations
    )
    
    return {
        "message": f"Ingestion started for {len(request.citations)} citations",
        "citations": request.citations
    }

@router.get("/status")
async def get_ingestion_status():
    """Get current ingestion status and costs"""
    cost_tracker = CostTracker()
    stats = await cost_tracker.get_daily_stats()
    
    return {
        "status": "operational",
        "daily_stats": stats,
        "queue_depth": await get_queue_depth()
    }
```

#### 2. Enhanced Legal Data Ingester

```python
# services/ingestion/legal_data_ingester.py (Enhanced)
from typing import List, Dict, Optional
import logging

class LegalDataIngester:
    """Enhanced legal data ingester with MVP implementation"""
    
    def __init__(self):
        self.core_ingester = CoreIngester()
        self.gap_detector = SimpleGapDetector()
        
    async def ingest_from_research_gaps(self, research_context: Dict) -> List[str]:
        """Simple gap detection from research context"""
        missing_citations = []
        
        # Extract citations from research context
        citations = self.gap_detector.extract_citations(research_context)
        
        # Check which ones we don't have
        for citation in citations:
            if not await self._document_exists(citation):
                missing_citations.append(citation)
                
        # Process missing citations
        if missing_citations:
            jobs = await self.core_ingester.process_batch(missing_citations)
            logging.info(f"Processed {len(missing_citations)} missing citations")
            
        return missing_citations
        
    async def ingest_jurisdiction_cases(self, jurisdiction: str, limit: int = 50):
        """Bulk ingest recent cases from a jurisdiction"""
        # This would be expanded in Phase 2
        pass
```

## Phase 2: Enhanced Processing (Weeks 5-8)

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Create comprehensive ingestion implementation proposal with MVP-first approach", "status": "completed", "priority": "high"}, {"id": "2", "content": "Design eventual consistency model instead of distributed transactions", "status": "completed", "priority": "high"}, {"id": "3", "content": "Add cost controls and LLM usage optimization strategies", "status": "in_progress", "priority": "medium"}, {"id": "4", "content": "Design batch processing approach for gap detection", "status": "pending", "priority": "medium"}]