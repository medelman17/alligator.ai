# ADR-001: Ingestion System Architecture and Integration

## Status
Proposed

## Context
We need to design how the automated legal document ingestion system integrates with our existing enhanced legal research platform. Key considerations include:

- We have an operational enhanced Neo4j service with sophisticated legal schema
- Existing API Gateway with dependency injection and service lifecycle management
- Sample legal data already present in the system
- Need to scale from sample data to real-world legal document ingestion

## Questions to Address

### 1. Integration with Enhanced Neo4j Service
**Question**: How should the ingestion system integrate with our existing enhanced Neo4j service?

**Options**:
- **A) Direct Integration**: Ingestion service uses existing Neo4j service classes
- **B) Separate Database Layer**: Ingestion writes to separate schema/database, then syncs
- **C) Event-Driven Integration**: Ingestion publishes events, enhanced service consumes

**Analysis Needed**:
- Does our enhanced schema support ingestion metadata (source, ingestion_date, processing_status)?
- How do we handle conflicts between ingested data and existing sample data?
- Do we need to track data lineage and provenance?

### 2. Enhanced Schema Modifications
**Question**: Do we need to modify the enhanced schema for ingestion metadata?

**Considerations**:
- Tracking data source (CourtListener, Justia, manual upload)
- Ingestion timestamps and processing status
- Data quality scores and validation flags
- Relationship to processing workflows (LLM analysis, citation extraction)

### 3. Service Architecture
**Question**: Should ingestion be a separate microservice or integrated into existing API?

**Options**:
- **A) Integrated Service**: Part of existing API gateway with new endpoints
- **B) Separate Microservice**: Independent service with its own API
- **C) Background Service**: Worker service triggered by API gateway

**Trade-offs**:
- Separation of concerns vs operational complexity
- Scaling independence vs shared infrastructure
- API design consistency vs specialized requirements

### 4. Relationship to Enhanced Analysis
**Question**: How does raw ingested data relate to our enhanced legal analysis capabilities?

**Workflow Considerations**:
- Raw document ingestion → Enhanced processing → Analysis-ready data
- Should enhanced analysis be part of ingestion pipeline or separate trigger?
- How do we prioritize which ingested documents get enhanced processing?

## Decision Points Needed

1. **Schema Strategy**: Extend enhanced schema vs separate ingestion schema
2. **Service Boundary**: Where does ingestion end and enhanced analysis begin?
3. **Data Flow**: Pull-based vs push-based integration patterns
4. **Error Handling**: How failures in ingestion affect enhanced service availability

## Dependencies
- Enhanced Neo4j service architecture (already implemented)
- API Gateway dependency injection system (already implemented)
- Cost controller requirements (to be defined)
- Data source API characteristics (CourtListener specifics needed)

## Next Steps
1. Analyze enhanced Neo4j schema for ingestion metadata support
2. Define data lineage and provenance requirements
3. Determine service boundary between ingestion and enhanced analysis
4. Design integration patterns with existing service architecture

## Related ADRs
- ADR-002: Data Sources & Quality (to be created)
- ADR-003: Cost & LLM Usage (to be created)
- ADR-004: Data Flow & Storage (to be created)
- ADR-005: Operational Concerns (to be created)