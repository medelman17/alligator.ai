# Memory Service

Multi-tier memory system for enhanced agent capabilities and personalization.

## Overview

Implements four types of memory to improve research quality:
- **Working Memory**: Session context and active research state
- **Episodic Memory**: Historical research patterns and successful strategies
- **Semantic Memory**: Evolving legal knowledge graph
- **Personalization Memory**: User and firm preferences

## Architecture

- `working/`: Redis-based session memory
- `episodic/`: PostgreSQL + ChromaDB for historical patterns
- `semantic/`: Neo4j + ChromaDB for knowledge evolution
- `personalization/`: User preference storage

## Key Features

- Automatic memory consolidation from working to long-term
- Pattern recognition for successful research strategies
- Knowledge graph evolution based on research outcomes
- Firm-specific legal preference learning
- Privacy-preserving memory isolation between firms