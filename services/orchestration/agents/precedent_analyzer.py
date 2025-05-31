"""
LangGraph agent for legal precedent analysis.
"""

import asyncio
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime, timezone
import logging

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic

from shared.models.legal_entities import Case, Citation, PracticeArea
from services.graph.neo4j_service import Neo4jService
from services.vector.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class PrecedentAnalysisState(TypedDict):
    """State for precedent analysis workflow."""
    query: str
    jurisdiction: Optional[str]
    practice_areas: List[str]
    target_case_id: Optional[str]
    
    # Search results
    semantic_results: List[Dict[str, Any]]
    citation_results: List[Dict[str, Any]]
    
    # Analysis results
    relevant_precedents: List[Dict[str, Any]]
    authority_analysis: Dict[str, Any]
    treatment_analysis: Dict[str, Any]
    
    # Final output
    precedent_memo: str
    confidence_score: float
    
    # Workflow metadata
    messages: Annotated[List[BaseMessage], "Messages in conversation"]
    current_step: str
    error_message: Optional[str]


class PrecedentAnalyzer:
    """LangGraph agent for comprehensive precedent analysis."""
    
    def __init__(
        self,
        neo4j_service: Neo4jService,
        chroma_service: ChromaService,
        anthropic_api_key: str
    ):
        self.neo4j = neo4j_service
        self.chroma = chroma_service
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            api_key=anthropic_api_key,
            temperature=0.1,
            max_tokens=4000
        )
        
        # Build the LangGraph workflow
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for precedent analysis."""
        workflow = StateGraph(PrecedentAnalysisState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_analysis)
        workflow.add_node("semantic_search", self._semantic_search)
        workflow.add_node("citation_analysis", self._citation_analysis)
        workflow.add_node("filter_relevance", self._filter_relevance)
        workflow.add_node("analyze_authority", self._analyze_authority)
        workflow.add_node("analyze_treatment", self._analyze_treatment)
        workflow.add_node("generate_memo", self._generate_memo)
        workflow.add_node("error_handler", self._handle_error)
        
        # Define the workflow edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "semantic_search")
        workflow.add_edge("semantic_search", "citation_analysis")
        workflow.add_edge("citation_analysis", "filter_relevance")
        workflow.add_edge("filter_relevance", "analyze_authority")
        workflow.add_edge("analyze_authority", "analyze_treatment")
        workflow.add_edge("analyze_treatment", "generate_memo")
        
        workflow.add_edge("generate_memo", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    async def analyze_precedents(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        target_case_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive precedent analysis."""
        
        initial_state = PrecedentAnalysisState(
            query=query,
            jurisdiction=jurisdiction,
            practice_areas=practice_areas or [],
            target_case_id=target_case_id,
            semantic_results=[],
            citation_results=[],
            relevant_precedents=[],
            authority_analysis={},
            treatment_analysis={},
            precedent_memo="",
            confidence_score=0.0,
            messages=[HumanMessage(content=query)],
            current_step="initialize",
            error_message=None
        )
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "precedent_memo": final_state["precedent_memo"],
                "relevant_precedents": final_state["relevant_precedents"],
                "authority_analysis": final_state["authority_analysis"],
                "treatment_analysis": final_state["treatment_analysis"],
                "confidence_score": final_state["confidence_score"],
                "semantic_results_count": len(final_state["semantic_results"]),
                "citation_results_count": len(final_state["citation_results"])
            }
            
        except Exception as e:
            logger.error(f"Error in precedent analysis: {e}")
            return {
                "error": str(e),
                "precedent_memo": "Analysis failed due to an error.",
                "confidence_score": 0.0
            }
    
    async def _initialize_analysis(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Initialize the precedent analysis."""
        logger.info(f"Initializing precedent analysis for query: {state['query']}")
        
        state["current_step"] = "initialize"
        state["messages"].append(
            AIMessage(content="Starting comprehensive precedent analysis...")
        )
        
        return state
    
    async def _semantic_search(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Perform semantic search for relevant cases."""
        state["current_step"] = "semantic_search"
        
        try:
            # Search for semantically similar cases
            semantic_results = await self.chroma.semantic_search(
                query=state["query"],
                document_types=["case"],
                jurisdiction=state["jurisdiction"],
                practice_areas=state["practice_areas"],
                limit=20
            )
            
            state["semantic_results"] = semantic_results
            
            logger.info(f"Found {len(semantic_results)} semantically similar cases")
            
            state["messages"].append(
                AIMessage(content=f"Found {len(semantic_results)} semantically relevant cases")
            )
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            state["error_message"] = f"Semantic search failed: {e}"
        
        return state
    
    async def _citation_analysis(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Analyze citation networks for relevant precedents."""
        state["current_step"] = "citation_analysis"
        
        try:
            citation_results = []
            
            # If we have a target case, traverse its citation network
            if state["target_case_id"]:
                # Get cases that cite the target case
                citing_cases = await self.neo4j.get_citing_cases(
                    state["target_case_id"], limit=30
                )
                
                # Get cases cited by the target case
                cited_cases = await self.neo4j.get_cited_cases(
                    state["target_case_id"], limit=30
                )
                
                # Combine and format results
                for case, citation in citing_cases:
                    citation_results.append({
                        "case": case.model_dump(),
                        "citation": citation.model_dump(),
                        "relationship": "cites_target"
                    })
                
                for case, citation in cited_cases:
                    citation_results.append({
                        "case": case.model_dump(),
                        "citation": citation.model_dump(),
                        "relationship": "cited_by_target"
                    })
            
            # Also search by criteria if no target case
            else:
                practice_area_enums = []
                for area in state["practice_areas"]:
                    try:
                        practice_area_enums.append(PracticeArea(area))
                    except ValueError:
                        continue
                
                related_cases = await self.neo4j.find_cases_by_criteria(
                    jurisdiction=state["jurisdiction"],
                    practice_areas=state["practice_areas"],
                    limit=30
                )
                
                for case in related_cases:
                    citation_results.append({
                        "case": case.model_dump(),
                        "citation": None,
                        "relationship": "practice_area_match"
                    })
            
            state["citation_results"] = citation_results
            
            logger.info(f"Found {len(citation_results)} citation-related cases")
            
            state["messages"].append(
                AIMessage(content=f"Analyzed citation network, found {len(citation_results)} related cases")
            )
            
        except Exception as e:
            logger.error(f"Error in citation analysis: {e}")
            state["error_message"] = f"Citation analysis failed: {e}"
        
        return state
    
    async def _filter_relevance(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Filter and rank cases by relevance."""
        state["current_step"] = "filter_relevance"
        
        try:
            # Combine semantic and citation results
            all_cases = []
            
            # Add semantic results with their similarity scores
            for result in state["semantic_results"]:
                all_cases.append({
                    "case_data": result,
                    "relevance_score": result["similarity_score"],
                    "source": "semantic",
                    "authority_score": result["metadata"].get("authority_score", 0.0)
                })
            
            # Add citation results with authority-based scoring
            for result in state["citation_results"]:
                case_data = result["case"]
                relevance_score = case_data.get("authority_score", 0.0) / 10.0  # Normalize to 0-1
                
                # Boost score based on citation relationship
                if result["relationship"] == "cites_target":
                    relevance_score += 0.2
                elif result["relationship"] == "cited_by_target":
                    relevance_score += 0.3
                
                all_cases.append({
                    "case_data": case_data,
                    "relevance_score": min(relevance_score, 1.0),
                    "source": "citation",
                    "authority_score": case_data.get("authority_score", 0.0),
                    "citation_info": result.get("citation")
                })
            
            # Remove duplicates and sort by relevance
            seen_cases = set()
            unique_cases = []
            
            for case in all_cases:
                case_id = case["case_data"].get("id") or case["case_data"].get("source_id")
                if case_id and case_id not in seen_cases:
                    seen_cases.add(case_id)
                    unique_cases.append(case)
            
            # Sort by combined relevance and authority score
            unique_cases.sort(
                key=lambda x: (x["relevance_score"] * 0.7 + (x["authority_score"] / 10.0) * 0.3),
                reverse=True
            )
            
            # Take top 10 most relevant cases
            state["relevant_precedents"] = unique_cases[:10]
            
            logger.info(f"Filtered to {len(state['relevant_precedents'])} most relevant precedents")
            
            state["messages"].append(
                AIMessage(content=f"Identified {len(state['relevant_precedents'])} highly relevant precedents")
            )
            
        except Exception as e:
            logger.error(f"Error filtering relevance: {e}")
            state["error_message"] = f"Relevance filtering failed: {e}"
        
        return state
    
    async def _analyze_authority(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Analyze the authority level of found precedents."""
        state["current_step"] = "analyze_authority"
        
        try:
            authority_analysis = {
                "supreme_court_cases": [],
                "appellate_cases": [],
                "district_cases": [],
                "binding_precedents": [],
                "persuasive_precedents": [],
                "average_authority_score": 0.0
            }
            
            total_authority = 0.0
            
            for precedent in state["relevant_precedents"]:
                case_data = precedent["case_data"]
                authority_score = case_data.get("authority_score", 0.0)
                total_authority += authority_score
                
                jurisdiction = case_data.get("jurisdiction", "")
                court_id = case_data.get("court_id", "")
                
                # Categorize by court level
                if "supreme" in court_id.lower():
                    authority_analysis["supreme_court_cases"].append(precedent)
                elif "appellate" in court_id.lower() or "ca-" in court_id:
                    authority_analysis["appellate_cases"].append(precedent)
                else:
                    authority_analysis["district_cases"].append(precedent)
                
                # Determine binding vs persuasive authority
                if state["jurisdiction"]:
                    if (jurisdiction == state["jurisdiction"] or 
                        (jurisdiction == "US" and state["jurisdiction"].startswith("US"))):
                        authority_analysis["binding_precedents"].append(precedent)
                    else:
                        authority_analysis["persuasive_precedents"].append(precedent)
                else:
                    # If no jurisdiction specified, US cases are generally more authoritative
                    if jurisdiction == "US":
                        authority_analysis["binding_precedents"].append(precedent)
                    else:
                        authority_analysis["persuasive_precedents"].append(precedent)
            
            if state["relevant_precedents"]:
                authority_analysis["average_authority_score"] = total_authority / len(state["relevant_precedents"])
            
            state["authority_analysis"] = authority_analysis
            
            logger.info(f"Authority analysis: {len(authority_analysis['binding_precedents'])} binding, "
                       f"{len(authority_analysis['persuasive_precedents'])} persuasive")
            
        except Exception as e:
            logger.error(f"Error in authority analysis: {e}")
            state["error_message"] = f"Authority analysis failed: {e}"
        
        return state
    
    async def _analyze_treatment(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Analyze how precedents have been treated over time."""
        state["current_step"] = "analyze_treatment"
        
        try:
            treatment_analysis = {
                "good_law_cases": [],
                "questioned_cases": [],
                "overruled_cases": [],
                "recent_developments": [],
                "trend_analysis": ""
            }
            
            for precedent in state["relevant_precedents"]:
                case_data = precedent["case_data"]
                status = case_data.get("status", "good_law")
                
                if status == "good_law":
                    treatment_analysis["good_law_cases"].append(precedent)
                elif status in ["questioned", "limited"]:
                    treatment_analysis["questioned_cases"].append(precedent)
                elif status in ["overruled", "superseded"]:
                    treatment_analysis["overruled_cases"].append(precedent)
                
                # Check for recent cases (last 5 years)
                decision_date = case_data.get("decision_date")
                if decision_date:
                    try:
                        if isinstance(decision_date, str):
                            decision_dt = datetime.fromisoformat(decision_date)
                        else:
                            decision_dt = decision_date
                        
                        years_ago = (datetime.now(timezone.utc) - decision_dt).days / 365
                        if years_ago <= 5:
                            treatment_analysis["recent_developments"].append(precedent)
                    except:
                        pass
            
            # Generate trend analysis
            if treatment_analysis["recent_developments"]:
                treatment_analysis["trend_analysis"] = f"Found {len(treatment_analysis['recent_developments'])} recent developments in this area of law."
            else:
                treatment_analysis["trend_analysis"] = "No significant recent developments found."
            
            state["treatment_analysis"] = treatment_analysis
            
            logger.info(f"Treatment analysis: {len(treatment_analysis['good_law_cases'])} good law, "
                       f"{len(treatment_analysis['questioned_cases'])} questioned")
            
        except Exception as e:
            logger.error(f"Error in treatment analysis: {e}")
            state["error_message"] = f"Treatment analysis failed: {e}"
        
        return state
    
    async def _generate_memo(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Generate comprehensive precedent analysis memo."""
        state["current_step"] = "generate_memo"
        
        try:
            # Prepare context for the LLM
            context = self._prepare_memo_context(state)
            
            memo_prompt = f"""
            As a legal research AI, generate a comprehensive precedent analysis memo based on the following research:

            QUERY: {state['query']}
            JURISDICTION: {state.get('jurisdiction', 'Not specified')}
            PRACTICE AREAS: {', '.join(state['practice_areas']) if state['practice_areas'] else 'Not specified'}

            RESEARCH FINDINGS:
            {context}

            Please provide a detailed memo that includes:
            1. Executive Summary
            2. Key Precedents Analysis
            3. Authority Assessment
            4. Current Legal Status
            5. Recommendations for Legal Strategy

            Format the memo professionally with clear headings and citations.
            """
            
            # Generate memo using Claude
            response = await self.llm.ainvoke([HumanMessage(content=memo_prompt)])
            
            state["precedent_memo"] = response.content
            
            # Calculate confidence score based on results quality
            confidence_score = self._calculate_confidence_score(state)
            state["confidence_score"] = confidence_score
            
            logger.info(f"Generated precedent memo (confidence: {confidence_score:.2f})")
            
            state["messages"].append(
                AIMessage(content="Completed comprehensive precedent analysis memo")
            )
            
        except Exception as e:
            logger.error(f"Error generating memo: {e}")
            state["error_message"] = f"Memo generation failed: {e}"
        
        return state
    
    def _prepare_memo_context(self, state: PrecedentAnalysisState) -> str:
        """Prepare context summary for memo generation."""
        context_parts = []
        
        # Authority analysis summary
        authority = state["authority_analysis"]
        context_parts.append(f"""
        AUTHORITY ANALYSIS:
        - Supreme Court Cases: {len(authority.get('supreme_court_cases', []))}
        - Appellate Cases: {len(authority.get('appellate_cases', []))}
        - Binding Precedents: {len(authority.get('binding_precedents', []))}
        - Persuasive Precedents: {len(authority.get('persuasive_precedents', []))}
        - Average Authority Score: {authority.get('average_authority_score', 0):.2f}/10.0
        """)
        
        # Treatment analysis summary
        treatment = state["treatment_analysis"]
        context_parts.append(f"""
        TREATMENT ANALYSIS:
        - Good Law Cases: {len(treatment.get('good_law_cases', []))}
        - Questioned Cases: {len(treatment.get('questioned_cases', []))}
        - Overruled Cases: {len(treatment.get('overruled_cases', []))}
        - Recent Developments: {len(treatment.get('recent_developments', []))}
        - Trend: {treatment.get('trend_analysis', '')}
        """)
        
        # Top precedents
        context_parts.append("\nTOP PRECEDENTS:")
        for i, precedent in enumerate(state["relevant_precedents"][:5], 1):
            case_data = precedent["case_data"]
            case_name = case_data.get("case_name") or case_data.get("title", "Unknown Case")
            citation = case_data.get("citation", "No citation")
            summary = case_data.get("summary", "No summary available")
            
            context_parts.append(f"""
            {i}. {case_name}
               Citation: {citation}
               Relevance Score: {precedent['relevance_score']:.2f}
               Summary: {summary[:200]}...
            """)
        
        return "\n".join(context_parts)
    
    def _calculate_confidence_score(self, state: PrecedentAnalysisState) -> float:
        """Calculate confidence score for the analysis."""
        score = 0.0
        
        # Base score from number of relevant precedents
        precedent_count = len(state["relevant_precedents"])
        if precedent_count >= 5:
            score += 0.3
        elif precedent_count >= 3:
            score += 0.2
        elif precedent_count >= 1:
            score += 0.1
        
        # Authority score contribution
        authority = state["authority_analysis"]
        if authority.get("supreme_court_cases"):
            score += 0.3
        elif authority.get("appellate_cases"):
            score += 0.2
        
        avg_authority = authority.get("average_authority_score", 0)
        score += (avg_authority / 10.0) * 0.2
        
        # Treatment analysis contribution
        treatment = state["treatment_analysis"]
        good_law_ratio = len(treatment.get("good_law_cases", [])) / max(precedent_count, 1)
        score += good_law_ratio * 0.2
        
        return min(score, 1.0)
    
    async def _handle_error(self, state: PrecedentAnalysisState) -> PrecedentAnalysisState:
        """Handle errors in the workflow."""
        error_msg = state.get("error_message", "Unknown error occurred")
        
        state["precedent_memo"] = f"Analysis could not be completed due to error: {error_msg}"
        state["confidence_score"] = 0.0
        
        logger.error(f"Precedent analysis failed: {error_msg}")
        
        return state


# Example usage
async def example_usage():
    """Example of using the precedent analyzer."""
    from services.graph.neo4j_service import Neo4jService
    from services.vector.chroma_service import ChromaService
    
    # Initialize services
    neo4j_service = Neo4jService("bolt://localhost:7687", "neo4j", "citation_graph_2024")
    chroma_service = ChromaService()
    
    # Initialize analyzer
    analyzer = PrecedentAnalyzer(
        neo4j_service=neo4j_service,
        chroma_service=chroma_service,
        anthropic_api_key="your-anthropic-api-key"
    )
    
    try:
        await neo4j_service.connect()
        
        # Perform precedent analysis
        result = await analyzer.analyze_precedents(
            query="police qualified immunity for excessive force",
            jurisdiction="US",
            practice_areas=["civil_rights", "constitutional"]
        )
        
        print("PRECEDENT ANALYSIS MEMO:")
        print("=" * 50)
        print(result["precedent_memo"])
        print(f"\nConfidence Score: {result['confidence_score']:.2f}")
        
    finally:
        await neo4j_service.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())