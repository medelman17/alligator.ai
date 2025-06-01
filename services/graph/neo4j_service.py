"""
Neo4j database service for legal citation graph operations.

Enhanced version with sophisticated legal research capabilities including:
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
from shared.database.neo4j_schema import CASE_QUERIES, GRAPH_ALGORITHMS
from shared.database.enhanced_neo4j_schema import ENHANCED_LEGAL_QUERIES, EnhancedNeo4jSchemaManager


logger = logging.getLogger(__name__)


class Neo4jService:
    """
    Enhanced Neo4j service for sophisticated legal research operations.
    
    Provides both legacy compatibility and advanced legal research features:
    - Traditional CRUD operations for cases, courts, judges
    - Enhanced citation analysis with treatment classification
    - Authority scoring with multi-factor calculations
    - Legal research query optimization
    - Good law verification and precedent discovery
    """
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.connected = False
        self.enhanced_schema_available = False
        self.schema_manager = EnhancedNeo4jSchemaManager(uri, user, password)
    
    async def connect(self):
        """Establish connection to Neo4j and initialize enhanced schema if needed."""
        try:
            await self.driver.verify_connectivity()
            self.connected = True
            logger.info("✅ Connected to Neo4j database")
            
            # Check for and initialize enhanced schema
            await self._check_enhanced_schema()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    async def _check_enhanced_schema(self):
        """Check if enhanced schema is available and initialize if needed."""
        async with self.driver.session() as session:
            try:
                # Check if enhanced schema exists
                result = await session.run(
                    "MATCH (c:Case) WHERE c.good_law_status IS NOT NULL RETURN count(c) as enhanced_cases LIMIT 1"
                )
                record = await result.single()
                
                if record and record["enhanced_cases"] > 0:
                    self.enhanced_schema_available = True
                    logger.info("✅ Enhanced legal schema detected")
                else:
                    logger.info("🚀 Initializing enhanced legal schema...")
                    await self.schema_manager.create_enhanced_schema()
                    self.enhanced_schema_available = True
                    
            except Exception as e:
                logger.warning(f"⚠️ Enhanced schema initialization failed, using basic schema: {e}")
                self.enhanced_schema_available = False
    
    async def close(self):
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
        if hasattr(self, 'schema_manager'):
            await self.schema_manager.close()
    
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
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available, falling back to basic precedent search")
            return await self._basic_precedent_search(case_id, target_jurisdictions, practice_areas, limit)
        
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
                        "landmark_case": getattr(case_data, 'landmark_case', False),
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
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available, using basic citation analysis")
            return await self._basic_citation_analysis(case_id)
        
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["analyze_citation_treatment"],
                case_id=case_id
            )
            record = await result.single()
            
            if record:
                # Convert any Neo4j temporal objects to Python datetime objects
                treatment_analysis = self._convert_neo4j_temporals(record["treatment_analysis"])
                return treatment_analysis
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
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available, using basic good law check")
            return {"case_id": case_id, "good_law_confidence": "unknown", "message": "Enhanced schema required"}
        
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["good_law_verification"],
                case_id=case_id
            )
            record = await result.single()
            
            if record:
                # Convert any Neo4j temporal objects to Python datetime objects  
                verification_result = self._convert_neo4j_temporals(record["verification_result"])
                return verification_result
            else:
                return {
                    "case_id": case_id,
                    "current_status": "unknown",
                    "good_law_confidence": "unknown",
                    "overruled_by": [],
                    "negative_treatment_count": 0,
                    "positive_treatment_count": 0
                }
    
    async def calculate_legal_authority_pagerank(self) -> Dict[str, Any]:
        """
        Calculate PageRank authority scores with legal domain weighting.
        
        Uses enhanced citation network with authority factors:
        - Citation strength
        - Treatment type
        - Court hierarchy  
        - Temporal relevance
        """
        if not self.enhanced_schema_available:
            logger.warning("Enhanced schema not available, using basic PageRank")
            return await self._basic_pagerank()
        
        async with self.driver.session() as session:
            result = await session.run(
                ENHANCED_LEGAL_QUERIES["calculate_legal_authority_pagerank"]
            )
            record = await result.single()
            
            return {
                "nodes_updated": record["nodePropertiesWritten"],
                "iterations": record["ranIterations"],
                "converged": record["didConverged"],
                "algorithm": "legal_authority_pagerank"
            } if record else {"error": "PageRank calculation failed"}
    
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
            # Try enhanced full-text search first
            if self.enhanced_schema_available:
                try:
                    return await self._enhanced_semantic_search(session, search_terms, jurisdictions, 
                                                               practice_areas, court_levels, date_range, 
                                                               good_law_only, limit)
                except Exception as e:
                    logger.warning(f"Enhanced search failed, falling back to basic: {e}")
            
            # Fallback to basic text search
            return await self._basic_text_search(session, search_terms, jurisdictions, practice_areas, limit)
    
    # === ENHANCED HELPER METHODS ===
    
    def _convert_neo4j_temporals(self, data: Any) -> Any:
        """
        Recursively convert Neo4j temporal objects to Python datetime objects.
        
        This handles:
        - neo4j.time.DateTime objects
        - neo4j.time.Date objects  
        - Nested dictionaries and lists
        - ISO datetime strings
        """
        if isinstance(data, dict):
            return {key: self._convert_neo4j_temporals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_neo4j_temporals(item) for item in data]
        elif data is not None:
            field_type = str(type(data))
            
            if isinstance(data, str):
                # Check if it's an ISO datetime string that we can convert
                if len(data) >= 10 and 'T' in data or data.count('-') >= 2:
                    try:
                        return datetime.fromisoformat(data.replace('Z', '+00:00'))
                    except ValueError:
                        return data
                else:
                    return data
            elif 'neo4j.time.Date' in field_type:
                # Neo4j Date object
                neo4j_date = data.to_native()
                return datetime.combine(neo4j_date, datetime.min.time())
            elif 'neo4j.time.DateTime' in field_type:
                # Neo4j DateTime object
                return data.to_native()
            elif 'neo4j.time.Duration' in field_type:
                # Neo4j Duration object - convert to total seconds
                return data.total_seconds()
            elif hasattr(data, 'to_native'):
                # Generic Neo4j temporal object
                converted = data.to_native()
                if hasattr(converted, 'date') and not hasattr(converted, 'hour'):
                    # If it's still a date object, convert to datetime
                    return datetime.combine(converted, datetime.min.time())
                return converted
            elif hasattr(data, 'year') and not hasattr(data, 'hour'):
                # Python date object - convert to datetime
                return datetime.combine(data, datetime.min.time())
            else:
                return data
        else:
            return data
    
    async def _basic_precedent_search(self, case_id: str, jurisdictions: List[str], practice_areas: List[str], limit: int):
        """Fallback precedent search for basic schema."""
        results = await self.traverse_citation_network(case_id, max_depth=2, limit=limit)
        return [{
            "case": result["case"],
            "relevance_score": 5.0 - result["distance"],  # Simple distance-based scoring
            "authority_factors": {
                "authority_score": result["case"].authority_score,
                "jurisdiction": result["case"].jurisdiction
            }
        } for result in results if result["case"].jurisdiction in jurisdictions]
    
    async def _basic_citation_analysis(self, case_id: str):
        """Basic citation analysis without enhanced treatment types."""
        citing_cases = await self.get_citing_cases(case_id, limit=100)
        cited_cases = await self.get_cited_cases(case_id, limit=100)
        
        return {
            "case": await self.get_case_by_id(case_id),
            "total_citations": len(citing_cases),
            "positive_citations": len(citing_cases),  # Assume all positive for basic
            "negative_citations": 0,
            "neutral_citations": 0,
            "good_law_confidence": "moderate",
            "recent_citations": [
                {
                    "case_name": case.case_name,
                    "treatment": citation.treatment if hasattr(citation, 'treatment') else "cited",
                    "date": case.decision_date.isoformat() if case.decision_date else None
                }
                for case, citation in citing_cases[:10]
            ]
        }
    
    async def _basic_pagerank(self):
        """Basic PageRank calculation."""
        nodes_updated = await self.calculate_authority_scores()
        return {
            "nodes_updated": nodes_updated,
            "algorithm": "basic_pagerank",
            "iterations": "unknown"
        }
    
    async def _enhanced_semantic_search(self, session, search_terms, jurisdictions, practice_areas, 
                                       court_levels, date_range, good_law_only, limit):
        """Enhanced semantic search with full-text indexing."""
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
        result = await session.run(query, **params)
        records = await result.data()
        
        return [{
            "case": self._record_to_case(record["c"]),
            "text_score": record["score"],
            "relevance_score": record["relevance_score"],
            "authority_score": record["c"]["authority_score"]
        } for record in records]
    
    async def _basic_text_search(self, session, search_terms, jurisdictions, practice_areas, limit):
        """Fallback text search when full-text index is unavailable."""
        where_conditions = []
        params = {"search_terms": search_terms.lower(), "limit": limit}
        
        query_parts = ["""
            MATCH (c:Case)
            WHERE toLower(c.case_name) CONTAINS $search_terms
               OR toLower(c.summary) CONTAINS $search_terms
               OR toLower(c.holding) CONTAINS $search_terms
        """]
        
        if jurisdictions:
            where_conditions.append("c.jurisdiction IN $jurisdictions")
            params["jurisdictions"] = jurisdictions
        
        if practice_areas:
            where_conditions.append("ANY(area IN c.practice_areas WHERE area IN $practice_areas)")
            params["practice_areas"] = practice_areas
        
        if where_conditions:
            query_parts.append("AND " + " AND ".join(where_conditions))
        
        query_parts.append("""
            RETURN c, c.authority_score as relevance_score
            ORDER BY relevance_score DESC
            LIMIT $limit
        """)
        
        query = "\n".join(query_parts)
        result = await session.run(query, **params)
        records = await result.data()
        
        return [{
            "case": self._record_to_case(record["c"]),
            "text_score": 0.5,  # Default score for fallback
            "relevance_score": record["relevance_score"],
            "authority_score": record["relevance_score"]
        } for record in records]
    
    # === TRADITIONAL CASE OPERATIONS (ENHANCED) ===
    async def create_case(self, case: Case) -> Case:
        """Create or update a case in the graph."""
        async with self.driver.session() as session:
            properties = case.model_dump(exclude={'id'})
            # Convert datetime objects to ISO strings for Neo4j
            for key, value in properties.items():
                if isinstance(value, datetime):
                    properties[key] = value.isoformat()
            
            result = await session.run(
                CASE_QUERIES["create_case"],
                id=case.id,
                properties=properties
            )
            record = await result.single()
            return case  # Return the original case object
    
    async def find_case_by_citation(self, citation: str) -> Optional[Case]:
        """Find a case by its citation."""
        async with self.driver.session() as session:
            result = await session.run(
                CASE_QUERIES["find_case_by_citation"],
                citation=citation
            )
            record = await result.single()
            if record:
                return self._record_to_case(record["c"])
            return None
    
    async def get_citing_cases(self, case_id: str, limit: int = 50) -> List[Tuple[Case, Citation]]:
        """Get cases that cite the given case."""
        async with self.driver.session() as session:
            result = await session.run(
                CASE_QUERIES["get_citing_cases"],
                case_id=case_id
            )
            records = await result.data()
            
            results = []
            for record in records[:limit]:
                citing_case = self._record_to_case(record["citing"])
                citation_rel = self._record_to_citation(record["r"])
                # Set the proper case IDs for the citation
                citation_rel.citing_case_id = citing_case.id
                citation_rel.cited_case_id = case_id
                results.append((citing_case, citation_rel))
            
            return results
    
    async def get_cited_cases(self, case_id: str, limit: int = 50) -> List[Tuple[Case, Citation]]:
        """Get cases cited by the given case."""
        async with self.driver.session() as session:
            result = await session.run(
                CASE_QUERIES["get_cited_cases"],
                case_id=case_id
            )
            records = await result.data()
            
            results = []
            for record in records[:limit]:
                cited_case = self._record_to_case(record["cited"])
                citation_rel = self._record_to_citation(record["r"])
                # Set the proper case IDs for the citation
                citation_rel.citing_case_id = case_id
                citation_rel.cited_case_id = cited_case.id
                results.append((cited_case, citation_rel))
            
            return results
    
    async def traverse_citation_network(
        self, 
        case_id: str, 
        max_depth: int = 3, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Traverse the citation network to find related cases."""
        async with self.driver.session() as session:
            result = await session.run(
                CASE_QUERIES["citation_network_traversal"],
                case_id=case_id,
                limit=limit
            )
            records = await result.data()
            
            results = []
            for record in records:
                related_case = self._record_to_case(record["related"])
                results.append({
                    "case": related_case,
                    "distance": record["distance"],
                    "path_length": len(record["path"].relationships)
                })
            
            return results
    
    async def find_cases_by_criteria(
        self,
        jurisdiction: Optional[str] = None,
        practice_areas: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        court_level: Optional[str] = None,
        limit: int = 50
    ) -> List[Case]:
        """Find cases by various criteria."""
        query_parts = ["MATCH (c:Case)"]
        where_conditions = []
        params = {"limit": limit}
        
        if jurisdiction:
            where_conditions.append("c.jurisdiction = $jurisdiction")
            params["jurisdiction"] = jurisdiction
        
        if practice_areas:
            where_conditions.append("ANY(area IN c.practice_areas WHERE area IN $practice_areas)")
            params["practice_areas"] = practice_areas
        
        if date_range:
            where_conditions.append("c.decision_date >= $start_date AND c.decision_date <= $end_date")
            params["start_date"] = date_range[0].isoformat()
            params["end_date"] = date_range[1].isoformat()
        
        if court_level:
            query_parts.append("MATCH (c)-[:DECIDED_BY]->(ct:Court)")
            where_conditions.append("ct.level = $court_level")
            params["court_level"] = court_level
        
        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))
        
        query_parts.extend([
            "RETURN c",
            "ORDER BY c.authority_score DESC, c.decision_date DESC",
            "LIMIT $limit"
        ])
        
        query = "\n".join(query_parts)
        
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            return [self._record_to_case(record["c"]) for record in records]
    
    # Citation operations
    async def create_citation(self, citation: Citation) -> Citation:
        """Create a citation relationship between cases."""
        async with self.driver.session() as session:
            query = """
            MATCH (citing:Case {id: $citing_case_id})
            MATCH (cited:Case {id: $cited_case_id})
            MERGE (citing)-[r:CITES {id: $citation_id}]->(cited)
            SET r += $properties
            RETURN r
            """
            
            properties = citation.model_dump(exclude={'id', 'citing_case_id', 'cited_case_id'})
            # Convert datetime objects
            for key, value in properties.items():
                if isinstance(value, datetime):
                    properties[key] = value.isoformat()
            
            await session.run(
                query,
                citing_case_id=citation.citing_case_id,
                cited_case_id=citation.cited_case_id,
                citation_id=citation.id,
                properties=properties
            )
            
            return citation
    
    # Authority and ranking operations
    async def calculate_authority_scores(self) -> int:
        """Calculate PageRank authority scores for all cases."""
        async with self.driver.session() as session:
            # First create graph projection if it doesn't exist
            try:
                await session.run(GRAPH_ALGORITHMS["create_case_citation_projection"])
            except Exception as e:
                # Projection might already exist, log and continue
                logging.debug(f"Graph projection creation failed (likely already exists): {e}")
            
            # Run PageRank algorithm
            result = await session.run(GRAPH_ALGORITHMS["run_pagerank"])
            record = await result.single()
            return record["nodePropertiesWritten"] if record else 0
    
    async def find_overruling_chain(self, case_id: str) -> List[Dict[str, Any]]:
        """Find the overruling chain for a case."""
        async with self.driver.session() as session:
            result = await session.run(
                CASE_QUERIES["overruling_chain"],
                case_id=case_id
            )
            records = await result.data()
            
            chains = []
            for record in records:
                path = record["path"]
                overruling_case = self._record_to_case(record["end"])
                chains.append({
                    "overruling_case": overruling_case,
                    "path_length": len(path.relationships),
                    "relationships": [rel.type for rel in path.relationships]
                })
            
            return chains
    
    async def get_judge_case_patterns(
        self, 
        judge_name: str, 
        practice_areas: Optional[List[str]] = None
    ) -> List[Case]:
        """Get cases decided by a specific judge in given practice areas."""
        async with self.driver.session() as session:
            params = {"judge_name": judge_name}
            if practice_areas:
                params["practice_areas"] = practice_areas
            
            result = await session.run(
                CASE_QUERIES["judge_case_patterns"],
                **params
            )
            records = await result.data()
            return [self._record_to_case(record["c"]) for record in records]
    
    # Court operations
    async def create_court(self, court: Court) -> Court:
        """Create or update a court."""
        async with self.driver.session() as session:
            properties = court.model_dump(exclude={'id'})
            # Convert datetime objects
            for key, value in properties.items():
                if isinstance(value, datetime):
                    properties[key] = value.isoformat()
            
            query = """
            MERGE (ct:Court {id: $id})
            SET ct += $properties
            RETURN ct
            """
            
            await session.run(query, id=court.id, properties=properties)
            return court
    
    async def create_judge(self, judge: Judge) -> Judge:
        """Create or update a judge."""
        async with self.driver.session() as session:
            properties = judge.model_dump(exclude={'id'})
            # Convert datetime objects
            for key, value in properties.items():
                if isinstance(value, datetime):
                    properties[key] = value.isoformat()
            
            query = """
            MERGE (j:Judge {id: $id})
            SET j += $properties
            RETURN j
            """
            
            await session.run(query, id=judge.id, properties=properties)
            return judge
    
    # Utility methods
    def _record_to_case(self, record_data) -> Case:
        """Convert Neo4j record to Case object."""
        # Handle both Neo4j Node objects and dictionaries
        if hasattr(record_data, '_properties'):
            # Neo4j Node object
            data = dict(record_data._properties)
        else:
            # Already a dictionary
            data = dict(record_data)
        
        # Convert date objects to datetime objects
        for field in ['decision_date', 'filing_date', 'created_at', 'updated_at']:
            if field in data and data[field]:
                field_type = str(type(data[field]))
                
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                elif 'neo4j.time.Date' in field_type:
                    # Neo4j Date object
                    neo4j_date = data[field].to_native()
                    data[field] = datetime.combine(neo4j_date, datetime.min.time())
                elif 'neo4j.time.DateTime' in field_type:
                    # Neo4j DateTime object
                    data[field] = data[field].to_native()
                elif hasattr(data[field], 'to_native'):
                    # Generic Neo4j temporal object
                    data[field] = data[field].to_native()
                    if hasattr(data[field], 'date'):
                        # If it's still a date object, convert to datetime
                        data[field] = datetime.combine(data[field], datetime.min.time())
                elif hasattr(data[field], 'year'):
                    # Python date object
                    if hasattr(data[field], 'hour'):
                        # Already a datetime
                        pass
                    else:
                        # Convert date to datetime
                        data[field] = datetime.combine(data[field], datetime.min.time())
        
        # Ensure required fields have default values
        if 'full_name' not in data or not data['full_name']:
            data['full_name'] = data.get('case_name', 'Unknown Case')
        
        if 'court_id' not in data or not data['court_id']:
            data['court_id'] = 'unknown-court'
        
        # Handle fields that don't match the Case model exactly
        # Convert practice_areas to the format expected by the model
        if 'practice_areas' in data and data['practice_areas']:
            # Neo4j may return practice areas as strings, convert to list if needed
            if isinstance(data['practice_areas'], str):
                data['practice_areas'] = [data['practice_areas']]
        
        # Convert fields not in the base Case model to metadata
        case_fields = {
            'id', 'citation', 'case_name', 'full_name', 'court_id', 'jurisdiction',
            'decision_date', 'filing_date', 'judges', 'status', 'practice_areas',
            'summary', 'holding', 'procedural_posture', 'disposition', 'authority_score',
            'citation_count', 'overruling_cases', 'metadata', 'created_at', 'updated_at'
        }
        
        # Move extra fields to metadata
        metadata = data.get('metadata', {})
        extra_fields = {}
        for key, value in list(data.items()):
            if key not in case_fields:
                extra_fields[key] = value
                del data[key]
        
        if extra_fields:
            metadata.update(extra_fields)
            data['metadata'] = metadata
        
        # Map good_law_status to status if present
        if 'good_law_status' in data:
            status_mapping = {
                'good_law': 'GOOD_LAW',
                'bad_law': 'BAD_LAW', 
                'overruled': 'OVERRULED',
                'questioned': 'QUESTIONED',
                'limited': 'LIMITED',
                'superseded': 'SUPERSEDED'
            }
            good_law_status = data.pop('good_law_status')
            if good_law_status in status_mapping:
                data['status'] = status_mapping[good_law_status]
        
        try:
            return Case(**data)
        except Exception as e:
            logger.error(f"Failed to create Case object: {e}")
            logger.error(f"Data keys: {list(data.keys())}")
            logger.error(f"Full data: {data}")
            raise
    
    def _record_to_citation(self, record_data) -> Citation:
        """Convert Neo4j record to Citation object."""
        # Handle both Neo4j Relationship objects and dictionaries
        if hasattr(record_data, '_properties'):
            # Neo4j Relationship object
            data = dict(record_data._properties)
        else:
            # Already a dictionary
            data = dict(record_data)
        
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        # Map enhanced citation fields to basic Citation model
        citation_fields = {
            'id', 'citing_case_id', 'cited_case_id', 'treatment', 'context',
            'page_references', 'quotations', 'strength', 'depth', 'created_at', 'updated_at'
        }
        
        # Create a basic citation object with core fields
        citation_data = {}
        
        # Generate ID if not present
        if 'id' not in data:
            citation_data['id'] = f"citation-{hash(str(data))}"
        else:
            citation_data['id'] = data['id']
        
        # Map treatment
        if 'treatment' in data:
            citation_data['treatment'] = data['treatment']
        else:
            citation_data['treatment'] = 'cites'
        
        # Map strength
        if 'strength' in data:
            citation_data['strength'] = float(data['strength'])
        else:
            citation_data['strength'] = 1.0
        
        # Map other fields if they exist
        if 'context' in data:
            citation_data['context'] = data['context']
        if 'legal_context' in data:
            citation_data['context'] = data['legal_context']
        
        if 'page_references' in data:
            page_refs = data['page_references']
            if isinstance(page_refs, list):
                citation_data['page_references'] = page_refs
            else:
                citation_data['page_references'] = [str(page_refs)]
        
        if 'created_at' in data:
            citation_data['created_at'] = data['created_at']
        
        if 'updated_at' in data:
            citation_data['updated_at'] = data['updated_at']
        
        # These will need to be set by the calling method
        citation_data['citing_case_id'] = 'unknown'
        citation_data['cited_case_id'] = 'unknown'
        
        try:
            return Citation(**citation_data)
        except Exception as e:
            logger.error(f"Failed to create Citation object: {e}")
            logger.error(f"Citation data: {citation_data}")
            # Return a minimal citation object
            return Citation(
                id=citation_data.get('id', 'unknown'),
                citing_case_id='unknown',
                cited_case_id='unknown',
                treatment=citation_data.get('treatment', 'cites'),
                strength=citation_data.get('strength', 1.0)
            )
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                await result.single()
                return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
    
    # Additional methods needed by API endpoints
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
    
    async def calculate_authority_score(self, case_id: str) -> float:
        """Calculate authority score for a specific case."""
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (c:Case {id: $case_id}) RETURN coalesce(c.authority_score, 0.0) as score",
                case_id=case_id
            )
            record = await result.single()
            if record:
                return float(record["score"])
            return 0.0
    
    async def update_case(self, case_id: str, update_data: dict) -> None:
        """Update case properties."""
        async with self.driver.session() as session:
            # Convert datetime objects to ISO strings
            for key, value in update_data.items():
                if isinstance(value, datetime):
                    update_data[key] = value.isoformat()
            
            await session.run(
                "MATCH (c:Case {id: $case_id}) SET c += $update_data",
                case_id=case_id,
                update_data=update_data
            )
    
    async def delete_case(self, case_id: str) -> None:
        """Delete a case and all its relationships."""
        async with self.driver.session() as session:
            await session.run(
                "MATCH (c:Case {id: $case_id}) DETACH DELETE c",
                case_id=case_id
            )
    
    async def get_citation_network(self, case_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get citation network for a case."""
        citing_cases = await self.get_citing_cases(case_id, limit=100)
        cited_cases = await self.get_cited_cases(case_id, limit=100)
        
        return {
            "citing_cases": citing_cases,
            "cited_cases": cited_cases
        }


# Example usage and testing
async def example_usage():
    """Example of how to use the Neo4j service."""
    service = Neo4jService("bolt://localhost:7687", "neo4j", "password")
    
    try:
        await service.connect()
        
        # Create a sample case
        sample_case = Case(
            id="brown-v-board-1954",
            citation="347 U.S. 483",
            case_name="Brown v. Board of Education",
            full_name="Brown v. Board of Education of Topeka",
            court_id="us-supreme-court",
            jurisdiction="US",
            decision_date=datetime(1954, 5, 17),
            judges=["Warren, C.J."],
            practice_areas=["constitutional", "civil_rights"],
            summary="Declared state laws establishing separate public schools for black and white students to be unconstitutional.",
            holding="Separate educational facilities are inherently unequal.",
            authority_score=9.8
        )
        
        created_case = await service.create_case(sample_case)
        print(f"Created case: {created_case.case_name}")
        
        # Find the case
        found_case = await service.find_case_by_citation("347 U.S. 483")
        if found_case:
            print(f"Found case: {found_case.case_name}")
        
        # Test health check
        is_healthy = await service.health_check()
        print(f"Database healthy: {is_healthy}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(example_usage())