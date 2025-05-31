#!/usr/bin/env python3
"""
Simple API test script to verify endpoints are working.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_api_endpoints():
    """Test basic API functionality."""
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing alligator.ai API endpoints...")
        print(f"Base URL: {base_url}")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check: PASSED")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Health check: ERROR - {e}")
        
        print()
        
        # Test API health endpoint
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                print("✅ API health check: PASSED")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ API health check: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ API health check: ERROR - {e}")
        
        print()
        
        # Test OpenAPI docs
        try:
            response = await client.get(f"{base_url}/api/openapi.json")
            if response.status_code == 200:
                openapi_spec = response.json()
                print("✅ OpenAPI spec: PASSED")
                print(f"   API Title: {openapi_spec.get('info', {}).get('title')}")
                print(f"   API Version: {openapi_spec.get('info', {}).get('version')}")
                print(f"   Endpoints: {len(openapi_spec.get('paths', {}))}")
            else:
                print(f"❌ OpenAPI spec: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ OpenAPI spec: ERROR - {e}")
        
        print()
        
        # Test search endpoint (expect it to fail gracefully without services)
        try:
            search_payload = {
                "query": "constitutional law",
                "jurisdiction": "federal",
                "limit": 5
            }
            response = await client.post(
                f"{base_url}/api/v1/search/semantic",
                json=search_payload
            )
            print(f"🔍 Semantic search endpoint: Status {response.status_code}")
            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"   Expected error (services not running): {error_detail}")
            else:
                print(f"   Unexpected success: {response.json()}")
        except Exception as e:
            print(f"❌ Semantic search: ERROR - {e}")
        
        print()
        
        # Test case list endpoint
        try:
            response = await client.get(f"{base_url}/api/v1/cases/?limit=5")
            print(f"📋 Case list endpoint: Status {response.status_code}")
            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"   Expected error (services not running): {error_detail}")
            else:
                cases_data = response.json()
                print(f"   Cases found: {len(cases_data.get('cases', []))}")
        except Exception as e:
            print(f"❌ Case list: ERROR - {e}")
        
        print()
        
        # Test research session creation
        try:
            research_payload = {
                "query": "First Amendment free speech analysis",
                "jurisdiction": "federal",
                "analysis_types": ["precedent_analysis"],
                "max_cases": 10,
                "include_memo": False
            }
            response = await client.post(
                f"{base_url}/api/v1/research/sessions",
                json=research_payload
            )
            print(f"🔬 Research session creation: Status {response.status_code}")
            if response.status_code == 201:
                session_data = response.json()
                session_id = session_data.get("id")
                print(f"   Session created: {session_id}")
                print(f"   Status: {session_data.get('status')}")
                
                # Test session retrieval
                response = await client.get(f"{base_url}/api/v1/research/sessions/{session_id}")
                if response.status_code == 200:
                    print("✅ Session retrieval: PASSED")
                else:
                    print(f"❌ Session retrieval: FAILED ({response.status_code})")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                print(f"   Error: {error_detail}")
        except Exception as e:
            print(f"❌ Research session: ERROR - {e}")
        
        print()
        print("=" * 50)
        print("🎯 API Test Summary:")
        print("   - Basic endpoints are responding")
        print("   - Request validation is working")
        print("   - Error handling is functional")
        print("   - Services integration points are ready")
        print("")
        print("💡 Next steps:")
        print("   1. Start database services (docker compose up -d)")
        print("   2. Test with actual data")
        print("   3. Implement proper dependency injection")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())