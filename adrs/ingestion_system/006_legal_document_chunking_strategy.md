# ADR-006: Legal Document Chunking Strategy

## Status
Proposed

## Context
Legal documents present unique challenges for LLM processing due to their length, complex logical structure, and interconnected legal reasoning. Court opinions can span 50+ pages with intricate citation networks, legal holdings that span multiple sections, and judicial reasoning that requires contextual understanding. 

**The chunking strategy is CRITICAL** - poor chunking destroys legal context and reasoning chains, while intelligent chunking preserves legal logic and enables sophisticated analysis.

## The Legal Document Chunking Challenge

### **Unique Characteristics of Legal Documents**

1. **Extreme Length**: Supreme Court opinions often 20-100+ pages
2. **Structured Reasoning**: Facts → Procedure → Legal Issues → Holdings → Reasoning → Conclusion
3. **Citation Density**: Heavy cross-references to prior cases, statutes, and legal concepts
4. **Contextual Dependencies**: Legal arguments build upon each other sequentially
5. **Multiple Opinion Types**: Majority, concurrence, dissent - each with different logical structures
6. **Technical Legal Language**: Precise terminology where context changes meaning

### **What Goes Wrong with Naive Chunking**

```python
# ❌ TERRIBLE APPROACH - Arbitrary Text Splitting
def naive_chunking(legal_document, chunk_size=4000):
    # This DESTROYS legal reasoning!
    return [legal_document[i:i+chunk_size] for i in range(0, len(legal_document), chunk_size)]
```

**Problems with naive chunking**:
- **Fragments legal arguments** mid-reasoning
- **Breaks citation context** (reference separated from analysis)
- **Destroys holding integrity** (legal rule split across chunks)
- **Loses judicial structure** (facts mixed with legal analysis)
- **Eliminates cross-references** between legal concepts

## Proposed Legal-Aware Chunking Strategies

### **🏗️ STRATEGY 1: Semantic Legal Structure Chunking**

Respect the inherent structure of legal documents:

```python
class LegalStructureChunker:
    def __init__(self):
        self.legal_sections = {
            "case_caption": {"priority": 1, "max_tokens": 500},
            "factual_background": {"priority": 2, "max_tokens": 2000},
            "procedural_history": {"priority": 3, "max_tokens": 1500},
            "legal_issues": {"priority": 4, "max_tokens": 1000},
            "holdings_and_reasoning": {"priority": 5, "max_tokens": 4000},
            "conclusion": {"priority": 6, "max_tokens": 1000},
            "dissenting_opinions": {"priority": 7, "max_tokens": 3000}
        }
    
    def chunk_by_legal_structure(self, legal_document):
        """Chunk based on legal document structure, not arbitrary length"""
        
        # Step 1: Identify legal sections using legal document markers
        sections = self.identify_legal_sections(legal_document)
        
        # Step 2: Preserve complete legal arguments within chunks
        chunks = []
        for section_name, section_text in sections.items():
            if len(section_text) > self.legal_sections[section_name]["max_tokens"]:
                # Subdivide large sections at logical breakpoints
                sub_chunks = self.subdivide_legal_section(section_text, section_name)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "content": section_text,
                    "section_type": section_name,
                    "legal_context": self.extract_legal_context(section_text)
                })
        
        return chunks
```

### **🔗 STRATEGY 2: Citation-Aware Chunking**

Preserve citation context and legal authority chains:

```python
class CitationAwareChunker:
    def __init__(self):
        self.citation_window = 1000  # Tokens before/after citation for context
        
    def chunk_preserving_citations(self, legal_document):
        """Ensure citations maintain proper context"""
        
        # Step 1: Identify all citations and their contexts
        citations = self.extract_citations_with_context(legal_document)
        
        # Step 2: Create chunks that preserve citation reasoning
        chunks = []
        for citation in citations:
            citation_chunk = {
                "cited_case": citation.case_reference,
                "citation_context": citation.surrounding_text,
                "legal_proposition": citation.legal_point_being_made,
                "treatment_type": citation.how_case_is_used,  # positive, negative, distinguishing
                "reasoning_chain": citation.logical_argument
            }
            chunks.append(citation_chunk)
        
        return chunks
    
    def extract_citations_with_context(self, document):
        """Extract citations with sufficient context for legal analysis"""
        citations = []
        
        # Legal citation patterns (more sophisticated than simple regex)
        citation_patterns = self.get_legal_citation_patterns()
        
        for match in citation_patterns.finditer(document):
            citation_start = max(0, match.start() - self.citation_window)
            citation_end = min(len(document), match.end() + self.citation_window)
            
            full_context = document[citation_start:citation_end]
            
            citations.append({
                "case_reference": match.group(),
                "surrounding_text": full_context,
                "position_in_document": match.start(),
                "legal_context": self.analyze_citation_purpose(full_context)
            })
        
        return citations
```

