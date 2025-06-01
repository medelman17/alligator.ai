# ADR-003: Cost Management and LLM Usage Strategy

## Status
Proposed

## Context
The ingestion system must deliver **BEST IN CLASS** legal research capabilities. Quality is paramount - we cannot afford to compromise on legal accuracy, completeness, or sophistication. The challenge: architect an excellence-first LLM strategy that achieves maximum legal research quality while implementing intelligent efficiency optimizations (not cost-cutting).

## Questions to Address

### 1. LLM Role in API-Based Ingestion Pipeline ✅ RESOLVED
**Question**: What role do LLMs play in the CourtListener API-based ingestion process?

**🎯 PHASE 1 STRATEGY: API-Constrained Progressive Enhancement**

With **5,000 API calls/hour limit**, we need to be extremely strategic:

**Stage 1: Smart Case Selection** (API Budget Management)
```python
def select_cases_for_ingestion():
    # Priority: Supreme Court > Circuit > District
    # Focus on high-citation cases first
    # Recent decisions get priority boost
    
    api_budget_remaining = rate_limiter.get_remaining_calls()
    
    if api_budget_remaining > 1000:
        # High budget: aggressive case discovery
        return get_priority_cases(limit=100, include_citations=True)
    elif api_budget_remaining > 100:
        # Medium budget: focus on core cases
        return get_priority_cases(limit=20, supreme_court_only=True)
    else:
        # Low budget: essential cases only
        return get_priority_cases(limit=5, critical_only=True)
```

**Stage 2: LLM Enhancement** (Cost-Controlled Processing)
```python
class APIConstrainedLLMProcessor:
    def process_case_batch(self, cases_from_api):
        # Process multiple API-retrieved cases together
        return {
            "practice_area_classification": self.classify_batch(cases),
            "citation_treatment_analysis": self.analyze_citations(cases),
            "legal_authority_scoring": self.score_authority(cases),
            "summary_generation": self.generate_summaries(cases)
        }
```

**🏆 EXCELLENCE-TIER LLM Applications** (Premium Models, No Compromises):
1. **Legal Authority Analysis**: Deep understanding of precedential weight and legal hierarchy
2. **Citation Treatment Analysis**: Sophisticated analysis of how cases interact (positive/negative/neutral/distinguishing)
3. **Judicial Reasoning Extraction**: Understanding the legal logic and decision-making patterns
4. **Precedent Relationship Mapping**: Complex legal doctrine evolution and interaction chains
5. **Legal Holding Extraction**: Precise identification of the legal rule established by each case
6. **Practice Area Classification**: Nuanced, multi-dimensional legal domain categorization

**🎯 COMPREHENSIVE LLM Applications** (High-Quality Models):
1. **Case Summary Generation**: Sophisticated legal summaries that capture nuance
2. **Legal Concept Extraction**: Building comprehensive legal ontology with relationships
3. **Judicial Writing Style Analysis**: Understanding individual judge patterns and preferences
4. **Legal Strategy Implications**: Analysis of how cases affect litigation strategies
5. **Regulatory Impact Analysis**: Understanding how cases affect regulatory interpretation

**⚙️ INTELLIGENT AUTOMATION** (Hybrid LLM + Rule-Based):
1. **Citation Extraction**: LLM-validated rule-based parsing for maximum accuracy
2. **Metadata Enhancement**: LLM verification of basic metadata for completeness
3. **Quality Assurance**: LLM-powered validation of all processed data

### 2. Excellence-First Quality Framework ✅ RESOLVED
**Question**: How do we architect for best-in-class legal research quality?

**🎯 EXCELLENCE-FIRST PRINCIPLES**

1. **Quality Over Cost**: Never compromise legal accuracy for cost savings
2. **Comprehensive Analysis**: Every case gets full legal analysis treatment
3. **Premium Models**: Use GPT-4, Claude-3-Opus for all legal reasoning tasks
4. **Redundant Validation**: Multiple validation passes for critical legal determinations
5. **Legal Expert Review**: LLM analysis enhanced with legal domain expertise

