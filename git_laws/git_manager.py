"""
Git repository management module.

Handles git repository operations including initialization,
file writing, committing with proper metadata, and branch management.
"""

from pathlib import Path
from typing import Dict, Optional

from git import Repo
from loguru import logger

from .law_processor import LawMetadata


class GitManager:
    """Handle git repository operations and commit management."""

    def __init__(self, output_dir: str):
        """
        Initialize Git manager with output directory.

        Args:
            output_dir: Directory path for the git repository
        """
        self.output_dir = Path(output_dir)
        self.repo: Optional[Repo] = None

    def create_or_open_repo(self) -> bool:
        """
        Create or open a git repository in the output directory.

        Returns:
            bool: True if repository is ready, False if failed

        Raises:
            Exception: If directory creation or git initialization fails
        """
        try:
            # Create output directory if it doesn't exist
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {self.output_dir}")

        except PermissionError:
            logger.error(f"Permission denied creating directory: {self.output_dir}")
            raise
        except Exception as e:
            logger.error(f"Failed to create output directory {self.output_dir}: {e}")
            raise

        try:
            # Initialize or open git repository
            self.repo = Repo.init(self.output_dir)
            logger.info("Initialized git repository")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize git repository: {e}")
            raise

    def commit_law_version(
        self,
        content: str,
        metadata: LawMetadata,
        commit_message: str,
        minister_info: Dict
    ) -> bool:
        """
        Write law content to file and create a git commit with proper metadata.

        Args:
            content: Processed HTML content of the law
            metadata: LawMetadata object with law information
            commit_message: Formatted commit message
            minister_info: Minister information for commit authorship

        Returns:
            bool: True if commit was successful, False otherwise
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return False

        try:
            # Write file
            output_file = self.output_dir / f"{metadata.law_code}.html"
            output_file.write_text(content, encoding='utf-8')
            logger.debug(f"Wrote law file: {output_file}")

            # Stage files
            self.repo.git.add(all=True)

            # Create commit with minister as committer and author
            commit_env = self._create_commit_environment(minister_info, metadata.law_date)

            self.repo.git.commit(
                date=metadata.law_date,
                m=commit_message,
                env=commit_env
            )

            logger.info(
                f"Committed {metadata.law_id} as {minister_info['name']} "
                f"({minister_info.get('ministry', 'Government')})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to write/commit {metadata.law_id}: {e}")
            return False

    def _create_commit_environment(self, minister_info: Dict, law_date) -> Dict[str, str]:
        """
        Create environment variables for git commit with minister information.

        Args:
            minister_info: Dictionary containing minister details
            law_date: Date when the law was accepted

        Returns:
            Dictionary of environment variables for git commit
        """
        minister_name = minister_info['name']
        minister_email = f"{minister_name.replace(' ', '.').lower()}@gov.si"
        date_str = law_date.strftime('%Y-%m-%d %H:%M:%S %z')

        return {
            'GIT_COMMITTER_NAME': minister_name,
            'GIT_COMMITTER_EMAIL': minister_email,
            'GIT_COMMITTER_DATE': date_str,
            'GIT_AUTHOR_NAME': minister_name,
            'GIT_AUTHOR_EMAIL': minister_email,
            'GIT_AUTHOR_DATE': date_str
        }

    def create_branches_for_law_families(self, law_families: Dict[str, list]) -> bool:
        """
        Create separate branches for different law families.

        Args:
            law_families: Dictionary mapping family names to lists of laws

        Returns:
            bool: True if branches were created successfully

        Note:
            This is a future enhancement for organizing laws into branches.
            Currently not used in the main workflow.
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return False

        try:
            for family_name, laws in law_families.items():
                if len(laws) > 1:  # Only create branch if there are multiple laws
                    branch_name = f"law-family-{family_name.lower().replace(' ', '-')}"

                    # Create and checkout new branch
                    new_branch = self.repo.create_head(branch_name)
                    new_branch.checkout()

                    logger.info(f"Created branch '{branch_name}' for {len(laws)} laws")

                    # Switch back to master
                    self.repo.heads.master.checkout()

            return True

        except Exception as e:
            logger.error(f"Failed to create law family branches: {e}")
            return False

    def get_repository_status(self) -> Dict:
        """
        Get current status of the git repository.

        Returns:
            Dictionary containing repository status information
        """
        if not self.repo:
            return {'initialized': False}

        try:
            return {
                'initialized': True,
                'path': str(self.output_dir),
                'active_branch': self.repo.active_branch.name,
                'commit_count': len(list(self.repo.iter_commits())),
                'untracked_files': len(self.repo.untracked_files),
                'modified_files': len([item.a_path for item in self.repo.index.diff(None)]),
                'staged_files': len([item.a_path for item in self.repo.index.diff("HEAD")])
            }

        except Exception as e:
            logger.error(f"Failed to get repository status: {e}")
            return {'initialized': True, 'error': str(e)}

    def cleanup_repository(self) -> bool:
        """
        Clean up repository resources.

        Returns:
            bool: True if cleanup was successful
        """
        try:
            if self.repo:
                self.repo.close()
                self.repo = None
                logger.debug("Git repository resources cleaned up")
            return True

        except Exception as e:
            logger.warning(f"Failed to cleanup repository: {e}")
            return False

    def validate_repository_state(self) -> bool:
        """
        Validate that the repository is in a good state for operations.

        Returns:
            bool: True if repository is ready for operations
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        if not self.output_dir.exists():
            logger.error(f"Output directory does not exist: {self.output_dir}")
            return False

        try:
            # Check if we can write to the directory
            test_file = self.output_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()

            logger.debug("Repository state validation passed")
            return True

        except Exception as e:
            logger.error(f"Repository validation failed: {e}")
            return False