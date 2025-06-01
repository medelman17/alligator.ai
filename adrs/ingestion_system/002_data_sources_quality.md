# ADR-002: Data Sources and Quality Management

## Status
Proposed

## Context
The ingestion system needs to handle multiple legal data sources with varying quality, formats, and availability. CourtListener is our Phase 1 MVP target, but we need a strategy that scales to multiple sources.

## Questions to Address

### 1. CourtListener API Characteristics ✅ RESEARCHED
**Question**: What exactly is the CourtListener API like? Rate limits? Cost structure?

**✅ Research Complete - Key Findings**:

#### **Cost Structure** 🎉
- **COMPLETELY FREE** - No cost for API access
- Funded by Free Law Project (501(c)(3) non-profit)
- No paid tiers or subscription fees
- Only constraint is rate limiting

#### **Rate Limits**
- **Authenticated users**: 5,000 queries per hour
- **Unauthenticated users**: 100 queries per day (experimentation only)
- **Citation Lookup API**: Additional throttling
  - 60 valid citations per minute
  - Max 250 citations per single request
- **Account Policy**: One account per project/person/organization (strictly enforced)

#### **Authentication Options**
- **Token Authentication** (recommended): `Authorization: Token <your-token-here>`
- **Cookie/Session Authentication**: For web applications
- **HTTP Basic Authentication**: Username/password fallback
- All methods secure, choice based on convenience

#### **API Endpoints Available**
- **Case Law APIs**: Dockets, Clusters, Opinions, Courts
- **Citation Network APIs**: Citation relationships between cases
- **Search API**: Advanced search across millions of documents
- **Judge APIs**: Judge biographical and career information
- **PACER/RECAP APIs**: Federal court dockets and filings
- **Oral Arguments APIs**: Audio recordings collection

#### **Data Structure and Quality**
- **3,354+ jurisdictions** (federal and state courts)
- **Millions of opinions** with full text
- **4-tier data model**: Courts → Dockets → Clusters → Opinions
- **Multiple text formats**: HTML, XML, plain text (prioritized by quality)
- **Citation networks**: Links between citing/cited cases
- **Rich metadata**: Court hierarchy, judge information, case dates

#### **API Features**
- **Advanced filtering**: Django-style lookups (`__gt`, `__lt`, `__range`)
- **Related filtering**: Join across APIs (`court__jurisdiction=FD`)
- **Deep pagination**: Handle large result sets efficiently
- **Field selection**: Bandwidth optimization
- **Counting**: Get totals without fetching all data
- **Bulk operations**: Efficient for large-scale ingestion

### 2. Data Quality Validation
**Question**: How do we handle data quality validation and normalization?

**Quality Dimensions**:
- **Completeness**: Required fields present (citation, case name, court, date)
- **Accuracy**: Valid court identifiers, proper date formats, citation format validation
- **Consistency**: Standardized jurisdiction codes, practice area mappings
- **Timeliness**: How recent is the data, when was it last updated

**Validation Strategy Options**:
- **A) Strict Validation**: Reject documents that don't meet quality standards
- **B) Best Effort**: Accept partial data, flag quality issues for manual review
- **C) Tiered Processing**: Different processing paths based on data quality scores

### 3. Incomplete/Malformed Data Handling
**Question**: What's our strategy for dealing with incomplete or malformed data?

**Common Issues**:
- Missing court information or invalid court IDs
- Unparseable dates or citation formats
- Truncated or corrupted document text
- Inconsistent case name variations

**Handling Strategies**:
- **Repair**: Attempt automatic correction using heuristics or external lookups
- **Queue for Review**: Flag for manual review and correction
- **Partial Ingest**: Store what we can, mark fields as incomplete
- **Rejection**: Skip documents that fail minimum quality thresholds

### 4. Ingestion Prioritization
**Question**: How do we prioritize which cases to ingest first?

**Prioritization Factors**:
- **Recency**: Newer cases first vs historical important cases
- **Authority**: Supreme Court > Appellate > District courts
- **Practice Areas**: Focus on specific legal domains initially
- **Citation Impact**: Cases with high citation counts
- **User Demand**: Cases requested by users or matching search patterns

