"""
Enhanced Neo4j service with sophisticated legal research capabilities.

This service implements the enhanced schema design with:
- Advanced citation treatment analysis
- Legal authority calculations with multi-factor scoring
- Good law verification and precedent discovery
- Doctrine evolution tracking
- Performance-optimized legal research queries
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from neo4j import AsyncGraphDatabase, Record
import logging

from shared.models.legal_entities import Case, Court, Judge, Citation, LegalConcept, Statute
from shared.database.enhanced_neo4j_schema import ENHANCED_LEGAL_QUERIES, EnhancedNeo4jSchemaManager

logger = logging.getLogger(__name__)


class EnhancedNeo4jService:
    """Enhanced Neo4j service for sophisticated legal research operations."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.connected = False
        self.schema_manager = EnhancedNeo4jSchemaManager(uri, user, password)
    
    async def connect(self):
        """Establish connection and initialize enhanced schema."""
        try:
            await self.driver.verify_connectivity()
            self.connected = True
            logger.info("✅ Connected to Neo4j database")
            
            # Initialize enhanced schema if needed
            await self._initialize_enhanced_schema()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    async def _initialize_enhanced_schema(self):
        """Initialize enhanced legal schema if not already present."""
        async with self.driver.session() as session:
            # Check if enhanced schema exists
            result = await session.run(
                "MATCH (c:Case) WHERE c.good_law_status IS NOT NULL RETURN count(c) as enhanced_cases"
            )
            record = await result.single()
            
            if not record or record["enhanced_cases"] == 0:
                logger.info("🚀 Initializing enhanced legal schema...")
                await self.schema_manager.create_enhanced_schema()
            else:
                logger.info("✅ Enhanced legal schema already present")
    
    async def close(self):
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
            self.schema_manager.close()
    
    # === ENHANCED LEGAL RESEARCH METHODS ===
    
    async def find_authoritative_precedents(
        self,
        case_id: str,
        target_jurisdictions: List[str],
        practice_areas: List[str],
        primary_jurisdiction: str = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Find authoritative precedents with sophisticated relevance scoring.
        
        Uses multi-factor authority calculation considering:
        - Landmark case status
        - Practice area overlap
        - Jurisdictional authority
        - Citation network analysis
        """
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["find_authoritative_precedents"],
                case_id=case_id,
                target_jurisdictions=target_jurisdictions,
                practice_areas=practice_areas,
                primary_jurisdiction=primary_jurisdiction or target_jurisdictions[0]
            )
            records = await result.data()
            
            precedents = []
            for record in records:
                case_data = self._record_to_case(record["related"])
                precedents.append({
                    "case": case_data,
                    "relevance_score": record["relevance_score"],
                    "authority_factors": {
                        "landmark_case": case_data.landmark_case if hasattr(case_data, 'landmark_case') else False,
                        "authority_score": case_data.authority_score,
                        "jurisdiction": case_data.jurisdiction,
                        "practice_areas": case_data.practice_areas
                    }
                })
            
            return precedents
    
    async def analyze_citation_treatment(self, case_id: str) -> Dict[str, Any]:
        """
        Analyze how a case has been treated by subsequent courts.
        
        Returns comprehensive treatment analysis including:
        - Positive/negative/neutral citation counts
        - Authority-weighted impact scores
        - Good law confidence assessment
        - Recent citation trends
        """
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["analyze_citation_treatment"],
                case_id=case_id
            )
            record = await result.single()
            
            if record:
                return record["treatment_analysis"]
            else:
                return {
                    "case": None,
                    "total_citations": 0,
                    "positive_citations": 0,
                    "negative_citations": 0,
                    "neutral_citations": 0,
                    "weighted_authority_impact": 0.0,
                    "good_law_confidence": "unknown",
                    "recent_citations": []
                }
    
    async def verify_good_law_status(self, case_id: str) -> Dict[str, Any]:
        """
        Verify if a case is still good law.
        
        Analyzes citation treatments to determine:
        - Current legal status
        - Overruling cases (if any)
        - Good law confidence level
        - Treatment trend analysis
        """
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["good_law_verification"],
                case_id=case_id
            )
            record = await result.single()
            
            return record["verification_result"] if record else {
                "case_id": case_id,
                "current_status": "unknown",
                "good_law_confidence": "unknown",
                "overruled_by": [],
                "negative_treatment_count": 0,
                "positive_treatment_count": 0
            }
    
    async def track_doctrine_evolution(self, doctrine_tags: List[str]) -> List[Dict[str, Any]]:
        """
        Track evolution of legal doctrines through citation chains.
        
        Analyzes how legal principles evolve over time through
        landmark cases and subsequent interpretations.
        """
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["find_doctrinal_evolution"],
                doctrine_tags=doctrine_tags
            )
            records = await result.data()
            
            return [record["doctrine_evolution"] for record in records]
    
    async def calculate_legal_authority_pagerank(self) -> Dict[str, Any]:
        """
        Calculate PageRank authority scores with legal domain weighting.
        
        Uses enhanced citation network with authority factors:
        - Citation strength
        - Treatment type
        - Court hierarchy
        - Temporal relevance
        """
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["calculate_legal_authority_pagerank"]
            )
            record = await result.single()
            
            return {
                "nodes_updated": record["nodePropertiesWritten"],
                "iterations": record["ranIterations"],
                "converged": record["didConverge"],
                "algorithm": "legal_authority_pagerank"
            } if record else {"error": "PageRank calculation failed"}
    
    # === ENHANCED CASE OPERATIONS ===
    
    async def create_case_with_legal_metadata(self, case: Case, legal_metadata: Dict[str, Any] = None) -> Case:
        """Create case with enhanced legal metadata."""
        async with self.driver.session() as session:
            properties = case.model_dump(exclude={'id'})
            
            # Add enhanced legal properties
            if legal_metadata:
                properties.update({
                    "good_law_status": legal_metadata.get("good_law_status", "good_law"),
                    "landmark_case": legal_metadata.get("landmark_case", False),
                    "doctrine_tags": legal_metadata.get("doctrine_tags", []),
                    "legal_issues": legal_metadata.get("legal_issues", []),
                    "procedural_history": legal_metadata.get("procedural_history", ""),
                    "key_facts": legal_metadata.get("key_facts", "")
                })
            
            # Convert datetime objects
            for key, value in properties.items():
                if isinstance(value, (datetime, date)):
                    properties[key] = value.isoformat()
            
            query = """
            MERGE (c:Case {id: $id})
            SET c += $properties
            RETURN c
            """
            
            await session.run(query, id=case.id, properties=properties)
            return case
    
    async def create_enhanced_citation(
        self,
        citing_case_id: str,
        cited_case_id: str,
        treatment: str,
        strength: float = 0.5,
        legal_context: str = None,
        binding_precedent: bool = None,
        additional_properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create enhanced citation with sophisticated legal properties.
        
        Args:
            citing_case_id: ID of the citing case
            cited_case_id: ID of the cited case  
            treatment: Legal treatment type (follows, distinguishes, overruled, etc.)
            strength: Citation strength (0.0-1.0)
            legal_context: Legal domain context
            binding_precedent: Whether citation is binding
            additional_properties: Other citation properties
        """
        async with self.driver.session() as session:
            # Build citation properties
            cite_properties = {
                "treatment": treatment,
                "strength": strength,
                "certainty": additional_properties.get("certainty", 0.8) if additional_properties else 0.8,
                "created_at": datetime.now().isoformat(),
                "legal_context": legal_context or "general",
                "holding_type": additional_properties.get("holding_type", "ratio") if additional_properties else "ratio"
            }
            
            if binding_precedent is not None:
                cite_properties["binding_precedent"] = binding_precedent
            
            if additional_properties:
                cite_properties.update({
                    k: v for k, v in additional_properties.items() 
                    if k not in cite_properties
                })
            
            # Calculate authority factors
            authority_query = """
            MATCH (citing:Case {id: $citing_case_id})-[:DECIDED_BY]->(citing_court:Court)
            MATCH (cited:Case {id: $cited_case_id})-[:DECIDED_BY]->(cited_court:Court)
            
            // Calculate jurisdictional authority
            WITH citing, cited, citing_court, cited_court,
            CASE 
                WHEN cited_court.jurisdiction IN citing_court.binding_jurisdictions THEN 1.0
                WHEN cited_court.jurisdiction IN citing_court.persuasive_jurisdictions THEN 0.6
                ELSE 0.3
            END as jurisdictional_authority,
            
            // Calculate temporal authority
            CASE 
                WHEN duration.between(cited.decision_date, date()).years <= 5 THEN 1.0
                WHEN duration.between(cited.decision_date, date()).years <= 10 THEN 0.8
                WHEN duration.between(cited.decision_date, date()).years <= 20 THEN 0.6
                ELSE 0.4
            END as temporal_authority,
            
            // Calculate hierarchical authority
            CASE
                WHEN cited_court.level = 'supreme_court' THEN 1.0
                WHEN cited_court.level = 'appellate' AND citing_court.level IN ['district', 'trial'] THEN 0.9
                WHEN cited_court.level = citing_court.level THEN 0.7
                ELSE 0.5
            END as hierarchical_authority
            
            // Create citation with calculated authority
            MERGE (citing)-[r:CITES]->(cited)
            SET r += $cite_properties,
                r.jurisdictional_authority = jurisdictional_authority,
                r.temporal_authority = temporal_authority,
                r.hierarchical_authority = hierarchical_authority,
                r.calculated_authority = 
                    cited_court.base_authority_weight * 
                    jurisdictional_authority * 
                    temporal_authority * 
                    hierarchical_authority * 
                    $strength
            
            RETURN r, citing_court.short_name as citing_court, cited_court.short_name as cited_court
            """
            
            result = await session.run(
                authority_query,
                citing_case_id=citing_case_id,
                cited_case_id=cited_case_id,
                cite_properties=cite_properties,
                strength=strength
            )
            record = await result.single()
            
            if record:
                return {
                    "citation_created": True,
                    "citing_court": record["citing_court"],
                    "cited_court": record["cited_court"],
                    "calculated_authority": record["r"]["calculated_authority"],
                    "treatment": treatment,
                    "strength": strength
                }
            else:
                return {"citation_created": False, "error": "Cases not found"}
    
    # === ENHANCED SEARCH OPERATIONS ===
    
    async def semantic_case_search(
        self,
        search_terms: str,
        jurisdictions: List[str] = None,
        practice_areas: List[str] = None,
        court_levels: List[str] = None,
        date_range: Tuple[date, date] = None,
        good_law_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Enhanced semantic search with legal domain filtering.
        
        Combines full-text search with legal metadata filtering
        for sophisticated case discovery.
        """
        async with self.driver.session() as session:
            # Build dynamic query based on filters
            query_parts = []
            where_conditions = []
            params = {"search_terms": search_terms, "limit": limit}
            
            # Full-text search
            query_parts.append("""
                CALL db.index.fulltext.queryNodes("legal_content_search", $search_terms) 
                YIELD node as c, score
                WHERE c:Case
            """)
            
            # Apply filters
            if good_law_only:
                where_conditions.append("c.good_law_status = 'good_law'")
            
            if jurisdictions:
                where_conditions.append("c.jurisdiction IN $jurisdictions")
                params["jurisdictions"] = jurisdictions
            
            if practice_areas:
                where_conditions.append("ANY(area IN c.practice_areas WHERE area IN $practice_areas)")
                params["practice_areas"] = practice_areas
            
            if court_levels:
                query_parts.append("MATCH (c)-[:DECIDED_BY]->(ct:Court)")
                where_conditions.append("ct.level IN $court_levels")
                params["court_levels"] = court_levels
            
            if date_range:
                where_conditions.append("c.decision_date >= $start_date AND c.decision_date <= $end_date")
                params["start_date"] = date_range[0].isoformat()
                params["end_date"] = date_range[1].isoformat()
            
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            query_parts.append("""
                RETURN c, score,
                    c.authority_score * score as relevance_score
                ORDER BY relevance_score DESC
                LIMIT $limit
            """)
            
            query = "\n".join(query_parts)
            
            try:
                result = await session.run(query, **params)
                records = await result.data()
                
                cases = []
                for record in records:
                    case_data = self._record_to_case(record["c"])
                    cases.append({
                        "case": case_data,
                        "text_score": record["score"],
                        "relevance_score": record["relevance_score"],
                        "authority_score": case_data.authority_score
                    })
                
                return cases
                
            except Exception as e:
                logger.warning(f"Full-text search failed, falling back to simple search: {e}")
                # Fallback to simple text matching
                return await self._fallback_text_search(search_terms, params, limit)
    
    async def _fallback_text_search(self, search_terms: str, params: Dict, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search when full-text index is unavailable."""
        async with self.driver.session() as session:
            query = """
            MATCH (c:Case)
            WHERE toLower(c.case_name) CONTAINS toLower($search_terms)
               OR toLower(c.summary) CONTAINS toLower($search_terms)
               OR toLower(c.holding) CONTAINS toLower($search_terms)
            RETURN c, c.authority_score as relevance_score
            ORDER BY relevance_score DESC
            LIMIT $limit
            """
            
            result = await session.run(query, search_terms=search_terms, limit=limit)
            records = await result.data()
            
            return [{
                "case": self._record_to_case(record["c"]),
                "text_score": 0.5,  # Default score for fallback
                "relevance_score": record["relevance_score"],
                "authority_score": record["relevance_score"]
            } for record in records]
    
    # === COURT AND JUDGE OPERATIONS ===
    
    async def create_enhanced_court(self, court: Court, authority_metadata: Dict[str, Any] = None) -> Court:
        """Create court with enhanced authority metadata."""
        async with self.driver.session() as session:
            properties = court.model_dump(exclude={'id'})
            
            # Add authority metadata
            if authority_metadata:
                properties.update({
                    "base_authority_weight": authority_metadata.get("base_authority_weight", 5.0),
                    "binding_jurisdictions": authority_metadata.get("binding_jurisdictions", []),
                    "persuasive_jurisdictions": authority_metadata.get("persuasive_jurisdictions", []),
                    "subject_specialties": authority_metadata.get("subject_specialties", []),
                    "conservative_score": authority_metadata.get("conservative_score", 0.5),
                    "precedent_adherence": authority_metadata.get("precedent_adherence", 0.8)
                })
            
            # Convert datetime objects
            for key, value in properties.items():
                if isinstance(value, (datetime, date)):
                    properties[key] = value.isoformat()
            
            query = """
            MERGE (ct:Court {id: $id})
            SET ct += $properties
            RETURN ct
            """
            
            await session.run(query, id=court.id, properties=properties)
            return court
    
    # === UTILITY AND CONVERSION METHODS ===
    
    def _record_to_case(self, record_data) -> Case:
        """Convert Neo4j record to Case object with enhanced fields."""
        data = dict(record_data)
        
        # Convert ISO strings back to datetime objects
        for field in ['decision_date', 'filing_date', 'created_at', 'updated_at']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    try:
                        data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # Handle malformed dates gracefully
                        data[field] = None
        
        # Handle enhanced fields that might not exist in basic Case model
        enhanced_fields = ['good_law_status', 'landmark_case', 'doctrine_tags', 'legal_issues']
        case_data = {k: v for k, v in data.items() if k not in enhanced_fields or hasattr(Case, k)}
        
        try:
            return Case(**case_data)
        except Exception as e:
            logger.warning(f"Failed to create Case object, using minimal data: {e}")
            # Return minimal Case object with required fields only
            required_fields = ['id', 'case_name', 'jurisdiction']
            minimal_data = {field: data.get(field, f"unknown_{field}") for field in required_fields}
            return Case(**minimal_data)
    
    async def health_check(self) -> bool:
        """Enhanced health check including schema validation."""
        try:
            async with self.driver.session() as session:
                # Basic connectivity test
                await session.run("RETURN 1 as test")
                
                # Check for enhanced schema elements
                result = await session.run("""
                    MATCH (c:Case) 
                    WHERE c.good_law_status IS NOT NULL 
                    RETURN count(c) as enhanced_cases LIMIT 1
                """)
                record = await result.single()
                
                if record and record["enhanced_cases"] > 0:
                    logger.debug("✅ Enhanced schema detected")
                else:
                    logger.warning("⚠️ Basic schema only, enhanced features may not work")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Neo4j health check failed: {e}")
            return False
    
    # === LEGACY COMPATIBILITY METHODS ===
    # These maintain compatibility with the existing API
    
    async def get_case_by_id(self, case_id: str) -> Optional[Case]:
        """Get a case by its ID."""
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (c:Case {id: $case_id}) RETURN c",
                case_id=case_id
            )
            record = await result.single()
            if record:
                return self._record_to_case(record["c"])
            return None
    
    async def find_cases_by_criteria(
        self,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        court_level: Optional[str] = None,
        limit: int = 50
    ) -> List[Case]:
        """Legacy method for finding cases by criteria."""
        # Convert to enhanced search
        converted_date_range = None
        if date_range:
            converted_date_range = (date_range[0].date(), date_range[1].date())
        
        results = await self.semantic_case_search(
            search_terms="*",  # Match all
            jurisdictions=[jurisdiction] if jurisdiction else None,
            practice_areas=practice_areas,
            court_levels=[court_level] if court_level else None,
            date_range=converted_date_range,
            good_law_only=False,  # Include all for legacy compatibility
            limit=limit
        )
        
        return [result["case"] for result in results]
    
    async def calculate_authority_score(self, case_id: str) -> float:
        """Calculate authority score for a specific case."""
        async with self.driver.session() as session:
            result = await session.run(
                """MATCH (c:Case {id: $case_id}) 
                   RETURN coalesce(c.legal_pagerank_score, c.authority_score, 0.0) as score""",
                case_id=case_id
            )
            record = await result.single()
            return float(record["score"]) if record else 0.0


# Example usage demonstrating enhanced capabilities
async def example_enhanced_usage():
    """Example of enhanced Neo4j service capabilities."""
    service = EnhancedNeo4jService("bolt://localhost:7687", "neo4j", "citation_graph_2024")
    
    try:
        await service.connect()
        logger.info("🚀 Testing enhanced legal research capabilities...")
        
        # Test 1: Find authoritative precedents
        precedents = await service.find_authoritative_precedents(
            case_id="brown-v-board-1954",
            target_jurisdictions=["US", "US-9"],
            practice_areas=["constitutional_law", "civil_rights"],
            primary_jurisdiction="US"
        )
        logger.info(f"Found {len(precedents)} authoritative precedents")
        
        # Test 2: Analyze citation treatment
        treatment = await service.analyze_citation_treatment("brown-v-board-1954")
        logger.info(f"Citation analysis: {treatment.get('good_law_confidence', 'unknown')} confidence")
        
        # Test 3: Verify good law status
        verification = await service.verify_good_law_status("brown-v-board-1954")
        logger.info(f"Good law status: {verification.get('good_law_confidence', 'unknown')}")
        
        # Test 4: Calculate PageRank authority
        pagerank_result = await service.calculate_legal_authority_pagerank()
        logger.info(f"PageRank updated {pagerank_result.get('nodes_updated', 0)} nodes")
        
        # Test 5: Enhanced semantic search
        search_results = await service.semantic_case_search(
            search_terms="equal protection constitutional",
            jurisdictions=["US"],
            practice_areas=["constitutional_law"],
            good_law_only=True,
            limit=10
        )
        logger.info(f"Semantic search found {len(search_results)} relevant cases")
        
        logger.info("✅ Enhanced legal research capabilities verified")
        
    except Exception as e:
        logger.error(f"❌ Enhanced usage example failed: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(example_enhanced_usage())