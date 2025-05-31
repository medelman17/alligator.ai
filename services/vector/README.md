# Vector Search Service

ChromaDB-powered semantic search service for finding similar legal documents.

## Overview

Provides semantic search capabilities for:
- Case law similarity matching
- Statutory text search
- Brief and memo similarity analysis
- Hybrid search combining semantic and citation relevance

## Architecture

- `embeddings/`: Legal domain-specific embedding generation
- `collections/`: ChromaDB collection management
- `search/`: Search algorithms and ranking logic

## Key Features

- Specialized legal embeddings trained on case law corpus
- Metadata filtering by jurisdiction, date, court level
- Hybrid ranking combining:
  - Semantic similarity scores
  - Citation authority from graph service
  - Temporal and jurisdictional relevance
- Batch processing for efficient document ingestion