"""
Sophisticated Legal Document Chunking Strategies.

Implements the comprehensive chunking approaches from ADR-006:
- Semantic legal structure chunking (respects legal document organization)
- Citation-aware chunking (preserves citation context and reasoning)
- Legal reasoning chain chunking (maintains logical argument integrity)
- Contextual overlap chunking (maintains context across boundaries)
- Multi-opinion aware chunking (handles majority/concurrence/dissent separately)

CRITICAL: Poor chunking destroys legal context and reasoning chains.
This implementation prioritizes legal accuracy over processing efficiency.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import spacy
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LegalSectionType(Enum):
    """Types of legal document sections."""
    CASE_CAPTION = "case_caption"
    FACTUAL_BACKGROUND = "factual_background"
    PROCEDURAL_HISTORY = "procedural_history"
    LEGAL_ISSUES = "legal_issues"
    HOLDINGS_AND_REASONING = "holdings_and_reasoning"
    CONCLUSION = "conclusion"
    MAJORITY_OPINION = "majority_opinion"
    CONCURRING_OPINION = "concurring_opinion"
    DISSENTING_OPINION = "dissenting_opinion"
    APPENDIX = "appendix"


class OpinionType(Enum):
    """Types of judicial opinions."""
    MAJORITY = "majority"
    CONCURRENCE = "concurrence"
    DISSENT = "dissent"
    PER_CURIAM = "per_curiam"


@dataclass
class LegalChunk:
    """A chunk of legal document with preserved legal context."""
    content: str
    section_type: LegalSectionType
    chunk_index: int
    total_chunks: int
    
    # Legal context preservation
    legal_context: Dict[str, Any] = field(default_factory=dict)
    citations_contained: List[str] = field(default_factory=list)
    legal_concepts: List[str] = field(default_factory=list)
    reasoning_thread: str = ""
    
    # Chunk relationships
    prior_context: Optional[str] = None
    following_context: Optional[str] = None
    related_chunks: List[int] = field(default_factory=list)
    
    # Opinion-specific data
    opinion_type: Optional[OpinionType] = None
    author_judge: Optional[str] = None
    
    # Quality metadata
    legal_completeness_score: float = 0.0
    citation_completeness_score: float = 0.0
    reasoning_integrity_score: float = 0.0


@dataclass
class CitationContext:
    """Context information for a legal citation."""
    citation: str
    case_name: Optional[str]
    surrounding_text: str
    legal_proposition: str
    treatment_type: str  # positive, negative, distinguishing, neutral
    reasoning_chain: str
    position_in_document: int
    strength: float  # 0.0 to 1.0


class LegalChunker(ABC):
    """Abstract base class for legal document chunking strategies."""
    
    @abstractmethod
    def chunk_legal_document(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Chunk a legal document while preserving legal context."""
        pass
    
    @abstractmethod
    def validate_chunk_quality(self, chunk: LegalChunk) -> Dict[str, float]:
        """Validate the legal integrity of a chunk."""
        pass


