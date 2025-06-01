# ADR-004: Data Flow and Storage Strategy

## Status
Proposed

## Context
We need to design how legal document data flows through our ingestion pipeline and how different stages of processing are stored. Key considerations include eventual consistency, data versioning, deduplication, and integration with our existing enhanced legal research capabilities.

## Questions to Address

### 1. Duplicate Handling and Updates
**Question**: How do we handle duplicates and updates to existing cases?

**Duplicate Detection Scenarios**:
- **Exact Duplicates**: Same document from same source (re-ingestion)
- **Source Variants**: Same case from different sources (CourtListener vs Justia)
- **Version Updates**: Updated/corrected versions of previously ingested documents
- **Citation Variants**: Different citation formats for same case

**Detection Strategies**:
- **Primary Key Matching**: Use normalized citation as primary identifier
- **Content Fingerprinting**: Hash-based duplicate detection on document text
- **Fuzzy Matching**: Similarity algorithms for case names and parties
- **Cross-Reference Validation**: Check against existing case database

**Update Handling Options**:
- **Versioning**: Keep all versions with timestamps
- **Overwrite**: Replace older version with newer data
- **Merge**: Combine data from multiple sources intelligently
- **Manual Review**: Flag conflicts for human decision

### 2. Raw vs Processed Data Storage
**Question**: Should we store raw ingested data separately from our processed/enhanced data?

**Storage Layer Architecture Options**:

**Option A: Single Storage with Processing Flags**
```
Neo4j: Cases with processing_status, source_metadata
ChromaDB: Enhanced embeddings only
Pros: Simple, unified query interface
Cons: Raw data mixed with enhanced data
```

**Option B: Separate Raw and Enhanced Storage**
```
Raw Storage: Original documents from sources
Enhanced Storage: Processed, analyzed, integrated data
Processing Pipeline: Raw → Enhanced with clear lineage
Pros: Clean separation, reprocessing capability
Cons: Additional complexity, data synchronization
```

**Option C: Staging Pipeline**
```
Ingestion DB → Processing Queue → Enhanced DB
Temporary staging for validation and enhancement
Pros: Quality control, batch processing efficiency
Cons: More moving parts, potential data lag
```

### 3. Data Versioning Strategy
**Question**: What's our versioning strategy for legal documents that change over time?

**Versioning Challenges**:
- **Document Updates**: Corrections, additions, or clarifications to existing cases
- **Processing Evolution**: Improved LLM analysis of previously ingested documents
- **Schema Changes**: Enhanced legal research schema updates
- **Source Changes**: Updates from CourtListener or other data providers

**Versioning Approaches**:
- **Immutable Events**: Store all changes as events, current state derived
- **Version Numbers**: Explicit versioning with v1, v2, etc.
- **Temporal Tables**: Database-level versioning with valid time ranges
- **Content-Addressed Storage**: Hash-based versioning of document content

### 4. Integration with Sample Data
**Question**: How do we handle the relationship between ingested cases and our existing sample data?

**Sample Data Challenges**:
- **Overlap Detection**: Ingested cases that match our sample cases
- **Authority Conflicts**: Different authority scores from different sources
- **Citation Relationships**: Merging citation networks from ingested and sample data
- **Quality Differences**: Sample data is curated, ingested data may be inconsistent

**Integration Strategies**:
- **Namespace Separation**: Keep sample and ingested data separate
- **Smart Merging**: Detect and merge overlapping cases intelligently
- **Source Priority**: Establish precedence rules (manual curation > CourtListener)
- **Migration Path**: Gradually replace sample data with real ingested data

## Decision Points Needed

### Data Architecture
1. **Storage Separation**: How to separate concerns between raw ingestion and enhanced processing
2. **Schema Design**: What metadata to track for ingestion, processing, and lineage
3. **Consistency Model**: Eventual consistency vs strong consistency requirements
4. **Query Patterns**: How users will access both raw and enhanced data

### Processing Pipeline
1. **Stage Boundaries**: Clear handoff points between ingestion stages
2. **Error Recovery**: How to replay/reprocess failed ingestion jobs
3. **Backpressure**: How to handle processing bottlenecks
4. **Monitoring**: Visibility into data flow and processing status

### Data Quality and Lineage
1. **Provenance Tracking**: Complete audit trail from source to enhanced analysis
2. **Quality Metrics**: Storage and tracking of data quality assessments
3. **Processing History**: Record of all transformations and enhancements
4. **Rollback Capability**: Ability to revert problematic changes

## Technical Architecture Proposal

### Data Flow Pipeline
```
1. Source APIs (CourtListener, etc.)
   ↓
2. Raw Ingestion Layer
   - Basic validation and normalization
   - Duplicate detection
   - Storage in raw format
   ↓
3. Processing Queue
   - Priority-based processing
   - Cost-aware LLM enhancement
   - Citation extraction and analysis
   ↓
4. Enhanced Storage Layer
   - Integration with existing enhanced Neo4j schema
   - Vector embeddings in ChromaDB
   - Full legal research capabilities
```

### Storage Schema Design
```sql
-- Ingestion Tracking Table (PostgreSQL)
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    source_document_id VARCHAR(255),
    document_type VARCHAR(50),
    priority INTEGER,
    status VARCHAR(20),
    raw_data JSONB,
    quality_score DECIMAL(3,2),
    processing_cost DECIMAL(10,2),
    created_at TIMESTAMP,
    processed_at TIMESTAMP,
    enhanced_case_id VARCHAR(255) -- FK to Neo4j case
);

-- Document Versions Table
CREATE TABLE document_versions (
    document_id VARCHAR(255),
    version INTEGER,
    content_hash VARCHAR(64),
    source VARCHAR(50),
    ingested_at TIMESTAMP,
    metadata JSONB,
    PRIMARY KEY (document_id, version)
);
```

### Enhanced Neo4j Schema Extensions
```cypher
// Add ingestion metadata to Case nodes
CREATE (c:Case {
    // ... existing case properties
    source: "courtlistener",
    ingestion_date: datetime(),
    processing_version: "1.0",
    quality_score: 0.95,
    content_hash: "sha256_hash"
})

// Track data lineage
CREATE (source:DataSource {
    id: "courtlistener",
    name: "CourtListener",
    base_url: "https://www.courtlistener.com/api/",
    last_sync: datetime()
})

CREATE (c:Case)-[:SOURCED_FROM]->(source:DataSource)
```

## Storage Efficiency Considerations

### Deduplication Strategy
- **Content-based deduplication**: Hash-based detection of identical documents
- **Incremental updates**: Only store changes/deltas for document updates
- **Compression**: Efficient storage of legal document text
- **Archival policies**: Move old versions to cheaper storage tiers

### Query Optimization
- **Materialized views**: Pre-computed common queries for ingestion status
- **Indexing strategy**: Optimize for common access patterns
- **Caching layers**: Redis for frequently accessed ingestion metadata
- **Read replicas**: Separate read/write workloads for better performance

## Dependencies
- ADR-001: Architecture Integration (service boundaries and existing schema)
- ADR-002: Data Sources & Quality (quality metadata requirements)
- ADR-003: Cost & LLM Usage (processing cost tracking)

## Next Steps
1. Design detailed storage schema for ingestion metadata and lineage
2. Define data flow interfaces between ingestion stages
3. Plan migration strategy for integrating with existing sample data
4. Design monitoring and observability for data pipeline

## Related ADRs
- ADR-001: Architecture Integration
- ADR-002: Data Sources & Quality
- ADR-003: Cost & LLM Usage
- ADR-005: Operational Concerns (to be created)