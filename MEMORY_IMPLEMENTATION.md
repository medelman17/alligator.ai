# Memory Implementation Guide for LangGraph Agents

## Storage Technology Stack

### 1. Redis (Working Memory)
**Use Case**: Fast, session-based memory with TTL
**Configuration**:
```python
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,  # Working memory
    "decode_responses": True,
    "socket_keepalive": True,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "health_check_interval": 30
}

# Key patterns
SESSION_KEY = "session:{session_id}:context"
CACHE_KEY = "cache:{session_id}:case:{case_id}"
HYPOTHESIS_KEY = "hypothesis:{session_id}:stack"
```

### 2. PostgreSQL (Structured Memory)
**Use Case**: Research history, user profiles, audit logs
**Schema Design**:
```sql
-- Research projects
CREATE TABLE research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL,
    attorney_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    objective TEXT NOT NULL,
    outcome_success_rating DECIMAL(3,2),
    metadata JSONB
);

-- Memory entries
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES research_projects(id),
    agent_type VARCHAR(50) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    relevance_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_memory_agent_type ON memory_entries(agent_type);
CREATE INDEX idx_memory_relevance ON memory_entries(relevance_score DESC);
CREATE INDEX idx_memory_content_gin ON memory_entries USING GIN(content);
```

### 3. ChromaDB (Vector Memory)
**Use Case**: Semantic search, similarity matching
**Collections Structure**:
```python
# Collection definitions
COLLECTIONS = {
    "research_memories": {
        "embedding_function": "legal-bert-embeddings",
        "metadata": {
            "description": "Episodic memories from research projects",
            "distance_metric": "cosine"
        }
    },
    "legal_concepts": {
        "embedding_function": "legal-bert-embeddings", 
        "metadata": {
            "description": "Semantic legal knowledge",
            "distance_metric": "cosine"
        }
    },
    "argument_patterns": {
        "embedding_function": "legal-bert-embeddings",
        "metadata": {
            "description": "Successful argument structures",
            "distance_metric": "cosine"
        }
    }
}
```

### 4. Neo4j (Graph Memory)
**Use Case**: Legal concept relationships, citation networks
**Graph Schema**:
```cypher
// Node types
(:LegalConcept {
    id: String,
    name: String,
    definition: String,
    jurisdiction: String,
    last_updated: DateTime
})

(:ResearchMemory {
    id: String,
    project_id: String,
    summary: String,
    success_score: Float,
    created_at: DateTime
})

(:ArgumentPattern {
    id: String,
    pattern_type: String,
    description: String,
    success_rate: Float,
    usage_count: Integer
})

// Relationship types
[:RELATED_TO {strength: Float, context: String}]
[:EVOLVED_FROM {date: DateTime, reason: String}]
[:USED_IN {success: Boolean, context: String}]
[:CONTRADICTS {severity: String, explanation: String}]
```

## LangGraph Integration Patterns

### 1. Memory-Aware Agent Base Class
```python
from typing import Dict, List, Any, Optional
from langchain.memory import BaseMemory
from langgraph.graph import StateGraph
import asyncio

class MemoryAwareAgent:
    def __init__(
        self,
        agent_id: str,
        memory_router: MemoryRouter,
        llm: BaseLLM
    ):
        self.agent_id = agent_id
        self.memory_router = memory_router
        self.llm = llm
        self.working_memory: Dict[str, Any] = {}
    
    async def retrieve_relevant_memories(
        self,
        context: Dict[str, Any],
        memory_types: List[str] = ["all"]
    ) -> Dict[str, List[Memory]]:
        """Retrieve memories relevant to current context"""
        query = MemoryQuery(
            agent_id=self.agent_id,
            context=context,
            memory_types=memory_types,
            limit=20
        )
        return await self.memory_router.retrieve(query)
    
    async def store_memory(
        self,
        memory_type: str,
        content: Any,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store new memory entry"""
        memory = Memory(
            agent_id=self.agent_id,
            type=memory_type,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        return await self.memory_router.store(memory)
    
    def update_working_memory(self, key: str, value: Any):
        """Update session-based working memory"""
        self.working_memory[key] = value
        # Also persist to Redis for multi-agent access
        redis_key = f"agent:{self.agent_id}:working:{key}"
        redis_client.setex(redis_key, 3600, json.dumps(value))
```

