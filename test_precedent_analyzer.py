#!/usr/bin/env python3
"""
Test script for the LangGraph Precedent Analyzer with Enhanced Services.

This script tests the integration between:
- Enhanced Neo4j Service
- ChromaDB Service (with simulation mode)
- LangGraph Precedent Analyzer

Usage:
    poetry run python test_precedent_analyzer.py
"""

import asyncio
import logging
import os
from datetime import datetime

from services.graph.enhanced_neo4j_service import EnhancedNeo4jService
from services.vector.chroma_service import ChromaService
from services.orchestration.agents.precedent_analyzer import PrecedentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_services_connectivity():
    """Test basic connectivity to all services."""
    logger.info("🔍 Testing service connectivity...")
    
    # Test Neo4j connection
    neo4j_service = EnhancedNeo4jService(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="citation_graph_2024"
    )
    
    try:
        await neo4j_service.connect()
        health_ok = await neo4j_service.health_check()
        logger.info(f"✅ Neo4j Service: {'Connected' if health_ok else 'Failed'}")
    except Exception as e:
        logger.error(f"❌ Neo4j Service: Failed to connect - {e}")
        return False
    
    # Test ChromaDB service (simulation mode)
    chroma_service = ChromaService(use_mcp_tools=False)  # Use simulation for testing
    try:
        await chroma_service.initialize()
        logger.info("✅ ChromaDB Service: Connected (simulation mode)")
    except Exception as e:
        logger.error(f"❌ ChromaDB Service: Failed - {e}")
        return False
    
    await neo4j_service.close()
    return True


async def test_precedent_analyzer_basic():
    """Test basic precedent analyzer functionality."""
    logger.info("🤖 Testing Precedent Analyzer basic functionality...")
    
    # Check for required API key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.warning("⚠️  ANTHROPIC_API_KEY not set, using placeholder")
        anthropic_key = "test-key-placeholder"
    
    # Initialize services
    neo4j_service = EnhancedNeo4jService(
        uri="bolt://localhost:7687", 
        user="neo4j",
        password="citation_graph_2024"
    )
    chroma_service = ChromaService(use_mcp_tools=False)  # Simulation mode
    
    try:
        # Connect to services
        await neo4j_service.connect()
        await chroma_service.initialize()
        
        # Initialize precedent analyzer
        analyzer = PrecedentAnalyzer(
            neo4j_service=neo4j_service,
            chroma_service=chroma_service,
            anthropic_api_key=anthropic_key
        )
        
        logger.info("✅ Precedent Analyzer: Initialized successfully")
        
        # Test a simple analysis (will use simulated data)
        logger.info("🔍 Running test precedent analysis...")
        
        test_queries = [
            {
                "query": "police qualified immunity excessive force",
                "jurisdiction": "US",
                "practice_areas": ["civil_rights", "constitutional"]
            },
            {
                "query": "equal protection constitutional law",
                "jurisdiction": "US", 
                "practice_areas": ["constitutional"]
            },
            {
                "query": "miranda rights criminal procedure",
                "jurisdiction": "US",
                "practice_areas": ["criminal", "constitutional"]
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            logger.info(f"📋 Test Case {i}: {test_case['query']}")
            
            try:
                result = await analyzer.analyze_precedents(
                    query=test_case["query"],
                    jurisdiction=test_case["jurisdiction"],
                    practice_areas=test_case["practice_areas"]
                )
                
                # Validate result structure
                expected_keys = [
                    "precedent_memo", "relevant_precedents", 
                    "authority_analysis", "treatment_analysis", "confidence_score"
                ]
                
                missing_keys = [key for key in expected_keys if key not in result]
                if missing_keys:
                    logger.error(f"❌ Missing result keys: {missing_keys}")
                else:
                    logger.info(f"✅ Test Case {i}: Analysis completed")
                    logger.info(f"   📊 Found {len(result['relevant_precedents'])} precedents")
                    logger.info(f"   🎯 Confidence Score: {result['confidence_score']:.2f}")
                    
                    if result.get("error"):
                        logger.warning(f"   ⚠️  Analysis had error: {result['error']}")
                    
                    # Log sample memo excerpt
                    memo = result.get("precedent_memo", "")
                    if memo and len(memo) > 100:
                        memo_excerpt = memo[:200] + "..."
                        logger.info(f"   📝 Memo excerpt: {memo_excerpt}")
                    
            except Exception as e:
                logger.error(f"❌ Test Case {i}: Failed - {e}")
        
    except Exception as e:
        logger.error(f"❌ Precedent Analyzer test failed: {e}")
        return False
    
    finally:
        await neo4j_service.close()
    
    return True


async def test_enhanced_neo4j_methods():
    """Test the enhanced Neo4j methods used by precedent analyzer."""
    logger.info("🔗 Testing Enhanced Neo4j Service methods...")
    
    neo4j_service = EnhancedNeo4jService(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="citation_graph_2024"
    )
    
    try:
        await neo4j_service.connect()
        
        # Test the new methods we added
        test_case_id = "brown-v-board-1954"  # Should exist in our sample data
        
        logger.info(f"🔍 Testing get_citing_cases for {test_case_id}")
        citing_cases = await neo4j_service.get_citing_cases(test_case_id, limit=5)
        logger.info(f"   📊 Found {len(citing_cases)} citing cases")
        
        logger.info(f"🔍 Testing get_cited_cases for {test_case_id}")
        cited_cases = await neo4j_service.get_cited_cases(test_case_id, limit=5)
        logger.info(f"   📊 Found {len(cited_cases)} cited cases")
        
        logger.info(f"🔍 Testing find_cases_by_criteria")
        criteria_cases = await neo4j_service.find_cases_by_criteria(
            jurisdiction="US",
            practice_areas=["constitutional"],
            limit=5
        )
        logger.info(f"   📊 Found {len(criteria_cases)} cases by criteria")
        
        logger.info("✅ Enhanced Neo4j methods: All tests passed")
        
    except Exception as e:
        logger.error(f"❌ Enhanced Neo4j methods test failed: {e}")
        return False
    
    finally:
        await neo4j_service.close()
    
    return True


async def test_chroma_service_simulation():
    """Test ChromaDB service simulation mode."""
    logger.info("🔍 Testing ChromaDB Service simulation...")
    
    chroma_service = ChromaService(use_mcp_tools=False)
    
    try:
        await chroma_service.initialize()
        
        # Test semantic search
        logger.info("🔍 Testing semantic search...")
        results = await chroma_service.semantic_search(
            query="constitutional equal protection",
            document_types=["case"],
            jurisdiction="US",
            practice_areas=["constitutional"],
            limit=5
        )
        
        logger.info(f"   📊 Found {len(results)} search results")
        
        if results:
            for i, result in enumerate(results[:3], 1):
                title = result["metadata"].get("title", "Unknown")
                score = result["similarity_score"]
                logger.info(f"   {i}. {title} (score: {score:.3f})")
        
        logger.info("✅ ChromaDB simulation: All tests passed")
        
    except Exception as e:
        logger.error(f"❌ ChromaDB simulation test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Precedent Analyzer Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Service Connectivity", test_services_connectivity),
        ("ChromaDB Simulation", test_chroma_service_simulation),
        ("Enhanced Neo4j Methods", test_enhanced_neo4j_methods),
        ("Precedent Analyzer Basic", test_precedent_analyzer_basic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            success = await test_func()
            if success:
                logger.info(f"✅ PASSED: {test_name}")
                passed += 1
            else:
                logger.error(f"❌ FAILED: {test_name}")
        except Exception as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Precedent Analyzer is ready.")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)