### **🧠 STRATEGY 3: Legal Reasoning Chain Chunking**

Preserve logical arguments and judicial reasoning:

```python
class LegalReasoningChunker:
    def __init__(self):
        self.reasoning_indicators = [
            "because", "therefore", "however", "nevertheless", "moreover",
            "consequently", "in contrast", "similarly", "for example",
            "specifically", "in particular", "indeed", "furthermore"
        ]
    
    def chunk_by_reasoning_chains(self, legal_document):
        """Preserve complete legal arguments and reasoning chains"""
        
        # Step 1: Identify logical argument boundaries
        reasoning_segments = self.identify_reasoning_segments(legal_document)
        
        # Step 2: Create chunks that preserve complete legal arguments
        chunks = []
        current_argument = []
        current_tokens = 0
        max_tokens = 3000
        
        for segment in reasoning_segments:
            segment_tokens = self.count_tokens(segment.text)
            
            if current_tokens + segment_tokens > max_tokens and current_argument:
                # Complete the current argument before starting new chunk
                if self.is_complete_legal_argument(current_argument):
                    chunks.append(self.create_reasoning_chunk(current_argument))
                    current_argument = [segment]
                    current_tokens = segment_tokens
                else:
                    # Extend chunk to complete the argument
                    current_argument.append(segment)
                    current_tokens += segment_tokens
            else:
                current_argument.append(segment)
                current_tokens += segment_tokens
        
        # Add final chunk
        if current_argument:
            chunks.append(self.create_reasoning_chunk(current_argument))
        
        return chunks
    
    def is_complete_legal_argument(self, segments):
        """Check if segments form a complete legal argument"""
        # Look for legal argument structure: premise → reasoning → conclusion
        has_premise = any("court held" in seg.text.lower() for seg in segments)
        has_reasoning = any(indicator in seg.text.lower() for indicator in self.reasoning_indicators for seg in segments)
        has_conclusion = any("therefore" in seg.text.lower() or "thus" in seg.text.lower() for seg in segments)
        
        return has_premise and has_reasoning and has_conclusion
```

### **📚 STRATEGY 4: Contextual Overlap Chunking**

Maintain context across chunk boundaries:

```python
class ContextualOverlapChunker:
    def __init__(self):
        self.overlap_tokens = 200  # Overlap between chunks for context
        self.legal_context_markers = [
            "the court held", "we conclude", "the issue is", "the question presented",
            "plaintiff argues", "defendant contends", "the statute provides"
        ]
    
    def chunk_with_legal_context_overlap(self, legal_document):
        """Create overlapping chunks that preserve legal context"""
        
        base_chunks = self.create_base_chunks(legal_document, chunk_size=3000)
        contextualized_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            enhanced_chunk = {
                "primary_content": chunk,
                "prior_context": self.get_prior_legal_context(base_chunks, i),
                "following_context": self.get_following_legal_context(base_chunks, i),
                "legal_thread": self.identify_continuing_legal_argument(base_chunks, i)
            }
            contextualized_chunks.append(enhanced_chunk)
        
        return contextualized_chunks
    
    def get_prior_legal_context(self, chunks, current_index):
        """Get relevant legal context from previous chunks"""
        if current_index == 0:
            return None
        
        prior_chunk = chunks[current_index - 1]
        
        # Extract key legal context (holdings, citations, arguments)
        return {
            "key_holdings": self.extract_holdings(prior_chunk),
            "active_citations": self.extract_active_citations(prior_chunk),
            "ongoing_argument": self.extract_argument_thread(prior_chunk)
        }
```

### **⚖️ STRATEGY 5: Multi-Opinion Aware Chunking**

Handle majority, concurrence, and dissent separately:

