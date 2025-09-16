"""
Minister lookup functionality for historical Slovenian governments.

This module provides functions to determine who was the actual minister
responsible for a law based on the ministry and the law's date, using
scraped data from the Slovenian government website.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from loguru import logger


class MinisterLookup:
    """Lookup historical ministers and government coalitions for Slovenian laws."""

    def __init__(self, data_file: str = "data/slovenian_ministers.json"):
        self.data_file = data_file
        self.governments = []
        self.load_data()

    def load_data(self):
        """Load minister and government data from JSON file."""
        data_path = Path(self.data_file)

        if not data_path.exists():
            logger.warning(f"Minister data file {self.data_file} not found. Run minister scraper first.")
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.governments = data.get('governments', [])
                logger.info(f"Loaded {len(self.governments)} governments with minister data")
        except Exception as e:
            logger.error(f"Failed to load minister data: {e}")
            self.governments = []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        if not date_str:
            return None

        # Handle DD.MM.YY format
        if '.' in date_str and len(date_str.split('.')[-1]) == 2:
            try:
                return datetime.strptime(date_str, '%d.%m.%y')
            except ValueError:
                pass

        # Handle YYYY-MM-DD format
        if '-' in date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass

        # Handle DD.MM.YYYY format
        if '.' in date_str and len(date_str.split('.')[-1]) == 4:
            try:
                return datetime.strptime(date_str, '%d.%m.%Y')
            except ValueError:
                pass

        return None

    def _normalize_ministry_name(self, ministry_name: str) -> str:
        """Normalize ministry names for matching."""
        if not ministry_name:
            return ""

        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', ministry_name.lower().strip())

        # Map common variations to standard forms
        mappings = {
            'financ': 'finance',
            'pravosodje': 'justice',
            'notranje': 'interior',
            'zdravje': 'health',
            'obramb': 'defense',
            'zunan': 'foreign',
            'gospodar': 'economy',
            'kmetijstvo': 'agriculture',
            'izobraževan': 'education',
            'kultur': 'culture',
            'okolje': 'environment',
            'infrastruktur': 'infrastructure',
            'delo': 'labor',
            'družin': 'family'
        }

        for key, value in mappings.items():
            if key in normalized:
                return value

        return normalized

    def get_government_by_date(self, law_date: str) -> Optional[Dict]:
        """Get government information for a given date."""
        target_date = self._parse_date(law_date)
        if not target_date:
            return None

        for gov in self.governments:
            start_date_str = gov.get('start_date', '')
            end_date_str = gov.get('end_date', '')

            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)

            if start_date and end_date and start_date <= target_date <= end_date:
                return gov

        return None

    def get_minister_by_ministry_and_date(self, ministry_name: str, law_date: str) -> Optional[str]:
        """
        Get the actual minister for a specific ministry and date.

        Args:
            ministry_name: Name of the ministry (e.g., "Ministrstvo za finance")
            law_date: Date when the law was accepted

        Returns:
            Minister name if found, None otherwise
        """
        government = self.get_government_by_date(law_date)
        if not government:
            return None

        # Normalize the target ministry name
        target_ministry = self._normalize_ministry_name(ministry_name)

        # Look through ministers in this government
        ministers = government.get('ministers', [])

        best_match = None
        best_score = 0

        for minister in ministers:
            minister_ministry = minister.get('ministry', '')
            normalized_minister_ministry = self._normalize_ministry_name(minister_ministry)

            # Calculate similarity score
            score = self._calculate_ministry_similarity(target_ministry, normalized_minister_ministry)

            if score > best_score and score > 0.3:  # Minimum threshold
                best_match = minister
                best_score = score

        if best_match:
            return best_match.get('name', '')

        return None

    def _calculate_ministry_similarity(self, target: str, candidate: str) -> float:
        """Calculate similarity between ministry names."""
        if not target or not candidate:
            return 0.0

        # Exact match
        if target == candidate:
            return 1.0

        # Check if key terms match
        target_words = set(target.split())
        candidate_words = set(candidate.split())

        # Key ministry terms
        key_terms = {'finance', 'justice', 'interior', 'health', 'defense',
                    'foreign', 'economy', 'agriculture', 'education', 'culture',
                    'environment', 'infrastructure', 'labor', 'family'}

        target_key_terms = target_words & key_terms
        candidate_key_terms = candidate_words & key_terms

        if target_key_terms and candidate_key_terms:
            # How many key terms match
            matching_terms = target_key_terms & candidate_key_terms
            return len(matching_terms) / max(len(target_key_terms), len(candidate_key_terms))

        # Fallback to basic word matching
        if target_words and candidate_words:
            matching_words = target_words & candidate_words
            return len(matching_words) / max(len(target_words), len(candidate_words))

        return 0.0

    def get_finance_minister_by_date(self, law_date: str) -> Optional[str]:
        """Get the Minister of Finance for a given date."""
        return self.get_minister_by_ministry_and_date("Ministrstvo za finance", law_date)

    def enhance_government_metadata(self, government_metadata: Dict, law_date: str) -> Dict:
        """
        Enhance the government metadata with actual minister names and government info.

        Args:
            government_metadata: Original metadata from PISRS API
            law_date: Date when the law was accepted

        Returns:
            Enhanced metadata with minister names and government coalition info
        """
        enhanced = government_metadata.copy()

        # Try to get actual minister name
        responsible_ministry = government_metadata.get('responsible_ministry', '')
        if responsible_ministry:
            actual_minister = self.get_minister_by_ministry_and_date(responsible_ministry, law_date)
            if actual_minister:
                enhanced['actual_minister'] = actual_minister
                enhanced['minister_attribution'] = f"Minister: {actual_minister}"

        # Add government information
        government = self.get_government_by_date(law_date)
        if government:
            enhanced['government_composition'] = {
                'prime_minister': government.get('pm', ''),
                'number': government.get('number', 0),
                'period': government.get('date_range', '')
            }
            enhanced['prime_minister'] = government.get('pm', '')

            # Update government info string
            gov_parts = []
            if enhanced.get('minister_attribution'):
                gov_parts.append(enhanced['minister_attribution'])
            elif responsible_ministry:
                gov_parts.append(f"Prepared by: {responsible_ministry}")

            if enhanced.get('adopting_body'):
                gov_parts.append(f"Adopted by: {enhanced['adopting_body']}")

            gov_parts.append(f"PM: {government.get('pm', '')}")
            gov_parts.append(f"Gov: {government.get('number', '')} ({government.get('date_range', '')})")

            enhanced['government_info'] = ' | '.join(gov_parts)

        return enhanced

    def get_statistics(self) -> Dict:
        """Get statistics about the loaded minister data."""
        total_ministers = 0
        governments_with_ministers = 0

        for gov in self.governments:
            ministers = gov.get('ministers', [])
            total_ministers += len(ministers)
            if ministers:
                governments_with_ministers += 1

        return {
            'total_governments': len(self.governments),
            'governments_with_ministers': governments_with_ministers,
            'total_ministers': total_ministers,
            'average_ministers_per_government': total_ministers / max(len(self.governments), 1)
        }


# Global instance
minister_lookup = MinisterLookup()