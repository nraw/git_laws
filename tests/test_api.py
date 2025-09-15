#!/usr/bin/env python3
"""
Test script to verify PISRS API access with correct endpoints from pisrs.json.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_pisrs_api():
    """Test PISRS API access using correct base URL and authentication."""
    api_key = os.getenv('PISRS_API_KEY')
    if not api_key:
        print("ERROR: PISRS_API_KEY not found in environment variables")
        return False
    
    print(f"Using API key: {api_key[:10]}...")
    
    # Correct authentication method from pisrs.json
    headers = {'X-API-Key': api_key}
    
    # Correct base URL from pisrs.json
    base_url = "https://pisrs.si/extapi"
    
    # Test different endpoints from pisrs.json
    test_endpoints = [
        ("/predpis/register-predpisov/seznam", "Basic regulation list"),
        ("/predpis/register-predpisov", "Detailed regulation data"),
        ("/npb", "NPB (consolidated text) data"),
        ("/sifranti", "Code lists"),
    ]
    
    for endpoint, description in test_endpoints:
        print(f"\nTesting endpoint: {endpoint} ({description})")
        
        try:
            url = f"{base_url}{endpoint}"
            params = {'pageSize': 2}  # Request just 2 items for testing
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  SUCCESS! Received data")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  Response: List with {len(data)} items")
                        if len(data) > 0:
                            print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    elif isinstance(data, dict):
                        print(f"  Response keys: {list(data.keys())}")
                        if 'data' in data:
                            print(f"  Data count: {len(data.get('data', []))}")
                    return True
                except Exception as e:
                    print(f"  JSON parse error: {e}")
                    print(f"  Raw response: {response.text[:200]}...")
                    
            elif response.status_code == 401:
                print(f"  Unauthorized - check API key")
            elif response.status_code == 403:
                print(f"  Forbidden - check permissions")
            elif response.status_code == 404:
                print(f"  Not found - endpoint might not exist")
            else:
                print(f"  Error: HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  Exception: {e}")
    
    return False

if __name__ == "__main__":
    print("Testing PISRS API access with correct endpoints...")
    success = test_pisrs_api()
    
    if not success:
        print("\nAll tests failed. Please check:")
        print("1. API key is correct")
        print("2. API key has proper permissions")
        print("3. Network connectivity")
    else:
        print("\nAPI access successful!")