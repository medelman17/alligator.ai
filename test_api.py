#!/usr/bin/env python3
"""
Simple API test script to verify endpoints are working.
"""

import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:8001"


async def test_api_endpoints():
    """Test the basic API endpoints."""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing alligator.ai API endpoints...")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health check: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   Services: {health_data.get('services', {})}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test root endpoint  
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"✅ Root endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   API: {data.get('name')} v{data.get('version')}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test search endpoints
        print("\n🔍 Testing search endpoints...")
        
        # Test semantic search (POST)
        try:
            search_payload = {
                "query": "police qualified immunity excessive force",
                "jurisdiction": "US",
                "limit": 5
            }
            response = await client.post(
                f"{BASE_URL}/search/semantic",
                json=search_payload
            )
            print(f"✅ Semantic search: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"   Found {len(results)} results")
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
        
        # Test case search (GET)
        try:
            params = {
                "q": "miranda rights",
                "jurisdiction": "US",
                "limit": 3
            }
            response = await client.get(
                f"{BASE_URL}/search/cases",
                params=params
            )
            print(f"✅ Case search: {response.status_code}")
            if response.status_code == 200:
                results = response.json()
                print(f"   Found {len(results)} results")
        except Exception as e:
            print(f"❌ Case search failed: {e}")
        
        # Test cases endpoints
        print("\n📁 Testing case management endpoints...")
        
        # Test list cases
        try:
            response = await client.get(
                f"{BASE_URL}/cases/",
                params={"page": 1, "page_size": 5}
            )
            print(f"✅ List cases: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total cases: {data.get('total_count', 0)}")
        except Exception as e:
            print(f"❌ List cases failed: {e}")
        
        # Test research endpoints
        print("\n🔬 Testing research endpoints...")
        
        # Test create research session
        try:
            research_payload = {
                "query": "Fourth Amendment search and seizure rights",
                "jurisdiction": "US",
                "analysis_types": ["precedent_analysis"],
                "max_cases": 10,
                "include_memo": True
            }
            response = await client.post(
                f"{BASE_URL}/research/sessions",
                json=research_payload
            )
            print(f"✅ Create research session: {response.status_code}")
            if response.status_code == 201:
                session = response.json()
                session_id = session.get("id")
                print(f"   Session ID: {session_id}")
                
                # Test get research session
                if session_id:
                    await asyncio.sleep(1)  # Give it a moment
                    response = await client.get(f"{BASE_URL}/research/sessions/{session_id}")
                    print(f"✅ Get research session: {response.status_code}")
                    if response.status_code == 200:
                        session_data = response.json()
                        print(f"   Status: {session_data.get('status')}")
                        
        except Exception as e:
            print(f"❌ Research endpoints failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 API testing complete!")


async def test_api_documentation():
    """Test API documentation endpoints."""
    async with httpx.AsyncClient() as client:
        print("\n📚 Testing API documentation...")
        
        try:
            # Test OpenAPI schema
            response = await client.get(f"{BASE_URL}/openapi.json")
            print(f"✅ OpenAPI schema: {response.status_code}")
            
            # Test Swagger UI  
            response = await client.get(f"{BASE_URL}/docs")
            print(f"✅ Swagger UI: {response.status_code}")
            
            # Test ReDoc
            response = await client.get(f"{BASE_URL}/redoc")
            print(f"✅ ReDoc: {response.status_code}")
            
        except Exception as e:
            print(f"❌ Documentation endpoints failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting API test suite...")
    print("Make sure the API server is running on http://localhost:8001")
    print()
    
    asyncio.run(test_api_endpoints())
    asyncio.run(test_api_documentation())