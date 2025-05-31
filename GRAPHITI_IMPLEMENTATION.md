# Graphiti Implementation Guide for Legal Research Platform

## Project Structure Enhancement

```
legal_research_platform/
├── agents/
│   ├── base/
│   │   ├── graphiti_aware_agent.py          # New: Graphiti integration base
│   │   └── memory_aware_agent.py            # Enhanced: Graphiti support
│   ├── research_orchestrator.py             # Enhanced: Temporal research
│   ├── precedent_analyzer.py                # Enhanced: Temporal precedent analysis
│   └── strategy_agent.py                    # Enhanced: Pattern learning
├── memory/
│   ├── graphiti_integration/                # New: Graphiti integration layer
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── search_configs.py
│   │   ├── legal_episodes.py
│   │   └── temporal_queries.py
│   ├── hybrid_search.py                     # New: Multi-modal search
│   └── memory_router.py                     # Enhanced: Graphiti routing
├── models/
│   ├── legal_entities.py                    # New: Graphiti legal entities
│   └── temporal_facts.py                    # New: Temporal fact models
├── services/
│   ├── graphiti_service.py                  # New: Graphiti service wrapper
│   └── knowledge_evolution.py               # New: Temporal knowledge tracking
└── config/
    └── graphiti_config.py                   # New: Graphiti configuration
```

## Core Implementation Components

### 1. Graphiti Client Integration

```python
# memory/graphiti_integration/client.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_RRF,
    EPISODE_HYBRID_SEARCH_RRF
)
import json
import asyncio

class LegalGraphitiClient:
    """Enhanced Graphiti client for legal research applications"""
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: str
    ):
        self.client = Graphiti(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key
        )
        self.legal_search_configs = LegalSearchConfigs()
    
    async def initialize(self):
        """Initialize Graphiti with legal-specific indices"""
        await self.client.close()  # Ensure clean state
        self.client = Graphiti(
            neo4j_uri=self.client.neo4j_uri,
            neo4j_user=self.client.neo4j_user,
            neo4j_password=self.client.neo4j_password,
            openai_api_key=self.client.openai_api_key
        )
    
    async def add_legal_episode(
        self,
        episode_type: str,
        content: Dict[str, Any],
        reference_time: datetime,
        source_description: str = "Legal Research Platform"
    ) -> str:
        """Add a legal episode to the knowledge graph"""
        episode_name = f"{episode_type}: {content.get('title', 'Legal Event')}"
        
        episode_id = await self.client.add_episode(
            name=episode_name,
            episode_body=json.dumps(content, default=str),
            source=EpisodeType.json,
            reference_time=reference_time,
            source_description=source_description
        )
        
        return episode_id
    
    async def search_legal_knowledge(
        self,
        query: str,
        center_node_uuid: Optional[str] = None,
        temporal_context: Optional[Dict[str, datetime]] = None,
        search_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Search legal knowledge with temporal awareness"""
        
        # Select appropriate search configuration
        search_config = self.legal_search_configs.get_config(search_type)
        
        # Apply temporal filtering if provided
        if temporal_context:
            search_config = self._apply_temporal_filters(
                search_config, temporal_context
            )
        
        # Perform search
        results = await self.client.search(
            query=query,
            center_node_uuid=center_node_uuid,
            config=search_config
        )
        
        return {
            "edges": [self._format_legal_edge(edge) for edge in results.edges],
            "nodes": [self._format_legal_node(node) for node in results.nodes],
            "query": query,
            "temporal_context": temporal_context,
            "total_results": len(results.edges) + len(results.nodes)
        }
    
    async def track_case_evolution(
        self,
        case_citation: str,
        evolution_event: Dict[str, Any],
        event_date: datetime
    ):
        """Track how a legal case's treatment evolves over time"""
        await self.add_legal_episode(
            episode_type="case_evolution",
            content={
                "case_citation": case_citation,
                "evolution_type": evolution_event.get("type"),
                "involving_case": evolution_event.get("involving_case"),
                "treatment": evolution_event.get("treatment"),
                "reasoning": evolution_event.get("reasoning"),
                "impact": evolution_event.get("impact")
            },
            reference_time=event_date,
            source_description="Case Law Monitor"
        )
    
    async def learn_research_pattern(
        self,
        research_objective: str,
        research_process: List[Dict[str, Any]],
        outcome: Dict[str, Any],
        completion_time: datetime
    ):
        """Learn from research patterns for future optimization"""
        await self.add_legal_episode(
            episode_type="research_pattern",
            content={
                "objective": research_objective,
                "process_steps": research_process,
                "outcome": outcome,
                "success_score": outcome.get("success_score"),
                "duration_minutes": outcome.get("duration_minutes"),
                "key_insights": outcome.get("key_insights", [])
            },
            reference_time=completion_time,
            source_description="Research Learning System"
        )
    
    async def get_user_research_context(
        self,
        user_id: str,
        practice_areas: List[str] = None
    ) -> Dict[str, Any]:
        """Get user-specific research context and preferences"""
        
        # Search for user-related research history
        user_context = await self.search_legal_knowledge(
            query=f"user research history and preferences for {user_id}",
            search_type="user_context"
        )
        
        # Filter by practice areas if specified
        if practice_areas:
            user_context = self._filter_by_practice_areas(
                user_context, practice_areas
            )
        
        return user_context
    
    def _format_legal_edge(self, edge) -> Dict[str, Any]:
        """Format Graphiti edge for legal research context"""
        return {
            "id": edge.uuid,
            "source_node": edge.source_node_uuid,
            "target_node": edge.target_node_uuid,
            "relationship": edge.fact,
            "confidence": getattr(edge, 'confidence', None),
            "valid_at": getattr(edge, 'valid_at', None),
            "invalid_at": getattr(edge, 'invalid_at', None),
            "episodes": [ep.uuid for ep in getattr(edge, 'episodes', [])]
        }
    
    def _format_legal_node(self, node) -> Dict[str, Any]:
        """Format Graphiti node for legal research context"""
        return {
            "id": node.uuid,
            "name": node.name,
            "type": getattr(node, 'entity_type', 'Entity'),
            "summary": getattr(node, 'summary', ''),
            "created_at": getattr(node, 'created_at', None),
            "metadata": getattr(node, 'metadata', {})
        }
    
    def _apply_temporal_filters(
        self, 
        search_config: Dict, 
        temporal_context: Dict[str, datetime]
    ) -> Dict:
        """Apply temporal filtering to search configuration"""
        # Implementation depends on Graphiti's temporal query capabilities
        # This is a placeholder for temporal filtering logic
        return search_config
    
    def _filter_by_practice_areas(
        self, 
        context: Dict[str, Any], 
        practice_areas: List[str]
    ) -> Dict[str, Any]:
        """Filter context by practice areas"""
        # Filter nodes and edges by practice area metadata
        filtered_edges = [
            edge for edge in context["edges"]
            if any(area.lower() in str(edge).lower() for area in practice_areas)
        ]
        filtered_nodes = [
            node for node in context["nodes"]
            if any(area.lower() in str(node).lower() for area in practice_areas)
        ]
        
        return {
            **context,
            "edges": filtered_edges,
            "nodes": filtered_nodes,
            "total_results": len(filtered_edges) + len(filtered_nodes)
        }
```

