# Graph Database Service

Neo4j-based citation network analysis service for legal authority scoring.

## Overview

Manages the citation graph database to:
- Track case law relationships (cites, overrules, distinguishes, follows)
- Calculate authority scores using PageRank algorithm
- Analyze jurisdiction-specific citation patterns
- Identify key precedents and citation clusters

## Architecture

- `models/`: Graph node and relationship schemas
- `queries/`: Optimized Cypher query modules
- `algorithms/`: Authority scoring and graph analysis

## Key Features

- Custom PageRank implementation weighted by:
  - Court hierarchy (Supreme Court > Circuit > District)
  - Temporal relevance (recent citations weighted higher)
  - Treatment type (positive vs negative citations)
- Efficient path finding for citation chains
- Jurisdiction-aware traversal algorithms