**🏆 Premium Processing Architecture**:
```python
class ExcellenceFirstProcessor:
    def __init__(self):
        # Premium Model Selection
        self.legal_reasoning_model = "gpt-4"  # Best available for legal analysis
        self.citation_analysis_model = "claude-3-opus"  # Excellent at text relationships
        self.validation_model = "gpt-4"  # Secondary validation pass
        
        # Quality Standards (Not Cost Constraints)
        self.minimum_confidence_threshold = 0.95  # Extremely high confidence required
        self.require_multi_model_consensus = True  # Multiple models must agree
        self.enable_legal_expert_validation = True  # Human expert review for edge cases
        
    def process_case_comprehensive(self, case):
        """Comprehensive legal analysis with no quality compromises"""
        
        # Stage 1: Deep Legal Analysis (Premium Models)
        legal_analysis = self.analyze_with_premium_models(case)
        
        # Stage 2: Cross-Validation (Multiple Models)
        validation_results = self.cross_validate_analysis(legal_analysis, case)
        
        # Stage 3: Confidence Assessment
        if validation_results.confidence < self.minimum_confidence_threshold:
            # Queue for expert review rather than accept lower quality
            self.queue_for_expert_review(case, legal_analysis, validation_results)
        
        # Stage 4: Comprehensive Enhancement
        return self.enhance_with_full_context(legal_analysis, validation_results)
```

**🎯 Intelligent Efficiency Framework**:
```python
class IntelligentEfficiencyOptimizer:
    """Optimize efficiency while maintaining excellence - NOT cost-cutting"""
    
    def optimize_processing_workflow(self, case):
        """Smart optimizations that improve quality AND efficiency"""
        
        # Efficiency Optimization 1: Contextual Batching
        # Process related cases together for better legal understanding
        related_cases = self.find_doctrinally_related_cases(case)
        if len(related_cases) >= 3:
            return self.process_doctrine_cluster(related_cases)
        
        # Efficiency Optimization 2: Incremental Enhancement
        # Build upon previous analysis rather than starting from scratch
        prior_analysis = self.get_related_case_analysis(case)
        if prior_analysis:
            return self.enhance_with_context(case, prior_analysis)
        
        # Efficiency Optimization 3: Smart Model Selection
        # Use the BEST model for each specific task
        return self.process_with_optimal_models(case)
    
    def calculate_legal_impact_priority(self, case):
        """Prioritize based on legal significance, not cost"""
        
        legal_significance = (
            case.court.authority_weight * 0.4 +      # Legal hierarchy importance
            case.citation_network_centrality * 0.3 + # Position in legal network
            case.doctrinal_novelty_score * 0.2 +     # Legal innovation impact
            case.precedential_strength * 0.1         # Future citation potential
        )
        
        return legal_significance  # Quality-based prioritization
```

**Cost Factors**:
- **Token Usage**: Input tokens (document length) + output tokens (generated content)
- **Model Selection**: GPT-4 vs GPT-3.5 vs Claude vs local models for different tasks
- **Processing Frequency**: Real-time vs batch processing economics
- **Quality vs Cost**: Trade-offs between thoroughness and budget constraints

**Budget Management Options**:
- **Daily/Monthly Caps**: Hard limits on LLM API spending
- **Per-Document Budgets**: Maximum cost per legal document processed
- **Tiered Processing**: Different LLM treatment based on document importance
- **Queue Management**: Process high-priority documents first when approaching limits

### 3. Citation-Driven Case Expansion Strategy ✅ RESOLVED
**Question**: How do we implement the citation-driven case discovery workflow?

**🎯 The Strategy You Outlined**:
```python
class CitationDrivenExpansion:
    def process_seed_case(self, case_id):
        """
        1. Gather all citations in the case
        2. Check if we don't have any of those cases in our database  
        3. For each case we don't have, download immediately and process immediately
        4. For each case we don't have in second order, queue for future batch
        """
        
        # Step 1: Extract citations from seed case
        seed_case = self.api_client.get_case(case_id)
        citations = self.extract_citations(seed_case)
        
        # Step 2: Check what we're missing
        missing_first_order = self.check_missing_cases(citations)
        
        # Step 3: Immediate download and processing for first-order citations
        immediate_queue = []
        for cited_case_id in missing_first_order:
            if self.budget_controller.can_process_case_now():
                case_data = self.api_client.get_case(cited_case_id)
                enhanced_case = self.llm_processor.process_case(case_data)
                self.store_enhanced_case(enhanced_case)
                immediate_queue.append(case_data)
            else:
                # API or LLM budget exhausted
                self.queue_for_later(cited_case_id, priority="high")
        
        # Step 4: Queue second-order citations for batch processing
        for processed_case in immediate_queue:
            second_order_citations = self.extract_citations(processed_case)
            missing_second_order = self.check_missing_cases(second_order_citations)
            
            for second_order_case_id in missing_second_order:
                self.queue_for_batch_processing(second_order_case_id, priority="medium")
```