### 2. Legal Search Configurations

```python
# memory/graphiti_integration/search_configs.py
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_RRF,
    EPISODE_HYBRID_SEARCH_RRF
)

class LegalSearchConfigs:
    """Legal-specific search configurations for Graphiti"""
    
    def __init__(self):
        self.configs = {
            "precedent_analysis": {
                "edge_config": EDGE_HYBRID_SEARCH_RRF,
                "node_config": NODE_HYBRID_SEARCH_RRF,
                "episode_config": EPISODE_HYBRID_SEARCH_RRF,
                "weights": {
                    "semantic": 0.4,
                    "keyword": 0.3,
                    "graph": 0.3
                },
                "filters": {
                    "entity_types": ["Case", "LegalConcept", "Judge"],
                    "relationship_types": ["CITES", "OVERRULES", "DISTINGUISHES"]
                }
            },
            "research_patterns": {
                "edge_config": EDGE_HYBRID_SEARCH_RRF,
                "node_config": NODE_HYBRID_SEARCH_RRF,
                "episode_config": EPISODE_HYBRID_SEARCH_RRF,
                "weights": {
                    "semantic": 0.5,
                    "keyword": 0.2,
                    "graph": 0.3
                },
                "filters": {
                    "entity_types": ["ResearchProject", "Strategy", "Outcome"],
                    "episode_types": ["research_pattern", "case_evolution"]
                }
            },
            "user_context": {
                "edge_config": EDGE_HYBRID_SEARCH_RRF,
                "node_config": NODE_HYBRID_SEARCH_RRF,
                "episode_config": EPISODE_HYBRID_SEARCH_RRF,
                "weights": {
                    "semantic": 0.3,
                    "keyword": 0.2,
                    "graph": 0.5  # Higher graph weight for user relationships
                },
                "filters": {
                    "entity_types": ["User", "Firm", "Preference"],
                    "relationship_types": ["PREFERS", "SUCCEEDS_WITH", "AVOIDS"]
                }
            },
            "comprehensive": {
                "edge_config": EDGE_HYBRID_SEARCH_RRF,
                "node_config": NODE_HYBRID_SEARCH_RRF,
                "episode_config": EPISODE_HYBRID_SEARCH_RRF,
                "weights": {
                    "semantic": 0.4,
                    "keyword": 0.3,
                    "graph": 0.3
                },
                "filters": {}  # No filtering for comprehensive search
            }
        }
    
    def get_config(self, search_type: str) -> Dict:
        """Get search configuration for specified type"""
        return self.configs.get(search_type, self.configs["comprehensive"])
```

### 3. Enhanced Memory-Aware Agent Base

