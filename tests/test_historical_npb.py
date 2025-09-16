#!/usr/bin/env python3
"""
Test script to explore historical NPB (consolidated text) retrieval.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_historical_npb_search():
    """Test NPB endpoint with date parameters to find historical consolidated texts."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Test NPB search for ZAKO4697 (ZDoh-2) with different date ranges
    test_cases = [
        {
            "name": "All NPB versions for ZDoh-2",
            "params": {"stevilkaDokumenta": "ZAKO4697", "pageSize": 100}
        },
        {
            "name": "NPB versions created 2007-2010", 
            "params": {"stevilkaDokumenta": "ZAKO4697", "datumDokumentaOd": "2007-01-01", "datumDokumentaDo": "2010-12-31", "pageSize": 100}
        },
        {
            "name": "NPB versions created 2010-2015",
            "params": {"stevilkaDokumenta": "ZAKO4697", "datumDokumentaOd": "2010-01-01", "datumDokumentaDo": "2015-12-31", "pageSize": 100}
        },
        {
            "name": "NPB versions created 2015-2020",
            "params": {"stevilkaDokumenta": "ZAKO4697", "datumDokumentaOd": "2015-01-01", "datumDokumentaDo": "2020-12-31", "pageSize": 100}
        },
        {
            "name": "NPB versions created 2020-2025",
            "params": {"stevilkaDokumenta": "ZAKO4697", "datumDokumentaOd": "2020-01-01", "datumDokumentaDo": "2025-12-31", "pageSize": 100}
        }
    ]
    
    url = f"{base_url}/npb"
    
    for test_case in test_cases:
        print(f"\n=== {test_case['name']} ===")
        
        try:
            response = requests.get(url, headers=headers, params=test_case['params'], timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                npb_items = data.get('data', [])
                print(f"Found {len(npb_items)} NPB items")
                
                for item in npb_items:
                    npb_id = item.get('id')
                    datum_dokumenta = item.get('datumDokumenta')
                    naziv = item.get('naziv', '')
                    stevilka = item.get('stevilkaDokumenta', '')
                    
                    print(f"  ID: {npb_id}, Date: {datum_dokumenta}, Number: {stevilka}")
                    print(f"  Title: {naziv[:100]}...")
                    
                    # Test getting content for this NPB ID
                    if npb_id:
                        try:
                            content_url = f"{base_url}/besedilo/{npb_id}"
                            content_response = requests.get(content_url, headers=headers, timeout=10)
                            if content_response.status_code == 200:
                                content_length = len(content_response.text)
                                content_hash = hash(content_response.text) % 10000
                                print(f"    Content: {content_length} chars, hash={content_hash}")
                            else:
                                print(f"    Content: HTTP {content_response.status_code}")
                        except Exception as e:
                            print(f"    Content: Error {e}")
                    print()
                    
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_historical_npb_search()