### 2. Memory-Enhanced State Management
```python
from langgraph.graph.state import StateSnapshot
from typing import TypedDict, Annotated, Sequence
import operator

class ResearchState(TypedDict):
    """State definition with memory components"""
    # Core state
    objective: str
    current_findings: List[Dict]
    completed_steps: List[str]
    
    # Memory state
    relevant_memories: Dict[str, List[Memory]]
    working_context: Dict[str, Any]
    memory_insights: List[str]
    
    # Meta state
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

class MemoryStateManager:
    """Manages state with integrated memory operations"""
    
    def __init__(self, memory_router: MemoryRouter):
        self.memory_router = memory_router
    
    async def enhance_state_with_memories(
        self,
        state: ResearchState,
        agent_type: str
    ) -> ResearchState:
        """Enhance state with relevant memories"""
        # Retrieve memories based on current state
        memories = await self.memory_router.retrieve(
            MemoryQuery(
                agent_type=agent_type,
                objective=state["objective"],
                context=state["working_context"],
                limit=10
            )
        )
        
        # Update state with memories
        state["relevant_memories"] = memories
        state["memory_insights"] = self._extract_insights(memories)
        
        return state
    
    def _extract_insights(
        self,
        memories: Dict[str, List[Memory]]
    ) -> List[str]:
        """Extract actionable insights from memories"""
        insights = []
        
        # Pattern matching from episodic memories
        if "episodic" in memories:
            for memory in memories["episodic"]:
                if memory.success_score > 0.8:
                    insights.append(
                        f"Similar research succeeded with: {memory.summary}"
                    )
        
        # Warning from failed attempts
        if "failures" in memories:
            for memory in memories["failures"]:
                insights.append(
                    f"Avoid: {memory.failure_reason}"
                )
        
        return insights
```

### 3. Agent-Specific Memory Integration

#### Research Orchestrator with Memory
```python
class ResearchOrchestratorAgent(MemoryAwareAgent):
    async def plan_research(self, state: ResearchState) -> ResearchState:
        # Retrieve relevant research plans from memory
        memories = await self.retrieve_relevant_memories(
            context={
                "objective": state["objective"],
                "jurisdiction": state.get("jurisdiction"),
                "practice_area": state.get("practice_area")
            },
            memory_types=["research_plans", "successful_workflows"]
        )
        
        # Enhance prompt with memory insights
        memory_context = self._format_memory_context(memories)
        
        prompt = f"""
        Plan a legal research workflow for: {state['objective']}
        
        Relevant past experiences:
        {memory_context}
        
        Consider what worked well before and adapt the approach.
        """
        
        # Generate plan with LLM
        plan = await self.llm.ainvoke(prompt)
        
        # Store the plan in working memory
        self.update_working_memory("research_plan", plan)
        
        # Update state
        state["next_agent"] = "precedent_analyzer"
        state["messages"].append(AIMessage(content=plan))
        
        return state
```

#### Precedent Analyzer with Memory
```python
class PrecedentAnalyzerAgent(MemoryAwareAgent):
    async def analyze_precedents(self, state: ResearchState) -> ResearchState:
        # Get memory insights about similar cases
        case_memories = await self.retrieve_relevant_memories(
            context={
                "legal_issues": state.get("legal_issues"),
                "jurisdiction": state.get("jurisdiction")
            },
            memory_types=["case_patterns", "authority_rankings"]
        )
        
        # Retrieve known precedent relationships from graph
        graph_insights = await self._query_precedent_graph(
            state["current_findings"]
        )
        
        # Combine memory and current search results
        enhanced_results = self._enhance_with_memory(
            current_results=state["current_findings"],
            memories=case_memories,
            graph_insights=graph_insights
        )
        
        # Store successful patterns
        if enhanced_results.quality_score > 0.8:
            await self.store_memory(
                memory_type="successful_precedent_chain",
                content={
                    "objective": state["objective"],
                    "precedents": enhanced_results.precedents,
                    "key_authorities": enhanced_results.authorities
                }
            )
        
        state["current_findings"] = enhanced_results
        return state
```

### 4. Memory Lifecycle in LangGraph Workflow
```python
from langgraph.graph import Graph, END

def create_research_workflow(memory_router: MemoryRouter) -> Graph:
    workflow = StateGraph(ResearchState)
    
    # Initialize agents with memory
    orchestrator = ResearchOrchestratorAgent("orchestrator", memory_router)
    analyzer = PrecedentAnalyzerAgent("analyzer", memory_router)
    strategist = StrategyAgent("strategist", memory_router)
    
    # Pre-processing: Load relevant memories
    async def initialize_with_memory(state: ResearchState) -> ResearchState:
        # Load user preferences
        user_prefs = await memory_router.get_user_preferences(
            state["user_id"]
        )
        state["working_context"]["preferences"] = user_prefs
        
        # Load firm-specific patterns
        firm_patterns = await memory_router.get_firm_patterns(
            state["firm_id"]
        )
        state["working_context"]["firm_patterns"] = firm_patterns
        
        return state
    
    # Post-processing: Store learnings
    async def store_learnings(state: ResearchState) -> ResearchState:
        # Store the complete research project
        project_id = await memory_router.store_research_project({
            "objective": state["objective"],
            "findings": state["current_findings"],
            "outcome": state.get("outcome"),
            "duration": state.get("duration"),
            "agent_paths": state.get("completed_steps")
        })
        
        # Extract and store patterns
        patterns = extract_patterns(state)
        for pattern in patterns:
            await memory_router.store_pattern(pattern)
        
        return state
    
    # Wire up the workflow
    workflow.add_node("initialize", initialize_with_memory)
    workflow.add_node("orchestrate", orchestrator.plan_research)
    workflow.add_node("analyze", analyzer.analyze_precedents)
    workflow.add_node("strategize", strategist.develop_strategy)
    workflow.add_node("finalize", store_learnings)
    
    # Add edges
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "orchestrate")
    workflow.add_edge("orchestrate", "analyze")
    workflow.add_edge("analyze", "strategize")
    workflow.add_edge("strategize", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()
```

