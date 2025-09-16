#!/usr/bin/env python3
"""
Test the corrected amendment naming and metadata.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.api_client import pisrs_client

def test_amendment_naming():
    """Test that NPB versions now get proper amendment names."""
    print("=== Testing Corrected Amendment Naming ===")
    
    law_id = "ZAKO4697"
    npb_versions = pisrs_client.get_historical_npb_versions(law_id)
    
    if not npb_versions:
        print("No NPB versions found")
        return
    
    print(f"Found {len(npb_versions)} NPB versions")
    
    # Test first 10 versions to see amendment naming
    for i, version in enumerate(npb_versions[:10]):
        kratica = version.get('KRATICA', '')
        amendment_name = version.get('_amendment_name', '')
        version_number = version.get('_version_number', '')
        date = version.get('D_SPREJEMA', '')
        
        print(f"{i+1:2d}. {kratica:8s} (v{version_number}) - {date} - ID: {version['ID']}")
        
        # Test commit message format
        government_metadata = version.get('_government_metadata', {})
        
        commit_msg_parts = [f"{amendment_name} - {version['ID']} - {version['NASLOV']}"]
        
        if government_metadata and government_metadata.get('government_info'):
            commit_msg_parts.append(government_metadata['government_info'])
        
        commit_msg = '\n'.join(commit_msg_parts)
        
        print(f"    Commit message preview:")
        for line in commit_msg.split('\n'):
            print(f"    {line}")
        print()

if __name__ == "__main__":
    test_amendment_naming()