#!/usr/bin/env python3
"""
Debug script to examine PISRS API response structure.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_register_predpisov():
    """Debug the register-predpisov endpoint response structure."""
    api_key = os.getenv('PISRS_API_KEY')
    if not api_key:
        print("ERROR: PISRS_API_KEY not found in environment variables")
        return False
    
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Test the register-predpisov endpoint with pagination
    url = f"{base_url}/predpis/register-predpisov"
    params = {'pageSize': 2, 'page': 1}  # Just get 2 items
    
    print(f"Testing URL: {url}")
    print(f"Parameters: {params}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse structure:")
            print(f"Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                
                # Check for common pagination structures
                if 'data' in data:
                    print(f"data field type: {type(data['data'])}")
                    if isinstance(data['data'], list) and len(data['data']) > 0:
                        print(f"First data item keys: {list(data['data'][0].keys())}")
                        print(f"First data item sample: {json.dumps(data['data'][0], indent=2, ensure_ascii=False)[:500]}...")
                
                if 'result' in data:
                    print(f"result field type: {type(data['result'])}")
                    if isinstance(data['result'], list) and len(data['result']) > 0:
                        print(f"First result item keys: {list(data['result'][0].keys())}")
                        print(f"First result item sample: {json.dumps(data['result'][0], indent=2, ensure_ascii=False)[:500]}...")
                
                # Show full structure for small response
                print(f"\nFull response structure (keys only):")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                    else:
                        print(f"  {key}: {type(value)} = {value}")
                        
            elif isinstance(data, list):
                print(f"Response is a list with {len(data)} items")
                if len(data) > 0:
                    print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def debug_npb():
    """Debug the NPB endpoint response structure."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Test the NPB endpoint
    url = f"{base_url}/npb"
    params = {'pageSize': 2, 'page': 1}  # Just get 2 items
    
    print(f"\n\nTesting NPB endpoint:")
    print(f"URL: {url}")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                        if len(value) > 0 and isinstance(value[0], dict):
                            print(f"    First item keys: {list(value[0].keys())}")
                    else:
                        print(f"  {key}: {type(value)} = {value}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_register_predpisov()
    debug_npb()