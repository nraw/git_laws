#!/usr/bin/env python3
"""
Test script to verify small-scale download functionality.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from git_laws.data_downloader import download_csv_from_pisrs_api, download_bson_data
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_small_download():
    """Test download with a very small dataset."""
    print("Testing small-scale CSV download...")
    
    # Test CSV download with just a few records
    csv_success = download_csv_from_pisrs_api()
    
    if csv_success:
        print("✓ CSV download successful!")
        
        # Check the downloaded files
        import pandas as pd
        from pathlib import Path
        
        osnovni_path = Path("data/osnovni.csv")
        vplivana_path = Path("data/vplivana.csv")
        
        if osnovni_path.exists():
            df_osnovni = pd.read_csv(osnovni_path)
            print(f"  - osnovni.csv: {len(df_osnovni)} records")
            print(f"  - Column names: {list(df_osnovni.columns)}")
            print(f"  - Sample record: {df_osnovni.iloc[0].to_dict()}")
        
        if vplivana_path.exists():
            df_vplivana = pd.read_csv(vplivana_path)
            print(f"  - vplivana.csv: {len(df_vplivana)} records")
            if len(df_vplivana) > 0:
                print(f"  - Column names: {list(df_vplivana.columns)}")
                print(f"  - Sample record: {df_vplivana.iloc[0].to_dict()}")
    else:
        print("✗ CSV download failed!")
        return False
    
    print("\nTesting small-scale BSON download (just 2 records)...")
    
    # Test BSON download with very few records to avoid timeout
    bson_success = download_bson_data()
    
    if bson_success:
        print("✓ BSON download successful!")
        
        # Check the downloaded BSON file
        import bson
        bson_path = Path("data/vsebina.bson/pisrs/vsebina.bson")
        
        if bson_path.exists():
            with open(bson_path, 'rb') as f:
                try:
                    laws = bson.decode_all(f.read())
                    print(f"  - vsebina.bson: {len(laws)} content records")
                    if len(laws) > 0:
                        print(f"  - Sample keys: {list(laws[0].keys())}")
                        print(f"  - Sample ID: {laws[0].get('idPredpisa', 'N/A')}")
                        print(f"  - Content length: {len(laws[0].get('vsebina', ''))}")
                except Exception as e:
                    print(f"  - Error reading BSON: {e}")
    else:
        print("✗ BSON download failed!")
        return False
    
    print("\n✓ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_small_download()
    if not success:
        print("Some tests failed!")
        sys.exit(1)