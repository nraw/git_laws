#!/usr/bin/env python3
"""
Test script to find NPB versions of ZDoh-2 (ZAKO4697) using different search methods.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def search_zdoh_npb():
    """Search for NPB versions of ZDoh-2 using different approaches."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Different search strategies for finding ZDoh-2 NPB versions
    search_strategies = [
        {
            "name": "Search by MOPED ID",
            "params": {"stevilkaDokumenta": "ZAKO4697", "pageSize": 50}
        },
        {
            "name": "Search by law code ZDoh-2",
            "params": {"naziv": "ZDoh-2", "pageSize": 50}
        },
        {
            "name": "Search by full title dohodnina",
            "params": {"naziv": "dohodnina", "pageSize": 50}
        },
        {
            "name": "Search by date range when ZDoh-2 was active",
            "params": {"datumDokumentaOd": "2006-01-01", "datumDokumentaDo": "2024-12-31", "pageSize": 50}
        }
    ]
    
    url = f"{base_url}/npb"
    
    for strategy in search_strategies:
        print(f"\n=== {strategy['name']} ===")
        
        try:
            response = requests.get(url, headers=headers, params=strategy['params'], timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                npb_items = data.get('data', [])
                print(f"Found {len(npb_items)} NPB items")
                
                # Filter for items that might be ZDoh-2 related
                zdoh_items = []
                for item in npb_items:
                    naziv = item.get('naziv', '').lower()
                    stevilka = item.get('stevilkaDokumenta', '')
                    
                    if any(term in naziv for term in ['zdoh', 'dohodnin', 'income']):
                        zdoh_items.append(item)
                
                print(f"Found {len(zdoh_items)} items potentially related to ZDoh-2:")
                
                for item in zdoh_items[:10]:  # Show first 10 matches
                    npb_id = item.get('id')
                    datum_dokumenta = item.get('datumDokumenta')
                    naziv = item.get('naziv', '')
                    stevilka = item.get('stevilkaDokumenta', '')
                    
                    print(f"  ID: {npb_id}, Date: {datum_dokumenta}, Number: {stevilka}")
                    print(f"  Title: {naziv[:150]}...")
                    print()
                    
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {e}")

def search_in_register_predpisov():
    """Search the main register for ZDoh-2 and check if it has NPB references."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    print(f"\n=== Searching main register for ZAKO4697 details ===")
    
    url = f"{base_url}/predpis/register-predpisov"
    params = {"mopedID": "ZAKO4697", "pageSize": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                law = data['data'][0]
                print("Found law details:")
                print(f"  ID: {law.get('id')}")
                print(f"  MOPED ID: {law.get('mopedId')}")
                print(f"  KRATICA: {law.get('kratica')}")
                print(f"  NAZIV: {law.get('naziv')}")
                print(f"  EPA: {law.get('epa')}")
                print(f"  SOP: {law.get('sop')}")
                print(f"  EVA: {law.get('eva')}")
                
                # Check if there are any NPB-related fields
                for key, value in law.items():
                    if 'npb' in key.lower() or 'besedilo' in key.lower():
                        print(f"  NPB field {key}: {value}")
                        
                return law
        else:
            print(f"Error: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

if __name__ == "__main__":
    # First check the main register
    law_details = search_in_register_predpisov()
    
    # Then search for NPB versions
    search_zdoh_npb()
    
    if law_details:
        print(f"\n=== Testing alternative NPB search with law details ===")
        # Try searching with different identifiers from the law details
        api_key = os.getenv('PISRS_API_KEY')
        headers = {'X-API-Key': api_key}
        base_url = "https://pisrs.si/extapi"
        
        search_params = []
        if law_details.get('epa'):
            search_params.append({"epa": law_details['epa'], "pageSize": 50})
        if law_details.get('sop'):
            search_params.append({"sop": law_details['sop'], "pageSize": 50})
        if law_details.get('eva'):
            search_params.append({"eva": law_details['eva'], "pageSize": 50})
            
        for params in search_params:
            param_name = list(params.keys())[0]
            print(f"\nSearching NPB by {param_name}: {params[param_name]}")
            
            try:
                url = f"{base_url}/npb"
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    npb_items = data.get('data', [])
                    print(f"Found {len(npb_items)} NPB items")
                    
                    for item in npb_items[:5]:  # Show first 5
                        print(f"  ID: {item.get('id')}, Date: {item.get('datumDokumenta')}")
                        print(f"  Title: {item.get('naziv', '')[:100]}...")
                        print()
                else:
                    print(f"Error: {response.status_code}")
            except Exception as e:
                print(f"Exception: {e}")