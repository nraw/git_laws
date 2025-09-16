"""
Enhanced minister lookup functionality using manually curated government data.

This module provides precise minister attribution based on manually extracted
and structured government composition data from gov.si.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from loguru import logger


class ManualMinisterLookup:
    """Lookup historical ministers using manually curated government data."""

    def __init__(self, data_file: str = "data/government_ministers_manual.json"):
        self.data_file = data_file
        self.governments = []
        self.load_data()

    def load_data(self):
        """Load minister and government data from manually curated JSON file."""
        data_path = Path(self.data_file)

        if not data_path.exists():
            logger.warning(f"Manual minister data file {self.data_file} not found.")
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.governments = data.get('governments', [])
                logger.info(f"Loaded {len(self.governments)} manually curated governments")
        except Exception as e:
            logger.error(f"Failed to load manual minister data: {e}")
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

    def get_government_by_date(self, law_date: str) -> Optional[Dict]:
        """Get government information for a given date."""
        target_date = self._parse_date(law_date)
        if not target_date:
            return None

        for gov in self.governments:
            period = gov.get('period', {})
            start_date_str = period.get('start_date', '')
            end_date_str = period.get('end_date', '')

            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)

            if start_date and end_date and start_date <= target_date <= end_date:
                return gov

        return None

    def get_minister_by_ministry_code_and_date(self, ministry_code: str, law_date: str) -> Optional[str]:
        """
        Get the minister for a specific ministry code and date.

        Args:
            ministry_code: Standard ministry code (e.g., "MF" for Finance)
            law_date: Date when the law was accepted

        Returns:
            Minister name if found, None otherwise
        """
        government = self.get_government_by_date(law_date)
        if not government:
            return None

        target_date = self._parse_date(law_date)
        if not target_date:
            return None

        # Look through ministers in this government
        ministers = government.get('ministers', [])

        for minister in ministers:
            if minister.get('ministry_code') == ministry_code:
                # Check if minister was in office on the target date
                minister_start = self._parse_date(minister.get('start_date', ''))
                minister_end = self._parse_date(minister.get('end_date', ''))

                if minister_start and minister_end:
                    if minister_start <= target_date <= minister_end:
                        return minister.get('name', '')

        return None

    def get_minister_by_ministry_name_and_date(self, ministry_name: str, law_date: str) -> Optional[str]:
        """
        Get the minister for a specific ministry name and date.

        Args:
            ministry_name: Ministry name (e.g., "Ministrstvo za finance")
            law_date: Date when the law was accepted

        Returns:
            Minister name if found, None otherwise
        """
        # Map common ministry names to codes
        ministry_mappings = {
            'finance': 'MF',
            'financ': 'MF',
            'ministrstvo za finance': 'MF',
            'justice': 'MP',
            'pravosodje': 'MP',
            'ministrstvo za pravosodje': 'MP',
            'interior': 'MNZ',
            'notranje': 'MNZ',
            'ministrstvo za notranje zadeve': 'MNZ',
            'defense': 'MORS',
            'obrambo': 'MORS',
            'ministrstvo za obrambo': 'MORS',
            'foreign': 'MZZ',
            'zunan': 'MZZ',
            'ministrstvo za zunanje zadeve': 'MZZ',
            'health': 'MZ',
            'zdravje': 'MZ',
            'ministrstvo za zdravje': 'MZ',
            'education': 'MIZS',
            'izobraževan': 'MIZS',
            'ministrstvo za izobraževanje': 'MIZS',
            'culture': 'MK',
            'kultur': 'MK',
            'ministrstvo za kulturo': 'MK',
            'agriculture': 'MKGP',
            'kmetijstvo': 'MKGP',
            'ministrstvo za kmetijstvo': 'MKGP'
        }

        ministry_lower = ministry_name.lower()
        ministry_code = None

        # Find matching ministry code
        for key, code in ministry_mappings.items():
            if key in ministry_lower:
                ministry_code = code
                break

        if not ministry_code:
            return None

        return self.get_minister_by_ministry_code_and_date(ministry_code, law_date)

    def get_finance_minister_by_date(self, law_date: str) -> Optional[str]:
        """Get the Minister of Finance for a given date."""
        return self.get_minister_by_ministry_code_and_date("MF", law_date)

    def get_all_ministers_by_date(self, law_date: str) -> List[Dict]:
        """Get all ministers in office on a specific date."""
        government = self.get_government_by_date(law_date)
        if not government:
            return []

        target_date = self._parse_date(law_date)
        if not target_date:
            return []

        active_ministers = []
        ministers = government.get('ministers', [])

        for minister in ministers:
            minister_start = self._parse_date(minister.get('start_date', ''))
            minister_end = self._parse_date(minister.get('end_date', ''))

            if minister_start and minister_end:
                if minister_start <= target_date <= minister_end:
                    active_ministers.append(minister)

        return active_ministers

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
            actual_minister = self.get_minister_by_ministry_name_and_date(responsible_ministry, law_date)
            if actual_minister:
                enhanced['actual_minister'] = actual_minister
                enhanced['minister_attribution'] = f"Minister: {actual_minister}"

        # Add government information
        government = self.get_government_by_date(law_date)
        if government:
            leadership = government.get('leadership', {})
            pm_info = leadership.get('prime_minister', {})
            period = government.get('period', {})
            political = government.get('political_composition', {})

            enhanced['government_composition'] = {
                'prime_minister': pm_info.get('name', ''),
                'number': government.get('number', 0),
                'period': f"{period.get('start_date', '')} - {period.get('end_date', '')}",
                'coalition': political.get('coalition', ''),
                'parties': political.get('parties', [])
            }
            enhanced['prime_minister'] = pm_info.get('name', '')

            # Update government info string
            gov_parts = []
            if enhanced.get('minister_attribution'):
                gov_parts.append(enhanced['minister_attribution'])
            elif responsible_ministry:
                gov_parts.append(f"Prepared by: {responsible_ministry}")

            if enhanced.get('adopting_body'):
                gov_parts.append(f"Adopted by: {enhanced['adopting_body']}")

            gov_parts.append(f"PM: {pm_info.get('name', '')}")
            gov_parts.append(f"Gov: {government.get('number', '')} ({period.get('start_date', '')} - {period.get('end_date', '')})")

            if political.get('coalition'):
                gov_parts.append(f"Coalition: {political['coalition']}")

            enhanced['government_info'] = ' | '.join(gov_parts)

        return enhanced

    def get_statistics(self) -> Dict:
        """Get statistics about the loaded minister data."""
        total_ministers = 0
        total_appointments = 0

        for gov in self.governments:
            ministers = gov.get('ministers', [])
            total_appointments += len(ministers)

            # Count unique ministers
            minister_names = set(minister.get('name', '') for minister in ministers)
            total_ministers += len(minister_names)

        return {
            'total_governments': len(self.governments),
            'total_minister_appointments': total_appointments,
            'estimated_unique_ministers': total_ministers,
            'data_coverage': f"{len(self.governments)} governments manually curated"
        }

    def list_all_finance_ministers(self) -> List[Dict]:
        """Get chronological list of all Finance Ministers."""
        finance_ministers = []

        for gov in self.governments:
            ministers = gov.get('ministers', [])

            for minister in ministers:
                if minister.get('ministry_code') == 'MF':
                    finance_ministers.append({
                        'name': minister.get('name', ''),
                        'government': gov.get('number', 0),
                        'start_date': minister.get('start_date', ''),
                        'end_date': minister.get('end_date', ''),
                        'title': minister.get('title', ''),
                        'predecessor': minister.get('predecessor', ''),
                        'termination_reason': minister.get('termination_reason', '')
                    })

        # Sort by start date
        finance_ministers.sort(key=lambda x: self._parse_date(x['start_date']) or datetime.min)
        return finance_ministers


# Global instance
manual_minister_lookup = ManualMinisterLookup()