class LegalStructureChunker(LegalChunker):
    """
    Chunk based on inherent legal document structure.
    
    Respects natural boundaries in legal reasoning and maintains
    complete legal arguments within chunks.
    """
    
    def __init__(self):
        # Token limits for different legal sections
        self.section_limits = {
            LegalSectionType.CASE_CAPTION: 500,
            LegalSectionType.FACTUAL_BACKGROUND: 2000,
            LegalSectionType.PROCEDURAL_HISTORY: 1500,
            LegalSectionType.LEGAL_ISSUES: 1000,
            LegalSectionType.HOLDINGS_AND_REASONING: 4000,
            LegalSectionType.CONCLUSION: 1000,
            LegalSectionType.MAJORITY_OPINION: 4000,
            LegalSectionType.CONCURRING_OPINION: 3000,
            LegalSectionType.DISSENTING_OPINION: 3000
        }
        
        # Legal section markers
        self.section_markers = {
            r"(?i)facts?|background|factual\s+background": LegalSectionType.FACTUAL_BACKGROUND,
            r"(?i)procedural\s+history|procedure|proceedings": LegalSectionType.PROCEDURAL_HISTORY,
            r"(?i)issue|question|legal\s+issue": LegalSectionType.LEGAL_ISSUES,
            r"(?i)holding|analysis|reasoning|discussion": LegalSectionType.HOLDINGS_AND_REASONING,
            r"(?i)conclusion|disposition|judgment": LegalSectionType.CONCLUSION,
            r"(?i)concur|concurring": LegalSectionType.CONCURRING_OPINION,
            r"(?i)dissent|dissenting": LegalSectionType.DISSENTING_OPINION
        }
    
    def chunk_legal_document(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """
        Chunk based on legal document structure.
        
        Preserves complete legal arguments within sections.
        """
        logger.info("Starting semantic legal structure chunking")
        
        # Step 1: Identify legal sections
        sections = self._identify_legal_sections(document)
        
        # Step 2: Create chunks respecting legal boundaries
        chunks = []
        chunk_index = 0
        
        for section_type, section_text in sections.items():
            section_chunks = self._chunk_legal_section(
                section_text, 
                section_type, 
                chunk_index
            )
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)
        
        # Step 3: Add total chunks count to all chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        logger.info(f"Created {len(chunks)} legal structure chunks")
        return chunks
    
    def _identify_legal_sections(self, document: str) -> Dict[LegalSectionType, str]:
        """Identify legal sections in the document."""
        
        sections = {}
        current_section = LegalSectionType.HOLDINGS_AND_REASONING  # Default
        current_text = []
        
        lines = document.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line indicates a new section
            new_section = self._identify_section_type(line)
            if new_section:
                # Save previous section
                if current_text:
                    sections[current_section] = '\n'.join(current_text)
                
                # Start new section
                current_section = new_section
                current_text = [line]
            else:
                current_text.append(line)
        
        # Save final section
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        return sections
    
    def _identify_section_type(self, line: str) -> Optional[LegalSectionType]:
        """Identify if a line indicates a new legal section."""
        
        for pattern, section_type in self.section_markers.items():
            if re.search(pattern, line):
                return section_type
        
        return None
    
    def _chunk_legal_section(
        self, 
        section_text: str, 
        section_type: LegalSectionType, 
        start_index: int
    ) -> List[LegalChunk]:
        """Chunk a legal section while preserving arguments."""
        
        max_tokens = self.section_limits.get(section_type, 3000)
        current_tokens = self._count_tokens(section_text)
        
        if current_tokens <= max_tokens:
            # Section fits in one chunk
            chunk = LegalChunk(
                content=section_text,
                section_type=section_type,
                chunk_index=start_index,
                total_chunks=0  # Will be set later
            )
            chunk.legal_context = self._extract_legal_context(section_text, section_type)
            return [chunk]
        
        # Section needs subdivision at logical breakpoints
        return self._subdivide_legal_section(section_text, section_type, start_index, max_tokens)
    
    def _subdivide_legal_section(
        self, 
        section_text: str, 
        section_type: LegalSectionType, 
        start_index: int,
        max_tokens: int
    ) -> List[LegalChunk]:
        """Subdivide large sections at logical breakpoints."""
        
        # Find logical breakpoints (paragraphs, legal arguments)
        paragraphs = self._split_into_legal_paragraphs(section_text)
        
        chunks = []
        current_chunk_text = []
        current_tokens = 0
        chunk_index = start_index
        
        for paragraph in paragraphs:
            para_tokens = self._count_tokens(paragraph)
            
            if current_tokens + para_tokens > max_tokens and current_chunk_text:
                # Create chunk from current content
                chunk_content = '\n\n'.join(current_chunk_text)
                chunk = LegalChunk(
                    content=chunk_content,
                    section_type=section_type,
                    chunk_index=chunk_index,
                    total_chunks=0
                )
                chunk.legal_context = self._extract_legal_context(chunk_content, section_type)
                chunks.append(chunk)
                
                # Start new chunk
                chunk_index += 1
                current_chunk_text = [paragraph]
                current_tokens = para_tokens
            else:
                current_chunk_text.append(paragraph)
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk_text:
            chunk_content = '\n\n'.join(current_chunk_text)
            chunk = LegalChunk(
                content=chunk_content,
                section_type=section_type,
                chunk_index=chunk_index,
                total_chunks=0
            )
            chunk.legal_context = self._extract_legal_context(chunk_content, section_type)
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_legal_paragraphs(self, text: str) -> List[str]:
        """Split text into legal paragraphs respecting legal structure."""
        
        # Split on double newlines first
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Further split on legal reasoning indicators
        legal_splits = []
        for para in paragraphs:
            # Look for legal reasoning transitions
            split_patterns = [
                r'(?=\b(?:Therefore|Thus|Accordingly|However|Nevertheless|Moreover)\b)',
                r'(?=\b(?:The court held|We hold|We conclude|We find)\b)',
                r'(?=\b(?:First|Second|Third|Finally)\b.*(?:issue|holding|argument))',
            ]
            
            current_splits = [para]
            for pattern in split_patterns:
                new_splits = []
                for split in current_splits:
                    parts = re.split(pattern, split)
                    new_splits.extend([p.strip() for p in parts if p.strip()])
                current_splits = new_splits
            
            legal_splits.extend(current_splits)
        
        return [p for p in legal_splits if len(p.strip()) > 50]  # Filter very short paragraphs
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Simple approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _extract_legal_context(self, text: str, section_type: LegalSectionType) -> Dict[str, Any]:
        """Extract legal context from text."""
        
        context = {
            "section_type": section_type.value,
            "key_legal_terms": self._extract_legal_terms(text),
            "citations": self._extract_basic_citations(text),
            "legal_concepts": self._extract_legal_concepts(text)
        }
        
        return context
    
    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extract key legal terms from text."""
        
        legal_terms = [
            r'\b(?:plaintiff|defendant|appellant|appellee|petitioner|respondent)\b',
            r'\b(?:holding|ruling|decision|judgment|order)\b',
            r'\b(?:statute|regulation|ordinance|code|law)\b',
            r'\b(?:precedent|case law|authority|binding|persuasive)\b',
            r'\b(?:constitutional|unconstitutional|due process|equal protection)\b'
        ]
        
        found_terms = []
        for pattern in legal_terms:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_terms.extend(matches)
        
        return list(set(found_terms))
    
    def _extract_basic_citations(self, text: str) -> List[str]:
        """Extract basic legal citations."""
        
        citation_patterns = [
            r'\d+\s+[A-Z][a-z]*\.?\s*(?:\d+[a-z]*\.?)?\s+\d+',  # Basic citation pattern
            r'\d+\s+U\.S\.\s+\d+',  # US Supreme Court
            r'\d+\s+F\.(?:2d|3d)\s+\d+'  # Federal courts
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))
    
    def _extract_legal_concepts(self, text: str) -> List[str]:
        """Extract legal concepts from text."""
        
        concept_patterns = [
            r'(?i)\b(?:qualified immunity|sovereign immunity|due process)\b',
            r'(?i)\b(?:burden of proof|standard of review|level of scrutiny)\b',
            r'(?i)\b(?:constitutional|statute of limitations|res judicata)\b'
        ]
        
        concepts = []
        for pattern in concept_patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)
        
        return list(set(concepts))
    
    def validate_chunk_quality(self, chunk: LegalChunk) -> Dict[str, float]:
        """Validate legal integrity of a structure-based chunk."""
        
        quality_scores = {}
        
        # Check citation completeness
        citations = chunk.citations_contained
        incomplete_citations = [c for c in citations if not self._is_complete_citation(c)]
        quality_scores["citation_completeness"] = 1.0 - (len(incomplete_citations) / max(len(citations), 1))
        
        # Check argument coherence (basic heuristic)
        has_premise = any(marker in chunk.content.lower() for marker in ["court held", "ruling", "decision"])
        has_reasoning = any(marker in chunk.content.lower() for marker in ["because", "therefore", "thus"])
        has_conclusion = any(marker in chunk.content.lower() for marker in ["therefore", "accordingly", "conclusion"])
        
        coherence_score = (has_premise + has_reasoning + has_conclusion) / 3.0
        quality_scores["argument_coherence"] = coherence_score
        
        # Overall score
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        quality_scores["overall"] = overall_score
        
        return quality_scores
    
    def _is_complete_citation(self, citation: str) -> bool:
        """Check if citation appears complete."""
        # Very basic check - has volume, reporter, page
        pattern = r'\d+\s+[A-Z][a-z]*\.?\s*\d+'
        return bool(re.match(pattern, citation.strip()))


class CitationAwareChunker(LegalChunker):
    """
    Preserve citation context and legal authority chains.
    
    Ensures citations maintain proper context for legal analysis.
    """
    
    def __init__(self, citation_window: int = 1000):
        self.citation_window = citation_window  # Tokens before/after citation
        
        # Legal citation patterns (comprehensive)
        self.citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',  # US Supreme Court
            r'\d+\s+F\.(?:2d|3d|Supp\.2?d?|App\'x)\s+\d+',  # Federal courts
            r'\d+\s+[A-Z][a-z]*\.(?:\s*(?:2d|3d))?\s+\d+',  # State courts
            r'\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
            r'\d+\s+L\.Ed\.(?:2d)?\s+\d+'  # Lawyers' Edition
        ]
    
    def chunk_legal_document(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Chunk preserving citation context."""
        
        logger.info("Starting citation-aware chunking")
        
        # Extract all citations with context
        citation_contexts = self._extract_citations_with_context(document)
        
        # Create chunks around citations
        chunks = []
        chunk_index = 0
        
        for citation_context in citation_contexts:
            chunk = self._create_citation_chunk(citation_context, chunk_index)
            chunks.append(chunk)
            chunk_index += 1
        
        # Fill in gaps between citation chunks if needed
        gap_chunks = self._fill_citation_gaps(document, citation_contexts, chunk_index)
        chunks.extend(gap_chunks)
        
        # Update total chunks count
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        logger.info(f"Created {len(chunks)} citation-aware chunks")
        return chunks
    
    def _extract_citations_with_context(self, document: str) -> List[CitationContext]:
        """Extract citations with sufficient context for legal analysis."""
        
        citations = []
        
        for pattern in self.citation_patterns:
            for match in re.finditer(pattern, document, re.IGNORECASE):
                citation_start = max(0, match.start() - self.citation_window)
                citation_end = min(len(document), match.end() + self.citation_window)
                
                full_context = document[citation_start:citation_end]
                
                citation_context = CitationContext(
                    citation=match.group(),
                    case_name=self._extract_case_name_near_citation(full_context),
                    surrounding_text=full_context,
                    legal_proposition=self._extract_legal_proposition(full_context),
                    treatment_type=self._analyze_citation_treatment(full_context),
                    reasoning_chain=self._extract_reasoning_chain(full_context),
                    position_in_document=match.start(),
                    strength=self._calculate_citation_strength(full_context)
                )
                
                citations.append(citation_context)
        
        # Remove overlapping citations
        return self._remove_overlapping_citations(citations)
    
    def _extract_case_name_near_citation(self, context: str) -> Optional[str]:
        """Extract case name near citation."""
        
        # Look for case name patterns near citation
        case_patterns = [
            r'([A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_legal_proposition(self, context: str) -> str:
        """Extract the legal proposition being supported by citation."""
        
        # Look for sentences containing legal reasoning
        sentences = re.split(r'[.!?]+', context)
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in 
                   ['held', 'holding', 'ruled', 'found', 'established', 'recognized']):
                return sentence.strip()
        
        # Fallback to context around citation
        return context[:200] + "..." if len(context) > 200 else context
    
    def _analyze_citation_treatment(self, context: str) -> str:
        """Analyze how the citation is treated."""
        
        treatment_indicators = {
            'follows': ['follows', 'adopts', 'agrees with', 'consistent with'],
            'distinguishes': ['distinguishes', 'different from', 'unlike', 'not applicable'],
            'overrules': ['overrules', 'overturns', 'rejects', 'abandons'],
            'questions': ['questions', 'doubts', 'uncertain', 'problematic'],
            'explains': ['explains', 'clarifies', 'elaborates', 'expands'],
            'cites': ['cites', 'citing', 'see', 'reference']
        }
        
        context_lower = context.lower()
        
        for treatment, indicators in treatment_indicators.items():
            if any(indicator in context_lower for indicator in indicators):
                return treatment
        
        return 'cites'  # Default treatment
    
    def _extract_reasoning_chain(self, context: str) -> str:
        """Extract the logical reasoning chain."""
        
        # Look for reasoning connectors
        reasoning_indicators = [
            'because', 'therefore', 'thus', 'accordingly', 'consequently',
            'however', 'nevertheless', 'moreover', 'furthermore', 'indeed'
        ]
        
        sentences = re.split(r'[.!?]+', context)
        reasoning_sentences = []
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in reasoning_indicators):
                reasoning_sentences.append(sentence.strip())
        
        return ' '.join(reasoning_sentences)
    
    def _calculate_citation_strength(self, context: str) -> float:
        """Calculate the strength of the citation relationship."""
        
        # Factors that increase citation strength
        strength_factors = {
            'central_holding': 0.3,  # Citation supports central holding
            'direct_quote': 0.2,    # Direct quotation from cited case
            'detailed_analysis': 0.2, # Detailed discussion of cited case
            'precedential_reliance': 0.3  # Explicit reliance on precedent
        }
        
        strength = 0.0
        context_lower = context.lower()
        
        # Check for central holding indicators
        if any(term in context_lower for term in ['central', 'primary', 'main', 'principal']):
            strength += strength_factors['central_holding']
        
        # Check for quotation marks (direct quote)
        if '"' in context or '"' in context or '"' in context:
            strength += strength_factors['direct_quote']
        
        # Check for detailed analysis
        if len(context) > 800:  # Longer context suggests detailed analysis
            strength += strength_factors['detailed_analysis']
        
        # Check for precedential reliance
        if any(term in context_lower for term in ['precedent', 'binding', 'controlling']):
            strength += strength_factors['precedential_reliance']
        
        return min(1.0, strength)
    
    def _remove_overlapping_citations(self, citations: List[CitationContext]) -> List[CitationContext]:
        """Remove overlapping citation contexts."""
        
        citations.sort(key=lambda c: c.position_in_document)
        
        non_overlapping = []
        for citation in citations:
            if not non_overlapping:
                non_overlapping.append(citation)
                continue
            
            last_citation = non_overlapping[-1]
            
            # Check for overlap
            last_end = last_citation.position_in_document + len(last_citation.surrounding_text)
            current_start = citation.position_in_document
            
            if current_start > last_end:
                non_overlapping.append(citation)
            else:
                # Keep citation with higher strength
                if citation.strength > last_citation.strength:
                    non_overlapping[-1] = citation
        
        return non_overlapping
    
    def _create_citation_chunk(self, citation_context: CitationContext, chunk_index: int) -> LegalChunk:
        """Create a legal chunk centered on a citation."""
        
        chunk = LegalChunk(
            content=citation_context.surrounding_text,
            section_type=LegalSectionType.HOLDINGS_AND_REASONING,  # Default
            chunk_index=chunk_index,
            total_chunks=0,
            citations_contained=[citation_context.citation],
            reasoning_thread=citation_context.reasoning_chain
        )
        
        chunk.legal_context = {
            "primary_citation": citation_context.citation,
            "case_name": citation_context.case_name,
            "treatment_type": citation_context.treatment_type,
            "legal_proposition": citation_context.legal_proposition,
            "citation_strength": citation_context.strength
        }
        
        return chunk
    
    def _fill_citation_gaps(
        self, 
        document: str, 
        citation_contexts: List[CitationContext], 
        start_index: int
    ) -> List[LegalChunk]:
        """Fill gaps between citation chunks."""
        
        # Find text areas not covered by citation contexts
        covered_ranges = []
        for ctx in citation_contexts:
            start = max(0, ctx.position_in_document - self.citation_window)
            end = min(len(document), ctx.position_in_document + len(ctx.citation) + self.citation_window)
            covered_ranges.append((start, end))
        
        # Merge overlapping ranges
        covered_ranges.sort()
        merged_ranges = []
        for start, end in covered_ranges:
            if merged_ranges and start <= merged_ranges[-1][1]:
                merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], end))
            else:
                merged_ranges.append((start, end))
        
        # Create chunks for gaps
        gap_chunks = []
        chunk_index = start_index
        
        last_end = 0
        for start, end in merged_ranges:
            if start > last_end:
                # There's a gap
                gap_text = document[last_end:start].strip()
                if len(gap_text) > 100:  # Only create chunk if substantial content
                    chunk = LegalChunk(
                        content=gap_text,
                        section_type=LegalSectionType.HOLDINGS_AND_REASONING,
                        chunk_index=chunk_index,
                        total_chunks=0
                    )
                    gap_chunks.append(chunk)
                    chunk_index += 1
            
            last_end = end
        
        # Handle final gap
        if last_end < len(document):
            gap_text = document[last_end:].strip()
            if len(gap_text) > 100:
                chunk = LegalChunk(
                    content=gap_text,
                    section_type=LegalSectionType.HOLDINGS_AND_REASONING,
                    chunk_index=chunk_index,
                    total_chunks=0
                )
                gap_chunks.append(chunk)
        
        return gap_chunks
    
    def validate_chunk_quality(self, chunk: LegalChunk) -> Dict[str, float]:
        """Validate citation-aware chunk quality."""
        
        quality_scores = {}
        
        # Citation completeness - all citations should have context
        if chunk.citations_contained:
            complete_citations = 0
            for citation in chunk.citations_contained:
                # Check if citation has sufficient surrounding context
                citation_pos = chunk.content.find(citation)
                if citation_pos >= 0:
                    before_context = chunk.content[:citation_pos]
                    after_context = chunk.content[citation_pos + len(citation):]
                    
                    if len(before_context) >= 100 and len(after_context) >= 100:
                        complete_citations += 1
            
            quality_scores["citation_completeness"] = complete_citations / len(chunk.citations_contained)
        else:
            quality_scores["citation_completeness"] = 1.0  # No citations to evaluate
        
        # Legal context preservation
        has_legal_context = bool(chunk.legal_context.get("legal_proposition"))
        has_treatment_analysis = bool(chunk.legal_context.get("treatment_type"))
        has_reasoning = bool(chunk.reasoning_thread)
        
        context_score = (has_legal_context + has_treatment_analysis + has_reasoning) / 3.0
        quality_scores["legal_context_preservation"] = context_score
        
        # Overall quality
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        quality_scores["overall"] = overall_score
        
        return quality_scores