```python
# agents/base/graphiti_aware_agent.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from agents.base.memory_aware_agent import MemoryAwareAgent
from memory.graphiti_integration.client import LegalGraphitiClient
from models.temporal_facts import TemporalFact, LegalContext

class GraphitiAwareAgent(MemoryAwareAgent):
    """Enhanced agent base class with Graphiti temporal knowledge capabilities"""
    
    def __init__(
        self,
        agent_id: str,
        graphiti_client: LegalGraphitiClient,
        memory_router=None,
        llm=None
    ):
        super().__init__(agent_id, memory_router, llm)
        self.graphiti = graphiti_client
        self.user_node_uuid: Optional[str] = None
        self.case_node_uuid: Optional[str] = None
        self.firm_node_uuid: Optional[str] = None
        self.current_context: Optional[LegalContext] = None
    
    async def initialize_legal_context(
        self,
        user_id: str,
        case_id: str,
        firm_id: str,
        practice_areas: List[str] = None
    ):
        """Initialize legal context for the agent"""
        # Get or create user node
        self.user_node_uuid = await self._get_or_create_user_node(user_id)
        
        # Get or create case node
        self.case_node_uuid = await self._get_or_create_case_node(case_id)
        
        # Get or create firm node
        self.firm_node_uuid = await self._get_or_create_firm_node(firm_id)
        
        # Load user research context
        user_context = await self.graphiti.get_user_research_context(
            user_id, practice_areas
        )
        
        self.current_context = LegalContext(
            user_id=user_id,
            case_id=case_id,
            firm_id=firm_id,
            practice_areas=practice_areas or [],
            user_context=user_context,
            initialized_at=datetime.now(timezone.utc)
        )
    
    async def retrieve_temporal_knowledge(
        self,
        query: str,
        temporal_scope: str = "relevant",
        knowledge_types: List[str] = None
    ) -> List[TemporalFact]:
        """Retrieve temporally-aware legal knowledge"""
        
        # Determine temporal context based on scope
        temporal_context = self._build_temporal_context(temporal_scope)
        
        # Search Graphiti for relevant knowledge
        results = await self.graphiti.search_legal_knowledge(
            query=query,
            center_node_uuid=self.case_node_uuid,
            temporal_context=temporal_context,
            search_type="comprehensive"
        )
        
        # Convert to TemporalFact objects
        temporal_facts = []
        for edge in results["edges"]:
            temporal_facts.append(TemporalFact.from_graphiti_edge(edge))
        
        for node in results["nodes"]:
            temporal_facts.append(TemporalFact.from_graphiti_node(node))
        
        # Filter by knowledge types if specified
        if knowledge_types:
            temporal_facts = [
                fact for fact in temporal_facts
                if fact.knowledge_type in knowledge_types
            ]
        
        return temporal_facts
    
    async def store_research_insight(
        self,
        insight_type: str,
        content: Dict[str, Any],
        confidence: float = None,
        temporal_validity: Dict[str, datetime] = None
    ) -> str:
        """Store research insight in temporal knowledge graph"""
        
        # Add timestamp and context
        enhanced_content = {
            **content,
            "agent_id": self.agent_id,
            "user_context": self.current_context.user_id if self.current_context else None,
            "case_context": self.current_context.case_id if self.current_context else None,
            "confidence": confidence,
            "temporal_validity": temporal_validity
        }
        
        # Store in Graphiti
        episode_id = await self.graphiti.add_legal_episode(
            episode_type=insight_type,
            content=enhanced_content,
            reference_time=datetime.now(timezone.utc),
            source_description=f"Agent: {self.agent_id}"
        )
        
        return episode_id
    
    async def learn_from_outcome(
        self,
        process_description: str,
        outcome: Dict[str, Any],
        success_metrics: Dict[str, float]
    ):
        """Learn from research process outcomes"""
        
        learning_content = {
            "process": process_description,
            "outcome": outcome,
            "success_metrics": success_metrics,
            "context": {
                "user_id": self.current_context.user_id if self.current_context else None,
                "practice_areas": self.current_context.practice_areas if self.current_context else [],
                "agent_type": type(self).__name__
            }
        }
        
        await self.graphiti.learn_research_pattern(
            research_objective=process_description,
            research_process=[learning_content["process"]],
            outcome=outcome,
            completion_time=datetime.now(timezone.utc)
        )
    
    async def get_personalized_recommendations(
        self,
        current_task: str,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on temporal knowledge"""
        
        # Search for similar past tasks
        similar_tasks = await self.retrieve_temporal_knowledge(
            query=f"similar tasks to: {current_task}",
            temporal_scope="user_history",
            knowledge_types=["research_pattern", "strategy", "outcome"]
        )
        
        # Analyze patterns and generate recommendations
        recommendations = self._analyze_patterns_for_recommendations(
            similar_tasks, current_task, context
        )
        
        return recommendations
    
    def _build_temporal_context(self, scope: str) -> Dict[str, datetime]:
        """Build temporal context based on scope"""
        now = datetime.now(timezone.utc)
        
        temporal_contexts = {
            "recent": {
                "start": now.replace(month=now.month-3),  # Last 3 months
                "end": now
            },
            "user_history": {
                "start": now.replace(year=now.year-2),  # Last 2 years
                "end": now
            },
            "relevant": {
                "start": now.replace(year=now.year-5),  # Last 5 years
                "end": now
            },
            "all_time": {}  # No temporal restrictions
        }
        
        return temporal_contexts.get(scope, temporal_contexts["relevant"])
    
    async def _get_or_create_user_node(self, user_id: str) -> str:
        """Get or create user node in Graphiti"""
        # Search for existing user node
        user_search = await self.graphiti.search_legal_knowledge(
            query=f"user {user_id}",
            search_type="user_context"
        )
        
        # Return existing node if found
        for node in user_search["nodes"]:
            if node["name"] == user_id:
                return node["id"]
        
        # Create new user node
        episode_id = await self.graphiti.add_legal_episode(
            episode_type="user_creation",
            content={
                "user_id": user_id,
                "entity_type": "User",
                "created_by": "system"
            },
            reference_time=datetime.now(timezone.utc)
        )
        
        # Note: In a real implementation, you'd need to retrieve the created node UUID
        # This would require additional Graphiti API calls
        return f"user_{user_id}"  # Placeholder
    
    async def _get_or_create_case_node(self, case_id: str) -> str:
        """Get or create case node in Graphiti"""
        # Similar implementation to user node creation
        return f"case_{case_id}"  # Placeholder
    
    async def _get_or_create_firm_node(self, firm_id: str) -> str:
        """Get or create firm node in Graphiti"""
        # Similar implementation to user node creation
        return f"firm_{firm_id}"  # Placeholder
    
    def _analyze_patterns_for_recommendations(
        self,
        temporal_facts: List[TemporalFact],
        current_task: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze temporal patterns to generate recommendations"""
        recommendations = []
        
        # Group facts by outcome success
        successful_patterns = [
            fact for fact in temporal_facts
            if fact.metadata.get("success_score", 0) > 0.7
        ]
        
        # Extract successful strategies
        for pattern in successful_patterns:
            if pattern.knowledge_type == "research_pattern":
                recommendations.append({
                    "type": "strategy",
                    "recommendation": f"Consider approach: {pattern.content.get('process')}",
                    "confidence": pattern.metadata.get("confidence", 0.5),
                    "based_on": pattern.fact_id,
                    "historical_success": pattern.metadata.get("success_score")
                })
        
        return recommendations
```

