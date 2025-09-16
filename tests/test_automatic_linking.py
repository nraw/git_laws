#!/usr/bin/env python3
"""
Test automatic e-uprava linking functionality.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.api_client import pisrs_client
from git_laws.euprava_linker import euprava_linker

def test_automatic_linking():
    """Test automatic e-uprava link discovery."""
    print("=== Testing Automatic E-uprava Linking ===")
    
    # Get sample law data
    law_id = "ZAKO4697"
    npb_versions = pisrs_client.get_historical_npb_versions(law_id)
    
    if not npb_versions:
        print("No NPB versions found")
        return
    
    # Test with the most recent version (most likely to have e-uprava correlation)
    recent_version = npb_versions[-1]
    
    print(f"Testing with recent NPB version:")
    print(f"  ID: {recent_version['ID']}")
    print(f"  Date: {recent_version['D_SPREJEMA']}")
    print(f"  EVA: {recent_version.get('EVA', 'N/A')}")
    
    gov_metadata = recent_version.get('_government_metadata', {})
    print(f"  Ministry: {gov_metadata.get('responsible_ministry', 'N/A')}")
    
    print("\nSearching for e-uprava proposals...")
    
    # Try to find e-uprava links
    euprava_links = euprava_linker.find_proposal_links(recent_version)
    
    if euprava_links:
        print(f"✅ Found {len(euprava_links)} potential e-uprava links:")
        for i, link in enumerate(euprava_links, 1):
            print(f"  {i}. {link}")
    else:
        print("❌ No direct e-uprava links found")
    
    print("\n" + "="*60)
    print("GENERATED COMMIT MESSAGE:")
    print("="*60)
    
    # Generate enhanced commit message
    commit_msg = euprava_linker.generate_enhanced_commit_message(recent_version)
    print(commit_msg)
    
    print("="*60)
    
    return euprava_links

def test_with_multiple_versions():
    """Test with several recent versions to increase chances of finding links."""
    print("\n=== Testing Multiple Recent Versions ===")
    
    law_id = "ZAKO4697"
    npb_versions = pisrs_client.get_historical_npb_versions(law_id)
    
    if len(npb_versions) < 3:
        print("Not enough versions to test")
        return
    
    # Test the 3 most recent versions
    recent_versions = npb_versions[-3:]
    
    total_links_found = 0
    
    for i, version in enumerate(recent_versions):
        print(f"\n--- Testing Version {i+1} (NPB ID: {version['ID']}) ---")
        print(f"Date: {version['D_SPREJEMA']}")
        
        euprava_links = euprava_linker.find_proposal_links(version)
        
        if euprava_links:
            print(f"✅ Found {len(euprava_links)} links")
            total_links_found += len(euprava_links)
            for link in euprava_links:
                print(f"  → {link}")
        else:
            print("❌ No links found")
    
    print(f"\nTOTAL LINKS FOUND: {total_links_found}")
    
    if total_links_found > 0:
        print("🎉 SUCCESS: Automatic e-uprava linking is working!")
    else:
        print("⚠️  No automatic links found, but enhanced search guidance is available")

if __name__ == "__main__":
    test_automatic_linking()
    test_with_multiple_versions()