**Implementation Options**:
- **Queue-Based**: Priority queue with configurable scoring
- **Rule-Based**: Hard rules for inclusion/exclusion criteria
- **ML-Based**: Learn from user behavior and case importance
- **Manual Curation**: Legal experts define priority lists

## Decision Points Needed

### Data Source Integration
1. **API Client Design**: Generic source interface vs source-specific implementations
2. **Rate Limiting**: How to respect API limits while maintaining throughput
3. **Authentication**: Secure API key management and rotation
4. **Error Recovery**: Handling API downtime and transient failures

### Quality Management
1. **Quality Metrics**: What constitutes "good enough" legal document quality
2. **Validation Pipeline**: Real-time vs batch validation approaches
3. **Quality Scoring**: Algorithmic scoring vs manual review workflows
4. **Improvement Feedback**: How quality issues inform source selection

### Data Normalization
1. **Court Mapping**: How to map source court identifiers to our court schema
2. **Practice Area Classification**: Automatic categorization vs manual tagging
3. **Citation Parsing**: Standardization of citation formats across sources
4. **Date Handling**: Timezone and format normalization

## Decisions Made ✅

### CourtListener Integration Strategy
**Decision**: Use CourtListener as primary data source for Phase 1 MVP

**Rationale**:
- **Zero cost** eliminates budget constraints 
- **5,000 queries/hour** supports substantial ingestion throughput
- **Rich data model** aligns well with our enhanced Neo4j schema
- **Established API** with comprehensive documentation and stability
- **Citation networks** provide exactly what we need for legal authority analysis

### Rate Limit Management Strategy
**Decision**: Implement smart throttling with 4,000 requests/hour target (80% of limit)

**Implementation**:
- Token bucket algorithm with 4,000/hour = ~1.1 requests/second
- Request queuing and batching for efficiency
- Automatic backoff if approaching limits
- Single account for organization (per CourtListener policy)

### Data Quality Framework
**Decision**: Multi-tier validation with quality scoring

**Validation Levels**:
1. **Required Field Validation**: citation, case_name, court, decision_date
2. **Format Validation**: Citation parsing, date validation, court ID mapping
3. **Content Quality Scoring**: Text completeness, metadata richness
4. **Legal Authority Validation**: Court hierarchy verification, jurisdiction consistency

### Prioritization Strategy  
**Decision**: Authority-based priority queue with recency weighting

**Priority Algorithm**:
```python
priority_score = (
    court_authority_weight * 0.4 +  # Supreme Court > Appellate > District
    recency_score * 0.3 +           # Newer cases prioritized
    citation_impact * 0.2 +         # High-citation cases
    practice_area_relevance * 0.1   # Target legal domains
)
```

## Requirements Defined ✅

### CourtListener Integration ✅ COMPLETE
- [x] Research CourtListener API documentation
- [x] Determine rate limits and authentication requirements  
- [x] Identify available metadata fields
- [x] Test API response formats and reliability

### Next Implementation Steps
- [ ] Create CourtListener API client with token authentication
- [ ] Implement rate limiting with token bucket algorithm
- [ ] Design data mapping from CourtListener to our enhanced schema
- [ ] Build quality validation pipeline for legal documents

### Quality Framework
- [ ] Define minimum quality standards for legal documents
- [ ] Create quality scoring algorithm
- [ ] Design validation rule engine
- [ ] Plan manual review workflow for edge cases

### Prioritization Algorithm
- [ ] Weight factors for case importance scoring
- [ ] Implement queue management system
- [ ] Design feedback mechanisms for priority adjustment
- [ ] Plan A/B testing for prioritization strategies

## Dependencies
- ADR-001: Architecture Integration (service boundaries)
- ADR-003: Cost & LLM Usage (budget constraints on quality processing)
- ADR-004: Data Flow & Storage (how quality metadata is stored)

## Next Steps
1. Research CourtListener API capabilities and limitations
2. Define legal document quality standards and metrics
3. Design data validation and normalization pipeline
4. Create prioritization framework for case ingestion

## Related ADRs
- ADR-001: Architecture Integration
- ADR-003: Cost & LLM Usage (to be created)
- ADR-004: Data Flow & Storage (to be created)
- ADR-005: Operational Concerns (to be created)