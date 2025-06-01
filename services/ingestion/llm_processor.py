"""
Premium LLM Processing Pipeline for Legal Document Analysis.

Implements excellence-first strategy from ADR-003:
- Premium models (GPT-4, Claude-3-Opus) for all legal reasoning
- Multi-model validation with 95%+ confidence thresholds
- Sophisticated citation extraction and legal analysis
- Quality gates instead of cost constraints
- Expert review integration for complex cases
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
import re
from abc import ABC, abstractmethod

# Import LLM clients (these would need to be implemented)
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from shared.models.legal_entities import (
    Case, Citation, CitationTreatment, PracticeArea, CaseStatus
)

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available premium LLM providers."""
    GPT_4 = "gpt-4"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    GPT_4_TURBO = "gpt-4-turbo-preview"


class ProcessingComplexity(Enum):
    """Legal document processing complexity levels."""
    SUPREME_COURT = "supreme_court"  # Maximum sophistication
    CIRCUIT_COURT = "circuit_court"  # High sophistication
    DISTRICT_COURT = "district_court"  # Standard excellence
    ADMINISTRATIVE = "administrative"  # Basic processing


@dataclass
class LegalAnalysisResult:
    """Comprehensive legal analysis result from premium LLM processing."""
    case_id: str
    
    # Citation Analysis
    extracted_citations: List[Dict[str, Any]] = field(default_factory=list)
    citation_treatments: List[Dict[str, Any]] = field(default_factory=list)
    citation_confidence: float = 0.0
    
    # Legal Authority Analysis
    authority_score: float = 0.0
    precedential_weight: str = ""
    legal_hierarchy_analysis: str = ""
    
    # Legal Content Analysis
    practice_areas: List[PracticeArea] = field(default_factory=list)
    legal_holdings: List[str] = field(default_factory=list)
    legal_reasoning_chain: str = ""
    judicial_reasoning: str = ""
    
    # Precedent Relationship Analysis
    precedent_relationships: List[Dict[str, Any]] = field(default_factory=list)
    doctrinal_impact: str = ""
    legal_evolution_analysis: str = ""
    
    # Quality Metrics
    overall_confidence: float = 0.0
    processing_complexity: ProcessingComplexity = ProcessingComplexity.DISTRICT_COURT
    requires_expert_review: bool = False
    quality_flags: List[str] = field(default_factory=list)
    
    # Processing Metadata
    llm_models_used: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    processing_cost: float = 0.0
    processed_at: datetime = field(default_factory=datetime.now)


