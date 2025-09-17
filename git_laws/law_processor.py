"""
Law content processing and business logic module.

Handles content transformation, HTML processing, commit message generation,
and other business logic operations for law documents.
"""

import re
from typing import Dict, List, NamedTuple, Optional

import pandas as pd
from bs4 import BeautifulSoup as bs
from loguru import logger


class LawMetadata(NamedTuple):
    """Container for law metadata used in processing."""
    law_id: str
    law_code: str
    law_title: str
    law_date: pd.Timestamp
    government_metadata: Dict
    amendment_name: str


class LawProcessor:
    """Business logic for law relationships and content processing."""

    def __init__(self):
        """Initialize the law processor."""
        pass

    def process_law_content(self, raw_content: str) -> Optional[str]:
        """
        Process raw law content into clean, formatted HTML.

        Args:
            raw_content: Raw HTML content from API

        Returns:
            Cleaned and prettified HTML content, or None if processing fails
        """
        if not raw_content or not raw_content.strip():
            logger.warning("Empty content provided for processing")
            return None

        try:
            # Clean up the content - normalize whitespace
            content_clean = re.sub(r"( |\n|\r)+", " ", raw_content)

            # Parse and prettify HTML
            soup = bs(content_clean, features="html.parser")
            pretty_html = soup.prettify()

            logger.debug(f"Processed content: {len(raw_content)} -> {len(pretty_html)} chars")
            return pretty_html

        except Exception as e:
            logger.error(f"Failed to process HTML content: {e}")
            return None

    def extract_law_metadata(self, law_row: pd.Series) -> LawMetadata:
        """
        Extract structured metadata from a law DataFrame row.

        Args:
            law_row: Pandas Series containing law data

        Returns:
            LawMetadata object with extracted information
        """
        return LawMetadata(
            law_id=law_row["ID"],
            law_code=law_row["KRATICA"],
            law_title=law_row["NASLOV"],
            law_date=law_row["date_accepted"],
            government_metadata=law_row.get('_government_metadata', {}),
            amendment_name=law_row.get('_amendment_name', law_row["KRATICA"])
        )

    def generate_commit_message(self, metadata: LawMetadata) -> str:
        """
        Generate a git commit message from law metadata.

        Args:
            metadata: LawMetadata object with law information

        Returns:
            Formatted commit message string
        """
        # Create enhanced commit message with actual amendment name
        commit_msg_parts = [
            f"{metadata.amendment_name} - {metadata.law_id} - {metadata.law_title}"
        ]

        # Add government metadata if available
        if metadata.government_metadata and metadata.government_metadata.get('government_info'):
            commit_msg_parts.append(metadata.government_metadata['government_info'])

        commit_msg = '\n'.join(commit_msg_parts)
        logger.debug(f"Generated commit message: {commit_msg[:100]}...")

        return commit_msg

    def validate_law_data(self, law_row: pd.Series) -> bool:
        """
        Validate that a law row contains required data for processing.

        Args:
            law_row: Pandas Series containing law data

        Returns:
            bool: True if law data is valid for processing
        """
        required_fields = ["ID", "KRATICA", "NASLOV", "date_accepted"]

        for field in required_fields:
            if field not in law_row or pd.isna(law_row[field]):
                logger.warning(f"Missing required field '{field}' in law data")
                return False

        # Check if date is valid
        if not isinstance(law_row["date_accepted"], pd.Timestamp):
            logger.warning("Invalid date format in law data")
            return False

        # Check government metadata for ministry information
        government_metadata = law_row.get('_government_metadata', {})
        if not government_metadata or not government_metadata.get('responsible_ministry'):
            logger.warning(f"No responsible ministry found for law {law_row['ID']}")
            return False

        return True

    def get_law_timeline(self, law_versions: pd.DataFrame) -> List[LawMetadata]:
        """
        Get chronological timeline of law versions.

        Args:
            law_versions: DataFrame containing all versions of a law

        Returns:
            List of LawMetadata objects sorted by date
        """
        if law_versions.empty:
            logger.warning("No law versions provided for timeline")
            return []

        timeline = []
        for _, law_row in law_versions.iterrows():
            if self.validate_law_data(law_row):
                metadata = self.extract_law_metadata(law_row)
                timeline.append(metadata)
            else:
                logger.warning(f"Skipping invalid law data for ID {law_row.get('ID', 'unknown')}")

        # Sort by date (should already be sorted, but ensure it)
        timeline.sort(key=lambda x: x.law_date)

        logger.info(f"Generated timeline with {len(timeline)} valid law versions")
        return timeline

    def extract_responsible_ministry(self, law_metadata: LawMetadata) -> Optional[str]:
        """
        Extract the responsible ministry from law metadata.

        Args:
            law_metadata: LawMetadata object

        Returns:
            Ministry name or None if not found
        """
        government_metadata = law_metadata.government_metadata

        if not government_metadata:
            logger.debug(f"No government metadata for law {law_metadata.law_id}")
            return None

        ministry = government_metadata.get('responsible_ministry')
        if not ministry:
            logger.debug(f"No responsible ministry in metadata for law {law_metadata.law_id}")
            return None

        logger.debug(f"Found responsible ministry: {ministry}")
        return ministry

    def is_npb_version(self, law_row: pd.Series) -> bool:
        """
        Check if a law row represents an NPB (consolidated) version.

        Args:
            law_row: Pandas Series containing law data

        Returns:
            bool: True if this is an NPB version
        """
        return law_row.get('_is_npb', False)

    def get_processing_stats(self, processed_laws: List[LawMetadata]) -> Dict:
        """
        Generate processing statistics for completed law processing.

        Args:
            processed_laws: List of successfully processed law metadata

        Returns:
            Dictionary containing processing statistics
        """
        if not processed_laws:
            return {
                'total_processed': 0,
                'date_range': None,
                'amendment_count': 0,
                'ministries': []
            }

        dates = [law.law_date for law in processed_laws]
        ministries = []

        for law in processed_laws:
            ministry = self.extract_responsible_ministry(law)
            if ministry and ministry not in ministries:
                ministries.append(ministry)

        stats = {
            'total_processed': len(processed_laws),
            'date_range': {
                'start': min(dates),
                'end': max(dates)
            },
            'amendment_count': len([law for law in processed_laws if law.amendment_name != law.law_code]),
            'ministries': ministries
        }

        logger.info(f"Processing stats: {stats['total_processed']} laws, "
                   f"{stats['amendment_count']} amendments, "
                   f"{len(stats['ministries'])} different ministries")

        return stats