```python
class MultiOpinionChunker:
    def __init__(self):
        self.opinion_markers = {
            "majority": ["the court holds", "we hold", "the majority"],
            "concurrence": ["concurring", "i concur", "writing separately"],
            "dissent": ["dissenting", "i dissent", "the dissent", "i would hold"]
        }
    
    def chunk_by_opinion_type(self, legal_document):
        """Separate and chunk different types of judicial opinions"""
        
        # Step 1: Identify opinion boundaries
        opinions = self.separate_opinions(legal_document)
        
        # Step 2: Chunk each opinion type with appropriate strategy
        chunked_opinions = {}
        
        for opinion_type, opinion_text in opinions.items():
            if opinion_type == "majority":
                # Most comprehensive chunking for majority opinion
                chunked_opinions[opinion_type] = self.chunk_majority_opinion(opinion_text)
            elif opinion_type == "concurrence":
                # Focus on points of agreement and additional reasoning
                chunked_opinions[opinion_type] = self.chunk_concurrence(opinion_text)
            elif opinion_type == "dissent":
                # Focus on disagreement and alternative legal reasoning
                chunked_opinions[opinion_type] = self.chunk_dissent(opinion_text)
        
        return chunked_opinions
```

## Advanced Legal Chunking Considerations

### **🎯 Legal Domain-Specific Challenges**

1. **Constitutional Law**: Complex multi-factor tests, balancing frameworks
2. **Contract Law**: Detailed fact patterns, interpretation rules
3. **Criminal Law**: Procedural requirements, burden of proof analysis
4. **Administrative Law**: Regulatory interpretation, agency deference
5. **Civil Rights**: Historical context, evolving legal standards

### **🔬 Quality Validation for Legal Chunks**

```python
class LegalChunkQualityValidator:
    def validate_chunk_quality(self, chunk):
        """Ensure chunks maintain legal integrity"""
        
        quality_metrics = {
            "citation_completeness": self.validate_citations_complete(chunk),
            "argument_coherence": self.validate_argument_flow(chunk),
            "legal_context_preservation": self.validate_context(chunk),
            "holding_integrity": self.validate_holdings_complete(chunk),
            "cross_reference_validity": self.validate_cross_references(chunk)
        }
        
        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
        
        if overall_quality < 0.9:  # 90% quality threshold
            return self.recommend_chunk_improvements(chunk, quality_metrics)
        
        return quality_metrics
```

## Implementation Strategy

### **🏗️ Hybrid Approach: Multi-Strategy Chunking**

```python
class LegalDocumentChunkingPipeline:
    def __init__(self):
        self.chunkers = {
            "structure": LegalStructureChunker(),
            "citation": CitationAwareChunker(), 
            "reasoning": LegalReasoningChunker(),
            "context": ContextualOverlapChunker(),
            "opinion": MultiOpinionChunker()
        }
    
    def chunk_legal_document(self, document, document_type, complexity_level):
        """Apply appropriate chunking strategy based on document characteristics"""
        
        if document_type == "supreme_court_opinion":
            # Use all strategies for maximum sophistication
            return self.comprehensive_chunking(document)
        elif document_type == "circuit_opinion":
            # Use structure + citation + reasoning
            return self.standard_chunking(document)
        elif document_type == "district_opinion":
            # Use structure + citation
            return self.basic_chunking(document)
        else:
            # Custom strategy based on document analysis
            return self.adaptive_chunking(document)
```

## Decision Points Needed

1. **Primary Chunking Strategy**: Which approach best preserves legal reasoning integrity?
2. **Chunk Size Optimization**: Optimal token counts for different types of legal analysis?
3. **Context Preservation**: How much overlap/context needed between chunks?
4. **Quality Validation**: How to measure and ensure chunk quality for legal analysis?
5. **Performance vs Quality**: Balance between processing efficiency and legal accuracy?

## Next Steps

1. **Legal Document Analysis**: Study structure patterns across different court levels
2. **Citation Pattern Research**: Comprehensive analysis of legal citation usage
3. **LLM Context Window Optimization**: Test different chunk sizes with legal analysis quality
4. **Expert Validation**: Legal expert review of chunking strategies
5. **Implementation and Testing**: Build and validate chunking pipeline

## Dependencies
- ADR-003: Cost & LLM Usage (chunking affects LLM processing efficiency)
- Legal domain expertise for validation
- Sample legal documents for testing and optimization

## Related ADRs
- ADR-003: Cost & LLM Usage Strategy
- ADR-004: Data Flow & Storage (to be created)
- ADR-001: Architecture Integration (to be created)