### 4. Enhanced Research Orchestrator

```python
# agents/research_orchestrator.py (Enhanced)
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from agents.base.graphiti_aware_agent import GraphitiAwareAgent
from models.research_state import ResearchState
from models.temporal_facts import TemporalFact

class TemporalResearchOrchestrator(GraphitiAwareAgent):
    """Research orchestrator with temporal knowledge and learning capabilities"""
    
    async def plan_research_with_historical_context(
        self,
        state: ResearchState
    ) -> ResearchState:
        """Plan research using historical patterns and temporal knowledge"""
        
        # Get historical research patterns
        historical_patterns = await self.retrieve_temporal_knowledge(
            query=f"research planning for: {state['objective']}",
            temporal_scope="user_history",
            knowledge_types=["research_pattern", "strategy"]
        )
        
        # Get personalized recommendations
        recommendations = await self.get_personalized_recommendations(
            current_task=f"research planning: {state['objective']}",
            context={
                "jurisdiction": state.get("jurisdiction"),
                "practice_area": state.get("practice_area"),
                "case_type": state.get("case_type")
            }
        )
        
        # Generate enhanced research plan
        research_plan = await self._generate_contextual_research_plan(
            state, historical_patterns, recommendations
        )
        
        # Store the planning decision for future learning
        await self.store_research_insight(
            insight_type="research_planning",
            content={
                "objective": state["objective"],
                "plan": research_plan,
                "historical_inputs": len(historical_patterns),
                "recommendations_used": len(recommendations)
            },
            confidence=research_plan.get("confidence_score")
        )
        
        # Update state
        state["research_plan"] = research_plan
        state["historical_context"] = self._summarize_historical_context(historical_patterns)
        state["next_agent"] = "precedent_analyzer"
        
        return state
    
    async def _generate_contextual_research_plan(
        self,
        state: ResearchState,
        historical_patterns: List[TemporalFact],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate research plan incorporating historical context"""
        
        # Analyze successful historical approaches
        successful_approaches = [
            pattern for pattern in historical_patterns
            if pattern.metadata.get("success_score", 0) > 0.8
        ]
        
        # Build context for LLM
        historical_context = "\n".join([
            f"- {pattern.content.get('approach', 'Unknown')}: "
            f"Success rate {pattern.metadata.get('success_score', 0):.2f}"
            for pattern in successful_approaches
        ])
        
        recommendation_context = "\n".join([
            f"- {rec['recommendation']} (confidence: {rec['confidence']:.2f})"
            for rec in recommendations
        ])
        
        prompt = f"""
        Plan a legal research workflow for: {state['objective']}
        
        Historical successful approaches:
        {historical_context}
        
        Personalized recommendations:
        {recommendation_context}
        
        Case context:
        - Jurisdiction: {state.get('jurisdiction', 'Not specified')}
        - Practice Area: {state.get('practice_area', 'Not specified')}
        - Legal Issues: {state.get('legal_issues', [])}
        
        Create a detailed research plan that:
        1. Incorporates lessons from historical successes
        2. Applies personalized recommendations
        3. Addresses the specific legal context
        4. Estimates time and resource requirements
        5. Identifies potential risks and mitigation strategies
        """
        
        # Generate plan using LLM
        plan_response = await self.llm.ainvoke(prompt)
        
        # Structure the response
        research_plan = {
            "steps": self._extract_research_steps(plan_response.content),
            "estimated_duration": self._extract_duration(plan_response.content),
            "resource_requirements": self._extract_resources(plan_response.content),
            "risk_factors": self._extract_risks(plan_response.content),
            "confidence_score": self._calculate_confidence(
                historical_patterns, recommendations
            ),
            "based_on_patterns": len(successful_approaches),
            "generated_at": datetime.now(timezone.utc)
        }
        
        return research_plan
    
    async def monitor_research_progress(
        self,
        research_id: str,
        current_state: ResearchState
    ) -> Dict[str, Any]:
        """Monitor research progress and adapt based on temporal patterns"""
        
        # Get progress patterns for similar research
        progress_patterns = await self.retrieve_temporal_knowledge(
            query=f"research progress patterns similar to current state",
            temporal_scope="relevant",
            knowledge_types=["progress_tracking", "bottleneck_analysis"]
        )
        
        # Analyze current progress against patterns
        progress_analysis = self._analyze_progress_against_patterns(
            current_state, progress_patterns
        )
        
        # Generate adaptive recommendations
        adaptive_recommendations = await self._generate_adaptive_recommendations(
            progress_analysis, current_state
        )
        
        return {
            "progress_analysis": progress_analysis,
            "recommendations": adaptive_recommendations,
            "predicted_completion": self._predict_completion_time(
                progress_patterns, current_state
            )
        }
    
    def _summarize_historical_context(
        self,
        historical_patterns: List[TemporalFact]
    ) -> Dict[str, Any]:
        """Summarize historical context for state management"""
        return {
            "total_patterns": len(historical_patterns),
            "successful_patterns": len([
                p for p in historical_patterns
                if p.metadata.get("success_score", 0) > 0.7
            ]),
            "most_recent": max([
                p.temporal_metadata.get("created_at", datetime.min)
                for p in historical_patterns
            ]) if historical_patterns else None,
            "average_success": sum([
                p.metadata.get("success_score", 0)
                for p in historical_patterns
            ]) / len(historical_patterns) if historical_patterns else 0
        }
    
    def _calculate_confidence(
        self,
        historical_patterns: List[TemporalFact],
        recommendations: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for research plan"""
        base_confidence = 0.5
        
        # Boost confidence based on historical success patterns
        if historical_patterns:
            avg_historical_success = sum([
                p.metadata.get("success_score", 0)
                for p in historical_patterns
            ]) / len(historical_patterns)
            base_confidence += (avg_historical_success - 0.5) * 0.3
        
        # Boost confidence based on recommendation quality
        if recommendations:
            avg_recommendation_confidence = sum([
                r.get("confidence", 0)
                for r in recommendations
            ]) / len(recommendations)
            base_confidence += (avg_recommendation_confidence - 0.5) * 0.2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    # Helper methods for plan extraction (simplified)
    def _extract_research_steps(self, content: str) -> List[str]:
        # Implementation would parse LLM response for research steps
        return ["Step 1", "Step 2", "Step 3"]  # Placeholder
    
    def _extract_duration(self, content: str) -> int:
        # Implementation would parse estimated duration
        return 120  # Placeholder: 120 minutes
    
    def _extract_resources(self, content: str) -> List[str]:
        # Implementation would parse resource requirements
        return ["Westlaw", "LexisNexis", "Expert consultation"]  # Placeholder
    
    def _extract_risks(self, content: str) -> List[str]:
        # Implementation would parse risk factors
        return ["Limited precedents", "Jurisdictional variations"]  # Placeholder
```

