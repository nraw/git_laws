#!/usr/bin/env python3
"""
Test actual correlation between PISRS EVA/EPA codes and e-uprava evidenca numbers.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from bs4 import BeautifulSoup
from git_laws.api_client import pisrs_client

def extract_evidenca_from_euprava(url):
    """Extract evidenca number from e-uprava page."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for evidenca patterns
            import re
            evidenca_pattern = r'evidenc[ae]?\s*[:\-]?\s*(\d{4}[-\s]\d{4}[-\s]\d{4})'
            match = re.search(evidenca_pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(' ', '-')
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def test_correlation_hypothesis():
    """Test if PISRS EVA codes correlate with e-uprava evidenca numbers."""
    print("=== Testing PISRS ↔ E-uprava Correlation Hypothesis ===")
    
    # Get sample PISRS data
    law_id = "ZAKO4697"  # ZDoh-2
    target_law = pisrs_client.get_law_by_moped_id(law_id)
    
    if target_law and target_law.get('_raw'):
        raw_data = target_law['_raw']
        eva_code = raw_data.get('eva', '')
        epa_code = raw_data.get('epa', '')
        sop_code = raw_data.get('sop', '')
        
        print(f"PISRS {law_id} identifiers:")
        print(f"  EVA: {eva_code}")
        print(f"  EPA: {epa_code}")
        print(f"  SOP: {sop_code}")
        print()
        
        # Test sample e-uprava URLs
        test_urls = [
            "https://e-uprava.gov.si/si/drzava-in-druzava/e-demokracija/predlogi-predpisov/predlog-predpisa.html?id=17855",
            "https://e-uprava.gov.si/si/drzava-in-druzava/e-demokracija/predlogi-predpisov/predlog-predpisa.html?id=17640", 
            "https://e-uprava.gov.si/drzava-in-druzba/e-demokracija/predlogi-predpisov/predlog-predpisa.html?id=10927"
        ]
        
        print("E-uprava evidenca numbers found:")
        for url in test_urls:
            evidenca = extract_evidenca_from_euprava(url)
            if evidenca:
                print(f"  {url.split('id=')[1]}: {evidenca}")
            else:
                print(f"  {url.split('id=')[1]}: No evidenca found")
        
        print()
        print("CORRELATION ANALYSIS:")
        print("- PISRS EVA format: YYYY-NNNN-NNNN (e.g., 2006-1611-0019)")
        print("- E-uprava evidenca format: YYYY-NNNN-NNNN (e.g., 2025-3350-0022)")
        print("- Both follow same pattern!")
        print()
        print("HYPOTHESIS: EVA codes from PISRS might directly correlate")
        print("with evidenca numbers in e-uprava for newer proposals.")
        
        return eva_code

def test_direct_search_approach():
    """Test if we can search e-uprava by constructing URLs based on PISRS data."""
    print("\n=== Testing Direct Search Approach ===")
    
    # For newer laws, we might be able to construct search URLs
    print("STRATEGY: Use PISRS metadata to construct e-uprava search queries")
    print()
    
    # Get recent amendment data
    law_id = "ZAKO4697"
    npb_versions = pisrs_client.get_historical_npb_versions(law_id)
    
    if npb_versions:
        print("Recent NPB versions (potential e-uprava correlation candidates):")
        
        # Look at the most recent versions
        recent_versions = npb_versions[-5:]  # Last 5 versions
        
        for version in recent_versions:
            date = version.get('D_SPREJEMA', '')
            title = version.get('NASLOV', '')
            eva = version.get('EVA', '')
            ministry = version.get('_government_metadata', {}).get('responsible_ministry', '')
            
            print(f"  Date: {date}, EVA: {eva}")
            print(f"  Ministry: {ministry}")
            print(f"  Title: {title[:60]}...")
            
            # Construct potential e-uprava search URL
            search_url = "https://e-uprava.gov.si/si/drzava-in-druzba/e-demokracija/predlogi-predpisov/"
            print(f"  Search at: {search_url}")
            print(f"  Query: ministry='{ministry}' OR evidenca='{eva}'")
            print()

if __name__ == "__main__":
    eva_code = test_correlation_hypothesis()
    test_direct_search_approach()
    
    print("\n=== ACTIONABLE CONCLUSION ===")
    print("Instead of manual search instructions, we could potentially:")
    print("1. For recent laws: Try to fetch e-uprava pages using EVA as evidenca")
    print("2. For older laws: Search by ministry + date range")  
    print("3. Create actual working links instead of search suggestions")
    print()
    print("NEXT STEP: Implement automatic e-uprava link generation!")