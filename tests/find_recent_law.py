#!/usr/bin/env python3
"""
Find a more recent law to test e-uprava linking with.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from git_laws.api_client import pisrs_client

def find_recent_laws():
    """Find laws from recent years that might have e-uprava correlations."""
    print("=== Finding Recent Laws for E-uprava Testing ===")
    
    try:
        # Search for recent laws using PISRS API
        headers = {'X-API-Key': os.getenv('PISRS_API_KEY')}
        base_url = "https://pisrs.si/extapi"
        
        # Search for laws from recent years
        url = f"{base_url}/predpis/register-predpisov"
        params = {
            'datumSprejetjaOd': '2023-01-01',
            'datumSprejemaDo': '2025-12-31',
            'vrstaAkta': 'Zakon',
            'pageSize': 20
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            laws = data.get('data', [])
            
            print(f"Found {len(laws)} recent laws (2023-2025)")
            
            for i, law in enumerate(laws):
                print(f"\n{i+1}. {law.get('mopedId', 'N/A')} - {law.get('kratica', 'N/A')}")
                print(f"   Title: {law.get('naziv', '')[:80]}...")
                print(f"   Date: {law.get('datumSprejetja', 'N/A')}")
                print(f"   EPA: {law.get('epa', 'N/A')}")
                print(f"   EVA: {law.get('eva', 'N/A')}")
                
                # Get ministry info
                ministry = "N/A"
                if 'organOdgovorenZaPripravo' in law and law['organOdgovorenZaPripravo']:
                    ministry_data = law['organOdgovorenZaPripravo']
                    if isinstance(ministry_data, list) and ministry_data:
                        ministry = ministry_data[0].get('naziv', 'N/A')
                    elif isinstance(ministry_data, dict):
                        ministry = ministry_data.get('naziv', 'N/A')
                
                print(f"   Ministry: {ministry}")
                
                if i >= 9:  # Show top 10
                    break
            
            return laws
        
        else:
            print(f"Error searching recent laws: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"Error finding recent laws: {e}")
        return []

def test_recent_law_euprava(moped_id: str):
    """Test e-uprava linking with a recent law."""
    print(f"\n=== Testing E-uprava Linking for {moped_id} ===")
    
    from git_laws.euprava_linker import euprava_linker
    
    # Get law data
    law_data = pisrs_client.get_law_by_moped_id(moped_id)
    
    if not law_data:
        print("Law not found")
        return
    
    print(f"Law: {law_data.get('KRATICA', '')} - {law_data.get('NASLOV', '')}")
    print(f"Date: {law_data.get('D_SPREJEMA', '')}")
    print(f"EVA: {law_data.get('EVA', '')}")
    
    # Try to find e-uprava links
    euprava_links = euprava_linker.find_proposal_links(law_data)
    
    if euprava_links:
        print(f"✅ Found {len(euprava_links)} e-uprava links:")
        for link in euprava_links:
            print(f"  → {link}")
    else:
        print("❌ No e-uprava links found")
    
    # Generate commit message
    print("\nGenerated commit message:")
    print("="*50)
    commit_msg = euprava_linker.generate_enhanced_commit_message(law_data)
    print(commit_msg)
    print("="*50)

if __name__ == "__main__":
    recent_laws = find_recent_laws()
    
    if recent_laws:
        # Test with the first recent law
        first_law = recent_laws[0]
        test_moped_id = first_law.get('mopedId')
        
        if test_moped_id:
            test_recent_law_euprava(test_moped_id)
    else:
        print("No recent laws found to test with")