### 5. Temporal Knowledge Models

```python
# models/temporal_facts.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

class KnowledgeType(Enum):
    CASE_LAW = "case_law"
    RESEARCH_PATTERN = "research_pattern"
    STRATEGY = "strategy"
    OUTCOME = "outcome"
    USER_PREFERENCE = "user_preference"
    LEGAL_CONCEPT = "legal_concept"
    PRECEDENT_RELATIONSHIP = "precedent_relationship"

@dataclass
class TemporalMetadata:
    """Temporal metadata for legal facts"""
    created_at: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    last_verified: Optional[datetime] = None
    confidence_decay_rate: float = 0.0  # How confidence decreases over time
    
    def is_valid_at(self, query_time: datetime) -> bool:
        """Check if fact is valid at specified time"""
        if self.valid_from and query_time < self.valid_from:
            return False
        if self.valid_until and query_time > self.valid_until:
            return False
        return True
    
    def current_confidence(self, base_confidence: float) -> float:
        """Calculate current confidence considering temporal decay"""
        if not self.confidence_decay_rate:
            return base_confidence
        
        days_since_creation = (datetime.now(timezone.utc) - self.created_at).days
        decay_factor = 1.0 - (self.confidence_decay_rate * days_since_creation / 365)
        return max(base_confidence * decay_factor, 0.1)

@dataclass
class TemporalFact:
    """Temporal fact representing legal knowledge with time awareness"""
    fact_id: str
    knowledge_type: KnowledgeType
    content: Dict[str, Any]
    temporal_metadata: TemporalMetadata
    metadata: Dict[str, Any]
    relationships: List[str] = None
    
    @classmethod
    def from_graphiti_edge(cls, edge_data: Dict[str, Any]) -> 'TemporalFact':
        """Create TemporalFact from Graphiti edge data"""
        return cls(
            fact_id=edge_data["id"],
            knowledge_type=cls._infer_knowledge_type(edge_data),
            content={
                "relationship": edge_data["relationship"],
                "source": edge_data["source_node"],
                "target": edge_data["target_node"]
            },
            temporal_metadata=TemporalMetadata(
                created_at=edge_data.get("created_at", datetime.now(timezone.utc)),
                valid_from=edge_data.get("valid_at"),
                valid_until=edge_data.get("invalid_at")
            ),
            metadata={
                "confidence": edge_data.get("confidence", 0.8),
                "source": "graphiti_edge"
            },
            relationships=edge_data.get("episodes", [])
        )
    
    @classmethod
    def from_graphiti_node(cls, node_data: Dict[str, Any]) -> 'TemporalFact':
        """Create TemporalFact from Graphiti node data"""
        return cls(
            fact_id=node_data["id"],
            knowledge_type=cls._infer_knowledge_type_from_node(node_data),
            content={
                "name": node_data["name"],
                "type": node_data["type"],
                "summary": node_data.get("summary", "")
            },
            temporal_metadata=TemporalMetadata(
                created_at=node_data.get("created_at", datetime.now(timezone.utc))
            ),
            metadata={
                "entity_metadata": node_data.get("metadata", {}),
                "source": "graphiti_node"
            }
        )
    
    @staticmethod
    def _infer_knowledge_type(edge_data: Dict[str, Any]) -> KnowledgeType:
        """Infer knowledge type from edge data"""
        relationship = edge_data.get("relationship", "").lower()
        
        if any(term in relationship for term in ["cites", "overrules", "distinguishes"]):
            return KnowledgeType.PRECEDENT_RELATIONSHIP
        elif "strategy" in relationship:
            return KnowledgeType.STRATEGY
        elif "outcome" in relationship:
            return KnowledgeType.OUTCOME
        else:
            return KnowledgeType.LEGAL_CONCEPT
    
    @staticmethod
    def _infer_knowledge_type_from_node(node_data: Dict[str, Any]) -> KnowledgeType:
        """Infer knowledge type from node data"""
        node_type = node_data.get("type", "").lower()
        
        if "case" in node_type:
            return KnowledgeType.CASE_LAW
        elif "user" in node_type or "preference" in node_type:
            return KnowledgeType.USER_PREFERENCE
        elif "research" in node_type:
            return KnowledgeType.RESEARCH_PATTERN
        else:
            return KnowledgeType.LEGAL_CONCEPT
    
    def is_currently_valid(self) -> bool:
        """Check if fact is currently valid"""
        return self.temporal_metadata.is_valid_at(datetime.now(timezone.utc))
    
    def relevance_score(self, query_context: Dict[str, Any]) -> float:
        """Calculate relevance score for given query context"""
        base_score = self.metadata.get("confidence", 0.5)
        
        # Apply temporal confidence decay
        current_confidence = self.temporal_metadata.current_confidence(base_score)
        
        # Apply context-specific adjustments
        context_boost = 0.0
        
        # Boost for knowledge type relevance
        if query_context.get("preferred_knowledge_types"):
            if self.knowledge_type in query_context["preferred_knowledge_types"]:
                context_boost += 0.1
        
        # Boost for temporal relevance
        if query_context.get("temporal_preference") == "recent":
            days_old = (datetime.now(timezone.utc) - self.temporal_metadata.created_at).days
            if days_old < 90:  # Recent = last 3 months
                context_boost += 0.1
        
        return min(current_confidence + context_boost, 1.0)

@dataclass
class LegalContext:
    """Legal context for research sessions"""
    user_id: str
    case_id: str
    firm_id: str
    practice_areas: List[str]
    user_context: Dict[str, Any]
    initialized_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "case_id": self.case_id,
            "firm_id": self.firm_id,
            "practice_areas": self.practice_areas,
            "user_context": self.user_context,
            "initialized_at": self.initialized_at.isoformat()
        }
```

