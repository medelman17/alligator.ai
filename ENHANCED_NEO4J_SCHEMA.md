# Enhanced Neo4j Legal Schema Design

## Overview
This document outlines the enhanced Neo4j schema design for alligator.ai's legal citation network, building on the existing foundation to support sophisticated legal research workflows.

## Core Enhancements Needed

### 1. Citation Treatment Sophistication

#### Current Schema Issues:
- Basic `treatment` property without legal domain specificity
- No support for citation strength or context
- Missing temporal and jurisdictional factors

#### Enhanced Citation Relationships:
```cypher
// Enhanced CITES relationship with legal sophistication
(citing:Case)-[r:CITES {
  // Core Treatment Classification
  treatment: "follows",                    // Legal treatment type
  strength: 0.85,                         // Citation strength (0-1)
  certainty: 0.9,                         // Court's certainty in treatment
  
  // Legal Context
  legal_context: "constitutional_law",     // Domain of citation
  doctrine: "due_process",                // Specific legal doctrine
  holding_type: "ratio",                 // ratio vs obiter dicta
  
  // Citation Details
  page_references: ["123", "125-127"],    // Specific page citations
  quotation_length: 45,                  // Length of quoted text
  signal_phrase: "In accordance with",    // How citation introduced
  parenthetical: "holding that...",       // Explanatory parenthetical
  
  // Temporal & Procedural
  created_at: datetime(),                // When citation created
  procedural_posture: "appeal",          // Context of citation
  outcome_alignment: true,               // Did courts reach same outcome
  
  // Authority Factors
  binding_precedent: true,               // Binding vs persuasive
  jurisdiction_match: 0.8,               // Jurisdictional alignment (0-1)
  temporal_weight: 0.9,                  // Temporal relevance (0-1)
}]->(cited:Case)
```

#### Legal Treatment Types:
```cypher
// Positive Treatments (strengthen authority)
"follows"           // 1.0  - Directly follows precedent
"affirmed"          // 1.0  - Appellate affirmance
"explained"         // 0.8  - Clarifies holding
"harmonized"        // 0.7  - Reconciles with other precedent
"expanded"          // 0.9  - Extends holding to new facts

// Neutral Treatments (information only)
"cited"             // 0.5  - General citation
"discussed"         // 0.5  - Analytical discussion
"mentioned"         // 0.3  - Passing reference
"compared"          // 0.4  - Factual comparison

// Negative Treatments (weaken authority)
"distinguished"     // -0.3 - Limited to specific facts
"questioned"        // -0.5 - Casts doubt on reasoning
"criticized"        // -0.7 - Direct criticism
"limited"           // -0.6 - Scope narrowed
"overruled"         // -1.0 - Explicitly overturned
"superseded"        // -0.9 - Replaced by statute/rule
```

### 2. Enhanced Court Hierarchy with Legal Authority

#### Current Issues:
- Simple authority weights (8.0, 10.0)
- No jurisdiction-specific authority
- Missing specialized courts

#### Enhanced Court Model:
```cypher
// Enhanced Court properties
CREATE (court:Court {
  id: "us-ca-9",
  name: "United States Court of Appeals for the Ninth Circuit",
  short_name: "9th Cir.",
  
  // Hierarchy & Authority
  level: "appellate",                    // supreme_court, appellate, district, state_supreme, etc.
  base_authority_weight: 8.0,           // Base authority score
  jurisdiction: "US-9",                 // Jurisdictional scope
  binding_jurisdictions: ["US-9"],      // Where decisions are binding
  persuasive_jurisdictions: ["US"],     // Where decisions are persuasive
  
  // Specialization
  subject_specialties: ["immigration", "environmental"], // Specialized subjects
  specialty_weight_boost: 1.2,          // Authority boost in specialty areas
  
  // Geographic & Temporal
  geographic_scope: ["CA", "OR", "WA", "AK", "HI", "NV", "ID", "MT", "AZ"],
  established_date: date("1891-03-03"),
  
  // Caseload & Efficiency
  annual_caseload: 4500,                // Cases per year
  reversal_rate: 0.78,                  // Rate of reversals by SCOTUS
  citation_influence: 0.85,             // How often cited by other courts
  
  // Judicial Philosophy Metrics
  conservative_score: 0.45,             // Liberal-conservative scale (0-1)
  precedent_adherence: 0.8,             // Stare decisis strength (0-1)
  statutory_interpretation: "textualist" // Interpretive methodology
})
```

