# Orchestration Service

Multi-agent orchestration service using LangGraph for complex legal research workflows.

## Overview

This service coordinates specialized AI agents to conduct comprehensive legal research:
- **Precedent Analyst**: Finds and analyzes relevant case law
- **Opposition Researcher**: Analyzes opposing arguments and weaknesses
- **Memo Generator**: Synthesizes research into legal memoranda
- **Citation Validator**: Ensures accuracy of legal citations

## Architecture

- `agents/`: Individual agent implementations
- `workflows/`: LangGraph workflow definitions
- `state/`: State management for multi-step research

## Key Features

- Parallel agent execution for efficiency
- State persistence across research sessions
- Dynamic workflow adaptation based on findings
- Integration with graph and vector search services