### 6. Hybrid Search Implementation

```python
# memory/hybrid_search.py
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
from memory.graphiti_integration.client import LegalGraphitiClient
from neo4j import AsyncGraphDatabase
import chromadb
from models.temporal_facts import TemporalFact, KnowledgeType

class HybridLegalSearchEngine:
    """Hybrid search engine combining Graphiti, Neo4j, and ChromaDB"""
    
    def __init__(
        self,
        graphiti_client: LegalGraphitiClient,
        neo4j_uri: str,
        neo4j_auth: tuple,
        chroma_client: chromadb.Client
    ):
        self.graphiti = graphiti_client
        self.neo4j_driver = AsyncGraphDatabase.driver(neo4j_uri, auth=neo4j_auth)
        self.chroma = chroma_client
        self.collection = chroma_client.get_or_create_collection("legal_documents")
    
    async def search(
        self,
        query: str,
        search_context: Dict[str, Any],
        temporal_constraints: Optional[Dict[str, datetime]] = None,
        result_limit: int = 50
    ) -> Dict[str, Any]:
        """Perform hybrid search across all knowledge sources"""
        
        # Execute searches in parallel
        search_tasks = [
            self._search_graphiti(query, search_context, temporal_constraints),
            self._search_neo4j(query, search_context),
            self._search_chroma(query, search_context)
        ]
        
        graphiti_results, neo4j_results, chroma_results = await asyncio.gather(
            *search_tasks, return_exceptions=True
        )
        
        # Handle any search failures gracefully
        if isinstance(graphiti_results, Exception):
            graphiti_results = {"temporal_facts": [], "nodes": [], "edges": []}
        if isinstance(neo4j_results, Exception):
            neo4j_results = {"cases": [], "citations": []}
        if isinstance(chroma_results, Exception):
            chroma_results = {"documents": [], "scores": []}
        
        # Merge and rank results
        merged_results = await self._merge_search_results(
            graphiti_results, neo4j_results, chroma_results, search_context
        )
        
        # Apply result limit
        final_results = self._limit_and_rank_results(merged_results, result_limit)
        
        return {
            "results": final_results,
            "search_metadata": {
                "query": query,
                "temporal_constraints": temporal_constraints,
                "source_counts": {
                    "graphiti": len(graphiti_results.get("temporal_facts", [])),
                    "neo4j": len(neo4j_results.get("cases", [])),
                    "chroma": len(chroma_results.get("documents", []))
                },
                "search_time": datetime.now(),
                "result_count": len(final_results)
            }
        }
    
    async def _search_graphiti(
        self,
        query: str,
        context: Dict[str, Any],
        temporal_constraints: Optional[Dict[str, datetime]]
    ) -> Dict[str, Any]:
        """Search Graphiti for temporal legal knowledge"""
        
        # Use case context as center node if available
        center_node = context.get("case_node_uuid")
        
        graphiti_results = await self.graphiti.search_legal_knowledge(
            query=query,
            center_node_uuid=center_node,
            temporal_context=temporal_constraints,
            search_type="comprehensive"
        )
        
        # Convert to TemporalFact objects
        temporal_facts = []
        for edge in graphiti_results.get("edges", []):
            temporal_facts.append(TemporalFact.from_graphiti_edge(edge))
        
        for node in graphiti_results.get("nodes", []):
            temporal_facts.append(TemporalFact.from_graphiti_node(node))
        
        return {
            "temporal_facts": temporal_facts,
            "nodes": graphiti_results.get("nodes", []),
            "edges": graphiti_results.get("edges", [])
        }
    
    async def _search_neo4j(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search Neo4j for static legal citations"""
        
        # Build Cypher query based on context
        cypher_query = self._build_citation_query(query, context)
        
        async with self.neo4j_driver.session() as session:
            result = await session.run(cypher_query, query=query)
            records = await result.data()
        
        # Process Neo4j results
        cases = []
        citations = []
        
        for record in records:
            if "case" in record:
                cases.append(record["case"])
            if "citation" in record:
                citations.append(record["citation"])
        
        return {
            "cases": cases,
            "citations": citations
        }
    
    async def _search_chroma(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search ChromaDB for semantic document similarity"""
        
        # Build metadata filter
        where_filter = {}
        if context.get("jurisdiction"):
            where_filter["jurisdiction"] = context["jurisdiction"]
        if context.get("practice_area"):
            where_filter["practice_area"] = context["practice_area"]
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=20,
            where=where_filter if where_filter else None
        )
        
        documents = []
        for i, doc_id in enumerate(results["ids"][0]):
            documents.append({
                "id": doc_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity_score": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return {
            "documents": documents,
            "scores": [doc["similarity_score"] for doc in documents]
        }
    
    async def _merge_search_results(
        self,
        graphiti_results: Dict[str, Any],
        neo4j_results: Dict[str, Any],
        chroma_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Merge and cross-reference results from all sources"""
        
        merged_results = []
        
        # Process Graphiti temporal facts
        for fact in graphiti_results.get("temporal_facts", []):
            result_item = {
                "id": fact.fact_id,
                "type": "temporal_fact",
                "content": fact.content,
                "source": "graphiti",
                "relevance_score": fact.relevance_score(context),
                "temporal_validity": fact.is_currently_valid(),
                "knowledge_type": fact.knowledge_type.value,
                "metadata": fact.metadata
            }
            merged_results.append(result_item)
        
        # Process Neo4j cases
        for case in neo4j_results.get("cases", []):
            result_item = {
                "id": case.get("id", f"neo4j_{len(merged_results)}"),
                "type": "case_law",
                "content": case,
                "source": "neo4j",
                "relevance_score": self._calculate_neo4j_relevance(case, context),
                "temporal_validity": True,  # Static legal data assumed valid
                "knowledge_type": "case_law"
            }
            merged_results.append(result_item)
        
        # Process ChromaDB documents
        for doc in chroma_results.get("documents", []):
            result_item = {
                "id": doc["id"],
                "type": "document",
                "content": {
                    "text": doc["content"],
                    "metadata": doc["metadata"]
                },
                "source": "chroma",
                "relevance_score": doc["similarity_score"],
                "temporal_validity": True,
                "knowledge_type": "document"
            }
            merged_results.append(result_item)
        
        return merged_results
    
    def _build_citation_query(self, query: str, context: Dict[str, Any]) -> str:
        """Build Cypher query for Neo4j citation search"""
        base_query = """
        MATCH (c:Case)-[:CITES*1..3]-(related:Case)
        WHERE c.name CONTAINS $query 
           OR c.citation CONTAINS $query
           OR related.name CONTAINS $query
        """
        
        # Add jurisdiction filter if specified
        if context.get("jurisdiction"):
            base_query += f" AND c.jurisdiction = '{context['jurisdiction']}'"
        
        base_query += """
        RETURN c as case, related, 
               size((c)-[:CITES]->()) as citation_count
        ORDER BY citation_count DESC
        LIMIT 20
        """
        
        return base_query
    
    def _calculate_neo4j_relevance(
        self,
        case: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for Neo4j case results"""
        base_score = 0.7  # Base relevance for citation network matches
        
        # Boost for jurisdiction match
        if context.get("jurisdiction") == case.get("jurisdiction"):
            base_score += 0.1
        
        # Boost for citation count (authority)
        citation_count = case.get("citation_count", 0)
        authority_boost = min(citation_count / 100, 0.2)  # Max 0.2 boost
        
        return min(base_score + authority_boost, 1.0)
    
    def _limit_and_rank_results(
        self,
        results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Apply final ranking and limit results"""
        
        # Sort by relevance score (descending)
        sorted_results = sorted(
            results,
            key=lambda x: x["relevance_score"],
            reverse=True
        )
        
        # Apply limit
        return sorted_results[:limit]
```

