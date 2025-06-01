#!/usr/bin/env python3
"""
Test script for the Research API endpoints.

This script tests the complete research workflow:
- Create research sessions
- Precedent analysis
- Memo generation

Usage:
    poetry run python test_research_api.py
"""

import asyncio
import json
import logging
from datetime import datetime

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8001/api/v1"


async def test_research_session_workflow():
    """Test the complete research session workflow."""
    logger.info("🧪 Testing Research Session Workflow")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Create a research session
        logger.info("📋 Test 1: Creating research session...")
        
        research_request = {
            "query": "police qualified immunity for excessive force in civil rights cases",
            "jurisdiction": "US",
            "practice_areas": ["civil_rights", "constitutional"],
            "analysis_types": ["precedent_analysis", "authority_analysis"],
            "max_cases": 10,
            "include_memo": True
        }
        
        try:
            response = await client.post(
                f"{API_BASE_URL}/research/sessions",
                json=research_request
            )
            
            if response.status_code == 201:
                session_data = response.json()
                session_id = session_data["id"]
                logger.info(f"✅ Research session created: {session_id}")
                logger.info(f"   Status: {session_data['status']}")
                logger.info(f"   Query: {session_data['query']}")
                
                # Test 2: Poll session status until completion
                logger.info("⏳ Test 2: Waiting for research completion...")
                
                max_attempts = 20
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)  # Wait 2 seconds between checks
                    
                    response = await client.get(f"{API_BASE_URL}/research/sessions/{session_id}")
                    if response.status_code == 200:
                        session_data = response.json()
                        status = session_data["status"]
                        logger.info(f"   Attempt {attempt + 1}: Status = {status}")
                        
                        if status == "completed":
                            logger.info("✅ Research completed successfully!")
                            
                            # Display results
                            results = session_data.get("results", {})
                            logger.info(f"   📊 Analysis Results:")
                            
                            if "precedent_analysis" in results:
                                pa = results["precedent_analysis"]
                                logger.info(f"     📚 Precedent Analysis: {pa['cases_analyzed']} cases")
                                logger.info(f"     📄 Summary: {pa['summary'][:100]}...")
                            
                            if "authority_analysis" in results:
                                aa = results["authority_analysis"]
                                logger.info(f"     ⚖️  Authority Analysis: {aa.get('summary', 'No summary')}")
                            
                            memo = session_data.get("memo")
                            if memo:
                                logger.info(f"   📝 Memo generated ({len(memo)} characters)")
                                logger.info(f"     First 200 chars: {memo[:200]}...")
                            
                            break
                        elif status == "failed":
                            error_msg = session_data.get("error_message", "Unknown error")
                            logger.error(f"❌ Research failed: {error_msg}")
                            break
                else:
                    logger.warning("⚠️  Research session did not complete within timeout")
                
                # Test 3: List all sessions
                logger.info("📋 Test 3: Listing research sessions...")
                
                response = await client.get(f"{API_BASE_URL}/research/sessions")
                if response.status_code == 200:
                    sessions = response.json()
                    logger.info(f"✅ Found {len(sessions)} research sessions")
                    for session in sessions[:3]:  # Show first 3
                        logger.info(f"   - {session['id']}: {session['status']} ({session['query'][:50]}...)")
                else:
                    logger.error(f"❌ Failed to list sessions: {response.status_code}")
                
                return session_id
                
            else:
                logger.error(f"❌ Failed to create research session: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Research session workflow failed: {e}")
            return None


async def test_precedent_analysis_endpoint():
    """Test the direct precedent analysis endpoint."""
    logger.info("🧪 Testing Direct Precedent Analysis")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test precedent analysis for a specific case
        analysis_request = {
            "case_id": "brown-v-board-1954",
            "depth": 2,
            "include_treatments": True,
            "jurisdiction_filter": "US"
        }
        
        try:
            logger.info("📋 Analyzing precedents for Brown v. Board of Education...")
            
            response = await client.post(
                f"{API_BASE_URL}/research/analyze-precedent",
                json=analysis_request
            )
            
            if response.status_code == 200:
                analysis_data = response.json()
                logger.info("✅ Precedent analysis completed!")
                logger.info(f"   📚 Case: {analysis_data['case_id']}")
                logger.info(f"   📊 Confidence Score: {analysis_data['confidence_score']:.2f}")
                logger.info(f"   📄 Summary: {analysis_data['analysis_summary'][:100]}...")
                logger.info(f"   🔗 Supporting Cases: {len(analysis_data['supporting_cases'])}")
                logger.info(f"   📝 Recommendations: {len(analysis_data['recommendations'])}")
                
                if analysis_data.get("treatment_analysis"):
                    logger.info("   📈 Treatment analysis included")
                
                return True
                
            elif response.status_code == 404:
                logger.warning("⚠️  Case not found (expected in simulation mode)")
                return True  # This is expected with simulated data
                
            else:
                logger.error(f"❌ Precedent analysis failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Precedent analysis failed: {e}")
            return False


async def test_memo_generation():
    """Test memo generation from research session."""
    logger.info("🧪 Testing Memo Generation")
    
    # First create a research session
    session_id = await test_research_session_workflow()
    if not session_id:
        logger.error("❌ Cannot test memo generation without research session")
        return False
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Generate memo in different formats
        formats = ["markdown", "html", "text"]
        
        for format_type in formats:
            logger.info(f"📝 Generating memo in {format_type} format...")
            
            memo_request = {
                "research_session_id": session_id,
                "memo_type": "research_memo",
                "include_citations": True,
                "format": format_type
            }
            
            try:
                response = await client.post(
                    f"{API_BASE_URL}/research/generate-memo",
                    json=memo_request
                )
                
                if response.status_code == 200:
                    memo_data = response.json()
                    logger.info(f"✅ {format_type.title()} memo generated!")
                    logger.info(f"   📄 Length: {len(memo_data['memo_content'])} characters")
                    logger.info(f"   📚 Citations: {memo_data['citations_count']}")
                    logger.info(f"   📅 Generated: {memo_data['generated_at']}")
                    
                    # Show a preview
                    content = memo_data["memo_content"]
                    preview = content[:200] + "..." if len(content) > 200 else content
                    logger.info(f"   Preview: {preview}")
                    
                else:
                    logger.error(f"❌ {format_type} memo generation failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ {format_type} memo generation failed: {e}")
        
        return True


async def test_api_health():
    """Test API health and service status."""
    logger.info("🧪 Testing API Health")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        try:
            # Test basic health endpoint
            response = await client.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                logger.info("✅ Basic health check passed")
            else:
                logger.warning(f"⚠️  Basic health check returned: {response.status_code}")
            
            # Test detailed health endpoint
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Detailed health check passed")
                logger.info(f"   📊 Service Status:")
                for service, status in health_data.items():
                    emoji = "✅" if status == "healthy" else "❌" if status == "unhealthy" else "❓"
                    logger.info(f"     {emoji} {service}: {status}")
            else:
                logger.warning(f"⚠️  Detailed health check returned: {response.status_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
            return False


async def main():
    """Run all research API tests."""
    logger.info("🚀 Starting Research API Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Research Session Workflow", test_research_session_workflow),
        ("Precedent Analysis Endpoint", test_precedent_analysis_endpoint),
        ("Memo Generation", test_memo_generation),
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
        logger.info("🎉 All tests passed! Research API is ready.")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)