#!/usr/bin/env python3
"""
Test enhanced metadata functionality for git commits.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.api_client import pisrs_client

def test_enhanced_metadata():
    """Test that we can extract enhanced metadata from PISRS API."""
    print("=== Testing Enhanced Metadata Extraction ===")
    
    # Test with ZAKO4697 (ZDoh-2)
    law_id = "ZAKO4697"
    print(f"Testing metadata extraction for {law_id}...")
    
    try:
        # Get historical NPB versions with enhanced metadata
        npb_versions = pisrs_client.get_historical_npb_versions(law_id)
        
        if not npb_versions:
            print("No NPB versions found")
            return
        
        print(f"Found {len(npb_versions)} NPB versions")
        
        # Test first few versions to see metadata
        for i, version in enumerate(npb_versions[:5]):
            print(f"\n--- Version {i+1} (NPB ID: {version['ID']}) ---")
            print(f"Date: {version['D_SPREJEMA']}")
            print(f"Title: {version['NASLOV'][:80]}...")
            
            # Test government metadata
            gov_metadata = version.get('_government_metadata', {})
            if gov_metadata:
                print(f"Responsible Ministry: {gov_metadata.get('responsible_ministry', 'N/A')}")
                print(f"Adopting Body: {gov_metadata.get('adopting_body', 'N/A')}")
                print(f"Government Info: {gov_metadata.get('government_info', 'N/A')}")
            
            # Test identifiers
            print(f"EPA: {version.get('EPA', 'N/A')}")
            print(f"SOP: {version.get('SOP', 'N/A')}")
            print(f"EVA: {version.get('EVA', 'N/A')}")
            
            # Test commit message format (matching main.py logic)
            commit_msg_parts = [f"{version['KRATICA']} - {version['ID']} - {version['NASLOV']}"]
            
            if gov_metadata and gov_metadata.get('government_info'):
                commit_msg_parts.append(gov_metadata['government_info'])
            
            identifiers = []
            if version.get('EPA'):
                identifiers.append(f"EPA: {version['EPA']}")
            if version.get('SOP'):
                identifiers.append(f"SOP: {version['SOP']}")
            if version.get('EVA'):
                identifiers.append(f"EVA: {version['EVA']}")
            
            if identifiers:
                commit_msg_parts.append(' | '.join(identifiers))
            
            commit_msg = '\n'.join(commit_msg_parts)
            print(f"\nSample commit message:")
            print("=" * 60)
            print(commit_msg)
            print("=" * 60)
            
    except Exception as e:
        print(f"Error testing enhanced metadata: {e}")

if __name__ == "__main__":
    test_enhanced_metadata()