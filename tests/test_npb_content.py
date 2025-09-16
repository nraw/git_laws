#!/usr/bin/env python3
"""
Test NPB content to verify we get different historical versions.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_npb_historical_content():
    """Get all NPB versions of ZDoh-2 and test their content."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Get all NPB versions using EPA (worked best in previous test)
    print("=== Getting all NPB versions of ZDoh-2 ===")
    
    url = f"{base_url}/npb"
    params = {"epa": "1071-IV", "pageSize": 100}  # Get more results
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            npb_items = data.get('data', [])
            
            print(f"Found {len(npb_items)} NPB versions")
            
            # Sort by date (oldest first)
            npb_items.sort(key=lambda x: x.get('datumDokumenta', ''))
            
            print("\nTesting content for each NPB version:")
            
            for i, item in enumerate(npb_items[:15]):  # Test first 15 to avoid timeout
                npb_id = item.get('id')
                datum_dokumenta = item.get('datumDokumenta')
                naziv = item.get('naziv', '')
                
                print(f"\n{i+1}. NPB ID: {npb_id}, Date: {datum_dokumenta}")
                print(f"   Title: {naziv[:80]}...")
                
                # Get content
                try:
                    content_url = f"{base_url}/besedilo/{npb_id}"
                    content_response = requests.get(content_url, headers=headers, timeout=15)
                    
                    if content_response.status_code == 200:
                        content = content_response.text
                        content_length = len(content)
                        content_hash = hash(content) % 10000
                        
                        print(f"   Content: {content_length} chars, hash={content_hash}")
                        
                        # Check for some key phrases to see if content changes
                        key_phrases = ['dohodnina', 'davek', 'olajšava', 'davčna osnova']
                        phrase_counts = {phrase: content.lower().count(phrase) for phrase in key_phrases}
                        print(f"   Key phrases: {phrase_counts}")
                        
                    else:
                        print(f"   Content: HTTP {content_response.status_code}")
                        
                except Exception as e:
                    print(f"   Content: Error - {e}")
                    
        else:
            print(f"Error getting NPB list: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_npb_historical_content()