#### Authority Calculation Algorithm:
```cypher
// Dynamic authority calculation considering multiple factors
MATCH (citing:Case)-[r:CITES]->(cited:Case)
MATCH (citing)-[:DECIDED_BY]->(citing_court:Court)
MATCH (cited)-[:DECIDED_BY]->(cited_court:Court)

// Calculate jurisdictional authority
WITH *,
CASE 
  WHEN cited_court.jurisdiction IN citing_court.binding_jurisdictions THEN 1.0
  WHEN cited_court.jurisdiction IN citing_court.persuasive_jurisdictions THEN 0.6
  ELSE 0.3
END as jurisdictional_authority,

// Calculate temporal authority (decay over time)
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
  WHEN cited_court.level = cited_court.level THEN 0.7
  ELSE 0.5
END as hierarchical_authority

// Set comprehensive authority score
SET r.calculated_authority = 
  cited_court.base_authority_weight * 
  jurisdictional_authority * 
  temporal_authority * 
  hierarchical_authority * 
  r.strength
```

### 3. Advanced Performance Indexes for Legal Research

#### Composite Indexes for Legal Query Patterns:
```cypher
// Multi-dimensional legal research indexes
CREATE INDEX case_research_composite IF NOT EXISTS 
FOR (c:Case) ON (c.jurisdiction, c.practice_areas, c.authority_score, c.decision_date)

CREATE INDEX citation_authority_composite IF NOT EXISTS 
FOR ()-[r:CITES]-() ON (r.treatment, r.calculated_authority, r.binding_precedent)

CREATE INDEX court_authority_composite IF NOT EXISTS 
FOR (ct:Court) ON (ct.level, ct.jurisdiction, ct.base_authority_weight)

// Legal doctrine evolution tracking
CREATE INDEX doctrine_evolution IF NOT EXISTS 
FOR (c:Case) ON (c.doctrine_tags, c.decision_date, c.authority_score)

// Good law verification index
CREATE INDEX case_status_verification IF NOT EXISTS 
FOR (c:Case) ON (c.good_law_status, c.last_status_check, c.jurisdiction)
```

#### Full-Text Search for Legal Content:
```cypher
// Enhanced full-text indexes for legal research
CREATE FULLTEXT INDEX legal_content_search IF NOT EXISTS
FOR (c:Case) ON EACH [
  c.case_name, 
  c.summary, 
  c.holding, 
  c.legal_issues,
  c.procedural_history,
  c.key_facts
]

CREATE FULLTEXT INDEX legal_doctrine_search IF NOT EXISTS  
FOR (c:Case|s:Statute|lc:LegalConcept) ON EACH [
  c.doctrine_tags,
  s.subject_areas, 
  lc.definition
]
```

### 4. Real-World Legal Sample Data

#### Sample Citation Network with Legal Complexity:
```cypher
// Constitutional Law Citation Chain
MERGE (brown:Case {
  id: "brown-v-board-1954",
  citation: "347 U.S. 483 (1954)",
  case_name: "Brown v. Board of Education",
  decision_date: date("1954-05-17"),
  jurisdiction: "US",
  practice_areas: ["constitutional_law", "civil_rights", "education"],
  holding: "Separate educational facilities are inherently unequal",
  authority_score: 9.8,
  landmark_case: true,
  good_law_status: "good_law",
  doctrine_tags: ["equal_protection", "separate_but_equal", "education_rights"]
})

MERGE (plessy:Case {
  id: "plessy-v-ferguson-1896", 
  citation: "163 U.S. 537 (1896)",
  case_name: "Plessy v. Ferguson",
  decision_date: date("1896-05-18"),
  jurisdiction: "US",
  practice_areas: ["constitutional_law", "civil_rights"],
  holding: "Separate but equal facilities are constitutional",
  authority_score: 8.5,
  landmark_case: true,
  good_law_status: "overruled",
  overruled_by: "brown-v-board-1954",
  doctrine_tags: ["equal_protection", "separate_but_equal"]
})

// Citation relationship showing doctrinal evolution
MERGE (brown)-[r:CITES {
  treatment: "overruled",
  strength: 1.0,
  certainty: 1.0,
  legal_context: "constitutional_law",
  doctrine: "equal_protection",
  holding_type: "ratio",
  created_at: datetime("1954-05-17T00:00:00"),
  binding_precedent: true,
  jurisdictional_authority: 1.0,
  temporal_weight: 1.0,
  calculated_authority: 9.8,
  doctrinal_shift: "paradigm_change",
  quotation_length: 0,
  signal_phrase: "We conclude that",
  parenthetical: "overruling the separate but equal doctrine"
}]->(plessy)
```

