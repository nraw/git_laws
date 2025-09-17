"""
Data loading and API interaction module.

Handles all data retrieval operations including API validation,
law data fetching, and minister lookup integration.
"""

from typing import Dict, Optional

import pandas as pd
from loguru import logger

from .api_client import pisrs_client
from .minister_lookup import find_minister


class DataLoader:
    """Handle loading and caching of law data from PISRS API."""

    def __init__(self):
        """Initialize the data loader with API client."""
        self.api_client = pisrs_client

    def validate_api_access(self) -> bool:
        """
        Validate PISRS API access.

        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            # Test API access by getting a simple response
            test_law = self.api_client.get_law_by_moped_id("ZAKO4697")
            if test_law:
                logger.info("✓ PISRS API access validated successfully")
                return True
            else:
                logger.error("✗ PISRS API test failed - could not retrieve test law")
                return False
        except Exception as e:
            logger.error(f"✗ PISRS API access failed: {e}")
            logger.error("Please check your PISRS_API_KEY in the .env file")
            return False

    def load_law_versions(self, law_id: str) -> Optional[pd.DataFrame]:
        """
        Load all historical versions of a law.

        Args:
            law_id: The MOPED ID of the law to load

        Returns:
            DataFrame with law versions sorted by date, or None if failed

        Raises:
            ValueError: If no versions are found for the law ID
        """
        try:
            logger.info(f"Fetching historical NPB versions for {law_id}...")
            npb_versions_data = self.api_client.get_historical_npb_versions(law_id)

            if not npb_versions_data:
                raise ValueError(f"No NPB versions found for law ID '{law_id}'")

            # Convert to DataFrame for compatibility with existing code
            affected_laws = pd.DataFrame(npb_versions_data)
            affected_laws["date_accepted"] = pd.to_datetime(
                affected_laws["D_SPREJEMA"],
                format="%d.%m.%y"
            )
            affected_laws = affected_laws.sort_values("date_accepted")

            logger.info(f"Found {len(affected_laws)} historical NPB versions to process")
            return affected_laws

        except Exception as e:
            logger.error(f"Error fetching NPB versions for {law_id}: {e}")
            raise

    def load_law_content(self, law_id: str, is_npb: bool = False) -> Optional[str]:
        """
        Load the content of a specific law version.

        Args:
            law_id: The law/NPB ID to load content for
            is_npb: Whether this is an NPB consolidated version

        Returns:
            Raw HTML content of the law, or None if not found
        """
        try:
            if is_npb:
                logger.debug(f"Fetching NPB consolidated content for {law_id}")
            else:
                logger.debug(f"Fetching individual law content for {law_id}")

            content = self.api_client.get_law_content(law_id, is_npb=is_npb)

            if not content or not content.strip():
                logger.warning(f"Empty or no content for law {law_id}")
                return None

            # Log content info for debugging
            content_length = len(content)
            content_hash = hash(content) % 10000  # Simple hash for comparison
            logger.debug(f"Got content for {law_id}: {content_length} chars, hash={content_hash}")

            return content

        except Exception as e:
            logger.error(f"Failed to load content for {law_id}: {e}")
            return None

    def get_responsible_minister(self, law_date, preparing_ministry: str) -> Dict:
        """
        Find the minister responsible based on the preparing ministry and date.

        Args:
            law_date: Date when the law was accepted
            preparing_ministry: The ministry that prepared the law

        Returns:
            Minister information dict

        Raises:
            ValueError: If no appropriate minister is found
        """
        # Format date for minister lookup (YYYY-MM-DD)
        date_str = law_date.strftime("%Y-%m-%d")

        # Try to find minister using the full ministry name directly
        minister = find_minister(preparing_ministry, date_str)

        if not minister:
            raise ValueError(
                f"No minister found for ministry '{preparing_ministry}' on date {date_str}"
            )

        return minister

    def validate_data_integrity(self, law_versions: pd.DataFrame) -> bool:
        """
        Validate the integrity of loaded law data.

        Args:
            law_versions: DataFrame containing law versions

        Returns:
            bool: True if data passes validation checks
        """
        if law_versions is None or law_versions.empty:
            logger.error("No law versions provided for validation")
            return False

        required_columns = ["ID", "KRATICA", "NASLOV", "date_accepted"]
        missing_columns = [col for col in required_columns if col not in law_versions.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False

        # Check for null values in critical columns
        null_counts = law_versions[required_columns].isnull().sum()
        if null_counts.sum() > 0:
            logger.warning(f"Found null values in data: {null_counts.to_dict()}")

        # Check date ordering
        dates = law_versions["date_accepted"].dropna()
        if not dates.is_monotonic_increasing:
            logger.warning("Law versions are not in chronological order")

        logger.info("Data integrity validation completed")
        return True