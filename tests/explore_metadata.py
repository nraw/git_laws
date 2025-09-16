#!/usr/bin/env python3
"""
Explore what metadata is available in PISRS API responses.
"""

import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def explore_pisrs_metadata():
    """Explore the full metadata available in PISRS API."""
    api_key = os.getenv('PISRS_API_KEY')
    headers = {'X-API-Key': api_key}
    base_url = "https://pisrs.si/extapi"
    
    # Get detailed data for ZAKO4697 to see all available fields
    print("=== Exploring PISRS API metadata for ZAKO4697 ===")
    
    # 1. Get basic law data
    url = f"{base_url}/predpis/register-predpisov"
    params = {"mopedID": "ZAKO4697", "pageSize": 1}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                law = data['data'][0]
                print("\n1. BASIC LAW METADATA:")
                print(json.dumps(law, indent=2, ensure_ascii=False))
                
                # 2. Check if there are related data endpoints
                print("\n2. CHECKING FOR ADDITIONAL METADATA ENDPOINTS...")
                
                # Try to get more detailed info using different endpoints
                law_id = law.get('id')
                if law_id:
                    # Try to get detailed law info
                    detail_endpoints = [
                        f"/predpis/{law_id}",
                        f"/predpis/podrobnosti/{law_id}",
                        f"/predpis/metadata/{law_id}",
                    ]
                    
                    for endpoint in detail_endpoints:
                        try:
                            detail_response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
                            if detail_response.status_code == 200:
                                print(f"\n✓ {endpoint} endpoint available:")
                                detail_data = detail_response.json()
                                print(json.dumps(detail_data, indent=2, ensure_ascii=False)[:1000] + "...")
                            elif detail_response.status_code != 404:
                                print(f"✗ {endpoint}: HTTP {detail_response.status_code}")
                        except Exception as e:
                            print(f"✗ {endpoint}: {e}")
                
                # 3. Check NPB metadata
                print("\n3. NPB METADATA EXPLORATION:")
                epa = law.get('epa')
                if epa:
                    npb_params = {"epa": epa, "pageSize": 3}  # Get first 3 NPB versions
                    npb_response = requests.get(f"{base_url}/npb", headers=headers, params=npb_params, timeout=30)
                    if npb_response.status_code == 200:
                        npb_data = npb_response.json()
                        if npb_data.get('data'):
                            print(f"Found {len(npb_data['data'])} NPB versions. First one:")
                            print(json.dumps(npb_data['data'][0], indent=2, ensure_ascii=False))
                
                # 4. Look for proposer information in existing fields
                print("\n4. PROPOSER/GOVERNMENT INFO IN EXISTING DATA:")
                proposer_fields = ['predlagatelj', 'proposer', 'organ', 'ministry', 'vlada', 'government']
                found_proposer_fields = []
                
                def find_proposer_info(obj, prefix=""):
                    for key, value in obj.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if any(field.lower() in key.lower() for field in proposer_fields):
                            found_proposer_fields.append((full_key, value))
                        if isinstance(value, dict):
                            find_proposer_info(value, full_key)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            for i, item in enumerate(value[:3]):  # Check first 3 items
                                find_proposer_info(item, f"{full_key}[{i}]")
                
                find_proposer_info(law)
                
                if found_proposer_fields:
                    print("Found potential proposer/government fields:")
                    for field, value in found_proposer_fields:
                        print(f"  {field}: {value}")
                else:
                    print("No obvious proposer/government fields found in basic data")
                
            else:
                print("No law data found")
        else:
            print(f"Error: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def explore_euprava_structure():
    """Explore e-uprava predlog predpisa URL structure."""
    print("\n\n=== E-UPRAVA STRUCTURE ANALYSIS ===")
    
    # Analyze the URL pattern from the example
    example_url = "https://e-uprava.gov.si/si/drzava-in-druzba/e-demokracija/predlogi-predpisov/predlog-predpisa.html?id=17855&lang=si"
    
    print(f"Example URL: {example_url}")
    print("\nURL Structure Analysis:")
    print("- Base: e-uprava.gov.si/si/drzava-in-druzba/e-demokracija/predlogi-predpisov/")
    print("- Pattern: predlog-predpisa.html?id={ID}&lang={LANG}")
    print("- Example ID: 17855")
    
    print("\nPossible approaches to link PISRS data with e-uprava:")
    print("1. EPA/SOP/EVA numbers might map to e-uprava IDs")
    print("2. NPB document numbers might contain e-uprava references") 
    print("3. Date-based correlation between PISRS and e-uprava")
    print("4. Text analysis to find proposal references in PISRS content")
    
    # Check if we can find any numeric patterns in PISRS data that might match
    print("\n4. NUMERIC PATTERN ANALYSIS:")
    print("Need to check if any PISRS numeric fields match e-uprava ID patterns...")

if __name__ == "__main__":
    explore_pisrs_metadata()
    explore_euprava_structure()