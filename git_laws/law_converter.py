"""
Law converter orchestrator module.

Main orchestrator class that coordinates data loading, processing,
and git operations to convert Slovenian legal documents into git repositories.
"""

from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from tqdm import tqdm

from .data_loader import DataLoader
from .git_manager import GitManager
from .law_processor import LawProcessor, LawMetadata


class LawConverter:
    """Main orchestrator for converting legal documents to git repositories."""

    def __init__(
        self,
        data_loader: Optional[DataLoader] = None,
        processor: Optional[LawProcessor] = None,
        git_manager: Optional[GitManager] = None
    ):
        """
        Initialize the law converter with dependency injection.

        Args:
            data_loader: DataLoader instance for API interactions
            processor: LawProcessor instance for content processing
            git_manager: GitManager instance for git operations
        """
        self.data_loader = data_loader or DataLoader()
        self.processor = processor or LawProcessor()
        self.git_manager = git_manager  # Will be set when convert_law is called

    def convert_law(self, law_id: str, output_dir: str) -> bool:
        """
        Convert a specific law and its amendments to a git repository.

        Args:
            law_id: MOPED ID of the law to convert (e.g., "ZAKO4697")
            output_dir: Directory path for the output git repository

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        logger.info(f"Starting conversion of law {law_id} to {output_dir}")

        # Initialize git manager with output directory
        self.git_manager = GitManager(output_dir)

        # Step 1: Validate API access
        if not self.data_loader.validate_api_access():
            logger.error("Cannot proceed without PISRS API access")
            return False

        # Step 2: Load law versions
        try:
            law_versions = self.data_loader.load_law_versions(law_id)
            if law_versions is None:
                logger.error(f"Failed to load law versions for {law_id}")
                return False

            # Validate data integrity
            if not self.data_loader.validate_data_integrity(law_versions):
                logger.error("Data integrity validation failed")
                return False

        except Exception as e:
            logger.error(f"Error loading law data: {e}")
            return False

        # Step 3: Initialize git repository
        try:
            if not self.git_manager.create_or_open_repo():
                logger.error("Failed to initialize git repository")
                return False

        except Exception as e:
            logger.error(f"Git initialization failed: {e}")
            return False

        # Step 4: Process law versions chronologically
        processed_count = 0
        skipped_count = 0

        # Get chronological timeline of laws
        law_timeline = self.processor.get_law_timeline(law_versions)
        if not law_timeline:
            logger.error("No valid law versions found for processing")
            return False

        logger.info(f"Processing {len(law_timeline)} law versions chronologically")

        for metadata in tqdm(law_timeline, desc="Processing laws"):
            success = self._process_single_law(metadata)
            if success:
                processed_count += 1
            else:
                skipped_count += 1

        # Step 5: Generate summary
        self._log_processing_summary(processed_count, skipped_count, output_dir)

        # Step 6: Cleanup
        self.git_manager.cleanup_repository()

        return processed_count > 0

    def _process_single_law(self, metadata: LawMetadata) -> bool:
        """
        Process a single law version through the complete pipeline.

        Args:
            metadata: LawMetadata object containing law information

        Returns:
            bool: True if processing was successful
        """
        try:
            logger.debug(f"Processing law {metadata.law_id} ({metadata.law_code})")

            # Step 1: Load law content (assuming all are NPB versions in the new flow)
            raw_content = self.data_loader.load_law_content(metadata.law_id, is_npb=True)

            if not raw_content:
                logger.warning(f"No content available for law {metadata.law_id}, skipping")
                return False

            # Step 2: Process content
            processed_content = self.processor.process_law_content(raw_content)
            if not processed_content:
                logger.warning(f"Content processing failed for law {metadata.law_id}")
                return False

            # Step 3: Get responsible ministry and minister
            ministry = self.processor.extract_responsible_ministry(metadata)
            if not ministry:
                logger.error(f"No responsible ministry found for law {metadata.law_id}")
                return False

            minister_info = self.data_loader.get_responsible_minister(
                metadata.law_date, ministry
            )

            # Step 4: Generate commit message
            commit_message = self.processor.generate_commit_message(metadata)

            # Step 5: Commit to git repository
            success = self.git_manager.commit_law_version(
                processed_content, metadata, commit_message, minister_info
            )

            if success:
                logger.debug(f"Successfully processed law {metadata.law_id}")
            else:
                logger.warning(f"Git commit failed for law {metadata.law_id}")

            return success

        except Exception as e:
            logger.error(f"Unexpected error processing law {metadata.law_id}: {e}")
            return False

    def convert_all_laws(self, output_dir: str, law_ids: List[str]) -> Dict[str, bool]:
        """
        Convert multiple laws to separate git repositories.

        Args:
            output_dir: Base directory for output repositories
            law_ids: List of MOPED IDs to convert

        Returns:
            Dictionary mapping law IDs to conversion success status
        """
        results = {}
        base_path = Path(output_dir)

        logger.info(f"Converting {len(law_ids)} laws to repositories in {output_dir}")

        for law_id in law_ids:
            law_output_dir = base_path / f"law_{law_id.lower()}"
            logger.info(f"Converting {law_id} to {law_output_dir}")

            try:
                success = self.convert_law(law_id, str(law_output_dir))
                results[law_id] = success

                if success:
                    logger.info(f"✓ Successfully converted {law_id}")
                else:
                    logger.error(f"✗ Failed to convert {law_id}")

            except Exception as e:
                logger.error(f"✗ Error converting {law_id}: {e}")
                results[law_id] = False

        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(law_ids)
        logger.info(f"Bulk conversion complete: {successful}/{total} laws converted successfully")

        return results

    def _log_processing_summary(self, processed_count: int, skipped_count: int, output_dir: str):
        """
        Log a summary of the processing results.

        Args:
            processed_count: Number of successfully processed laws
            skipped_count: Number of laws that were skipped
            output_dir: Output directory path
        """
        total_count = processed_count + skipped_count

        logger.info(f"Processing complete: {processed_count}/{total_count} laws processed")

        if processed_count > 0:
            logger.info(f"Git repository created at: {output_dir}")

            # Get repository status
            if self.git_manager:
                status = self.git_manager.get_repository_status()
                if status.get('commit_count'):
                    logger.info(f"Repository contains {status['commit_count']} commits")
        else:
            logger.warning("No laws were successfully processed")

        if skipped_count > 0:
            logger.warning(f"{skipped_count} laws were skipped due to errors or missing content")

    def get_processing_statistics(self) -> Dict:
        """
        Get statistics about the current processing session.

        Returns:
            Dictionary containing processing statistics
        """
        stats = {
            'api_status': 'available' if self.data_loader.validate_api_access() else 'unavailable',
            'git_status': self.git_manager.get_repository_status() if self.git_manager else None
        }

        return stats