**💡 Key Optimizations for API Constraints**:

1. **Intelligent Queuing**:
   - Immediate queue: High-authority first-order citations
   - Batch queue: Lower-priority second-order citations
   - Emergency queue: Cases needed for active user research

2. **Budget-Aware Processing**:
   - Check both API and LLM budget before each case
   - Graceful degradation when limits approached
   - Priority re-ordering based on remaining budget

3. **Citation Network Intelligence**:
   - Track citation relationships as we build the network
   - Identify high-value citation clusters for batch processing
   - Avoid duplicate API calls for cases we already have

### 3. Excellence-First Resource Management ✅ RESOLVED
**Question**: How do we manage resources while maintaining best-in-class quality?

**🏆 EXCELLENCE-FIRST RESOURCE STRATEGY**

Instead of "budget limits" and "fallbacks," we implement **Quality Assurance Gates**:

```python
class QualityAssuranceResourceManager:
    def __init__(self):
        # Quality Gates (Not Budget Limits)
        self.quality_thresholds = {
            "legal_accuracy": 0.98,      # Near-perfect legal analysis required
            "citation_completeness": 0.95, # Comprehensive citation analysis
            "precedent_mapping": 0.97,   # Thorough precedent relationships
            "expert_consensus": 0.90     # Multi-model agreement required
        }
        
        # Resource Scaling (Not Resource Limiting)
        self.resource_scaling_strategy = {
            "peak_demand": "scale_up_infrastructure",
            "complex_cases": "allocate_premium_models", 
            "novel_legal_issues": "engage_expert_review",
            "high_impact_cases": "comprehensive_multi_pass_analysis"
        }
    
    def manage_processing_quality(self, case_batch):
        """Scale resources UP to maintain quality, never DOWN"""
        
        for case in case_batch:
            required_quality = self.assess_required_quality_level(case)
            
            if required_quality == "SUPREME_COURT_LEVEL":
                # Maximum resources: Multiple premium models + expert review
                return self.supreme_court_processing_pipeline(case)
            elif required_quality == "CIRCUIT_COURT_LEVEL":
                # High resources: Premium models + cross-validation
                return self.circuit_court_processing_pipeline(case)
            else:
                # Standard excellence: Premium model + validation
                return self.standard_excellence_pipeline(case)
```

**🚀 Scaling Strategy (Not Degradation Strategy)**:

1. **Scale UP**: When demand increases, add more processing capacity
2. **Queue Management**: Prioritize by legal significance, not cost
3. **Expert Integration**: Human legal experts for complex edge cases
4. **Infrastructure Investment**: Invest in better tools, not cheaper processing

### 4. LLM Processing Architecture
**Question**: How do we structure LLM usage for cost efficiency and reliability?

**Processing Patterns**:
- **Batch Processing**: Group documents for efficient API utilization
- **Incremental Processing**: Process documents in stages to control costs
- **Selective Enhancement**: Only apply expensive LLM processing to valuable documents
- **Caching Strategy**: Avoid reprocessing similar documents

**Quality vs Speed vs Cost Matrix**:
```
High Priority + High Budget: GPT-4, comprehensive analysis
Medium Priority + Medium Budget: GPT-3.5, targeted analysis  
Low Priority + Low Budget: Local model, basic processing
Emergency + No Budget: Rule-based processing only
```

## Decision Points Needed

### LLM Integration Architecture
1. **Service Boundary**: Where does LLM processing happen in the pipeline?
2. **Model Selection**: Which LLMs for which tasks (cost/quality optimization)
3. **Processing Triggers**: What triggers LLM enhancement vs basic ingestion?
4. **Error Handling**: How to handle LLM API failures gracefully

