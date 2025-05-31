"""
Neo4j schema setup for legal citation graph.
"""

from typing import List
from neo4j import GraphDatabase


class Neo4jSchemaManager:
    """Manages Neo4j schema creation and constraints."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    async def create_schema(self):
        """Create complete Neo4j schema for legal citation graph."""
        async with self.driver.session() as session:
            # Create constraints
            await self._create_constraints(session)
            
            # Create indexes
            await self._create_indexes(session)
            
            # Create court hierarchy
            await self._create_court_hierarchy(session)
    
    async def _create_constraints(self, session):
        """Create unique constraints."""
        constraints = [
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT case_citation_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.citation IS UNIQUE",
            "CREATE CONSTRAINT court_id_unique IF NOT EXISTS FOR (ct:Court) REQUIRE ct.id IS UNIQUE",
            "CREATE CONSTRAINT judge_id_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT statute_id_unique IF NOT EXISTS FOR (s:Statute) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (lc:LegalConcept) REQUIRE lc.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                await session.run(constraint)
                print(f"Created constraint: {constraint}")
            except Exception as e:
                print(f"Constraint already exists or error: {e}")
    
    async def _create_indexes(self, session):
        """Create performance indexes."""
        indexes = [
            # Case indexes
            "CREATE INDEX case_decision_date IF NOT EXISTS FOR (c:Case) ON (c.decision_date)",
            "CREATE INDEX case_jurisdiction IF NOT EXISTS FOR (c:Case) ON (c.jurisdiction)",
            "CREATE INDEX case_authority_score IF NOT EXISTS FOR (c:Case) ON (c.authority_score)",
            "CREATE INDEX case_practice_areas IF NOT EXISTS FOR (c:Case) ON (c.practice_areas)",
            "CREATE TEXT INDEX case_name_text IF NOT EXISTS FOR (c:Case) ON (c.case_name)",
            "CREATE TEXT INDEX case_summary_text IF NOT EXISTS FOR (c:Case) ON (c.summary)",
            
            # Court indexes
            "CREATE INDEX court_level IF NOT EXISTS FOR (ct:Court) ON (ct.level)",
            "CREATE INDEX court_jurisdiction IF NOT EXISTS FOR (ct:Court) ON (ct.jurisdiction)",
            
            # Judge indexes
            "CREATE INDEX judge_name IF NOT EXISTS FOR (j:Judge) ON (j.name)",
            "CREATE INDEX judge_tenure IF NOT EXISTS FOR (j:Judge) ON (j.tenure_start, j.tenure_end)",
            
            # Citation indexes
            "CREATE INDEX citation_treatment IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.treatment)",
            "CREATE INDEX citation_strength IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.strength)",
            "CREATE INDEX citation_date IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.created_at)",
            
            # Statute indexes
            "CREATE INDEX statute_jurisdiction IF NOT EXISTS FOR (s:Statute) ON (s.jurisdiction)",
            "CREATE INDEX statute_effective_date IF NOT EXISTS FOR (s:Statute) ON (s.effective_date)",
            "CREATE TEXT INDEX statute_title_text IF NOT EXISTS FOR (s:Statute) ON (s.title)",
        ]
        
        for index in indexes:
            try:
                await session.run(index)
                print(f"Created index: {index}")
            except Exception as e:
                print(f"Index already exists or error: {e}")
    
    async def _create_court_hierarchy(self, session):
        """Create standard US court hierarchy."""
        court_hierarchy = """
        // US Supreme Court
        MERGE (supreme:Court {
            id: 'us-supreme-court',
            name: 'Supreme Court of the United States',
            short_name: 'SCOTUS',
            level: 'supreme_court',
            jurisdiction: 'US',
            authority_weight: 10.0
        })
        
        // Federal Courts of Appeals
        WITH supreme
        UNWIND [
            {id: 'us-ca-1', name: 'United States Court of Appeals for the First Circuit', short: '1st Cir.', jurisdiction: 'US-1'},
            {id: 'us-ca-2', name: 'United States Court of Appeals for the Second Circuit', short: '2nd Cir.', jurisdiction: 'US-2'},
            {id: 'us-ca-3', name: 'United States Court of Appeals for the Third Circuit', short: '3rd Cir.', jurisdiction: 'US-3'},
            {id: 'us-ca-4', name: 'United States Court of Appeals for the Fourth Circuit', short: '4th Cir.', jurisdiction: 'US-4'},
            {id: 'us-ca-5', name: 'United States Court of Appeals for the Fifth Circuit', short: '5th Cir.', jurisdiction: 'US-5'},
            {id: 'us-ca-6', name: 'United States Court of Appeals for the Sixth Circuit', short: '6th Cir.', jurisdiction: 'US-6'},
            {id: 'us-ca-7', name: 'United States Court of Appeals for the Seventh Circuit', short: '7th Cir.', jurisdiction: 'US-7'},
            {id: 'us-ca-8', name: 'United States Court of Appeals for the Eighth Circuit', short: '8th Cir.', jurisdiction: 'US-8'},
            {id: 'us-ca-9', name: 'United States Court of Appeals for the Ninth Circuit', short: '9th Cir.', jurisdiction: 'US-9'},
            {id: 'us-ca-10', name: 'United States Court of Appeals for the Tenth Circuit', short: '10th Cir.', jurisdiction: 'US-10'},
            {id: 'us-ca-11', name: 'United States Court of Appeals for the Eleventh Circuit', short: '11th Cir.', jurisdiction: 'US-11'},
            {id: 'us-ca-dc', name: 'United States Court of Appeals for the District of Columbia Circuit', short: 'D.C. Cir.', jurisdiction: 'US-DC'},
            {id: 'us-ca-fc', name: 'United States Court of Appeals for the Federal Circuit', short: 'Fed. Cir.', jurisdiction: 'US-FC'}
        ] AS court_data
        MERGE (appellate:Court {
            id: court_data.id,
            name: court_data.name,
            short_name: court_data.short,
            level: 'appellate',
            jurisdiction: court_data.jurisdiction,
            authority_weight: 8.0
        })
        MERGE (appellate)-[:APPEALS_TO]->(supreme)
        """
        
        try:
            await session.run(court_hierarchy)
            print("Created court hierarchy")
        except Exception as e:
            print(f"Error creating court hierarchy: {e}")
    
    def close(self):
        """Close the database connection."""
        self.driver.close()


# Cypher queries for common operations
CASE_QUERIES = {
    "create_case": """
        MERGE (c:Case {id: $id})
        SET c += $properties
        RETURN c
    """,
    
    "find_case_by_citation": """
        MATCH (c:Case {citation: $citation})
        RETURN c
    """,
    
    "get_citing_cases": """
        MATCH (c:Case {id: $case_id})<-[r:CITES]-(citing:Case)
        RETURN citing, r
        ORDER BY r.created_at DESC
    """,
    
    "get_cited_cases": """
        MATCH (c:Case {id: $case_id})-[r:CITES]->(cited:Case)
        RETURN cited, r
        ORDER BY r.strength DESC
    """,
    
    "citation_network_traversal": """
        MATCH path = (start:Case {id: $case_id})-[:CITES*1..3]-(related:Case)
        WHERE start <> related
        RETURN related, length(path) as distance, path
        ORDER BY distance, related.authority_score DESC
        LIMIT $limit
    """,
    
    "pagerank_authority": """
        CALL gds.pageRank.stream('case-citations')
        YIELD nodeId, score
        MATCH (c:Case) WHERE id(c) = nodeId
        SET c.authority_score = score
        RETURN c.id, c.citation, score
        ORDER BY score DESC
    """,
    
    "cases_by_jurisdiction_and_practice": """
        MATCH (c:Case)
        WHERE c.jurisdiction = $jurisdiction
          AND ANY(area IN c.practice_areas WHERE area IN $practice_areas)
        RETURN c
        ORDER BY c.authority_score DESC, c.decision_date DESC
        LIMIT $limit
    """,
    
    "overruling_chain": """
        MATCH path = (start:Case {id: $case_id})-[:CITES*]->(end:Case)
        WHERE ANY(rel IN relationships(path) WHERE rel.treatment = 'overrules')
        RETURN path, end
        ORDER BY length(path)
    """,
    
    "judge_case_patterns": """
        MATCH (j:Judge)-[:DECIDED]->(c:Case)
        WHERE j.name = $judge_name
          AND ANY(area IN c.practice_areas WHERE area IN $practice_areas)
        RETURN c, j
        ORDER BY c.decision_date DESC
    """,
}

GRAPH_ALGORITHMS = {
    "create_case_citation_projection": """
        CALL gds.graph.project(
            'case-citations',
            'Case',
            'CITES',
            {
                relationshipProperties: 'strength'
            }
        )
    """,
    
    "run_pagerank": """
        CALL gds.pageRank.write(
            'case-citations',
            {
                writeProperty: 'authority_score',
                relationshipWeightProperty: 'strength'
            }
        )
        YIELD nodePropertiesWritten, ranIterations
    """,
    
    "community_detection": """
        CALL gds.louvain.write(
            'case-citations',
            {
                writeProperty: 'community_id',
                relationshipWeightProperty: 'strength'
            }
        )
        YIELD nodePropertiesWritten, communityCount
    """,
    
    "betweenness_centrality": """
        CALL gds.betweenness.write(
            'case-citations',
            {
                writeProperty: 'betweenness_score'
            }
        )
        YIELD nodePropertiesWritten
    """,
}