### 5. Memory Retrieval Optimization
```python
class OptimizedMemoryRetriever:
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self.retrieval_cache = {}
    
    async def retrieve_with_caching(
        self,
        query: MemoryQuery
    ) -> Dict[str, List[Memory]]:
        # Check cache first
        cache_key = self._generate_cache_key(query)
        if cache_key in self.retrieval_cache:
            return self.retrieval_cache[cache_key]
        
        # Parallel retrieval from multiple sources
        results = await asyncio.gather(
            self._vector_search(query),
            self._graph_search(query),
            self._structured_search(query),
            return_exceptions=True
        )
        
        # Merge and rank results
        merged = self._merge_results(results)
        ranked = self._rank_by_relevance(merged, query)
        
        # Cache results
        self.retrieval_cache[cache_key] = ranked
        
        return ranked
    
    async def _vector_search(self, query: MemoryQuery) -> List[Memory]:
        # ChromaDB similarity search
        embeddings = await get_embeddings(query.context)
        results = await chroma_client.query(
            collection_name="research_memories",
            query_embeddings=[embeddings],
            n_results=query.limit,
            where={"agent_type": query.agent_type}
        )
        return self._convert_to_memories(results)
    
    async def _graph_search(self, query: MemoryQuery) -> List[Memory]:
        # Neo4j relationship traversal
        cypher_query = """
        MATCH (m:ResearchMemory)-[:RELATED_TO*1..3]-(c:LegalConcept)
        WHERE c.name IN $concepts
        AND m.success_score > 0.7
        RETURN m, collect(c) as concepts
        ORDER BY m.success_score DESC
        LIMIT $limit
        """
        results = await neo4j_client.run(
            cypher_query,
            concepts=query.legal_concepts,
            limit=query.limit
        )
        return self._convert_graph_results(results)
```

## Performance Optimization Strategies

### 1. Memory Warming
Pre-load frequently accessed memories:
```python
async def warm_memory_cache(user_id: str, firm_id: str):
    common_patterns = await get_common_patterns(firm_id)
    user_preferences = await get_user_preferences(user_id)
    recent_projects = await get_recent_projects(user_id, limit=5)
    
    # Pre-compute embeddings
    for pattern in common_patterns:
        await compute_and_cache_embeddings(pattern)
```

### 2. Selective Memory Loading
Only load memories relevant to current task:
```python
def get_memory_types_for_agent(agent_type: str) -> List[str]:
    memory_map = {
        "orchestrator": ["research_plans", "workflow_patterns"],
        "analyzer": ["case_patterns", "authority_rankings"],
        "strategist": ["argument_patterns", "outcome_correlations"],
        "memo_writer": ["writing_styles", "formatting_preferences"]
    }
    return memory_map.get(agent_type, ["general"])
```

### 3. Memory Pruning
Remove obsolete or low-value memories:
```python
async def prune_memories():
    # Remove memories not accessed in 6 months
    await remove_stale_memories(months=6)
    
    # Compress similar memories
    await merge_duplicate_patterns()
    
    # Archive low-relevance memories
    await archive_low_score_memories(threshold=0.3)
```

## Monitoring and Analytics

### Memory Usage Metrics
```python
MEMORY_METRICS = {
    "retrieval_latency": Histogram(),
    "memory_hit_rate": Counter(),
    "storage_size": Gauge(),
    "active_memories": Gauge(),
    "relevance_scores": Histogram()
}

async def track_memory_performance(operation: str, duration: float):
    MEMORY_METRICS["retrieval_latency"].observe(duration)
    MEMORY_METRICS["memory_hit_rate"].inc()
```

This implementation provides a robust foundation for integrating sophisticated memory capabilities into the LangGraph-based legal research agents.