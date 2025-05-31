"""
ChromaDB vector search service for legal document embeddings.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import uuid

from shared.models.legal_entities import ChromaDocument, Case, Statute, LegalConcept

logger = logging.getLogger(__name__)


class ChromaService:
    """Service for ChromaDB vector search operations."""
    
    def __init__(self):
        # Note: We'll use the MCP ChromaDB tools instead of direct client
        self.collection_mapping = {
            "cases": "legal_cases",
            "statutes": "legal_statutes", 
            "concepts": "legal_concepts",
            "briefs": "research_briefs"
        }
    
    async def add_case_document(self, case: Case, full_text: str) -> str:
        """Add a case document to the vector database."""
        doc = ChromaDocument(
            id=f"case_{case.id}",
            content=full_text,
            document_type="case",
            title=case.case_name,
            source_id=case.id,
            jurisdiction=case.jurisdiction,
            practice_areas=[area.value for area in case.practice_areas],
            court_level=None,  # Would need to look up court level
            decision_date=case.decision_date,
            authority_score=case.authority_score
        )
        
        return await self._add_document("legal_cases", doc)
    
    async def add_statute_document(self, statute: Statute) -> str:
        """Add a statute document to the vector database."""
        doc = ChromaDocument(
            id=f"statute_{statute.id}",
            content=statute.full_text,
            document_type="statute",
            title=statute.title,
            source_id=statute.id,
            jurisdiction=statute.jurisdiction,
            practice_areas=[area.value for area in statute.practice_areas],
            decision_date=statute.effective_date,
            authority_score=1.0  # Statutes have inherent authority
        )
        
        return await self._add_document("legal_statutes", doc)
    
    async def add_concept_document(self, concept: LegalConcept, description_text: str) -> str:
        """Add a legal concept document to the vector database."""
        doc = ChromaDocument(
            id=f"concept_{concept.id}",
            content=description_text,
            document_type="concept",
            title=concept.name,
            source_id=concept.id,
            practice_areas=[area.value for area in concept.practice_areas],
            authority_score=0.8  # Concepts have moderate authority
        )
        
        return await self._add_document("legal_concepts", doc)
    
    async def semantic_search(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across legal documents."""
        
        results = []
        
        # Determine which collections to search
        collections_to_search = []
        if not document_types:
            collections_to_search = list(self.collection_mapping.values())
        else:
            for doc_type in document_types:
                if doc_type in self.collection_mapping:
                    collections_to_search.append(self.collection_mapping[doc_type])
        
        # Search each collection
        for collection_name in collections_to_search:
            collection_results = await self._search_collection(
                collection_name=collection_name,
                query=query,
                jurisdiction=jurisdiction,
                practice_areas=practice_areas,
                date_range=date_range,
                limit=limit
            )
            results.extend(collection_results)
        
        # Sort by relevance score and apply final limit
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]
    
    async def find_similar_cases(
        self,
        case_text: str,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        exclude_case_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find cases similar to the given case text."""
        
        results = await self._search_collection(
            collection_name="legal_cases",
            query=case_text,
            jurisdiction=jurisdiction,
            practice_areas=practice_areas,
            limit=limit + 1  # Get one extra in case we need to exclude
        )
        
        # Filter out the excluded case if specified
        if exclude_case_id:
            results = [r for r in results if r["source_id"] != exclude_case_id]
        
        return results[:limit]
    
    async def hybrid_search(
        self,
        query: str,
        citation_cases: List[str],
        semantic_weight: float = 0.6,
        citation_weight: float = 0.4,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic similarity and citation relevance.
        This would be enhanced in Phase 2 with graph data.
        """
        
        # Get semantic search results
        semantic_results = await self.semantic_search(
            query=query,
            limit=limit * 2  # Get more results for better mixing
        )
        
        # For now, just weight semantic results
        # In Phase 2, we would combine with citation graph data
        hybrid_results = []
        for result in semantic_results:
            # Boost score if document is in citation_cases list
            citation_boost = 0.0
            if result["source_id"] in citation_cases:
                citation_boost = 0.3
            
            hybrid_score = (
                result["similarity_score"] * semantic_weight + 
                citation_boost * citation_weight
            )
            
            result["hybrid_score"] = hybrid_score
            hybrid_results.append(result)
        
        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return hybrid_results[:limit]
    
    async def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            # Use MCP ChromaDB tool to get document
            from main import mcp_chroma_get_documents
            
            result = await mcp_chroma_get_documents(
                collection_name=collection_name,
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if result and "documents" in result and result["documents"]:
                return {
                    "id": document_id,
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing document."""
        try:
            # Use MCP ChromaDB tool to update document
            from main import mcp_chroma_update_documents
            
            update_params = {"collection_name": collection_name, "ids": [document_id]}
            
            if content:
                update_params["documents"] = [content]
            if metadata:
                update_params["metadatas"] = [metadata]
            
            await mcp_chroma_update_documents(**update_params)
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            return False
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the collection."""
        try:
            # Use MCP ChromaDB tool to delete document
            from main import mcp_chroma_delete_documents
            
            await mcp_chroma_delete_documents(
                collection_name=collection_name,
                ids=[document_id]
            )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            # Use MCP ChromaDB tools to get collection info
            from main import mcp_chroma_get_collection_count, mcp_chroma_get_collection_info
            
            count = await mcp_chroma_get_collection_count(collection_name=collection_name)
            info = await mcp_chroma_get_collection_info(collection_name=collection_name)
            
            return {
                "name": collection_name,
                "document_count": count,
                "collection_info": info
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats for {collection_name}: {e}")
            return {}
    
    async def _add_document(self, collection_name: str, doc: ChromaDocument) -> str:
        """Add a document to the specified collection."""
        try:
            # Use MCP ChromaDB tool to add document
            from main import mcp_chroma_add_documents
            
            await mcp_chroma_add_documents(
                collection_name=collection_name,
                documents=[doc.content],
                metadatas=[doc.to_chroma_metadata()],
                ids=[doc.id]
            )
            
            logger.info(f"Added document {doc.id} to collection {collection_name}")
            return doc.id
            
        except Exception as e:
            logger.error(f"Error adding document to {collection_name}: {e}")
            raise
    
    async def _search_collection(
        self,
        collection_name: str,
        query: str,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search a specific collection with filters."""
        try:
            # Build metadata filter
            where_filter = {}
            
            if jurisdiction:
                where_filter["jurisdiction"] = jurisdiction
            
            if practice_areas:
                # ChromaDB doesn't support array contains, so we'll do string matching
                where_filter["practice_areas"] = {"$contains": practice_areas[0]}
            
            if date_range:
                # Add date range filtering
                where_filter["decision_date"] = {
                    "$gte": date_range[0].isoformat(),
                    "$lte": date_range[1].isoformat()
                }
            
            # Use MCP ChromaDB tool to query
            from main import mcp_chroma_query_documents
            
            result = await mcp_chroma_query_documents(
                collection_name=collection_name,
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if result and "documents" in result and result["documents"]:
                documents = result["documents"][0]
                metadatas = result["metadatas"][0] if result["metadatas"] else []
                distances = result["distances"][0] if result["distances"] else []
                ids = result["ids"][0] if result["ids"] else []
                
                for i, doc in enumerate(documents):
                    formatted_results.append({
                        "id": ids[i] if i < len(ids) else f"doc_{i}",
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "similarity_score": 1 - distances[i] if i < len(distances) else 0.0,
                        "source_id": metadatas[i].get("source_id") if i < len(metadatas) else None,
                        "document_type": metadatas[i].get("document_type") if i < len(metadatas) else None,
                        "collection": collection_name
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return []


# Example usage
async def example_usage():
    """Example of how to use the ChromaDB service."""
    service = ChromaService()
    
    # Example case
    sample_case = Case(
        id="miranda-v-arizona-1966",
        citation="384 U.S. 436",
        case_name="Miranda v. Arizona",
        full_name="Miranda v. Arizona",
        court_id="us-supreme-court",
        jurisdiction="US",
        decision_date=datetime(1966, 6, 13),
        practice_areas=["criminal", "constitutional"],
        summary="Established Miranda rights requiring police to inform suspects of their rights",
        holding="Suspects must be informed of their rights before interrogation",
        authority_score=9.5
    )
    
    # Add case to vector database
    case_text = f"{sample_case.summary} {sample_case.holding}"
    doc_id = await service.add_case_document(sample_case, case_text)
    print(f"Added case document: {doc_id}")
    
    # Semantic search
    results = await service.semantic_search(
        query="police interrogation rights",
        document_types=["case"],
        jurisdiction="US",
        limit=5
    )
    
    print(f"Found {len(results)} similar cases:")
    for result in results:
        print(f"- {result['metadata'].get('title', 'Unknown')} (score: {result['similarity_score']:.3f})")


if __name__ == "__main__":
    asyncio.run(example_usage())