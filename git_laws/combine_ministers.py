#!/usr/bin/env python3
"""
Script to combine all government minister JSON files into a single file
and provide functionality to query minister data by ministry and date.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import glob
from config import MINISTERS_DIR, MINISTERS_COMBINED_FILE

def combine_minister_files(input_dir: str = MINISTERS_DIR, output_file: str = MINISTERS_COMBINED_FILE) -> Dict:
    """
    Combine all government minister JSON files into a single structured file.

    Args:
        input_dir: Directory containing individual government JSON files
        output_file: Output file path for combined data

    Returns:
        Combined data structure
    """
    combined_data = {
        "metadata": {
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "Combined Slovenian government ministers data (1990-2022)",
            "source": "Combined from individual government files"
        },
        "governments": [],
        "ministers": []  # Flattened list of all ministers for easier querying
    }

    # Get all JSON files in the input directory
    json_files = sorted(glob.glob(os.path.join(input_dir, "government_*.json")))

    print(f"Found {len(json_files)} government files to combine...")

    for file_path in json_files:
        print(f"Processing {os.path.basename(file_path)}...")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        government = data["government"]
        combined_data["governments"].append(government)

        # Flatten ministers for easier querying
        if "ministers" in government:
            for minister in government["ministers"]:
                # Add government context to each minister
                minister_data = minister.copy()
                minister_data["government_number"] = government["number"]
                minister_data["government_period"] = government["period"]
                combined_data["ministers"].append(minister_data)

    # Save combined data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"Combined data saved to {output_file}")
    print(f"Total governments: {len(combined_data['governments'])}")
    print(f"Total minister records: {len(combined_data['ministers'])}")

    return combined_data

def find_minister_by_ministry_and_date(
    ministry_name: str,
    date: str,
    language: str = "en",
    data_file: str = MINISTERS_COMBINED_FILE
) -> Optional[Dict]:
    """
    Find the minister in charge of a specific ministry on a given date.

    Args:
        ministry_name: Name of the ministry (in English or Slovenian)
        date: Date in YYYY-MM-DD format
        language: Language for output ("en" or "sl")
        data_file: Path to combined ministers data file

    Returns:
        Dictionary containing minister information or None if not found
    """
    # Load combined data
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse the query date
    query_date = datetime.strptime(date, "%Y-%m-%d")

    # Search through all ministers
    for minister in data["ministers"]:
        # Check if ministry name matches (in either language)
        ministry_match = False
        if isinstance(minister.get("ministry"), dict):
            # Bilingual format
            ministry_en = minister["ministry"].get("en", "").lower()
            ministry_sl = minister["ministry"].get("sl", "").lower()
            ministry_match = (ministry_name.lower() in ministry_en or
                            ministry_name.lower() in ministry_sl or
                            ministry_en in ministry_name.lower() or
                            ministry_sl in ministry_name.lower())
        else:
            # Legacy string format
            ministry_match = ministry_name.lower() in minister.get("ministry", "").lower()

        if ministry_match:
            # Check if date falls within minister's term
            start_date = datetime.strptime(minister["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(minister["end_date"], "%Y-%m-%d")

            if start_date <= query_date <= end_date:
                # Format output based on requested language
                result = {
                    "name": minister["name"],
                    "start_date": minister["start_date"],
                    "end_date": minister["end_date"],
                    "government_number": minister["government_number"],
                    "government_period": minister["government_period"],
                    "ministry_code": minister.get("ministry_code", "")
                }

                # Add bilingual fields based on language preference
                if isinstance(minister.get("ministry"), dict):
                    result["ministry"] = minister["ministry"].get(language, minister["ministry"]["en"])
                    result["title"] = minister["title"].get(language, minister["title"]["en"]) if isinstance(minister.get("title"), dict) else minister.get("title", "")
                else:
                    result["ministry"] = minister.get("ministry", "")
                    result["title"] = minister.get("title", "")

                # Add optional fields if present
                if "termination_reason" in minister:
                    if isinstance(minister["termination_reason"], dict):
                        result["termination_reason"] = minister["termination_reason"].get(language, minister["termination_reason"]["en"])
                    else:
                        result["termination_reason"] = minister["termination_reason"]

                if "predecessor" in minister:
                    result["predecessor"] = minister["predecessor"]

                return result

    return None

def list_all_ministries(data_file: str = "data/ministers_combined.json", language: str = "en") -> List[str]:
    """
    Get a list of all unique ministry names in the dataset.

    Args:
        data_file: Path to combined ministers data file
        language: Language for ministry names ("en" or "sl")

    Returns:
        Sorted list of unique ministry names
    """
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ministries = set()
    for minister in data["ministers"]:
        if isinstance(minister.get("ministry"), dict):
            ministry_name = minister["ministry"].get(language, minister["ministry"]["en"])
        else:
            ministry_name = minister.get("ministry", "")

        if ministry_name:
            ministries.add(ministry_name)

    return sorted(list(ministries))

def get_ministry_timeline(
    ministry_name: str,
    language: str = "en",
    data_file: str = MINISTERS_COMBINED_FILE
) -> List[Dict]:
    """
    Get the complete timeline of ministers for a specific ministry.

    Args:
        ministry_name: Name of the ministry
        language: Language for output ("en" or "sl")
        data_file: Path to combined ministers data file

    Returns:
        List of ministers sorted by start date
    """
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ministers = []
    for minister in data["ministers"]:
        # Check if ministry name matches
        ministry_match = False
        if isinstance(minister.get("ministry"), dict):
            ministry_en = minister["ministry"].get("en", "").lower()
            ministry_sl = minister["ministry"].get("sl", "").lower()
            ministry_match = (ministry_name.lower() in ministry_en or
                            ministry_name.lower() in ministry_sl or
                            ministry_en in ministry_name.lower() or
                            ministry_sl in ministry_name.lower())
        else:
            ministry_match = ministry_name.lower() in minister.get("ministry", "").lower()

        if ministry_match:
            result = {
                "name": minister["name"],
                "start_date": minister["start_date"],
                "end_date": minister["end_date"],
                "government_number": minister["government_number"]
            }

            if isinstance(minister.get("ministry"), dict):
                result["ministry"] = minister["ministry"].get(language, minister["ministry"]["en"])
                result["title"] = minister["title"].get(language, minister["title"]["en"]) if isinstance(minister.get("title"), dict) else minister.get("title", "")
            else:
                result["ministry"] = minister.get("ministry", "")
                result["title"] = minister.get("title", "")

            ministers.append(result)

    # Sort by start date
    ministers.sort(key=lambda x: x["start_date"])
    return ministers

if __name__ == "__main__":
    # Combine all files
    combined_data = combine_minister_files()

    # Example usage
    print("\n--- Example Queries ---")

    # Find finance minister on a specific date
    result = find_minister_by_ministry_and_date("Finance", "2010-05-15", "en")
    if result:
        print(f"\nFinance Minister on 2010-05-15:")
        print(f"Name: {result['name']}")
        print(f"Title: {result['title']}")
        print(f"Ministry: {result['ministry']}")
        print(f"Term: {result['start_date']} to {result['end_date']}")

    # Find the same in Slovenian
    result_sl = find_minister_by_ministry_and_date("Finance", "2010-05-15", "sl")
    if result_sl:
        print(f"\nFinance Minister on 2010-05-15 (Slovenian):")
        print(f"Name: {result_sl['name']}")
        print(f"Title: {result_sl['title']}")
        print(f"Ministry: {result_sl['ministry']}")

    # Show all ministries
    print(f"\nTotal unique ministries: {len(list_all_ministries())}")

    print("\nScript completed successfully!")