### 7. Configuration and Deployment

```python
# config/graphiti_config.py
from pydantic_settings import BaseSettings
from typing import Optional

class GraphitiConfig(BaseSettings):
    """Configuration for Graphiti integration"""
    
    # Graphiti Neo4j Configuration
    GRAPHITI_NEO4J_URI: str = "bolt://localhost:7687"
    GRAPHITI_NEO4J_USER: str = "neo4j"
    GRAPHITI_NEO4J_PASSWORD: str
    
    # OpenAI Configuration for Graphiti
    OPENAI_API_KEY: str
    
    # Legal Neo4j Configuration (existing)
    LEGAL_NEO4J_URI: str = "bolt://localhost:7688"
    LEGAL_NEO4J_USER: str = "neo4j"
    LEGAL_NEO4J_PASSWORD: str
    
    # ChromaDB Configuration
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    
    # Performance Settings
    GRAPHITI_SEARCH_TIMEOUT: int = 30  # seconds
    HYBRID_SEARCH_TIMEOUT: int = 45  # seconds
    MAX_TEMPORAL_FACTS: int = 100
    
    # Learning Settings
    CONFIDENCE_DECAY_RATE: float = 0.1  # 10% per year
    MINIMUM_CONFIDENCE: float = 0.1
    LEARNING_THRESHOLD: float = 0.7  # Minimum success score to learn from
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Docker Compose Enhancement
docker_compose_addition = """
# Add to existing docker-compose.yml

services:
  # Graphiti Service
  graphiti:
    image: zepai/graphiti:latest
    ports:
      - "8001:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - NEO4J_URI=bolt://graphiti-neo4j:7687
      - NEO4J_USER=${GRAPHITI_NEO4J_USER}
      - NEO4J_PASSWORD=${GRAPHITI_NEO4J_PASSWORD}
    depends_on:
      - graphiti-neo4j
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Dedicated Neo4j for Graphiti
  graphiti-neo4j:
    image: neo4j:5.22.0
    ports:
      - "7475:7474"  # HTTP (different from legal-neo4j)
      - "7688:7687"  # Bolt (different from legal-neo4j)
    volumes:
      - graphiti_neo4j_data:/data
    environment:
      - NEO4J_AUTH=${GRAPHITI_NEO4J_USER}/${GRAPHITI_NEO4J_PASSWORD}
      - NEO4J_PLUGINS=["apoc"]
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${GRAPHITI_NEO4J_PASSWORD}", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  graphiti_neo4j_data:
"""
```

This implementation provides a comprehensive integration of Graphiti into your legal research platform, offering temporal knowledge capabilities, enhanced agent memory, and hybrid search functionality. The system maintains compatibility with your existing architecture while adding sophisticated temporal awareness crucial for legal research applications.