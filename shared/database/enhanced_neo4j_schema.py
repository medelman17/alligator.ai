"""
Enhanced Neo4j schema setup for sophisticated legal citation analysis.

This module extends the basic schema with legal domain-specific features:
- Advanced citation treatment types and authority calculations
- Sophisticated court hierarchy with jurisdictional authority
- Performance-optimized indexes for legal research patterns
- Real-world legal sample data
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class EnhancedNeo4jSchemaManager:
    """Enhanced Neo4j schema manager for legal research workflows."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    async def create_enhanced_schema(self):
        """Create comprehensive Neo4j schema for legal research."""
        async with self.driver.session() as session:
            logger.info("🏛️ Creating enhanced legal citation schema...")
            
            # Core schema (constraints, indexes, court hierarchy)
            await self._create_enhanced_constraints(session)
            await self._create_enhanced_indexes(session)
            await self._create_comprehensive_court_hierarchy(session)
            
            # Legal-specific enhancements
            await self._create_citation_treatment_system(session)
            await self._create_authority_calculation_functions(session)
            await self._create_legal_sample_data(session)
            
            # Graph algorithm projections
            await self._setup_graph_projections(session)
            
            logger.info("✅ Enhanced legal schema creation complete")
    
    async def _create_enhanced_constraints(self, session):
        """Create enhanced constraints for legal data integrity."""
        constraints = [
            # Core entity constraints
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT case_citation_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.citation IS UNIQUE",
            "CREATE CONSTRAINT court_id_unique IF NOT EXISTS FOR (ct:Court) REQUIRE ct.id IS UNIQUE",
            "CREATE CONSTRAINT judge_id_unique IF NOT EXISTS FOR (j:Judge) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT statute_id_unique IF NOT EXISTS FOR (s:Statute) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (lc:LegalConcept) REQUIRE lc.id IS UNIQUE",
            "CREATE CONSTRAINT opinion_id_unique IF NOT EXISTS FOR (o:Opinion) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT attorney_bar_unique IF NOT EXISTS FOR (a:Attorney) REQUIRE a.bar_number IS UNIQUE",
            
            # Legal-specific constraints
            "CREATE CONSTRAINT case_good_law_status IF NOT EXISTS FOR (c:Case) REQUIRE c.good_law_status IS NOT NULL",
            "CREATE CONSTRAINT court_authority_weight IF NOT EXISTS FOR (ct:Court) REQUIRE ct.base_authority_weight IS NOT NULL",
            "CREATE CONSTRAINT citation_treatment_valid IF NOT EXISTS FOR ()-[r:CITES]-() REQUIRE r.treatment IS NOT NULL",
        ]
        
        for constraint in constraints:
            try:
                await session.run(constraint)
                logger.debug(f"✅ Created constraint: {constraint[:50]}...")
            except Exception as e:
                logger.debug(f"⚠️ Constraint exists or error: {str(e)[:100]}...")
    
    async def _create_enhanced_indexes(self, session):
        """Create performance-optimized indexes for legal research."""
        indexes = [
            # Core legal research indexes
            "CREATE INDEX case_research_composite IF NOT EXISTS FOR (c:Case) ON (c.jurisdiction, c.practice_areas, c.authority_score, c.decision_date)",
            "CREATE INDEX citation_authority_composite IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.treatment, r.calculated_authority, r.binding_precedent)",
            "CREATE INDEX court_authority_composite IF NOT EXISTS FOR (ct:Court) ON (ct.level, ct.jurisdiction, ct.base_authority_weight)",
            
            # Case property indexes
            "CREATE INDEX case_decision_date IF NOT EXISTS FOR (c:Case) ON (c.decision_date)",
            "CREATE INDEX case_jurisdiction IF NOT EXISTS FOR (c:Case) ON (c.jurisdiction)",
            "CREATE INDEX case_authority_score IF NOT EXISTS FOR (c:Case) ON (c.authority_score)",
            "CREATE INDEX case_practice_areas IF NOT EXISTS FOR (c:Case) ON (c.practice_areas)",
            "CREATE INDEX case_good_law_status IF NOT EXISTS FOR (c:Case) ON (c.good_law_status)",
            "CREATE INDEX case_landmark_status IF NOT EXISTS FOR (c:Case) ON (c.landmark_case)",
            "CREATE INDEX case_doctrine_tags IF NOT EXISTS FOR (c:Case) ON (c.doctrine_tags)",
            
            # Citation relationship indexes  
            "CREATE INDEX citation_treatment IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.treatment)",
            "CREATE INDEX citation_strength IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.strength)",
            "CREATE INDEX citation_authority IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.calculated_authority)",
            "CREATE INDEX citation_date IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.created_at)",
            "CREATE INDEX citation_binding IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.binding_precedent)",
            "CREATE INDEX citation_context IF NOT EXISTS FOR ()-[r:CITES]-() ON (r.legal_context)",
            
            # Court indexes
            "CREATE INDEX court_level IF NOT EXISTS FOR (ct:Court) ON (ct.level)",
            "CREATE INDEX court_jurisdiction IF NOT EXISTS FOR (ct:Court) ON (ct.jurisdiction)",
            "CREATE INDEX court_specialty IF NOT EXISTS FOR (ct:Court) ON (ct.subject_specialties)",
            "CREATE INDEX court_authority_weight IF NOT EXISTS FOR (ct:Court) ON (ct.base_authority_weight)",
            
            # Judge indexes
            "CREATE INDEX judge_name IF NOT EXISTS FOR (j:Judge) ON (j.name)",
            "CREATE INDEX judge_tenure IF NOT EXISTS FOR (j:Judge) ON (j.tenure_start, j.tenure_end)",
            "CREATE INDEX judge_ideology IF NOT EXISTS FOR (j:Judge) ON (j.conservative_score)",
            "CREATE INDEX judge_court IF NOT EXISTS FOR (j:Judge) ON (j.current_court)",
            
            # Full-text search indexes
            "CREATE FULLTEXT INDEX legal_content_search IF NOT EXISTS FOR (c:Case) ON EACH [c.case_name, c.summary, c.holding, c.legal_issues]",
            "CREATE FULLTEXT INDEX legal_doctrine_search IF NOT EXISTS FOR (c:Case|s:Statute|lc:LegalConcept) ON EACH [c.doctrine_tags, s.subject_areas, lc.definition]",
            
            # Temporal indexes for legal evolution tracking
            "CREATE INDEX legal_doctrine_evolution IF NOT EXISTS FOR (c:Case) ON (c.doctrine_tags, c.decision_date, c.authority_score)",
            "CREATE INDEX statute_effective_date IF NOT EXISTS FOR (s:Statute) ON (s.effective_date, s.jurisdiction)",
        ]
        
        for index in indexes:
            try:
                await session.run(index)
                logger.debug(f"✅ Created index: {index[:50]}...")
            except Exception as e:
                logger.debug(f"⚠️ Index exists or error: {str(e)[:100]}...")
    
    async def _create_comprehensive_court_hierarchy(self, session):
        """Create comprehensive US court system with authority calculations."""
        court_setup = """
        // US Supreme Court
        MERGE (supreme:Court {
            id: 'us-supreme-court',
            name: 'Supreme Court of the United States',
            short_name: 'SCOTUS',
            level: 'supreme_court',
            jurisdiction: 'US',
            base_authority_weight: 10.0,
            binding_jurisdictions: ['US'],
            persuasive_jurisdictions: ['US'],
            established_date: date('1789-09-24'),
            annual_caseload: 80,
            reversal_rate: 0.0,
            citation_influence: 1.0,
            conservative_score: 0.55,
            precedent_adherence: 0.95
        })
        
        // Federal Circuit Courts with detailed information
        WITH supreme
        UNWIND [
            {id: 'us-ca-1', name: 'United States Court of Appeals for the First Circuit', short: '1st Cir.', 
             jurisdiction: 'US-1', states: ['ME', 'MA', 'NH', 'RI'], caseload: 1200, reversal: 0.12, 
             conservative: 0.42, citations: 0.75},
            {id: 'us-ca-2', name: 'United States Court of Appeals for the Second Circuit', short: '2nd Cir.',
             jurisdiction: 'US-2', states: ['CT', 'NY', 'VT'], caseload: 1800, reversal: 0.15,
             conservative: 0.38, citations: 0.85},
            {id: 'us-ca-3', name: 'United States Court of Appeals for the Third Circuit', short: '3rd Cir.',
             jurisdiction: 'US-3', states: ['DE', 'NJ', 'PA'], caseload: 1400, reversal: 0.13,
             conservative: 0.48, citations: 0.78},
            {id: 'us-ca-4', name: 'United States Court of Appeals for the Fourth Circuit', short: '4th Cir.',
             jurisdiction: 'US-4', states: ['MD', 'NC', 'SC', 'VA', 'WV'], caseload: 1600, reversal: 0.11,
             conservative: 0.62, citations: 0.72},
            {id: 'us-ca-5', name: 'United States Court of Appeals for the Fifth Circuit', short: '5th Cir.',
             jurisdiction: 'US-5', states: ['LA', 'MS', 'TX'], caseload: 2200, reversal: 0.09,
             conservative: 0.71, citations: 0.68},
            {id: 'us-ca-6', name: 'United States Court of Appeals for the Sixth Circuit', short: '6th Cir.',
             jurisdiction: 'US-6', states: ['KY', 'MI', 'OH', 'TN'], caseload: 1900, reversal: 0.14,
             conservative: 0.58, citations: 0.74},
            {id: 'us-ca-7', name: 'United States Court of Appeals for the Seventh Circuit', short: '7th Cir.',
             jurisdiction: 'US-7', states: ['IL', 'IN', 'WI'], caseload: 1300, reversal: 0.10,
             conservative: 0.51, citations: 0.81},
            {id: 'us-ca-8', name: 'United States Court of Appeals for the Eighth Circuit', short: '8th Cir.',
             jurisdiction: 'US-8', states: ['AR', 'IA', 'MN', 'MO', 'NE', 'ND', 'SD'], caseload: 1100, reversal: 0.08,
             conservative: 0.66, citations: 0.69},
            {id: 'us-ca-9', name: 'United States Court of Appeals for the Ninth Circuit', short: '9th Cir.',
             jurisdiction: 'US-9', states: ['AK', 'AZ', 'CA', 'HI', 'ID', 'MT', 'NV', 'OR', 'WA'], caseload: 4500, reversal: 0.78,
             conservative: 0.31, citations: 0.88},
            {id: 'us-ca-10', name: 'United States Court of Appeals for the Tenth Circuit', short: '10th Cir.',
             jurisdiction: 'US-10', states: ['CO', 'KS', 'NM', 'OK', 'UT', 'WY'], caseload: 1000, reversal: 0.12,
             conservative: 0.59, citations: 0.71},
            {id: 'us-ca-11', name: 'United States Court of Appeals for the Eleventh Circuit', short: '11th Cir.',
             jurisdiction: 'US-11', states: ['AL', 'FL', 'GA'], caseload: 2000, reversal: 0.13,
             conservative: 0.64, citations: 0.73},
            {id: 'us-ca-dc', name: 'United States Court of Appeals for the District of Columbia Circuit', short: 'D.C. Cir.',
             jurisdiction: 'US-DC', states: ['DC'], caseload: 800, reversal: 0.20,
             conservative: 0.47, citations: 0.92},
            {id: 'us-ca-fc', name: 'United States Court of Appeals for the Federal Circuit', short: 'Fed. Cir.',
             jurisdiction: 'US-FC', states: [], caseload: 1200, reversal: 0.16,
             conservative: 0.53, citations: 0.79}
        ] AS court_data
        
        MERGE (appellate:Court {
            id: court_data.id,
            name: court_data.name,
            short_name: court_data.short,
            level: 'appellate',
            jurisdiction: court_data.jurisdiction,
            base_authority_weight: 8.0,
            binding_jurisdictions: [court_data.jurisdiction],
            persuasive_jurisdictions: ['US'],
            geographic_scope: court_data.states,
            annual_caseload: court_data.caseload,
            reversal_rate: court_data.reversal,
            citation_influence: court_data.citations,
            conservative_score: court_data.conservative,
            precedent_adherence: 0.85
        })
        
        MERGE (appellate)-[:APPEALS_TO {
            appeal_type: 'direct',
            established: date('1891-03-03')
        }]->(supreme)
        """
        
        try:
            await session.run(court_setup)
            logger.info("✅ Created comprehensive court hierarchy")
        except Exception as e:
            logger.error(f"❌ Error creating court hierarchy: {e}")
    
    async def _create_citation_treatment_system(self, session):
        """Set up sophisticated citation treatment classification."""
        treatment_setup = """
        // Create citation treatment reference data
        MERGE (treatments:CitationTreatments {
            positive_treatments: [
                {type: 'follows', weight: 1.0, description: 'Directly follows precedent'},
                {type: 'affirmed', weight: 1.0, description: 'Appellate affirmance'},
                {type: 'explained', weight: 0.8, description: 'Clarifies holding'},
                {type: 'harmonized', weight: 0.7, description: 'Reconciles with other precedent'},
                {type: 'expanded', weight: 0.9, description: 'Extends holding to new facts'}
            ],
            neutral_treatments: [
                {type: 'cited', weight: 0.5, description: 'General citation'},
                {type: 'discussed', weight: 0.5, description: 'Analytical discussion'},
                {type: 'mentioned', weight: 0.3, description: 'Passing reference'},
                {type: 'compared', weight: 0.4, description: 'Factual comparison'}
            ],
            negative_treatments: [
                {type: 'distinguished', weight: -0.3, description: 'Limited to specific facts'},
                {type: 'questioned', weight: -0.5, description: 'Casts doubt on reasoning'},
                {type: 'criticized', weight: -0.7, description: 'Direct criticism'},
                {type: 'limited', weight: -0.6, description: 'Scope narrowed'},
                {type: 'overruled', weight: -1.0, description: 'Explicitly overturned'},
                {type: 'superseded', weight: -0.9, description: 'Replaced by statute/rule'}
            ]
        })
        """
        
        try:
            await session.run(treatment_setup)
            logger.info("✅ Created citation treatment system")
        except Exception as e:
            logger.error(f"❌ Error creating citation treatments: {e}")
    
    async def _create_authority_calculation_functions(self, session):
        """Create stored procedures for authority calculations."""
        # Note: In a real implementation, these would be more complex procedures
        # For now, we'll create example calculations in Cypher
        
        authority_functions = [
            """
            // Function to calculate jurisdictional authority
            CREATE OR REPLACE FUNCTION calculate_jurisdictional_authority(citing_jurisdiction STRING, cited_jurisdiction STRING, binding_jurisdictions LIST<STRING>, persuasive_jurisdictions LIST<STRING>) 
            RETURNS FLOAT
            LANGUAGE cypher AS $$
                RETURN CASE 
                    WHEN cited_jurisdiction IN binding_jurisdictions THEN 1.0
                    WHEN cited_jurisdiction IN persuasive_jurisdictions THEN 0.6
                    ELSE 0.3
                END
            $$
            """,
            """
            // Function to calculate temporal authority (decay over time)
            CREATE OR REPLACE FUNCTION calculate_temporal_authority(decision_date DATE)
            RETURNS FLOAT
            LANGUAGE cypher AS $$
                WITH duration.between(decision_date, date()).years AS years_ago
                RETURN CASE 
                    WHEN years_ago <= 5 THEN 1.0
                    WHEN years_ago <= 10 THEN 0.8
                    WHEN years_ago <= 20 THEN 0.6
                    ELSE 0.4
                END
            $$
            """
        ]
        
        # Note: Neo4j user-defined functions require Neo4j Enterprise
        # For community edition, we'll use inline calculations in queries
        logger.info("✅ Authority calculation functions prepared")
    
    async def _create_legal_sample_data(self, session):
        """Create realistic legal sample data for development and testing."""
        sample_data = """
        // Constitutional Law Landmark Cases
        
        // Brown v. Board - Overrules Plessy
        MERGE (brown:Case {
            id: 'brown-v-board-1954',
            citation: '347 U.S. 483 (1954)',
            case_name: 'Brown v. Board of Education of Topeka',
            decision_date: date('1954-05-17'),
            jurisdiction: 'US',
            practice_areas: ['constitutional_law', 'civil_rights', 'education'],
            holding: 'Separate educational facilities are inherently unequal and violate the Equal Protection Clause',
            summary: 'Unanimous Supreme Court decision that declared state laws establishing separate public schools for black and white students to be unconstitutional',
            authority_score: 9.8,
            landmark_case: true,
            good_law_status: 'good_law',
            doctrine_tags: ['equal_protection', 'separate_but_equal', 'education_rights', 'racial_discrimination'],
            legal_issues: ['Equal Protection Clause interpretation', 'Separate but equal doctrine', 'Educational segregation'],
            procedural_history: 'Consolidated cases from Kansas, South Carolina, Virginia, and Delaware',
            key_facts: 'Black children denied admission to public schools attended by white children under laws requiring racial segregation'
        })
        
        MERGE (plessy:Case {
            id: 'plessy-v-ferguson-1896',
            citation: '163 U.S. 537 (1896)',
            case_name: 'Plessy v. Ferguson', 
            decision_date: date('1896-05-18'),
            jurisdiction: 'US',
            practice_areas: ['constitutional_law', 'civil_rights', 'transportation'],
            holding: 'Separate but equal facilities are constitutional under the Equal Protection Clause',
            summary: 'Supreme Court decision upholding the constitutionality of racial segregation laws for public facilities',
            authority_score: 8.5,
            landmark_case: true,
            good_law_status: 'overruled',
            overruled_by: 'brown-v-board-1954',
            doctrine_tags: ['equal_protection', 'separate_but_equal', 'racial_segregation'],
            legal_issues: ['Equal Protection Clause', 'State police powers', 'Racial classification'],
            key_facts: 'Homer Plessy, 7/8 Caucasian, sat in whites-only railroad car in violation of Louisiana law'
        })
        
        // Citation relationship showing doctrinal evolution
        MERGE (brown)-[cite_plessy:CITES {
            treatment: 'overruled',
            strength: 1.0,
            certainty: 1.0,
            legal_context: 'constitutional_law',
            doctrine: 'equal_protection',
            holding_type: 'ratio',
            created_at: datetime('1954-05-17T00:00:00'),
            binding_precedent: true,
            jurisdictional_authority: 1.0,
            temporal_weight: 1.0,
            calculated_authority: 9.8,
            page_references: ['494-495'],
            quotation_length: 0,
            signal_phrase: 'We conclude that',
            parenthetical: 'overruling the separate but equal doctrine established in Plessy',
            procedural_posture: 'direct_appeal',
            outcome_alignment: false
        }]->(plessy)
        
        // Miranda v. Arizona - Criminal Procedure
        MERGE (miranda:Case {
            id: 'miranda-v-arizona-1966',
            citation: '384 U.S. 436 (1966)',
            case_name: 'Miranda v. Arizona',
            decision_date: date('1966-06-13'),
            jurisdiction: 'US',
            practice_areas: ['criminal_law', 'constitutional_law', 'procedure'],
            holding: 'Individuals must be informed of their constitutional rights before custodial interrogation',
            summary: 'Established requirement for police to inform suspects of their rights before interrogation',
            authority_score: 9.5,
            landmark_case: true,
            good_law_status: 'good_law',
            doctrine_tags: ['fifth_amendment', 'self_incrimination', 'due_process', 'custodial_interrogation'],
            legal_issues: ['Fifth Amendment privilege against self-incrimination', 'Sixth Amendment right to counsel'],
            key_facts: 'Ernesto Miranda confessed to crimes without being informed of his constitutional rights'
        })
        
        // Roe v. Wade - Privacy Rights  
        MERGE (roe:Case {
            id: 'roe-v-wade-1973',
            citation: '410 U.S. 113 (1973)',
            case_name: 'Roe v. Wade',
            decision_date: date('1973-01-22'),
            jurisdiction: 'US',
            practice_areas: ['constitutional_law', 'privacy_rights', 'reproductive_rights'],
            holding: 'Right to privacy under Due Process Clause extends to abortion decisions',
            summary: 'Established constitutional right to abortion under privacy doctrine',
            authority_score: 9.3,
            landmark_case: true,
            good_law_status: 'overruled',
            overruled_by: 'dobbs-v-jackson-2022',
            doctrine_tags: ['substantive_due_process', 'privacy_rights', 'reproductive_autonomy'],
            legal_issues: ['Fourteenth Amendment Due Process', 'Right to privacy', 'State regulation of abortion']
        })
        
        // Dobbs v. Jackson - Overrules Roe
        MERGE (dobbs:Case {
            id: 'dobbs-v-jackson-2022',
            citation: '597 U.S. ___ (2022)',
            case_name: 'Dobbs v. Jackson Women\\'s Health Organization',
            decision_date: date('2022-06-24'),
            jurisdiction: 'US',
            practice_areas: ['constitutional_law', 'reproductive_rights', 'federalism'],
            holding: 'Constitution does not confer right to abortion; authority returned to states',
            summary: 'Overturned Roe v. Wade and Planned Parenthood v. Casey, returning abortion regulation to states',
            authority_score: 9.1,
            landmark_case: true,
            good_law_status: 'good_law',
            doctrine_tags: ['substantive_due_process', 'federalism', 'constitutional_interpretation'],
            legal_issues: ['Substantive due process limits', 'Historical constitutional interpretation', 'State sovereignty']
        })
        
        // Create courts for these cases
        MERGE (scotus:Court {id: 'us-supreme-court'})
        
        // Associate cases with courts
        MERGE (brown)-[:DECIDED_BY]->(scotus)
        MERGE (plessy)-[:DECIDED_BY]->(scotus)
        MERGE (miranda)-[:DECIDED_BY]->(scotus)
        MERGE (roe)-[:DECIDED_BY]->(scotus)
        MERGE (dobbs)-[:DECIDED_BY]->(scotus)
        
        // Dobbs overrules Roe
        MERGE (dobbs)-[cite_roe:CITES {
            treatment: 'overruled',
            strength: 1.0,
            certainty: 1.0,
            legal_context: 'constitutional_law',
            doctrine: 'substantive_due_process',
            holding_type: 'ratio',
            created_at: datetime('2022-06-24T00:00:00'),
            binding_precedent: true,
            calculated_authority: 9.1,
            page_references: ['8-32'],
            signal_phrase: 'We therefore hold',
            parenthetical: 'overruling Roe and Casey',
            doctrinal_shift: 'paradigm_change'
        }]->(roe)
        """
        
        try:
            await session.run(sample_data)
            logger.info("✅ Created legal sample data")
        except Exception as e:
            logger.error(f"❌ Error creating sample data: {e}")
    
    async def _setup_graph_projections(self, session):
        """Set up graph algorithm projections for legal analysis."""
        projections = [
            """
            // Create legal authority network projection
            CALL gds.graph.project.cypher(
                'legal-authority-network',
                'MATCH (c:Case) RETURN id(c) AS id, c.authority_score AS authority_score, c.decision_date AS decision_date',
                'MATCH (c1:Case)-[r:CITES]->(c2:Case) RETURN id(c1) AS source, id(c2) AS target, r.calculated_authority AS weight, r.treatment AS treatment',
                {validateRelationships: false}
            )
            """,
            """
            // Create citation treatment network  
            CALL gds.graph.project.cypher(
                'citation-treatment-network',
                'MATCH (c:Case) RETURN id(c) AS id, c.good_law_status AS status',
                'MATCH (c1:Case)-[r:CITES]->(c2:Case) WHERE r.treatment IN ["follows", "explained", "affirmed"] RETURN id(c1) AS source, id(c2) AS target, 1.0 AS weight'
            )
            """
        ]
        
        for projection in projections:
            try:
                await session.run(projection)
                logger.info(f"✅ Created graph projection")
            except Exception as e:
                logger.warning(f"⚠️ Graph projection exists or error: {str(e)[:100]}...")
    
    def close(self):
        """Close the database connection."""
        self.driver.close()


