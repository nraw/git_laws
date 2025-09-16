"""
Minister Lookup Utility

Simple interface for querying Slovenian government minister data.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from config import MINISTERS_COMBINED_FILE

class MinisterLookup:
    """
    Class for querying Slovenian government minister data.
    """

    def __init__(self, data_file: str = MINISTERS_COMBINED_FILE):
        """
        Initialize the lookup with combined ministers data.

        Args:
            data_file: Path to the combined ministers JSON file
        """
        self.data_file = data_file
        self.data = None
        self.load_data()

    def load_data(self):
        """Load the combined ministers data."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {self.data_file}. Please run combine_ministers.py first.")

    def find_minister(self, ministry: str, date: str, language: str = "en") -> Optional[Dict]:
        """
        Find the minister in charge of a ministry on a specific date.

        Args:
            ministry: Ministry name (English or Slovenian, partial matches work)
            date: Date in YYYY-MM-DD format
            language: Output language ("en" or "sl")

        Returns:
            Minister information or None if not found

        Example:
            >>> lookup = MinisterLookup()
            >>> minister = lookup.find_minister("Finance", "2015-03-15")
            >>> print(f"{minister['name']} was Finance Minister")
        """
        query_date = datetime.strptime(date, "%Y-%m-%d")

        for minister in self.data["ministers"]:
            # Check ministry match
            if self._ministry_matches(minister, ministry):
                # Check date range
                start_date = datetime.strptime(minister["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(minister["end_date"], "%Y-%m-%d")

                if start_date <= query_date <= end_date:
                    return self._format_minister(minister, language)

        return None

    def get_ministry_timeline(self, ministry: str, language: str = "en") -> List[Dict]:
        """
        Get chronological list of all ministers for a specific ministry.

        Args:
            ministry: Ministry name
            language: Output language ("en" or "sl")

        Returns:
            List of ministers sorted by start date

        Example:
            >>> lookup = MinisterLookup()
            >>> timeline = lookup.get_ministry_timeline("Defense")
            >>> for minister in timeline:
            ...     print(f"{minister['name']} ({minister['start_date']} - {minister['end_date']})")
        """
        ministers = []
        for minister in self.data["ministers"]:
            if self._ministry_matches(minister, ministry):
                ministers.append(self._format_minister(minister, language))

        return sorted(ministers, key=lambda x: x["start_date"])

    def list_ministries(self, language: str = "en") -> List[str]:
        """
        Get list of all unique ministries.

        Args:
            language: Language for ministry names ("en" or "sl")

        Returns:
            Sorted list of ministry names
        """
        ministries = set()
        for minister in self.data["ministers"]:
            ministry_name = self._get_ministry_name(minister, language)
            if ministry_name:
                ministries.add(ministry_name)

        return sorted(list(ministries))

    def search_ministers(self, name: str, language: str = "en") -> List[Dict]:
        """
        Search for ministers by name (partial match).

        Args:
            name: Minister name or partial name
            language: Output language ("en" or "sl")

        Returns:
            List of matching ministers

        Example:
            >>> lookup = MinisterLookup()
            >>> results = lookup.search_ministers("Janša")
            >>> for minister in results:
            ...     print(f"{minister['name']} - {minister['ministry']} ({minister['start_date']})")
        """
        results = []
        for minister in self.data["ministers"]:
            if name.lower() in minister["name"].lower():
                results.append(self._format_minister(minister, language))

        return sorted(results, key=lambda x: x["start_date"])

    def get_government_ministers(self, government_number: int, language: str = "en") -> List[Dict]:
        """
        Get all ministers from a specific government.

        Args:
            government_number: Government number (1-14)
            language: Output language ("en" or "sl")

        Returns:
            List of ministers from that government
        """
        ministers = []
        for minister in self.data["ministers"]:
            if minister["government_number"] == government_number:
                ministers.append(self._format_minister(minister, language))

        return sorted(ministers, key=lambda x: x["start_date"])

    def who_was_minister_on(self, date: str, language: str = "en") -> List[Dict]:
        """
        Get all ministers who were in office on a specific date.

        Args:
            date: Date in YYYY-MM-DD format
            language: Output language ("en" or "sl")

        Returns:
            List of all ministers in office on that date
        """
        query_date = datetime.strptime(date, "%Y-%m-%d")
        ministers = []

        for minister in self.data["ministers"]:
            start_date = datetime.strptime(minister["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(minister["end_date"], "%Y-%m-%d")

            if start_date <= query_date <= end_date:
                ministers.append(self._format_minister(minister, language))

        return sorted(ministers, key=lambda x: self._get_ministry_name(x, language))

    def _ministry_matches(self, minister: Dict, ministry_query: str) -> bool:
        """Check if minister's ministry matches the query."""
        if isinstance(minister.get("ministry"), dict):
            ministry_en = minister["ministry"].get("en", "").lower()
            ministry_sl = minister["ministry"].get("sl", "").lower()
            query = ministry_query.lower()
            return (query in ministry_en or query in ministry_sl or
                   ministry_en in query or ministry_sl in query)
        else:
            return ministry_query.lower() in minister.get("ministry", "").lower()

    def _get_ministry_name(self, minister: Dict, language: str) -> str:
        """Get ministry name in specified language."""
        if isinstance(minister.get("ministry"), dict):
            return minister["ministry"].get(language, minister["ministry"]["en"])
        else:
            return minister.get("ministry", "")

    def _format_minister(self, minister: Dict, language: str) -> Dict:
        """Format minister data for output."""
        result = {
            "name": minister["name"],
            "start_date": minister["start_date"],
            "end_date": minister["end_date"],
            "government_number": minister["government_number"],
            "ministry_code": minister.get("ministry_code", "")
        }

        # Add language-specific fields
        result["ministry"] = self._get_ministry_name(minister, language)

        if isinstance(minister.get("title"), dict):
            result["title"] = minister["title"].get(language, minister["title"]["en"])
        else:
            result["title"] = minister.get("title", "")

        # Optional fields
        if "termination_reason" in minister:
            if isinstance(minister["termination_reason"], dict):
                result["termination_reason"] = minister["termination_reason"].get(language, minister["termination_reason"]["en"])
            else:
                result["termination_reason"] = minister["termination_reason"]

        if "predecessor" in minister:
            result["predecessor"] = minister["predecessor"]

        return result


# Convenience functions for quick usage
def find_minister(ministry: str, date: str, language: str = "en") -> Optional[Dict]:
    """Quick function to find minister by ministry and date."""
    lookup = MinisterLookup()
    return lookup.find_minister(ministry, date, language)

def get_timeline(ministry: str, language: str = "en") -> List[Dict]:
    """Quick function to get ministry timeline."""
    lookup = MinisterLookup()
    return lookup.get_ministry_timeline(ministry, language)

def list_ministries(language: str = "en") -> List[str]:
    """Quick function to list all ministries."""
    lookup = MinisterLookup()
    return lookup.list_ministries(language)


if __name__ == "__main__":
    # Example usage
    lookup = MinisterLookup()

    print("=== Minister Lookup Examples ===\n")

    # Example 1: Find specific minister
    minister = lookup.find_minister("Finance", "2015-06-15")
    if minister:
        print(f"Finance Minister on 2015-06-15:")
        print(f"  {minister['name']} ({minister['title']})")
        print(f"  Term: {minister['start_date']} to {minister['end_date']}")
        print()

    # Example 2: Get ministry timeline
    print("Defense Ministers timeline:")
    defense_ministers = lookup.get_ministry_timeline("Defense")
    for i, minister in enumerate(defense_ministers[:5]):  # Show first 5
        print(f"  {i+1}. {minister['name']} ({minister['start_date']} - {minister['end_date']})")
    if len(defense_ministers) > 5:
        print(f"  ... and {len(defense_ministers) - 5} more")
    print()

    # Example 3: Search by name
    print("All positions held by 'Janež Janša':")
    jansa_positions = lookup.search_ministers("Janez Janša")
    for position in jansa_positions:
        print(f"  {position['ministry']} ({position['start_date']} - {position['end_date']})")
    print()

    # Example 4: Who was in government on specific date
    print("Ministers in office on 2010-01-01:")
    ministers_2010 = lookup.who_was_minister_on("2010-01-01")
    for minister in ministers_2010[:10]:  # Show first 10
        print(f"  {minister['name']} - {minister['ministry']}")
    print(f"  ... total of {len(ministers_2010)} ministers")
    print()

    # Example 5: Bilingual example
    minister_en = lookup.find_minister("Health", "2020-06-01", "en")
    minister_sl = lookup.find_minister("Health", "2020-06-01", "sl")
    if minister_en and minister_sl:
        print("Bilingual example (Health Minister on 2020-06-01):")
        print(f"  English: {minister_en['name']} - {minister_en['title']}")
        print(f"  Slovenian: {minister_sl['name']} - {minister_sl['title']}")