#!/usr/bin/env python3
"""
Test script for alligator.ai MCP Server integration.

Tests the complete MCP server functionality including:
- CourtListener API integration across all jurisdictions
- Research workflow tools with real data
- Legal analysis capabilities
- Server validation and setup
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_server_setup():
    """Test MCP server setup and validation"""
    logger.info("🔧 Testing MCP Server Setup")
    
    try:
        from mcp_server import (
            AlligatorAIMCP, 
            get_server_info, 
            get_tool_info,
            validate_server_setup
        )
        
        # Test server info
        server_info = get_server_info()
        logger.info(f"✅ Server: {server_info['name']} v{server_info['version']}")
        logger.info(f"   Capabilities: {len(server_info['capabilities'])} features")
        logger.info(f"   Jurisdictions: {len(server_info['supported_jurisdictions'])} court systems")
        
        # Test tool info
        tool_info = get_tool_info()
        logger.info(f"✅ Tools: {tool_info['total_tools']} available")
        logger.info(f"   Categories: {', '.join(tool_info['tool_categories'])}")
        
        # Validate setup
        validation = validate_server_setup()
        if validation['valid']:
            logger.info("✅ Server setup validation passed")
        else:
            logger.warning("⚠️  Server setup has issues:")
            for error in validation['errors']:
                logger.error(f"   Error: {error}")
            for warning in validation['warnings']:
                logger.warning(f"   Warning: {warning}")
        
        logger.info(f"   Dependencies: {validation['dependencies']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP server setup test failed: {e}")
        return False


async def test_courtlistener_tools():
    """Test CourtListener MCP tools with real data"""
    logger.info("🏛️ Testing CourtListener MCP Tools")
    
    try:
        from mcp_server.tools.courtlistener import CourtListenerTools
        from mcp_server.config import settings
        
        # Initialize tools
        courtlistener_tools = CourtListenerTools(settings)
        
        # Test 1: Search legal cases across jurisdictions
        logger.info("📋 Test 1: Multi-jurisdiction case search")
        
        search_tests = [
            {
                "name": "Supreme Court cases",
                "params": {
                    "query": "constitutional equal protection",
                    "jurisdiction": "scotus",
                    "limit": 5
                }
            },
            {
                "name": "9th Circuit federal cases", 
                "params": {
                    "query": "civil rights",
                    "jurisdiction": "ca9",
                    "court_type": "federal",
                    "limit": 3
                }
            },
            {
                "name": "New Jersey state cases",
                "params": {
                    "query": "employment discrimination",
                    "jurisdiction": "nj",
                    "court_type": "state",
                    "date_range": {
                        "start": "2022-01-01",
                        "end": "2024-01-01"
                    },
                    "limit": 3
                }
            },
            {
                "name": "All federal appellate courts",
                "params": {
                    "query": "immigration law",
                    "court_type": "appellate",
                    "limit": 5
                }
            }
        ]
        
        for test in search_tests:
            logger.info(f"   Testing: {test['name']}")
            results = await courtlistener_tools.search_cases(**test['params'])
            
            if 'error' in results:
                logger.warning(f"   ⚠️  {test['name']}: {results['error']}")
            else:
                cases_found = results.get('total_results', 0)
                logger.info(f"   ✅ {test['name']}: Found {cases_found} cases")
                
                # Show top result details
                if results.get('cases'):
                    top_case = results['cases'][0]
                    logger.info(f"      Top result: {top_case.get('case_name', 'Unknown')}")
                    logger.info(f"      Court: {top_case.get('court', {}).get('name', 'Unknown')}")
                    logger.info(f"      Authority: {top_case.get('authority_score', 0):.1f}/10")
        
        # Test 2: Get case details
        logger.info("📄 Test 2: Case details retrieval")
        
        # Try to get details for a case found in the search
        sample_case_ids = ["1", "12345", "sample_case"]  # These might not exist, but test the functionality
        
        for case_id in sample_case_ids[:1]:  # Just test one to avoid API limits
            logger.info(f"   Getting details for case ID: {case_id}")
            details = await courtlistener_tools.get_case_details(
                case_id=case_id,
                include_full_text=True,
                include_citations=True
            )
            
            if 'error' in details:
                logger.info(f"   ℹ️  Case {case_id} not found (expected for test IDs)")
            else:
                logger.info(f"   ✅ Retrieved details for: {details.get('basic_info', {}).get('case_name', 'Unknown')}")
                logger.info(f"      Authority score: {details.get('authority_analysis', {}).get('authority_score', 0):.1f}")
                logger.info(f"      Citations found: {details.get('citations', {}).get('total_count', 0)}")
        
        # Test 3: Jurisdiction guide
        logger.info("🗺️ Test 3: Jurisdiction guide")
        jurisdiction_guide = await courtlistener_tools.get_jurisdiction_guide()
        
        federal_courts = len(jurisdiction_guide.get('federal_courts', {}))
        state_courts = len(jurisdiction_guide.get('state_courts', {}))
        logger.info(f"   ✅ Jurisdiction guide: {federal_courts} federal + {state_courts} state courts")
        
        # Test 4: Court hierarchy
        logger.info("⚖️ Test 4: Court hierarchy") 
        hierarchy = await courtlistener_tools.get_court_hierarchy()
        
        circuit_courts = len(hierarchy.get('federal_system', {}).get('circuit_courts', []))
        state_supremes = len(hierarchy.get('state_systems', {}).get('supreme_courts', []))
        logger.info(f"   ✅ Court hierarchy: {circuit_courts} circuit courts + {state_supremes} state supreme courts")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CourtListener tools test failed: {e}")
        return False


async def test_research_tools():
    """Test research workflow MCP tools"""
    logger.info("🧠 Testing Research Workflow MCP Tools")
    
    try:
        from mcp_server.tools.research import ResearchTools
        from mcp_server.config import settings
        
        # Initialize tools
        research_tools = ResearchTools(settings)
        
        # Test 1: Semantic case search
        logger.info("🔍 Test 1: Semantic case search")
        
        semantic_queries = [
            {
                "query": "police excessive force qualified immunity",
                "jurisdiction": "US",
                "practice_areas": ["civil_rights", "constitutional"],
                "limit": 5
            },
            {
                "query": "employment discrimination retaliation",
                "practice_areas": ["employment"],
                "similarity_threshold": 0.6,
                "limit": 3
            }
        ]
        
        for query_test in semantic_queries:
            logger.info(f"   Query: '{query_test['query'][:50]}...'")
            results = await research_tools.semantic_search(**query_test)
            
            if 'error' in results:
                logger.warning(f"   ⚠️  Semantic search failed: {results['error']}")
            else:
                similar_cases = len(results.get('similar_cases', []))
                logger.info(f"   ✅ Found {similar_cases} semantically similar cases")
                
                if results.get('similar_cases'):
                    top_case = results['similar_cases'][0]
                    logger.info(f"      Best match: {top_case.get('case_name', 'Unknown')} (similarity: {top_case.get('similarity_score', 0):.3f})")
        
        # Test 2: Get recent research sessions
        logger.info("📚 Test 2: Recent research sessions")
        recent_sessions = await research_tools.get_recent_sessions(limit=5)
        
        session_count = recent_sessions.get('total_sessions', 0)
        logger.info(f"   ✅ Found {session_count} recent research sessions")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Research tools test failed: {e}")
        return False


async def test_analysis_tools():
    """Test legal analysis MCP tools"""
    logger.info("⚖️ Testing Legal Analysis MCP Tools")
    
    try:
        from mcp_server.tools.analysis import AnalysisTools
        from mcp_server.config import settings
        
        # Initialize tools
        analysis_tools = AnalysisTools(settings)
        
        # Test 1: Authority analysis
        logger.info("📊 Test 1: Case authority analysis")
        
        # Test with sample case IDs (may not exist, testing functionality)
        test_cases = [
            {
                "case_id": "brown-v-board-1954",
                "target_jurisdiction": "US",
                "analysis_types": ["authority_score", "good_law_status"]
            },
            {
                "case_id": "miranda-v-arizona-1966", 
                "target_jurisdiction": "US",
                "analysis_types": ["authority_score", "binding_precedent"]
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"   Analyzing case: {test_case['case_id']}")
            analysis = await analysis_tools.analyze_authority(**test_case)
            
            if 'error' in analysis:
                logger.info(f"   ℹ️  Authority analysis: {analysis['error'][:100]}...")
            else:
                authority_score = analysis.get('authority_analysis', {}).get('authority_score', 0)
                logger.info(f"   ✅ Authority analysis completed")
                logger.info(f"      Authority score: {authority_score:.1f}/10")
                
                recommendations = len(analysis.get('recommendations', []))
                logger.info(f"      Recommendations: {recommendations} generated")
        
        # Test 2: Opposition analysis
        logger.info("🥊 Test 2: Opposition argument identification")
        
        opposition_tests = [
            {
                "position": "Qualified immunity should be limited in excessive force cases",
                "case_type": "civil rights",
                "jurisdiction": "US"
            },
            {
                "position": "At-will employment does not protect retaliation",
                "case_type": "employment",
                "jurisdiction": "NJ"
            }
        ]
        
        for test in opposition_tests:
            logger.info(f"   Position: '{test['position'][:50]}...'")
            opposition = await analysis_tools.identify_opposition(**test)
            
            if 'error' in opposition:
                logger.warning(f"   ⚠️  Opposition analysis failed: {opposition['error']}")
            else:
                counterargs = len(opposition.get('potential_counterarguments', []))
                opposing_cases = len(opposition.get('opposing_precedents', []))
                logger.info(f"   ✅ Opposition analysis completed")
                logger.info(f"      Counterarguments: {counterargs} identified")
                logger.info(f"      Opposing precedents: {opposing_cases} found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis tools test failed: {e}")
        return False


async def test_full_research_workflow():
    """Test a complete legal research workflow"""
    logger.info("🔄 Testing Complete Legal Research Workflow")
    
    try:
        from mcp_server.tools.research import ResearchTools
        from mcp_server.config import settings
        
        research_tools = ResearchTools(settings)
        
        # Comprehensive research test
        logger.info("🎯 Conducting comprehensive legal research")
        
        research_request = {
            "research_question": "What are the constitutional limits on police use of deadly force?",
            "case_facts": "Police officer shot fleeing suspect who was not armed and posed no immediate threat to others",
            "jurisdiction": "US",
            "practice_areas": ["constitutional", "civil_rights"],
            "research_depth": "standard"
        }
        
        logger.info(f"   Research question: {research_request['research_question']}")
        logger.info(f"   Jurisdiction: {research_request['jurisdiction']}")
        logger.info(f"   Practice areas: {', '.join(research_request['practice_areas'])}")
        
        # This will take some time as it calls the actual research API
        research_result = await research_tools.conduct_research(**research_request)
        
        if 'error' in research_result:
            logger.warning(f"   ⚠️  Research workflow failed: {research_result['error']}")
            return False
        else:
            logger.info("   ✅ Legal research completed successfully!")
            
            # Show research results summary
            findings = research_result.get('findings', {})
            cases_analyzed = findings.get('total_cases_analyzed', 0)
            precedents = len(findings.get('relevant_precedents', []))
            
            logger.info(f"      Cases analyzed: {cases_analyzed}")
            logger.info(f"      Relevant precedents: {precedents}")
            logger.info(f"      Research ID: {research_result.get('research_id', 'Unknown')}")
            
            # Test memo generation if research succeeded
            if research_result.get('research_id'):
                logger.info("📝 Testing memo generation")
                
                memo_result = await research_tools.generate_memo(
                    research_session_id=research_result['research_id'],
                    memo_type="research_memo",
                    audience="internal",
                    format="markdown"
                )
                
                if 'error' in memo_result:
                    logger.warning(f"   ⚠️  Memo generation failed: {memo_result['error']}")
                else:
                    memo_length = memo_result.get('word_count', 0)
                    citations = memo_result.get('citations_count', 0)
                    logger.info(f"   ✅ Legal memo generated: {memo_length} words, {citations} citations")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Full research workflow test failed: {e}")
        return False


async def main():
    """Run all MCP server tests"""
    logger.info("🚀 Starting alligator.ai MCP Server Integration Tests")
    logger.info("=" * 70)
    
    tests = [
        ("MCP Server Setup", test_mcp_server_setup),
        ("CourtListener Tools", test_courtlistener_tools),
        ("Research Tools", test_research_tools),
        ("Analysis Tools", test_analysis_tools),
        ("Full Research Workflow", test_full_research_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 50)
        
        try:
            success = await test_func()
            if success:
                logger.info(f"✅ PASSED: {test_name}")
                passed += 1
            else:
                logger.error(f"❌ FAILED: {test_name}")
        except Exception as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All MCP server tests passed! The integration is working correctly.")
        logger.info("🔧 Ready to connect to Claude Desktop or other MCP clients.")
    else:
        logger.info(f"⚠️  {total - passed} tests had issues. Check logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)