# Enhanced query library for sophisticated legal research
ENHANCED_LEGAL_QUERIES = {
    "find_authoritative_precedents": """
        // Find authoritative precedents with sophisticated relevance scoring
        MATCH (query_case:Case {id: $case_id})
        CALL {
            WITH query_case
            MATCH (query_case)-[:CITES*1..3]-(related:Case)
            WHERE related <> query_case 
                AND related.jurisdiction IN $target_jurisdictions
                AND any(area IN related.practice_areas WHERE area IN $practice_areas)
                AND related.good_law_status = 'good_law'
            
            // Calculate relevance score
            WITH related,
                CASE WHEN related.landmark_case THEN 1.5 ELSE 1.0 END as landmark_boost,
                CASE WHEN size([area IN related.practice_areas WHERE area IN $practice_areas]) > 1 
                     THEN 1.2 ELSE 1.0 END as practice_area_match,
                CASE WHEN related.jurisdiction = $primary_jurisdiction THEN 1.3 ELSE 1.0 END as jurisdiction_boost
            
            RETURN related, 
                related.authority_score * landmark_boost * practice_area_match * jurisdiction_boost AS relevance_score
            ORDER BY relevance_score DESC
            LIMIT 25
        }
        RETURN related, relevance_score
        ORDER BY relevance_score DESC
    """,
    
    "analyze_citation_treatment": """
        // Analyze how a case has been treated by subsequent courts
        MATCH (target:Case {id: $case_id})<-[citations:CITES]-(citing:Case)
        MATCH (citing)-[:DECIDED_BY]->(citing_court:Court)
        
        WITH target, citations, citing, citing_court,
            CASE citations.treatment
                WHEN 'follows' THEN 1.0
                WHEN 'explained' THEN 0.8
                WHEN 'affirmed' THEN 1.0
                WHEN 'distinguished' THEN -0.3
                WHEN 'questioned' THEN -0.5
                WHEN 'criticized' THEN -0.7
                WHEN 'overruled' THEN -1.0
                ELSE 0.0
            END as treatment_impact
        
        RETURN {
            case: target,
            total_citations: count(citations),
            positive_citations: count(CASE WHEN treatment_impact > 0 THEN 1 END),
            negative_citations: count(CASE WHEN treatment_impact < 0 THEN 1 END),
            neutral_citations: count(CASE WHEN treatment_impact = 0 THEN 1 END),
            weighted_authority_impact: sum(treatment_impact * citing_court.base_authority_weight),
            good_law_confidence: 
                CASE WHEN sum(treatment_impact * citing_court.base_authority_weight) > 0 
                     THEN 'strong' 
                     WHEN sum(treatment_impact * citing_court.base_authority_weight) < -2
                     THEN 'questionable'
                     ELSE 'moderate' 
                END,
            recent_citations: collect({
                date: citing.decision_date,
                treatment: citations.treatment,
                court: citing_court.short_name,
                case_name: citing.case_name
            })[0..10]
        } AS treatment_analysis
        ORDER BY citing.decision_date DESC
    """,
    
    "calculate_legal_authority_pagerank": """
        // Run PageRank with legal domain weighting
        CALL gds.pageRank.write(
            'legal-authority-network',
            {
                writeProperty: 'legal_pagerank_score',
                relationshipWeightProperty: 'weight',
                dampingFactor: 0.85,
                tolerance: 0.0000001,
                maxIterations: 100
            }
        )
        YIELD nodePropertiesWritten, ranIterations, didConverge
        RETURN nodePropertiesWritten, ranIterations, didConverge
    """,
    
    "find_doctrinal_evolution": """
        // Track evolution of legal doctrines through citation chains
        MATCH (foundational:Case)-[r:CITES*1..5]->(modern:Case)
        WHERE foundational.landmark_case = true
            AND any(doctrine IN $doctrine_tags WHERE doctrine IN foundational.doctrine_tags)
            AND modern.decision_date > foundational.decision_date
            AND all(rel IN r WHERE rel.treatment IN ['follows', 'explained', 'expanded'])
        
        WITH foundational, modern, r,
            [rel IN r WHERE rel.treatment = 'expanded'] AS expansions,
            [rel IN r WHERE rel.treatment = 'explained'] AS explanations
        
        RETURN {
            foundational_case: foundational.case_name,
            modern_case: modern.case_name,
            evolution_path_length: length(r),
            doctrinal_expansions: size(expansions),
            clarifications: size(explanations),
            time_span: duration.between(foundational.decision_date, modern.decision_date).years,
            doctrine_stability: 
                CASE WHEN size(expansions) > size(explanations) 
                     THEN 'expanding' 
                     ELSE 'stable' 
                END
        } AS doctrine_evolution
        ORDER BY time_span DESC
    """,
    
    "good_law_verification": """
        // Verify if a case is still good law
        MATCH (case:Case {id: $case_id})
        OPTIONAL MATCH (case)<-[negative:CITES]-(citing:Case)
        WHERE negative.treatment IN ['overruled', 'superseded', 'questioned', 'criticized']
        
        OPTIONAL MATCH (case)<-[positive:CITES]-(citing_positive:Case)
        WHERE positive.treatment IN ['follows', 'affirmed', 'explained']
        
        WITH case,
            count(negative) AS negative_treatments,
            count(positive) AS positive_treatments,
            collect(CASE WHEN negative.treatment = 'overruled' THEN citing END) AS overruling_cases
        
        RETURN {
            case_id: case.id,
            case_name: case.case_name,
            current_status: case.good_law_status,
            negative_treatment_count: negative_treatments,
            positive_treatment_count: positive_treatments,
            overruled_by: [c IN overruling_cases WHERE c IS NOT NULL | c.case_name],
            good_law_confidence: 
                CASE 
                    WHEN size([c IN overruling_cases WHERE c IS NOT NULL]) > 0 THEN 'overruled'
                    WHEN negative_treatments > positive_treatments * 2 THEN 'questionable'
                    WHEN positive_treatments > negative_treatments THEN 'strong'
                    ELSE 'moderate'
                END,
            last_verification: datetime()
        } AS verification_result
    """
}