### 5. Legal Research Query Optimizations

#### Precedent Discovery with Authority Weighting:
```cypher
// Find authoritative precedents with sophisticated relevance scoring
MATCH (query_case:Case {id: $case_id})
CALL {
  WITH query_case
  MATCH (query_case)-[:CITES*1..3]-(related:Case)
  WHERE related <> query_case 
    AND related.jurisdiction IN $target_jurisdictions
    AND any(area IN related.practice_areas WHERE area IN $practice_areas)
    AND related.good_law_status = "good_law"
  
  // Calculate relevance score
  WITH related,
    CASE WHEN related.landmark_case THEN 1.5 ELSE 1.0 END as landmark_boost,
    CASE WHEN size([area IN related.practice_areas WHERE area IN $practice_areas]) > 1 
         THEN 1.2 ELSE 1.0 END as practice_area_match,
    CASE WHEN related.jurisdiction = $primary_jurisdiction THEN 1.3 ELSE 1.0 END as jurisdiction_boost
  
  SET related.relevance_score = 
    related.authority_score * 
    landmark_boost * 
    practice_area_match * 
    jurisdiction_boost
  
  RETURN related
  ORDER BY related.relevance_score DESC
  LIMIT 25
}
RETURN related, related.relevance_score
```

#### Citation Treatment Analysis:
```cypher
// Analyze how a case has been treated by subsequent courts
MATCH (target:Case {id: $case_id})<-[citations:CITES]-(citing:Case)
MATCH (citing)-[:DECIDED_BY]->(citing_court:Court)

WITH target, citations, citing, citing_court,
  CASE citations.treatment
    WHEN 'follows' THEN 1.0
    WHEN 'explained' THEN 0.8
    WHEN 'distinguished' THEN -0.3
    WHEN 'questioned' THEN -0.5
    WHEN 'overruled' THEN -1.0
    ELSE 0.0
  END as treatment_impact

RETURN {
  case: target,
  positive_citations: count(CASE WHEN treatment_impact > 0 THEN 1 END),
  negative_citations: count(CASE WHEN treatment_impact < 0 THEN 1 END),
  neutral_citations: count(CASE WHEN treatment_impact = 0 THEN 1 END),
  weighted_authority_impact: sum(treatment_impact * citing_court.base_authority_weight),
  good_law_confidence: 
    CASE WHEN sum(treatment_impact * citing_court.base_authority_weight) > 0 
         THEN 'strong' 
         ELSE 'questionable' 
    END,
  most_authoritative_citing_court: citing_court.name,
  recent_treatment_trend: collect({
    date: citing.decision_date,
    treatment: citations.treatment,
    court: citing_court.short_name
  })[0..5]
}
ORDER BY citing.decision_date DESC
```

### 6. Graph Algorithm Enhancements

#### Legal Authority PageRank:
```cypher
// Create projection with legal authority weighting
CALL gds.graph.project(
  'legal-authority-network',
  ['Case'],
  ['CITES'],
  {
    nodeProperties: ['authority_score', 'decision_date'],
    relationshipProperties: ['calculated_authority', 'temporal_weight']
  }
)

// Run PageRank with legal domain weighting
CALL gds.pageRank.write(
  'legal-authority-network',
  {
    writeProperty: 'legal_pagerank_score',
    relationshipWeightProperty: 'calculated_authority',
    dampingFactor: 0.85,
    tolerance: 0.0000001,
    maxIterations: 100
  }
)
YIELD nodePropertiesWritten, ranIterations, didConverge
```

## Implementation Priority

### Phase 1: Core Enhancements (Immediate)
1. ✅ Enhanced citation treatment types and properties
2. ✅ Advanced authority calculation algorithms  
3. ✅ Performance indexes for legal research patterns
4. ✅ Good law verification system

### Phase 2: Data Quality (Next)
1. Real legal sample data with citation chains
2. Court hierarchy with all federal and state courts
3. Legal doctrine tagging and evolution tracking
4. Cross-jurisdictional influence analysis

### Phase 3: Advanced Features (Future)
1. Predictive authority scoring using ML
2. Automated citation treatment classification
3. Real-time good law verification
4. Judge behavioral pattern analysis