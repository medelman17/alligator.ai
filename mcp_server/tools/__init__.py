"""
MCP Server tools for alligator.ai Legal Research Platform.

This module provides comprehensive legal research tools accessible via the Model Context Protocol (MCP):

- CourtListener Integration: Search and analyze cases across all U.S. jurisdictions
- Research Workflows: AI-powered legal research with semantic search
- Legal Analysis: Authority analysis, citation treatment, and precedent evaluation
"""

from .courtlistener import CourtListenerTools
from .research import ResearchTools
from .analysis import AnalysisTools

__all__ = [
    "CourtListenerTools",
    "ResearchTools", 
    "AnalysisTools"
]

# Tool categories for MCP registration
TOOL_CATEGORIES = {
    "search": [
        "search_legal_cases",
        "get_case_details", 
        "citation_network_expansion"
    ],
    "research": [
        "conduct_legal_research",
        "semantic_case_search",
        "generate_legal_memo"
    ],
    "analysis": [
        "analyze_case_authority",
        "identify_opposing_arguments"
    ]
}

# Tool descriptions for documentation
TOOL_DESCRIPTIONS = {
    "search_legal_cases": "Search for legal cases across all U.S. jurisdictions using CourtListener API",
    "get_case_details": "Get detailed information about a specific legal case including full text and citations",
    "citation_network_expansion": "Discover related cases through citation analysis and network expansion",
    "conduct_legal_research": "Conduct comprehensive legal research using AI agents and semantic search",
    "semantic_case_search": "Find legally similar cases using semantic search and AI embeddings",
    "analyze_case_authority": "Analyze legal authority and precedential value using citation networks",
    "identify_opposing_arguments": "Identify potential opposing arguments and counterpoint cases",
    "generate_legal_memo": "Generate professional legal research memoranda from research results"
}

def get_available_tools():
    """Get list of all available MCP tools"""
    all_tools = []
    for category, tools in TOOL_CATEGORIES.items():
        all_tools.extend(tools)
    return all_tools

def get_tools_by_category(category: str):
    """Get tools in a specific category"""
    return TOOL_CATEGORIES.get(category, [])

def get_tool_description(tool_name: str):
    """Get description for a specific tool"""
    return TOOL_DESCRIPTIONS.get(tool_name, "No description available")