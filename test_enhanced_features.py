#!/usr/bin/env python3
"""
Test script for enhanced legal research features.

Tests the sophisticated legal research capabilities including:
- Enhanced schema initialization
- Citation treatment analysis
- Good law verification
- Authoritative precedent discovery
- Semantic case search
"""

import asyncio
import requests
import json
from datetime import datetime
import time

# API Configuration
API_BASE_URL = "http://localhost:8001"
API_V1_URL = f"{API_BASE_URL}/api/v1"

def test_api_health():
    """Test basic API health."""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def test_enhanced_health():
    """Test enhanced service health."""
    print("🔍 Testing enhanced service health...")
    try:
        response = requests.get(f"{API_V1_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Enhanced service health check passed")
            print(f"   Neo4j status: {health_data.get('neo4j', {}).get('status', 'unknown')}")
            print(f"   Enhanced schema: {health_data.get('neo4j', {}).get('enhanced_schema', 'unknown')}")
            return True
        else:
            print(f"❌ Enhanced health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Enhanced health check failed: {e}")
        return False

def test_sample_case_lookup():
    """Test lookup of sample legal cases."""
    print("\n🏛️ Testing sample case lookup...")
    sample_case_ids = [
        "brown-v-board-1954",
        "miranda-v-arizona-1966",
        "roe-v-wade-1973",
        "dobbs-v-jackson-2022"
    ]
    
    for case_id in sample_case_ids:
        try:
            response = requests.get(f"{API_V1_URL}/cases/{case_id}", timeout=10)
            if response.status_code == 200:
                case_data = response.json()
                case_name = case_data.get("case", {}).get("case_name", "Unknown")
                authority_score = case_data.get("authority_score", 0)
                print(f"✅ Found case: {case_name} (Authority: {authority_score:.2f})")
                
                # Check for enhanced fields
                if case_data.get("good_law_verification"):
                    confidence = case_data["good_law_verification"].get("confidence", "unknown")
                    print(f"   📊 Good law status: {confidence}")
                
            elif response.status_code == 404:
                print(f"📝 Sample case not found: {case_id}")
            else:
                print(f"❌ Error fetching {case_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing case {case_id}: {e}")

def test_enhanced_legal_analysis():
    """Test enhanced legal analysis endpoints."""
    print("\n⚖️ Testing enhanced legal analysis...")
    
    # Test with Brown v. Board (should exist in sample data)
    case_id = "brown-v-board-1954"
    
    # Test good law verification
    print(f"🔍 Testing good law verification for {case_id}...")
    try:
        response = requests.get(f"{API_V1_URL}/cases/{case_id}/good-law-status", timeout=10)
        if response.status_code == 200:
            verification = response.json()
            confidence = verification.get("good_law_confidence", "unknown")
            print(f"✅ Good law verification: {confidence}")
        elif response.status_code == 404:
            print(f"📝 Case not found for good law verification")
        else:
            print(f"❌ Good law verification failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Good law verification error: {e}")
    
    # Test treatment analysis
    print(f"🔍 Testing citation treatment analysis for {case_id}...")
    try:
        response = requests.get(f"{API_V1_URL}/cases/{case_id}/treatment-analysis", timeout=10)
        if response.status_code == 200:
            treatment = response.json()
            total_citations = treatment.get("total_citations", 0)
            print(f"✅ Treatment analysis: {total_citations} total citations")
        elif response.status_code == 404:
            print(f"📝 Case not found for treatment analysis")
        else:
            print(f"❌ Treatment analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Treatment analysis error: {e}")
    
    # Test authoritative precedents
    print(f"🔍 Testing authoritative precedent discovery for {case_id}...")
    try:
        response = requests.get(
            f"{API_V1_URL}/cases/{case_id}/authoritative-precedents",
            params={"target_jurisdictions": "US", "limit": 5},
            timeout=10
        )
        if response.status_code == 200:
            precedents = response.json()
            print(f"✅ Found {len(precedents)} authoritative precedents")
        elif response.status_code == 404:
            print(f"📝 Case not found for precedent discovery")
        else:
            print(f"❌ Precedent discovery failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Precedent discovery error: {e}")

def test_enhanced_search():
    """Test enhanced semantic search capabilities."""
    print("\n🔍 Testing enhanced semantic search...")
    
    # Test semantic search
    search_data = {
        "query": "equal protection constitutional rights",
        "jurisdiction": "US",
        "practice_areas": ["constitutional_law"],
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{API_V1_URL}/search/semantic",
            json=search_data,
            timeout=15
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Semantic search returned {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                case_name = result.get("case", {}).get("case_name", "Unknown")
                relevance = result.get("relevance_score", 0)
                authority = result.get("authority_score", 0)
                print(f"   {i}. {case_name} (Relevance: {relevance:.3f}, Authority: {authority:.2f})")
        else:
            print(f"❌ Semantic search failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Semantic search error: {e}")
    
    # Test case search
    try:
        response = requests.get(
            f"{API_V1_URL}/search/cases",
            params={
                "q": "constitutional law",
                "jurisdiction": "US",
                "limit": 3
            },
            timeout=15
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Case search returned {len(results)} results")
        else:
            print(f"❌ Case search failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Case search error: {e}")

def test_research_workflow():
    """Test enhanced research workflow."""
    print("\n🤖 Testing enhanced research workflow...")
    
    research_data = {
        "query": "constitutional equal protection analysis",
        "jurisdiction": "US",
        "practice_areas": ["constitutional_law"],
        "analysis_types": ["precedent_analysis", "authority_analysis"],
        "max_cases": 5,
        "include_memo": True
    }
    
    try:
        # Create research session
        response = requests.post(
            f"{API_V1_URL}/research/sessions",
            json=research_data,
            timeout=20
        )
        if response.status_code == 201:
            session = response.json()
            session_id = session["id"]
            print(f"✅ Created research session: {session_id}")
            
            # Wait a moment for background processing
            time.sleep(3)
            
            # Check session status
            response = requests.get(f"{API_V1_URL}/research/sessions/{session_id}", timeout=10)
            if response.status_code == 200:
                session_status = response.json()
                status = session_status.get("status", "unknown")
                print(f"✅ Research session status: {status}")
                
                if session_status.get("results"):
                    results = session_status["results"]
                    if "precedent_analysis" in results:
                        cases_analyzed = results["precedent_analysis"].get("cases_analyzed", 0)
                        print(f"   📊 Analyzed {cases_analyzed} precedents")
        else:
            print(f"❌ Research workflow failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Research workflow error: {e}")

def main():
    """Run all enhanced feature tests."""
    print("🚀 Testing Enhanced Legal Research Features")
    print("=" * 50)
    
    # Test basic connectivity
    if not test_api_health():
        print("❌ Basic API health check failed - aborting tests")
        return
    
    # Test enhanced health
    test_enhanced_health()
    
    # Test sample cases
    test_sample_case_lookup()
    
    # Test enhanced legal analysis
    test_enhanced_legal_analysis()
    
    # Test enhanced search
    test_enhanced_search()
    
    # Test research workflow
    test_research_workflow()
    
    print("\n" + "=" * 50)
    print("🏁 Enhanced feature testing complete!")

if __name__ == "__main__":
    main()