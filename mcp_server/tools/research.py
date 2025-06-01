"""
Research workflow tools for MCP server.

Integrates with the existing alligator.ai research API to provide:
- Comprehensive legal research workflows
- Semantic case search using ChromaDB
- Research session management  
- Legal memo generation
"""

import asyncio
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)


class ResearchTools:
    """Research workflow integration for MCP server"""
    
    def __init__(self, settings):
        self.settings = settings
        self.api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:8001')
        self.api_key = getattr(settings, 'API_KEY', None)
        
        # Session cache for tracking research
        self.research_sessions = {}
    
    async def conduct_research(
        self,
        research_question: str,
        case_facts: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        research_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive legal research using AI agents.
        
        Args:
            research_question: Legal research question or issue
            case_facts: Relevant facts of the case
            jurisdiction: Primary jurisdiction for research
            practice_areas: Relevant practice areas
            research_depth: Depth of analysis
            
        Returns:
            Research results with analysis and recommendations
        """
        try:
            # Map practice areas to API enum values (use lowercase)
            practice_area_mapping = {
                "constitutional": "constitutional_law",
                "criminal": "criminal_law", 
                "civil_rights": "civil_rights",
                "contract": "constitutional_law",  # Map to closest available
                "tort": "civil_rights",  # Map to closest available
                "employment": "employment",
                "environmental": "regulatory",  # Map to closest available
                "corporate": "corporate",
                "tax": "regulatory",  # Map to closest available
                "family": "civil_rights",  # Map to closest available
                "immigration": "civil_rights",  # Map to closest available
                "intellectual_property": "intellectual_property"
            }
            
            mapped_practice_areas = []
            if practice_areas:
                for area in practice_areas:
                    if area in practice_area_mapping:
                        mapped_practice_areas.append(practice_area_mapping[area])
            
            # Prepare research request
            research_request = {
                "query": research_question,
                "jurisdiction": jurisdiction,
                "practice_areas": mapped_practice_areas,
                "analysis_types": ["precedent_analysis"],  # Use lowercase
                "max_cases": {
                    "quick": 10,
                    "standard": 20,
                    "comprehensive": 50
                }.get(research_depth, 20),
                "include_memo": True
            }
            
            # Add case facts to query if provided
            if case_facts:
                research_request["query"] = f"{research_question}\\n\\nRelevant Facts: {case_facts}"
            
            # Call the research API
            async with httpx.AsyncClient(timeout=120.0) as client:
                headers = {"Content-Type": "application/json"}
                
                response = await client.post(
                    f"{self.api_base}/api/v1/research/sessions",
                    headers=headers,
                    json=research_request
                )
                
                if response.status_code != 201:
                    logger.error(f"Research API failed: {response.status_code} - {response.text}")
                    return {
                        "error": f"Research API failed: {response.status_code}",
                        "details": response.text
                    }
                
                session_data = response.json()
                session_id = session_data.get("id")
                
                # Poll for completion
                max_attempts = 24  # 2 minutes max (5 second intervals)
                for attempt in range(max_attempts):
                    await asyncio.sleep(5)
                    
                    status_response = await client.get(
                        f"{self.api_base}/api/v1/research/sessions/{session_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code == 200:
                        session_data = status_response.json()
                        status = session_data.get("status")
                        
                        if status == "completed":
                            break
                        elif status == "failed":
                            return {
                                "error": "Research session failed",
                                "details": session_data.get("error_message", "Unknown error")
                            }
                    
                    if attempt == max_attempts - 1:
                        return {
                            "error": "Research session timeout",
                            "session_id": session_id,
                            "status": session_data.get("status", "unknown")
                        }
                
                # Format comprehensive research results
                results = session_data.get("results", {})
                memo = session_data.get("memo", "")
                
                research_result = {
                    "research_id": session_id,
                    "research_question": research_question,
                    "jurisdiction": jurisdiction,
                    "practice_areas": practice_areas,
                    "research_depth": research_depth,
                    "status": "completed",
                    "completed_at": session_data.get("completed_at"),
                    "findings": {
                        "total_cases_analyzed": 0,
                        "relevant_precedents": [],
                        "authority_analysis": {},
                        "key_holdings": [],
                        "legal_principles": []
                    },
                    "analysis": {
                        "strengths": [],
                        "weaknesses": [], 
                        "opportunities": [],
                        "risks": []
                    },
                    "memo": memo,
                    "recommendations": [],
                    "next_steps": []
                }
                
                # Process precedent analysis results
                if "precedent_analysis" in results:
                    precedent_data = results["precedent_analysis"]
                    research_result["findings"]["total_cases_analyzed"] = precedent_data.get("cases_analyzed", 0)
                    
                    # Format precedent cases
                    for case in precedent_data.get("results", [])[:10]:
                        precedent = {
                            "case_id": case.get("case_id", ""),
                            "case_name": case.get("case_name", ""),
                            "citation": case.get("citation", ""),
                            "authority_score": case.get("authority_score", 0.0),
                            "relevance_score": case.get("relevance_score", 0.0),
                            "jurisdiction": case.get("jurisdiction", ""),
                            "practice_areas": case.get("practice_areas", []),
                            "decision_date": case.get("decision_date", ""),
                            "summary": case.get("summary", ""),
                            "key_holding": f"Authority: {case.get('authority_score', 0):.1f}/10, Relevance: {case.get('relevance_score', 0):.3f}"
                        }
                        research_result["findings"]["relevant_precedents"].append(precedent)
                        
                        # Extract key holdings
                        if case.get("summary"):
                            research_result["findings"]["key_holdings"].append({
                                "case": case.get("case_name", ""),
                                "holding": case.get("summary", "")
                            })
                
                # Add authority analysis if available
                if "authority_analysis" in results:
                    research_result["findings"]["authority_analysis"] = results["authority_analysis"]
                
                # Generate analysis based on results
                if research_result["findings"]["relevant_precedents"]:
                    high_authority_cases = [
                        p for p in research_result["findings"]["relevant_precedents"] 
                        if p["authority_score"] >= 7.0
                    ]
                    
                    research_result["analysis"]["strengths"] = [
                        f"Found {len(high_authority_cases)} high-authority precedents",
                        f"Total of {research_result['findings']['total_cases_analyzed']} cases analyzed",
                        "Strong precedential support available"
                    ]
                    
                    low_relevance_cases = [
                        p for p in research_result["findings"]["relevant_precedents"]
                        if p["relevance_score"] < 0.7
                    ]
                    
                    if low_relevance_cases:
                        research_result["analysis"]["weaknesses"] = [
                            f"{len(low_relevance_cases)} cases have lower relevance scores",
                            "May need additional fact-specific research"
                        ]
                    
                    research_result["recommendations"] = [
                        "Review high-authority precedents for applicable holdings",
                        "Analyze fact patterns for distinguishing factors",
                        "Consider jurisdiction-specific variations",
                        "Develop legal arguments based on strongest precedents"
                    ]
                    
                    research_result["next_steps"] = [
                        "Detailed case-by-case analysis of top precedents",
                        "Opposition research to identify counterarguments",
                        "Draft legal arguments and supporting citations",
                        "Consider additional research in related practice areas"
                    ]
                
                # Cache session for future reference
                self.research_sessions[session_id] = research_result
                
                logger.info(f"Completed research for: {research_question[:100]}...")
                return research_result
                
        except Exception as e:
            logger.error(f"Research workflow failed: {e}")
            return {
                "error": str(e),
                "research_question": research_question,
                "status": "failed"
            }
    
    async def semantic_search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find legally similar cases using semantic search.
        
        Args:
            query: Description of legal issue or fact pattern
            jurisdiction: Jurisdiction to search within
            practice_areas: Practice areas to filter by
            similarity_threshold: Minimum similarity score
            limit: Maximum results
            
        Returns:
            Semantically similar cases with scores
        """
        try:
            # Use the existing ChromaDB service through the vector service
            from services.vector.chroma_service import ChromaService
            
            chroma_service = ChromaService(use_mcp_tools=True)
            await chroma_service.initialize()
            
            # Perform semantic search
            search_results = await chroma_service.semantic_search(
                query=query,
                document_types=["case"],
                jurisdiction=jurisdiction,
                practice_areas=practice_areas,
                limit=limit
            )
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in search_results
                if result.get("similarity_score", 0.0) >= similarity_threshold
            ]
            
            # Format results for MCP
            formatted_results = {
                "query": query,
                "jurisdiction": jurisdiction,
                "practice_areas": practice_areas,
                "similarity_threshold": similarity_threshold,
                "total_results": len(filtered_results),
                "search_metadata": {
                    "collection": "legal_cases",
                    "embedding_model": "default",
                    "search_type": "semantic_similarity"
                },
                "similar_cases": []
            }
            
            for result in filtered_results:
                metadata = result.get("metadata", {})
                case_data = {
                    "case_id": result.get("id", ""),
                    "similarity_score": result.get("similarity_score", 0.0),
                    "case_name": metadata.get("case_name", metadata.get("title", "Unknown Case")),
                    "citation": metadata.get("citation", "No citation"),
                    "jurisdiction": metadata.get("jurisdiction", "Unknown"),
                    "court": metadata.get("court_id", "Unknown Court"),
                    "decision_date": metadata.get("decision_date", "Unknown"),
                    "practice_areas": metadata.get("practice_areas", "").split(",") if isinstance(metadata.get("practice_areas"), str) else metadata.get("practice_areas", []),
                    "authority_score": metadata.get("authority_score", 0.0),
                    "summary": f"Similarity: {result.get('similarity_score', 0):.3f} - {metadata.get('case_name', 'Unknown Case')}",
                    "content_preview": result.get("content", "")[:200] + "..." if result.get("content") else ""
                }
                formatted_results["similar_cases"].append(case_data)
            
            # Sort by similarity score
            formatted_results["similar_cases"].sort(
                key=lambda x: x["similarity_score"], 
                reverse=True
            )
            
            logger.info(f"Semantic search found {len(filtered_results)} similar cases for: {query[:100]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "total_results": 0,
                "similar_cases": []
            }
    
    async def generate_memo(
        self,
        research_session_id: str,
        memo_type: str = "research_memo",
        audience: str = "internal",
        format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Generate a legal research memorandum.
        
        Args:
            research_session_id: Research session ID
            memo_type: Type of memo to generate
            audience: Intended audience
            format: Output format
            
        Returns:
            Generated legal memo
        """
        try:
            # Call the memo generation API
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {"Content-Type": "application/json"}
                
                memo_request = {
                    "research_session_id": research_session_id,
                    "memo_type": memo_type,
                    "include_citations": True,
                    "format": format
                }
                
                response = await client.post(
                    f"{self.api_base}/api/v1/research/generate-memo",
                    headers=headers,
                    json=memo_request
                )
                
                if response.status_code != 200:
                    logger.error(f"Memo generation failed: {response.status_code} - {response.text}")
                    return {
                        "error": f"Memo generation failed: {response.status_code}",
                        "details": response.text
                    }
                
                memo_data = response.json()
                
                # Format memo response
                result = {
                    "research_session_id": research_session_id,
                    "memo_type": memo_type,
                    "audience": audience,
                    "format": format,
                    "memo_content": memo_data.get("memo_content", ""),
                    "citations_count": memo_data.get("citations_count", 0),
                    "generated_at": memo_data.get("generated_at"),
                    "word_count": len(memo_data.get("memo_content", "").split()),
                    "metadata": {
                        "generation_method": "AI-powered legal research platform",
                        "platform": "alligator.ai",
                        "quality_level": "professional"
                    }
                }
                
                logger.info(f"Generated {memo_type} memo for session {research_session_id}")
                return result
                
        except Exception as e:
            logger.error(f"Memo generation failed: {e}")
            return {
                "error": str(e),
                "research_session_id": research_session_id,
                "memo_type": memo_type
            }
    
    async def get_recent_sessions(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent research sessions"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                
                response = await client.get(
                    f"{self.api_base}/api/v1/research/sessions",
                    headers=headers,
                    params={"limit": limit}
                )
                
                if response.status_code == 200:
                    sessions_data = response.json()
                    
                    # Format for MCP response
                    formatted_sessions = {
                        "total_sessions": len(sessions_data),
                        "sessions": []
                    }
                    
                    for session in sessions_data:
                        session_info = {
                            "id": session.get("id", ""),
                            "query": session.get("query", ""),
                            "status": session.get("status", ""),
                            "jurisdiction": session.get("jurisdiction"),
                            "practice_areas": session.get("practice_areas", []),
                            "created_at": session.get("created_at"),
                            "completed_at": session.get("completed_at"),
                            "cases_analyzed": session.get("results", {}).get("precedent_analysis", {}).get("cases_analyzed", 0) if session.get("results") else 0
                        }
                        formatted_sessions["sessions"].append(session_info)
                    
                    return formatted_sessions
                else:
                    return {"total_sessions": 0, "sessions": [], "error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return {"total_sessions": 0, "sessions": [], "error": str(e)}
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed information about a research session"""
        try:
            # Check cache first
            if session_id in self.research_sessions:
                return self.research_sessions[session_id]
            
            # Call API
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                
                response = await client.get(
                    f"{self.api_base}/api/v1/research/sessions/{session_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    session_data = response.json()
                    
                    # Cache the session
                    self.research_sessions[session_id] = session_data
                    
                    return session_data
                else:
                    return {
                        "error": f"Session not found: {session_id}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get session details: {e}")
            return {"error": str(e), "session_id": session_id}