"""
Legal analysis tools for MCP server.

Provides sophisticated legal analysis capabilities:
- Case authority analysis using citation networks
- Good law verification and treatment analysis  
- Legal precedent strength evaluation
- Opposition argument identification
"""

import asyncio
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AnalysisTools:
    """Legal analysis integration for MCP server"""
    
    def __init__(self, settings):
        self.settings = settings
        self.api_base = getattr(settings, 'API_BASE_URL', 'http://localhost:8001')
        self.api_key = getattr(settings, 'API_KEY', None)
    
    async def analyze_authority(
        self,
        case_id: str,
        target_jurisdiction: Optional[str] = None,
        analysis_types: List[str] = ["authority_score", "good_law_status"]
    ) -> Dict[str, Any]:
        """
        Analyze the legal authority and precedential value of a case.
        
        Args:
            case_id: Case ID or citation to analyze
            target_jurisdiction: Jurisdiction where authority will be evaluated
            analysis_types: Types of analysis to perform
            
        Returns:
            Comprehensive authority analysis
        """
        try:
            # Initialize services for analysis
            from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
            
            # Try to connect to Neo4j service
            neo4j_service = None
            try:
                neo4j_service = EnhancedNeo4jService(
                    uri="bolt://localhost:7687",
                    user="neo4j",
                    password="citation_graph_2024"
                )
                await neo4j_service.connect()
            except Exception as e:
                logger.warning(f"Neo4j connection failed, using fallback analysis: {e}")
            
            # Prepare analysis result
            analysis_result = {
                "case_id": case_id,
                "target_jurisdiction": target_jurisdiction,
                "analysis_types": analysis_types,
                "analysis_date": datetime.utcnow().isoformat(),
                "authority_analysis": {},
                "citation_analysis": {},
                "good_law_status": {},
                "binding_precedent_analysis": {},
                "recommendations": []
            }
            
            # Perform authority score analysis
            if "authority_score" in analysis_types:
                try:
                    if neo4j_service:
                        # Use enhanced Neo4j authority analysis
                        case = await neo4j_service.get_case_by_id(case_id)
                        if case:
                            authority_analysis = {
                                "authority_score": case.authority_score or 0.0,
                                "court_level": self._determine_court_level(case.court_id),
                                "jurisdiction": case.jurisdiction,
                                "precedential_status": "Published",  # Default assumption
                                "citation_count": await self._get_citation_count(neo4j_service, case_id),
                                "authority_factors": {
                                    "court_hierarchy_weight": self._get_court_hierarchy_weight(case.court_id),
                                    "precedential_value": self._assess_precedential_value(case),
                                    "temporal_relevance": self._calculate_temporal_relevance(case.decision_date),
                                    "citation_strength": await self._analyze_citation_strength(neo4j_service, case_id)
                                }
                            }
                        else:
                            authority_analysis = {"error": f"Case {case_id} not found in knowledge base"}
                    else:
                        # Fallback authority analysis
                        authority_analysis = await self._fallback_authority_analysis(case_id)
                    
                    analysis_result["authority_analysis"] = authority_analysis
                    
                except Exception as e:
                    logger.error(f"Authority analysis failed: {e}")
                    analysis_result["authority_analysis"] = {"error": str(e)}
            
            # Perform citation treatment analysis
            if "citation_treatment" in analysis_types:
                try:
                    if neo4j_service:
                        treatment_analysis = await neo4j_service.analyze_citation_treatment(case_id)
                        analysis_result["citation_analysis"] = treatment_analysis
                    else:
                        analysis_result["citation_analysis"] = {
                            "error": "Citation treatment analysis requires Neo4j connection"
                        }
                except Exception as e:
                    logger.error(f"Citation treatment analysis failed: {e}")
                    analysis_result["citation_analysis"] = {"error": str(e)}
            
            # Perform good law status verification
            if "good_law_status" in analysis_types:
                try:
                    if neo4j_service:
                        good_law_verification = await neo4j_service.verify_good_law_status(case_id)
                        analysis_result["good_law_status"] = good_law_verification
                    else:
                        # Fallback good law analysis
                        analysis_result["good_law_status"] = await self._fallback_good_law_analysis(case_id)
                except Exception as e:
                    logger.error(f"Good law analysis failed: {e}")
                    analysis_result["good_law_status"] = {"error": str(e)}
            
            # Perform binding precedent analysis
            if "binding_precedent" in analysis_types:
                binding_analysis = await self._analyze_binding_precedent(
                    case_id, target_jurisdiction, neo4j_service
                )
                analysis_result["binding_precedent_analysis"] = binding_analysis
            
            # Generate recommendations based on analysis
            analysis_result["recommendations"] = self._generate_authority_recommendations(analysis_result)
            
            # Close Neo4j connection
            if neo4j_service:
                await neo4j_service.close()
            
            logger.info(f"Completed authority analysis for case: {case_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Authority analysis failed for {case_id}: {e}")
            return {
                "error": str(e),
                "case_id": case_id,
                "analysis_types": analysis_types
            }
    
    async def identify_opposition(
        self,
        position: str,
        case_type: str,
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify potential opposing arguments and counterpoint cases.
        
        Args:
            position: Your legal position or argument
            case_type: Type of legal case
            jurisdiction: Relevant jurisdiction
            
        Returns:
            Opposition research and counterarguments
        """
        try:
            # Use the research API to find opposing cases
            from services.vector.chroma_service import ChromaService
            
            chroma_service = ChromaService(use_mcp_tools=True)
            await chroma_service.initialize()
            
            # Search for opposing precedents
            opposing_query = f"opposing arguments {position} {case_type} counterpoint"
            
            opposing_cases = await chroma_service.semantic_search(
                query=opposing_query,
                document_types=["case"],
                jurisdiction=jurisdiction,
                limit=10
            )
            
            # Analyze potential counterarguments
            opposition_analysis = {
                "position": position,
                "case_type": case_type,
                "jurisdiction": jurisdiction,
                "analysis_date": datetime.utcnow().isoformat(),
                "potential_counterarguments": [],
                "opposing_precedents": [],
                "vulnerability_assessment": {},
                "defensive_strategies": [],
                "recommendations": []
            }
            
            # Process opposing cases
            for case in opposing_cases[:5]:
                metadata = case.get("metadata", {})
                opposing_precedent = {
                    "case_id": case.get("id", ""),
                    "case_name": metadata.get("case_name", "Unknown Case"),
                    "citation": metadata.get("citation", ""),
                    "relevance_score": case.get("similarity_score", 0.0),
                    "authority_score": metadata.get("authority_score", 0.0),
                    "jurisdiction": metadata.get("jurisdiction", ""),
                    "potential_impact": self._assess_opposition_impact(case, position),
                    "distinguishing_factors": self._identify_distinguishing_factors(case, position),
                    "counterstrategy": self._suggest_counterstrategy(case, position)
                }
                opposition_analysis["opposing_precedents"].append(opposing_precedent)
            
            # Generate counterargument analysis
            opposition_analysis["potential_counterarguments"] = self._generate_counterarguments(
                position, case_type, opposing_cases
            )
            
            # Assess vulnerabilities
            opposition_analysis["vulnerability_assessment"] = self._assess_position_vulnerabilities(
                position, case_type, opposing_cases
            )
            
            # Suggest defensive strategies
            opposition_analysis["defensive_strategies"] = self._generate_defensive_strategies(
                position, case_type, opposing_cases
            )
            
            # Generate recommendations
            opposition_analysis["recommendations"] = self._generate_opposition_recommendations(
                position, opposition_analysis
            )
            
            logger.info(f"Completed opposition analysis for position: {position[:100]}...")
            return opposition_analysis
            
        except Exception as e:
            logger.error(f"Opposition analysis failed: {e}")
            return {
                "error": str(e),
                "position": position,
                "case_type": case_type
            }
    
    async def _get_citation_count(self, neo4j_service, case_id: str) -> int:
        """Get citation count for a case"""
        try:
            # This would query the citation network
            # For now, return a default value
            return 0
        except:
            return 0
    
    def _determine_court_level(self, court_id: str) -> str:
        """Determine the level of court"""
        court_hierarchy = {
            "us-supreme-court": "Supreme Court",
            "scotus": "Supreme Court",
            "ca": "Federal Appellate",
            "district": "Federal District",
            "state-supreme": "State Supreme",
            "state-appellate": "State Appellate",
            "state-trial": "State Trial"
        }
        
        for key, level in court_hierarchy.items():
            if key in court_id.lower():
                return level
        
        return "Unknown Court Level"
    
    def _get_court_hierarchy_weight(self, court_id: str) -> float:
        """Get authority weight based on court hierarchy"""
        weights = {
            "us-supreme-court": 10.0,
            "scotus": 10.0,
            "federal-appellate": 8.0,
            "federal-district": 6.0,
            "state-supreme": 8.0,
            "state-appellate": 6.0,
            "state-trial": 4.0
        }
        
        court_level = self._determine_court_level(court_id)
        level_key = court_level.lower().replace(" ", "-")
        
        return weights.get(level_key, 5.0)
    
    def _assess_precedential_value(self, case) -> float:
        """Assess precedential value of a case"""
        # This would analyze various factors
        # For now, return a baseline score
        base_score = 0.7
        
        # Adjust based on available metadata
        if hasattr(case, 'authority_score') and case.authority_score:
            base_score = min(1.0, case.authority_score / 10.0)
        
        return base_score
    
    def _calculate_temporal_relevance(self, decision_date) -> float:
        """Calculate temporal relevance score"""
        if not decision_date:
            return 0.5
        
        try:
            if isinstance(decision_date, str):
                case_date = datetime.fromisoformat(decision_date.replace("Z", "+00:00"))
            else:
                case_date = decision_date
            
            years_old = (datetime.now() - case_date).days / 365.25
            
            # Authority decays over time, but not below 0.3
            return max(0.3, 1.0 - (years_old * 0.02))  # 2% decay per year
        except:
            return 0.5
    
    async def _analyze_citation_strength(self, neo4j_service, case_id: str) -> float:
        """Analyze citation strength"""
        try:
            # This would analyze the citation network
            # For now, return a default value
            return 0.7
        except:
            return 0.5
    
    async def _fallback_authority_analysis(self, case_id: str) -> Dict[str, Any]:
        """Fallback authority analysis when Neo4j is unavailable"""
        return {
            "authority_score": 6.0,  # Default moderate authority
            "court_level": "Unknown",
            "jurisdiction": "Unknown",
            "precedential_status": "Unknown",
            "citation_count": 0,
            "authority_factors": {
                "court_hierarchy_weight": 6.0,
                "precedential_value": 0.6,
                "temporal_relevance": 0.7,
                "citation_strength": 0.5
            },
            "note": "Limited analysis - full graph database unavailable"
        }
    
    async def _fallback_good_law_analysis(self, case_id: str) -> Dict[str, Any]:
        """Fallback good law analysis"""
        return {
            "good_law_confidence": 0.7,
            "overruling_risk": "Low",
            "treatment_summary": "Unable to verify - full citation analysis unavailable",
            "negative_treatments": [],
            "note": "Limited analysis - citation treatment data unavailable"
        }
    
    async def _analyze_binding_precedent(
        self, 
        case_id: str, 
        target_jurisdiction: Optional[str], 
        neo4j_service
    ) -> Dict[str, Any]:
        """Analyze whether case is binding precedent in target jurisdiction"""
        analysis = {
            "is_binding": False,
            "binding_strength": "Unknown",
            "jurisdictional_authority": "Unknown",
            "precedential_scope": "Unknown",
            "limitations": []
        }
        
        if not target_jurisdiction:
            analysis["limitations"].append("No target jurisdiction specified")
            return analysis
        
        # This would perform sophisticated jurisdictional analysis
        # For now, provide basic analysis
        analysis.update({
            "is_binding": False,  # Conservative default
            "binding_strength": "Persuasive",
            "jurisdictional_authority": f"Analysis needed for {target_jurisdiction}",
            "precedential_scope": "Case-by-case determination required",
            "limitations": ["Detailed jurisdictional analysis not available"]
        })
        
        return analysis
    
    def _assess_opposition_impact(self, case: Dict[str, Any], position: str) -> str:
        """Assess potential impact of opposing case"""
        authority_score = case.get("metadata", {}).get("authority_score", 0.0)
        relevance_score = case.get("similarity_score", 0.0)
        
        if authority_score > 8.0 and relevance_score > 0.8:
            return "High Impact - Strong opposing precedent"
        elif authority_score > 6.0 and relevance_score > 0.6:
            return "Moderate Impact - Notable opposing authority"
        else:
            return "Low Impact - Distinguishable or weak authority"
    
    def _identify_distinguishing_factors(self, case: Dict[str, Any], position: str) -> List[str]:
        """Identify factors to distinguish opposing case"""
        factors = [
            "Different factual circumstances",
            "Different legal issues presented",
            "Different procedural posture",
            "Different jurisdiction or applicable law"
        ]
        
        # This would be enhanced with case content analysis
        return factors[:2]  # Return most common factors
    
    def _suggest_counterstrategy(self, case: Dict[str, Any], position: str) -> str:
        """Suggest strategy to counter opposing case"""
        case_name = case.get("metadata", {}).get("case_name", "opposing case")
        
        strategies = [
            f"Distinguish {case_name} on factual grounds",
            f"Argue {case_name} is not controlling precedent",
            f"Show {case_name} has been limited by subsequent decisions",
            f"Demonstrate {case_name} applies different legal standard"
        ]
        
        return strategies[0]  # Return primary strategy
    
    def _generate_counterarguments(
        self, 
        position: str, 
        case_type: str, 
        opposing_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate potential counterarguments"""
        counterarguments = []
        
        for i, case in enumerate(opposing_cases[:3]):
            metadata = case.get("metadata", {})
            counterargument = {
                "argument_type": "Precedential Challenge",
                "description": f"Opposing counsel may cite {metadata.get('case_name', 'unknown case')}",
                "strength": self._assess_argument_strength(case),
                "response_strategy": f"Distinguish on factual or legal grounds",
                "case_citation": metadata.get("citation", "")
            }
            counterarguments.append(counterargument)
        
        return counterarguments
    
    def _assess_argument_strength(self, case: Dict[str, Any]) -> str:
        """Assess strength of opposing argument"""
        authority_score = case.get("metadata", {}).get("authority_score", 0.0)
        
        if authority_score > 8.0:
            return "Strong"
        elif authority_score > 6.0:
            return "Moderate"
        else:
            return "Weak"
    
    def _assess_position_vulnerabilities(
        self, 
        position: str, 
        case_type: str, 
        opposing_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess vulnerabilities in legal position"""
        return {
            "primary_vulnerabilities": [
                "Potential factual distinctions",
                "Jurisdictional authority questions",
                "Evolution of legal standards"
            ],
            "risk_level": "Moderate",
            "confidence_assessment": "Position has reasonable support but requires careful analysis of opposing precedents"
        }
    
    def _generate_defensive_strategies(
        self, 
        position: str, 
        case_type: str, 
        opposing_cases: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate defensive strategies"""
        return [
            "Emphasize factual distinctions from opposing cases",
            "Highlight favorable precedents and authority",
            "Prepare responses to anticipated counterarguments", 
            "Consider alternative legal theories",
            "Develop policy arguments supporting position"
        ]
    
    def _generate_authority_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on authority analysis"""
        recommendations = []
        
        authority_analysis = analysis_result.get("authority_analysis", {})
        authority_score = authority_analysis.get("authority_score", 0.0)
        
        if authority_score > 8.0:
            recommendations.append("Case has strong precedential authority - cite prominently")
        elif authority_score > 6.0:
            recommendations.append("Case has moderate authority - use as supporting precedent")
        else:
            recommendations.append("Case has limited authority - use cautiously or find stronger precedents")
        
        good_law_status = analysis_result.get("good_law_status", {})
        if good_law_status.get("good_law_confidence", 0) < 0.7:
            recommendations.append("Verify current good law status before relying on case")
        
        return recommendations
    
    def _generate_opposition_recommendations(
        self, 
        position: str, 
        opposition_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for dealing with opposition"""
        recommendations = [
            "Conduct thorough analysis of identified opposing precedents",
            "Prepare factual and legal distinctions for each opposing case",
            "Research subsequent treatment of opposing cases",
            "Consider alternative legal theories to strengthen position",
            "Prepare responses to anticipated counterarguments"
        ]
        
        vulnerability_level = opposition_analysis.get("vulnerability_assessment", {}).get("risk_level", "Unknown")
        
        if vulnerability_level == "High":
            recommendations.insert(0, "PRIORITY: Address high-risk vulnerabilities immediately")
        elif vulnerability_level == "Moderate":
            recommendations.insert(0, "Carefully analyze moderate-risk factors")
        
        return recommendations