#!/usr/bin/env python3
"""
Inspect NPB data to understand what information is available for each version.
"""

import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.api_client import pisrs_client

def inspect_npb_details():
    """Examine NPB data structure to find amendment information."""
    print("=== Inspecting NPB Data Structure ===")
    
    # Get NPB versions for ZDoh-2
    law_id = "ZAKO4697"
    npb_versions = pisrs_client.get_historical_npb_versions(law_id)
    
    if not npb_versions:
        print("No NPB versions found")
        return
    
    print(f"Found {len(npb_versions)} NPB versions")
    
    # Look at a few different versions to see what data is available
    for i, version in enumerate(npb_versions[:5]):
        print(f"\n=== NPB Version {i+1} ===")
        print(f"ID: {version['ID']}")
        print(f"Date: {version['D_SPREJEMA']}")
        print(f"Title: {version['NASLOV']}")
        
        # Examine the raw NPB data
        raw_npb = version.get('_raw', {})
        print("\nRaw NPB fields:")
        for key, value in raw_npb.items():
            if isinstance(value, str) and len(str(value)) < 100:
                print(f"  {key}: {value}")
            elif isinstance(value, (int, float, bool)):
                print(f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}: [list with {len(value)} items]")
            elif isinstance(value, dict):
                print(f"  {key}: [dict with {len(value)} keys: {list(value.keys())[:5]}]")
            else:
                print(f"  {key}: {type(value)}")
        
        print(f"\n  Full raw data for version {i+1}:")
        print("  " + "="*60)
        print(json.dumps(raw_npb, indent=2, ensure_ascii=False)[:800] + "...")
        print("  " + "="*60)

def inspect_amendment_relationships():
    """Try to find amendment relationships in PISRS data."""
    print("\n\n=== Looking for Amendment Information ===")
    
    # Get the base law data to see amendment references
    law_id = "ZAKO4697"
    base_law = pisrs_client.get_law_by_moped_id(law_id)
    
    if base_law and base_law.get('_raw'):
        raw_data = base_law['_raw']
        print(f"Base law: {base_law['KRATICA']}")
        
        # Look for amendment-related fields
        print("\nAmendment-related fields in base law:")
        amendment_fields = ['posegiVPredpis', 'vpliviNaPredpis', 'spremembe', 'amendments']
        
        for field in amendment_fields:
            if field in raw_data:
                value = raw_data[field]
                print(f"\n{field}:")
                if isinstance(value, list):
                    print(f"  List with {len(value)} items:")
                    for i, item in enumerate(value[:3]):  # Show first 3
                        if isinstance(item, dict):
                            moped_id = item.get('mopedID', 'N/A')
                            naziv = item.get('naziv', 'N/A')
                            print(f"    {i+1}. {moped_id}: {naziv[:60]}...")
                        else:
                            print(f"    {i+1}. {item}")
                else:
                    print(f"  {value}")
    
    print("\nStrategy: Use 'posegiVPredpis' to find individual amendments!")

if __name__ == "__main__":
    inspect_npb_details()
    inspect_amendment_relationships()