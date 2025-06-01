"""
New Jersey Legal Data Ingestion System.

A comprehensive system for ingesting legal data from New Jersey courts,
implementing excellence-first processing with premium LLM analysis,
sophisticated legal document chunking, and citation-driven case expansion.

Key Components:
- CourtListenerClient: API client for New Jersey case discovery  
- ExcellenceFirstProcessor: Premium LLM processing pipeline
- LegalDocumentChunkingPipeline: Sophisticated legal chunking strategies
- NewJerseyJurisdictionMapper: Court hierarchy and jurisdiction mapping
- NewJerseyIngestionOrchestrator: Main orchestrator integrating all components

Architecture Implementation:
- ADR-002: Data Sources & Quality (CourtListener integration)
- ADR-003: Cost & LLM Usage (Excellence-first strategy)
- ADR-006: Legal Document Chunking (Sophisticated chunking strategies)

Legacy Components (for backwards compatibility):
- LegalDataIngester: Original sample data ingester
"""

# New Jersey MVP Ingestion System
from .courtlistener_client import CourtListenerClient, NewJerseyCourtType, CaseIngestionJob
from .llm_processor import ExcellenceFirstProcessor, LegalAnalysisResult, ProcessingComplexity
from .legal_chunking import LegalDocumentChunkingPipeline, LegalChunk, LegalSectionType
from .nj_jurisdiction_mapper import NewJerseyJurisdictionMapper, CourtHierarchyInfo
from .ingestion_orchestrator import NewJerseyIngestionOrchestrator, IngestionStatus, IngestionPriority

# Legacy components
from .legal_data_ingester import LegalDataIngester

__all__ = [
    # Main orchestrator
    'NewJerseyIngestionOrchestrator',
    
    # Core components
    'CourtListenerClient',
    'ExcellenceFirstProcessor', 
    'LegalDocumentChunkingPipeline',
    'NewJerseyJurisdictionMapper',
    
    # Data types
    'NewJerseyCourtType',
    'CaseIngestionJob',
    'LegalAnalysisResult',
    'ProcessingComplexity',
    'LegalChunk',
    'LegalSectionType',
    'CourtHierarchyInfo',
    'IngestionStatus',
    'IngestionPriority',
    
    # Legacy
    'LegalDataIngester'
]

# Version info
__version__ = "1.0.0"
__author__ = "alligator.ai Legal Research Platform"