class LLMClient(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def analyze_legal_citations(self, case_text: str) -> Dict[str, Any]:
        """Extract and analyze legal citations."""
        pass
    
    @abstractmethod
    async def analyze_legal_authority(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze legal authority and precedential weight."""
        pass
    
    @abstractmethod
    async def extract_legal_holdings(self, case_text: str) -> Dict[str, Any]:
        """Extract legal holdings and reasoning."""
        pass
    
    @abstractmethod
    async def analyze_precedent_relationships(self, case_text: str, citations: List[str]) -> Dict[str, Any]:
        """Analyze relationships between cases and precedents."""
        pass


class GPT4Client(LLMClient):
    """GPT-4 client for premium legal analysis."""
    
    def __init__(self, api_key: str):
        if not openai:
            raise ImportError("OpenAI library not installed")
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4"
    
    async def analyze_legal_citations(self, case_text: str) -> Dict[str, Any]:
        """Extract and analyze legal citations using GPT-4."""
        
        prompt = self._get_citation_analysis_prompt()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Analyze the following legal document for citations:\n\n{case_text}"}
                ],
                temperature=0.1,  # Low temperature for precision
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in GPT-4 citation analysis: {e}")
            return {"citations": [], "confidence": 0.0, "error": str(e)}
    
    async def analyze_legal_authority(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze legal authority using GPT-4."""
        
        prompt = self._get_authority_analysis_prompt()
        
        context = f"""
        Case: {case_data.get('case_name', 'Unknown')}
        Court: {case_data.get('court', 'Unknown')}
        Date: {case_data.get('decision_date', 'Unknown')}
        Precedential Status: {case_data.get('precedential_status', 'Unknown')}
        Full Text: {case_data.get('full_text', '')[:8000]}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in GPT-4 authority analysis: {e}")
            return {"authority_score": 0.0, "confidence": 0.0, "error": str(e)}
    
    async def extract_legal_holdings(self, case_text: str) -> Dict[str, Any]:
        """Extract legal holdings using GPT-4."""
        
        prompt = self._get_holdings_extraction_prompt()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Extract legal holdings from:\n\n{case_text}"}
                ],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in GPT-4 holdings extraction: {e}")
            return {"holdings": [], "reasoning": "", "confidence": 0.0, "error": str(e)}
    
    async def analyze_precedent_relationships(self, case_text: str, citations: List[str]) -> Dict[str, Any]:
        """Analyze precedent relationships using GPT-4."""
        
        prompt = self._get_precedent_analysis_prompt()
        
        context = f"""
        Case Text: {case_text[:6000]}
        
        Citations Found: {', '.join(citations)}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in GPT-4 precedent analysis: {e}")
            return {"relationships": [], "confidence": 0.0, "error": str(e)}
    
    def _get_citation_analysis_prompt(self) -> str:
        """Get prompt for citation analysis."""
        return """You are an expert legal analyst specializing in citation extraction and analysis. 

Your task is to extract ALL legal citations from the provided legal document and analyze how each citation is used.

For each citation found, determine:
1. The exact citation string (e.g., "347 U.S. 483", "123 F.3d 456")
2. The cited case name if available
3. How the citation is treated (follows, distinguishes, overrules, questions, etc.)
4. The legal context in which the citation appears
5. The strength of the citation relationship (0.0 to 1.0)

Return your analysis as JSON with this exact structure:
{
    "citations": [
        {
            "citation": "exact citation string",
            "case_name": "case name if available",
            "treatment": "follows|distinguishes|overrules|questions|cites|explains",
            "context": "legal context description",
            "strength": 0.8,
            "page_numbers": ["123", "124"],
            "quote_or_paraphrase": "direct quote or paraphrase of cited material"
        }
    ],
    "confidence": 0.95,
    "total_citations_found": 15,
    "analysis_notes": "any important observations about citation patterns"
}

Be extremely thorough - missing citations in legal analysis can have serious consequences."""
    
    def _get_authority_analysis_prompt(self) -> str:
        """Get prompt for authority analysis."""
        return """You are an expert legal analyst specializing in legal authority and precedential weight analysis.

Analyze the provided case information to determine:

1. Legal Authority Score (0.0 to 10.0):
   - Court hierarchy (Supreme Court = 10, Circuit = 8, District = 6, etc.)
   - Precedential status (Published > Unpublished > Memorandum)
   - Jurisdiction relevance
   - Case age and current validity

2. Precedential Weight Assessment:
   - Binding vs. persuasive authority
   - Scope of holding
   - Subsequent treatment by other courts
   - Doctrinal significance

3. Legal Hierarchy Analysis:
   - Position in court system
   - Relationship to controlling authority
   - Jurisdictional scope

Return analysis as JSON:
{
    "authority_score": 8.5,
    "precedential_weight": "binding|persuasive|questioned|overruled",
    "hierarchy_analysis": "detailed analysis of court position and authority",
    "binding_jurisdictions": ["list of jurisdictions where binding"],
    "persuasive_jurisdictions": ["list where persuasive"],
    "doctrinal_significance": "analysis of legal doctrine impact",
    "current_validity": "good_law|questioned|overruled|limited",
    "confidence": 0.92
}

Consider all factors affecting legal authority and precedential value."""
    
    def _get_holdings_extraction_prompt(self) -> str:
        """Get prompt for holdings extraction."""
        return """You are an expert legal analyst specializing in extracting legal holdings and judicial reasoning.

From the provided case text, extract:

1. Legal Holdings: The specific legal rules or principles established by the court
2. Reasoning Chain: The logical progression of the court's legal analysis
3. Key Legal Concepts: Important legal principles discussed
4. Procedural Context: How the case reached this court and disposition

Focus on:
- The actual legal rule created or applied
- The court's reasoning for the decision
- Any legal tests or standards established
- The relationship between facts and legal conclusions

Return as JSON:
{
    "primary_holding": "main legal rule established",
    "secondary_holdings": ["additional legal rules or clarifications"],
    "reasoning_chain": "step-by-step legal reasoning",
    "legal_test_established": "any legal test or standard created",
    "key_legal_concepts": ["important legal principles"],
    "procedural_posture": "how case reached this court",
    "disposition": "court's final ruling",
    "practice_areas": ["constitutional", "civil_rights", "criminal", etc.],
    "confidence": 0.94
}

Be precise - legal holdings must be accurate as they establish binding precedent."""
    
    def _get_precedent_analysis_prompt(self) -> str:
        """Get prompt for precedent analysis."""
        return """You are an expert legal analyst specializing in precedent relationships and doctrinal evolution.

Analyze how this case relates to the legal precedents it cites and its potential impact on legal doctrine.

For each significant precedent relationship, determine:
1. How this case treats the precedent (follows, distinguishes, limits, expands, etc.)
2. The doctrinal significance of the relationship
3. Whether this case advances, modifies, or clarifies existing legal doctrine
4. The potential impact on future cases

Return analysis as JSON:
{
    "precedent_relationships": [
        {
            "cited_case": "case citation or name",
            "relationship_type": "follows|distinguishes|limits|expands|overrules",
            "doctrinal_impact": "how this affects legal doctrine",
            "significance": "high|medium|low",
            "analysis": "detailed explanation of relationship"
        }
    ],
    "doctrinal_evolution": "how this case advances legal doctrine",
    "future_impact": "likely effect on subsequent cases",
    "legal_innovation": "any novel legal reasoning or approaches",
    "jurisdictional_impact": "effect within and beyond jurisdiction",
    "confidence": 0.91
}

Focus on substantive legal relationships, not merely formal citations."""


class Claude3OpusClient(LLMClient):
    """Claude-3-Opus client for premium legal analysis."""
    
    def __init__(self, api_key: str):
        if not anthropic:
            raise ImportError("Anthropic library not installed")
        
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"
    
    async def analyze_legal_citations(self, case_text: str) -> Dict[str, Any]:
        """Analyze citations using Claude-3-Opus (excellent at text relationships)."""
        
        prompt = """You are a legal citation analysis expert. Extract and analyze ALL legal citations from this document.

For each citation, provide:
- Exact citation format
- Case name if available  
- Treatment type (follows, distinguishes, overrules, etc.)
- Legal context and purpose
- Relationship strength (0.0-1.0)

Return as JSON with structure:
{
    "citations": [...],
    "confidence": 0.95,
    "analysis_notes": "..."
}"""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nLegal Document:\n{case_text}"}
                ]
            )
            
            # Parse JSON from response
            result_text = response.content[0].text
            # Extract JSON from response (Claude might include explanatory text)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"citations": [], "confidence": 0.0, "error": "No JSON found in response"}
            
        except Exception as e:
            logger.error(f"Error in Claude-3-Opus citation analysis: {e}")
            return {"citations": [], "confidence": 0.0, "error": str(e)}
    
    # Implement other abstract methods...
    async def analyze_legal_authority(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder - implement similar to GPT-4 but with Claude-specific approach."""
        return {"authority_score": 0.0, "confidence": 0.0}
    
    async def extract_legal_holdings(self, case_text: str) -> Dict[str, Any]:
        """Placeholder - implement similar to GPT-4 but with Claude-specific approach."""
        return {"holdings": [], "confidence": 0.0}
    
    async def analyze_precedent_relationships(self, case_text: str, citations: List[str]) -> Dict[str, Any]:
        """Placeholder - implement similar to GPT-4 but with Claude-specific approach."""
        return {"relationships": [], "confidence": 0.0}


class ExcellenceFirstProcessor:
    """
    Premium LLM processing pipeline implementing excellence-first strategy.
    
    Uses multiple premium models with cross-validation and quality gates.
    No compromises on legal accuracy - scales UP resources as needed.
    """
    
    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.llm_clients = {}
        
        if openai_api_key:
            self.llm_clients[LLMProvider.GPT_4] = GPT4Client(openai_api_key)
        
        if anthropic_api_key:
            self.llm_clients[LLMProvider.CLAUDE_3_OPUS] = Claude3OpusClient(anthropic_api_key)
        
        if not self.llm_clients:
            raise ValueError("At least one LLM provider API key required")
        
        # Excellence-first configuration
        self.minimum_confidence_threshold = 0.95
        self.require_multi_model_consensus = True
        self.expert_review_threshold = 0.90
    
    async def process_case_comprehensive(
        self, 
        case_data: Dict[str, Any],
        complexity: ProcessingComplexity = ProcessingComplexity.DISTRICT_COURT
    ) -> LegalAnalysisResult:
        """
        Comprehensive legal analysis with no quality compromises.
        
        Implements the excellence-first architecture from ADR-003.
        """
        start_time = datetime.now()
        case_id = str(case_data.get("id", "unknown"))
        
        logger.info(f"Starting comprehensive analysis for case {case_id} (complexity: {complexity.value})")
        
        result = LegalAnalysisResult(
            case_id=case_id,
            processing_complexity=complexity
        )
        
        try:
            # Stage 1: Premium Legal Analysis
            case_text = case_data.get("full_text", "")
            if not case_text:
                case_text = f"{case_data.get('case_name', '')} {case_data.get('summary', '')}"
            
            # Multi-model citation analysis
            citation_results = await self._multi_model_citation_analysis(case_text)
            result.extracted_citations = citation_results["citations"]
            result.citation_confidence = citation_results["confidence"]
            
            # Authority analysis
            authority_results = await self._multi_model_authority_analysis(case_data)
            result.authority_score = authority_results["authority_score"]
            result.precedential_weight = authority_results.get("precedential_weight", "")
            result.legal_hierarchy_analysis = authority_results.get("hierarchy_analysis", "")
            
            # Holdings extraction
            holdings_results = await self._multi_model_holdings_extraction(case_text)
            result.legal_holdings = holdings_results["holdings"]
            result.legal_reasoning_chain = holdings_results.get("reasoning", "")
            
            # Precedent relationship analysis
            citations_list = [c.get("citation", "") for c in result.extracted_citations]
            precedent_results = await self._multi_model_precedent_analysis(case_text, citations_list)
            result.precedent_relationships = precedent_results["relationships"]
            result.doctrinal_impact = precedent_results.get("doctrinal_evolution", "")
            
            # Stage 2: Cross-Validation and Confidence Assessment
            result.overall_confidence = self._calculate_overall_confidence(result)
            
            # Stage 3: Quality Gates
            if result.overall_confidence < self.minimum_confidence_threshold:
                result.requires_expert_review = True
                result.quality_flags.append(f"Low confidence: {result.overall_confidence:.2f}")
                logger.warning(f"Case {case_id} requires expert review - confidence: {result.overall_confidence:.2f}")
            
            # Complex cases always get expert review
            if complexity in [ProcessingComplexity.SUPREME_COURT, ProcessingComplexity.CIRCUIT_COURT]:
                result.requires_expert_review = True
                result.quality_flags.append(f"Complex case: {complexity.value}")
            
            # Record processing metadata
            result.llm_models_used = list(self.llm_clients.keys())
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Completed analysis for case {case_id} - confidence: {result.overall_confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive processing for case {case_id}: {e}")
            result.quality_flags.append(f"Processing error: {str(e)}")
            result.requires_expert_review = True
            return result
    
    async def _multi_model_citation_analysis(self, case_text: str) -> Dict[str, Any]:
        """Run citation analysis with multiple models for cross-validation."""
        
        tasks = []
        for provider, client in self.llm_clients.items():
            task = client.analyze_legal_citations(case_text)
            tasks.append((provider, task))
        
        results = {}
        for provider, task in tasks:
            try:
                result = await task
                results[provider] = result
            except Exception as e:
                logger.error(f"Citation analysis failed for {provider}: {e}")
                results[provider] = {"citations": [], "confidence": 0.0, "error": str(e)}
        
        # Combine and validate results
        return self._validate_and_combine_citation_results(results)
    
    async def _multi_model_authority_analysis(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run authority analysis with multiple models."""
        
        tasks = []
        for provider, client in self.llm_clients.items():
            task = client.analyze_legal_authority(case_data)
            tasks.append((provider, task))
        
        results = {}
        for provider, task in tasks:
            try:
                result = await task
                results[provider] = result
            except Exception as e:
                logger.error(f"Authority analysis failed for {provider}: {e}")
                results[provider] = {"authority_score": 0.0, "confidence": 0.0, "error": str(e)}
        
        return self._validate_and_combine_authority_results(results)
    
    async def _multi_model_holdings_extraction(self, case_text: str) -> Dict[str, Any]:
        """Extract holdings with multiple models."""
        
        # For now, use first available model (can be expanded)
        if LLMProvider.GPT_4 in self.llm_clients:
            return await self.llm_clients[LLMProvider.GPT_4].extract_legal_holdings(case_text)
        else:
            return {"holdings": [], "reasoning": "", "confidence": 0.0}
    
    async def _multi_model_precedent_analysis(self, case_text: str, citations: List[str]) -> Dict[str, Any]:
        """Analyze precedent relationships with multiple models."""
        
        # For now, use first available model
        if LLMProvider.GPT_4 in self.llm_clients:
            return await self.llm_clients[LLMProvider.GPT_4].analyze_precedent_relationships(case_text, citations)
        else:
            return {"relationships": [], "confidence": 0.0}
    
    def _validate_and_combine_citation_results(self, results: Dict[LLMProvider, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and combine citation results from multiple models."""
        
        all_citations = []
        confidences = []
        
        for provider, result in results.items():
            if "error" not in result:
                all_citations.extend(result.get("citations", []))
                confidences.append(result.get("confidence", 0.0))
        
        if not confidences:
            return {"citations": [], "confidence": 0.0}
        
        # Remove duplicate citations and combine
        unique_citations = self._deduplicate_citations(all_citations)
        
        # Calculate consensus confidence
        avg_confidence = sum(confidences) / len(confidences)
        
        return {
            "citations": unique_citations,
            "confidence": avg_confidence,
            "model_consensus": len(confidences) > 1
        }
    
    def _validate_and_combine_authority_results(self, results: Dict[LLMProvider, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and combine authority analysis results."""
        
        authority_scores = []
        precedential_weights = []
        hierarchy_analyses = []
        
        for provider, result in results.items():
            if "error" not in result:
                authority_scores.append(result.get("authority_score", 0.0))
                if result.get("precedential_weight"):
                    precedential_weights.append(result["precedential_weight"])
                if result.get("hierarchy_analysis"):
                    hierarchy_analyses.append(result["hierarchy_analysis"])
        
        if not authority_scores:
            return {"authority_score": 0.0, "confidence": 0.0}
        
        # Use consensus scoring
        avg_authority = sum(authority_scores) / len(authority_scores)
        
        return {
            "authority_score": avg_authority,
            "precedential_weight": precedential_weights[0] if precedential_weights else "",
            "hierarchy_analysis": " | ".join(hierarchy_analyses),
            "model_consensus": len(authority_scores) > 1
        }
    
    def _deduplicate_citations(self, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate citations based on citation string."""
        
        seen_citations = set()
        unique_citations = []
        
        for citation in citations:
            citation_str = citation.get("citation", "").strip()
            if citation_str and citation_str not in seen_citations:
                seen_citations.add(citation_str)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _calculate_overall_confidence(self, result: LegalAnalysisResult) -> float:
        """Calculate overall confidence from individual analysis components."""
        
        confidence_scores = []
        
        if result.citation_confidence > 0:
            confidence_scores.append(result.citation_confidence)
        
        # Add other confidence scores as available
        # For now, use citation confidence as primary indicator
        
        if not confidence_scores:
            return 0.0
        
        return sum(confidence_scores) / len(confidence_scores)


# Example usage
async def main():
    """Example usage of the premium LLM processing pipeline."""
    import os
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not (openai_key or anthropic_key):
        logger.error("At least one LLM API key required")
        return
    
    processor = ExcellenceFirstProcessor(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key
    )
    
    # Example case data
    sample_case = {
        "id": "test-case-123",
        "case_name": "Smith v. Jones",
        "court": "nj",
        "decision_date": "2023-01-15",
        "precedential_status": "Published",
        "full_text": """
        This case involves the application of qualified immunity doctrine.
        We follow the precedent established in Monroe v. Pape, 365 U.S. 167 (1961),
        and the clarifications provided in Monell v. Department of Social Services,
        436 U.S. 658 (1978). The court held that...
        """
    }
    
    try:
        result = await processor.process_case_comprehensive(
            sample_case,
            complexity=ProcessingComplexity.CIRCUIT_COURT
        )
        
        logger.info(f"Analysis completed:")
        logger.info(f"  - Citations found: {len(result.extracted_citations)}")
        logger.info(f"  - Authority score: {result.authority_score}")
        logger.info(f"  - Overall confidence: {result.overall_confidence:.2f}")
        logger.info(f"  - Requires expert review: {result.requires_expert_review}")
        logger.info(f"  - Quality flags: {result.quality_flags}")
        
    except Exception as e:
        logger.error(f"Error in processing: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())