### Cost Management Framework
1. **Budget Allocation**: How to distribute LLM budget across different document types
2. **Monitoring System**: Real-time cost tracking and alerting
3. **Optimization Strategy**: A/B testing for cost-effective prompt engineering
4. **Scaling Strategy**: How costs scale with document volume growth

### Processing Efficiency
1. **Prompt Engineering**: Optimized prompts for legal document processing
2. **Batch Optimization**: Efficient batching strategies for API calls
3. **Caching Strategy**: When and how to cache LLM results
4. **Model Fine-tuning**: Cost/benefit of fine-tuned vs general models

## Technical Requirements

### Cost Controller Component
- [ ] Real-time budget tracking and consumption monitoring
- [ ] Configurable budget limits (daily, monthly, per-document)
- [ ] Cost prediction based on document characteristics
- [ ] Budget alerting and automatic fallback triggers

### LLM Service Abstraction
- [ ] Multi-provider LLM client (OpenAI, Anthropic, local models)
- [ ] Cost-aware model selection algorithms
- [ ] Retry logic with exponential backoff
- [ ] Request/response logging for cost analysis

### Processing Pipeline
- [ ] Tiered processing workflows based on budget availability
- [ ] Document priority scoring for LLM resource allocation
- [ ] Fallback processing paths when LLM services unavailable
- [ ] Quality metrics to measure LLM processing effectiveness

## Cost Optimization Strategies

### Prompt Engineering
- **Minimize Input Tokens**: Extract only relevant sections for LLM processing
- **Maximize Output Efficiency**: Structured outputs to reduce generation costs
- **Template Reuse**: Standard prompts for common legal document types
- **Context Optimization**: Smart context window management

### Model Selection Strategy
```
Document Type | Priority | Model Choice | Rationale
Supreme Court | High     | GPT-4       | Maximum accuracy for key precedents
Circuit Court | Medium   | GPT-3.5     | Good balance of quality and cost
District Court| Low      | Local Model | Volume processing, basic extraction
Administrative| Variable | Rule-based  | Structured data, no LLM needed
```

### Batch Processing Economics
- **Document Grouping**: Similar documents in same API call
- **Parallel Processing**: Multiple async requests within rate limits
- **Peak/Off-Peak**: Schedule expensive processing during cheaper API times
- **Volume Discounts**: Negotiate better rates for high-volume usage

## Final Decisions Made ✅

### **🏆 Excellence-First Architecture Decision**
**Premium Quality with Intelligent Efficiency**: Use best-available models (GPT-4, Claude-3-Opus) for all legal analysis, with smart optimizations that IMPROVE both quality and efficiency.

### **🎯 Quality Assurance Framework** 
**Multi-Model Validation**: Every legal determination validated by multiple premium models with 95%+ confidence thresholds. Human expert review for edge cases.

### **⚡ Intelligent Processing Strategy**
**Contextual Enhancement**: Process related cases together for deeper legal understanding. Build upon prior analysis for incremental knowledge building.

### **🚀 Resource Scaling Strategy**
**Scale UP, Never DOWN**: When facing resource constraints, increase capacity rather than compromise quality. Legal accuracy is non-negotiable.

## Implementation Ready ✅

### Next Implementation Steps  
- [x] Define citation-driven case expansion workflow
- [x] Design excellence-first quality framework
- [x] Specify premium LLM processing architecture with multi-model validation
- [ ] Implement CourtListener API client with intelligent rate management
- [ ] Build sophisticated citation extraction with LLM validation
- [ ] Create premium LLM processing pipeline with quality gates
- [ ] Design expert review integration for complex legal edge cases
- [ ] Implement contextual batching for related case analysis

## Dependencies
- ADR-001: Architecture Integration (service boundaries for LLM processing)
- ADR-002: Data Sources & Quality ✅ COMPLETE (CourtListener research done)
- ADR-004: Data Flow & Storage (how to store LLM-enhanced citation networks)

## Related ADRs
- ADR-001: Architecture Integration
- ADR-002: Data Sources & Quality
- ADR-004: Data Flow & Storage (to be created)
- ADR-005: Operational Concerns (to be created)