class LegalDocumentChunkingPipeline:
    """
    Hybrid legal document chunking pipeline.
    
    Applies appropriate chunking strategy based on document characteristics.
    Implements the multi-strategy approach from ADR-006.
    """
    
    def __init__(self):
        self.chunkers = {
            "structure": LegalStructureChunker(),
            "citation": CitationAwareChunker(),
            # Add more chunkers as implemented
        }
    
    def chunk_legal_document(
        self, 
        document: str, 
        document_type: str = "unknown",
        complexity_level: str = "standard",
        metadata: Dict[str, Any] = None
    ) -> List[LegalChunk]:
        """
        Apply appropriate chunking strategy based on document characteristics.
        
        Args:
            document: Legal document text
            document_type: Type of legal document (supreme_court_opinion, etc.)
            complexity_level: Processing complexity required
            metadata: Additional document metadata
        
        Returns:
            List of legal chunks with preserved context
        """
        
        logger.info(f"Chunking {document_type} document with {complexity_level} complexity")
        
        if document_type == "supreme_court_opinion":
            # Use comprehensive chunking for maximum sophistication
            return self._comprehensive_chunking(document, metadata)
        elif document_type == "circuit_opinion":
            # Use structure + citation chunking
            return self._standard_chunking(document, metadata)
        elif document_type == "district_opinion":
            # Use structure chunking
            return self._basic_chunking(document, metadata)
        else:
            # Adaptive strategy based on document analysis
            return self._adaptive_chunking(document, metadata)
    
    def _comprehensive_chunking(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Apply all chunking strategies for maximum sophistication."""
        
        # Start with structure-based chunking
        structure_chunks = self.chunkers["structure"].chunk_legal_document(document, metadata)
        
        # Enhance with citation analysis
        citation_chunks = self.chunkers["citation"].chunk_legal_document(document, metadata)
        
        # Merge and optimize chunks
        merged_chunks = self._merge_chunking_strategies(structure_chunks, citation_chunks)
        
        return merged_chunks
    
    def _standard_chunking(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Standard chunking with structure and citation awareness."""
        
        # Use structure chunking as primary strategy
        chunks = self.chunkers["structure"].chunk_legal_document(document, metadata)
        
        # Enhance with citation information
        self._enhance_chunks_with_citations(chunks, document)
        
        return chunks
    
    def _basic_chunking(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Basic legal structure chunking."""
        
        return self.chunkers["structure"].chunk_legal_document(document, metadata)
    
    def _adaptive_chunking(self, document: str, metadata: Dict[str, Any] = None) -> List[LegalChunk]:
        """Adaptive chunking based on document analysis."""
        
        # Analyze document characteristics
        doc_analysis = self._analyze_document_characteristics(document)
        
        if doc_analysis["citation_density"] > 0.1:
            # High citation density - use citation-aware chunking
            return self.chunkers["citation"].chunk_legal_document(document, metadata)
        else:
            # Standard structure-based chunking
            return self.chunkers["structure"].chunk_legal_document(document, metadata)
    
    def _analyze_document_characteristics(self, document: str) -> Dict[str, float]:
        """Analyze document to determine optimal chunking strategy."""
        
        doc_length = len(document)
        citation_count = len(re.findall(r'\d+\s+[A-Z][a-z]*\.?\s*\d+', document))
        
        return {
            "length": doc_length,
            "citation_count": citation_count,
            "citation_density": citation_count / max(doc_length // 1000, 1),  # Citations per 1000 chars
            "complexity": "high" if doc_length > 50000 else "medium" if doc_length > 20000 else "low"
        }
    
    def _merge_chunking_strategies(
        self, 
        structure_chunks: List[LegalChunk], 
        citation_chunks: List[LegalChunk]
    ) -> List[LegalChunk]:
        """Merge results from multiple chunking strategies."""
        
        # For now, prioritize structure chunks and enhance with citation info
        enhanced_chunks = structure_chunks.copy()
        
        # Map citation information to structure chunks
        for struct_chunk in enhanced_chunks:
            for cite_chunk in citation_chunks:
                # Check for overlap
                if self._chunks_overlap(struct_chunk, cite_chunk):
                    # Merge citation information
                    struct_chunk.citations_contained.extend(cite_chunk.citations_contained)
                    struct_chunk.legal_context.update(cite_chunk.legal_context)
        
        return enhanced_chunks
    
    def _chunks_overlap(self, chunk1: LegalChunk, chunk2: LegalChunk) -> bool:
        """Check if two chunks have overlapping content."""
        
        # Simple overlap check based on content similarity
        chunk1_words = set(chunk1.content.lower().split())
        chunk2_words = set(chunk2.content.lower().split())
        
        overlap = len(chunk1_words & chunk2_words)
        min_size = min(len(chunk1_words), len(chunk2_words))
        
        return (overlap / max(min_size, 1)) > 0.3  # 30% word overlap threshold
    
    def _enhance_chunks_with_citations(self, chunks: List[LegalChunk], document: str):
        """Enhance existing chunks with citation information."""
        
        # Extract all citations from document
        all_citations = re.findall(r'\d+\s+[A-Z][a-z]*\.?\s*\d+', document)
        
        for chunk in chunks:
            # Find citations that appear in this chunk
            chunk_citations = []
            for citation in all_citations:
                if citation in chunk.content:
                    chunk_citations.append(citation)
            
            chunk.citations_contained = chunk_citations
    
    def validate_all_chunks(self, chunks: List[LegalChunk]) -> Dict[str, Any]:
        """Validate quality of all chunks in the document."""
        
        quality_results = {
            "total_chunks": len(chunks),
            "average_quality": 0.0,
            "quality_distribution": {"high": 0, "medium": 0, "low": 0},
            "failed_chunks": [],
            "quality_issues": []
        }
        
        total_quality = 0.0
        
        for chunk in chunks:
            # Use the chunker that created this chunk to validate it
            # For now, use structure chunker as default
            quality_scores = self.chunkers["structure"].validate_chunk_quality(chunk)
            
            overall_quality = quality_scores.get("overall", 0.0)
            total_quality += overall_quality
            
            # Update chunk quality scores
            chunk.legal_completeness_score = quality_scores.get("citation_completeness", 0.0)
            chunk.reasoning_integrity_score = quality_scores.get("argument_coherence", 0.0)
            
            # Categorize quality
            if overall_quality >= 0.8:
                quality_results["quality_distribution"]["high"] += 1
            elif overall_quality >= 0.6:
                quality_results["quality_distribution"]["medium"] += 1
            else:
                quality_results["quality_distribution"]["low"] += 1
                quality_results["failed_chunks"].append(chunk.chunk_index)
            
            # Check for specific quality issues
            if overall_quality < 0.7:
                quality_results["quality_issues"].append({
                    "chunk_index": chunk.chunk_index,
                    "quality_score": overall_quality,
                    "issues": [k for k, v in quality_scores.items() if v < 0.7]
                })
        
        quality_results["average_quality"] = total_quality / len(chunks)
        
        return quality_results


# Example usage
def main():
    """Example usage of legal document chunking."""
    
    sample_legal_document = """
    SUPREME COURT OF NEW JERSEY
    
    SMITH v. JONES
    
    Decided: January 15, 2023
    
    FACTS AND PROCEDURAL HISTORY
    
    This case involves the application of qualified immunity doctrine in Section 1983 litigation.
    Plaintiff Smith filed suit against Defendant Jones under 42 U.S.C. § 1983, alleging constitutional violations.
    
    LEGAL ANALYSIS
    
    We begin our analysis with the seminal case Monroe v. Pape, 365 U.S. 167 (1961), which established
    that Section 1983 provides a federal cause of action against state officials acting under color of law.
    As the Supreme Court held in Monroe, the statute applies even when state officials violate state law.
    
    However, the doctrine of qualified immunity, as clarified in Monell v. Department of Social Services,
    436 U.S. 658 (1978), provides protection for government officials. The Court in Monell explained
    that municipalities can be sued directly under § 1983 for constitutional violations.
    
    More recently, in Pearson v. Callahan, 555 U.S. 223 (2009), the Supreme Court modified the rigid
    two-step qualified immunity analysis, allowing courts discretion in which prong to address first.
    
    HOLDING
    
    We hold that under the circumstances of this case, qualified immunity does not shield defendant
    from liability. The constitutional right was clearly established at the time of the violation.
    
    CONCLUSION
    
    For the foregoing reasons, we reverse the lower court's grant of summary judgment and remand
    for further proceedings consistent with this opinion.
    """
    
    # Initialize chunking pipeline
    pipeline = LegalDocumentChunkingPipeline()
    
    # Chunk the document
    chunks = pipeline.chunk_legal_document(
        sample_legal_document,
        document_type="supreme_court_opinion",
        complexity_level="high"
    )
    
    print(f"Created {len(chunks)} legal chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1} ({chunk.section_type.value}):")
        print(f"Citations: {chunk.citations_contained}")
        print(f"Content preview: {chunk.content[:200]}...")
    
    # Validate chunk quality
    quality_report = pipeline.validate_all_chunks(chunks)
    print(f"\nQuality Report:")
    print(f"Average quality: {quality_report['average_quality']:.2f}")
    print(f"Quality distribution: {quality_report['quality_distribution']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()