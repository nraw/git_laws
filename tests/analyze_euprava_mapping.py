#!/usr/bin/env python3
"""
Analyze potential mapping strategies between PISRS data and e-uprava proposal URLs.

Based on research:
1. e-uprava uses numeric IDs in URLs (e.g., id=17855)
2. PISRS has EPA, SOP, EVA identifiers
3. No direct mapping is immediately obvious

This script explores potential correlation patterns.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.api_client import pisrs_client

def analyze_mapping_potential():
    """Analyze potential mapping strategies between PISRS and e-uprava."""
    print("=== E-uprava URL Mapping Analysis ===")
    print("Based on research findings:")
    print("- e-uprava uses numeric IDs (e.g., id=17855)")
    print("- PISRS provides EPA, SOP, EVA identifiers")
    print("- Evidence numbers follow format YYYY-NNNN-NNNN")
    print()
    
    # Get sample data from PISRS
    law_id = "ZAKO4697"
    target_law = pisrs_client.get_law_by_moped_id(law_id)
    
    if target_law and target_law.get('_raw'):
        raw_data = target_law['_raw']
        print(f"Sample PISRS data for {law_id}:")
        print(f"  EPA: {raw_data.get('epa')}")
        print(f"  SOP: {raw_data.get('sop')}")  
        print(f"  EVA: {raw_data.get('eva')}")
        print(f"  Date Accepted: {raw_data.get('datumSprejetja')}")
        print()
        
        # Analyze potential mapping strategies
        print("POTENTIAL MAPPING STRATEGIES:")
        print()
        
        print("1. DIRECT IDENTIFIER MAPPING")
        print("   - Look for EPA/SOP/EVA references in e-uprava proposal text")
        print("   - Search e-uprava by law title or ministry")
        print("   - Match by date ranges")
        print()
        
        print("2. MINISTRY/GOVERNMENT CORRELATION") 
        print("   - Map ministry names between systems")
        print("   - Cross-reference by responsible ministry")
        ministry = "N/A"
        if 'organOdgovorenZaPripravo' in raw_data:
            ministry_data = raw_data['organOdgovorenZaPripravo']
            if isinstance(ministry_data, list) and ministry_data:
                ministry = ministry_data[0].get('naziv', 'N/A')
            elif isinstance(ministry_data, dict):
                ministry = ministry_data.get('naziv', 'N/A')
        print(f"   - For ZDoh-2: {ministry}")
        print()
        
        print("3. TEMPORAL CORRELATION")
        print("   - Match by law acceptance/proposal dates")
        print("   - Look for amendments in date proximity")
        print(f"   - ZDoh-2 accepted: {raw_data.get('datumSprejetja')}")
        print()
        
        print("4. EVIDENCE NUMBER PATTERN ANALYSIS")
        print("   - e-uprava evidence: YYYY-NNNN-NNNN format")
        print("   - Could correlate with SOP or other PISRS identifiers")
        print(f"   - SOP pattern: {raw_data.get('sop')} (YYYY-MM-NNNN format)")
        print()
        
        print("5. RECOMMENDATION FOR IMPLEMENTATION:")
        print("   Since direct mapping isn't available, suggest a multi-step approach:")
        print("   a) For each NPB version, include EPA/SOP/EVA in commit message")
        print("   b) Add government ministry and date information")
        print("   c) Create a note in commit message about potential e-uprava correlation")
        print("   d) Users can manually search e-uprava using the provided identifiers")
        print()
        
        print("ENHANCED COMMIT MESSAGE EXAMPLE:")
        print("="*60)
        sample_commit = f"""ZDoh-2 - 10856982 - Zakon o dohodnini (ZDoh-2)
Prepared by: {ministry} | Adopted by: Državni zbor RS
EPA: {raw_data.get('epa')} | SOP: {raw_data.get('sop')} | EVA: {raw_data.get('eva')}

Note: To find related e-uprava proposals, search:
https://e-uprava.gov.si/si/drzava-in-druzba/e-demokracija/predlogi-predpisov/
using EPA/SOP identifiers or ministry name."""
        
        print(sample_commit)
        print("="*60)

def suggest_implementation_approach():
    """Suggest concrete implementation steps."""
    print("\n=== IMPLEMENTATION RECOMMENDATIONS ===")
    print()
    
    print("PHASE 1: Enhanced Metadata (COMPLETED)")
    print("✓ Add government ministry to commit messages")
    print("✓ Include EPA/SOP/EVA identifiers")  
    print("✓ Add adopting body information")
    print()
    
    print("PHASE 2: E-uprava Link Suggestions")
    print("□ Add e-uprava search URL template to commit messages")
    print("□ Include ministry name for e-uprava filtering")
    print("□ Add note about manual correlation process")
    print()
    
    print("PHASE 3: Future Enhancements (Optional)")
    print("□ Create mapping database of known correlations")
    print("□ Implement web scraping to find matches")
    print("□ Add government timeline correlation")
    print()
    
    print("IMMEDIATE NEXT STEP:")
    print("Update commit messages to include e-uprava search guidance")

if __name__ == "__main__":
    analyze_mapping_potential()
    suggest_implementation_approach()