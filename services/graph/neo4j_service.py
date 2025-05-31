"""
Neo4j database service for legal citation graph operations.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from neo4j import AsyncGraphDatabase, Record
import logging

from shared.models.legal_entities import Case, Court, Judge, Citation, LegalConcept, Statute
from shared.database.neo4j_schema import CASE_QUERIES, GRAPH_ALGORITHMS


logger = logging.getLogger(__name__)


class Neo4jService:
    """Service for Neo4j graph database operations."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.connected = False
    
    async def connect(self):
        """Establish connection to Neo4j."""
        try:
            await self.driver.verify_connectivity()
            self.connected = True
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
    
    # Case operations
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
            except Exception:
                # Projection might already exist
                pass
            
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
        data = dict(record_data)
        
        # Convert ISO strings back to datetime objects
        for field in ['decision_date', 'filing_date', 'created_at', 'updated_at']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return Case(**data)
    
    def _record_to_citation(self, record_data) -> Citation:
        """Convert Neo4j record to Citation object."""
        data = dict(record_data)
        
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return Citation(**data)
    
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