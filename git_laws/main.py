import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup as bs
from git import Repo
from loguru import logger
from tqdm import tqdm

from .api_client import pisrs_client
from .minister_lookup import find_minister


def get_responsible_minister(law_date, preparing_ministry):
    """
    Find the minister responsible based on the preparing ministry and date.

    Args:
        law_date: Date when the law was accepted
        preparing_ministry: The ministry that prepared the law (e.g., "Ministrstvo za finance")

    Returns:
        Minister information dict

    Raises:
        ValueError: If no appropriate minister is found
    """
    # Format date for minister lookup (YYYY-MM-DD)
    date_str = law_date.strftime("%Y-%m-%d")

    # Try to find minister using the full ministry name directly
    # The minister lookup function handles both English and Slovenian matching
    minister = find_minister(preparing_ministry, date_str)

    if not minister:
        raise ValueError(f"No minister found for ministry '{preparing_ministry}' on date {date_str}")

    return minister


def validate_api_access():
    """Validate PISRS API access."""
    try:
        # Test API access by getting a simple response
        test_law = pisrs_client.get_law_by_moped_id("ZAKO4697")  # Test with a known law
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


def main(law_id=None, output_dir=None):
    """Main function to process Slovenian legal documents into git repositories."""
    logger.info("Starting git-laws processing with targeted API approach")
    
    # Validate API access instead of data files
    if not validate_api_access():
        logger.error("Cannot proceed without PISRS API access")
        sys.exit(1)
    
    if law_id is None:
        law_id = "ZAKO4697"
    
    # Get the target law and all laws that affect it using the API
    logger.info(f"Fetching law {law_id} and related laws from PISRS API...")
    
    try:
        # Get all historical NPB (consolidated text) versions of the target law
        logger.info(f"Fetching historical NPB versions for {law_id}...")
        npb_versions_data = pisrs_client.get_historical_npb_versions(law_id)
        
        if not npb_versions_data:
            logger.error(f"No NPB versions found for law ID '{law_id}'")
            logger.error("Please check that the law ID is correct and has consolidated versions")
            sys.exit(1)
        
        # Convert to DataFrame for compatibility with existing code
        affected_laws = pd.DataFrame(npb_versions_data)
        affected_laws["date_accepted"] = pd.to_datetime(affected_laws["D_SPREJEMA"], format="%d.%m.%y")
        affected_laws = affected_laws.sort_values("date_accepted")
        
        logger.info(f"Found {len(affected_laws)} historical NPB versions to process")
        
        # Get law code from the first version
        law_code = affected_laws.iloc[0].KRATICA
        logger.info(f"Processing law {law_id} ({law_code}) - {len(affected_laws)} consolidated versions")
        
    except Exception as e:
        logger.error(f"Error fetching NPB versions for {law_id}: {e}")
        sys.exit(1)

    # Set up output directory
    if output_dir is None:
        data_location = "/tmp/slovenian_laws/"
    else:
        data_location = output_dir
    
    try:
        Path(data_location).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {data_location}")
    except PermissionError:
        logger.error(f"Permission denied creating directory: {data_location}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to create output directory {data_location}: {e}")
        sys.exit(1)
    
    # Initialize git repository
    try:
        repo = Repo.init(data_location)
        logger.info("Initialized git repository")
    except Exception as e:
        logger.error(f"Failed to initialize git repository: {e}")
        sys.exit(1)
    
    # Process each affected law
    processed_count = 0
    skipped_count = 0
    
    for _, affected_law_row in tqdm(affected_laws.iterrows(), desc="Processing laws"):
        try:
            affected_law_id = affected_law_row["ID"]
            affected_law_title = affected_law_row["NASLOV"]
            affected_law_code = affected_law_row["KRATICA"]
            affected_law_date = affected_law_row["date_accepted"]
            
            # Create enhanced commit message with actual amendment name
            amendment_name = affected_law_row.get('_amendment_name', affected_law_code)
            commit_msg_parts = [f"{amendment_name} - {affected_law_id} - {affected_law_title}"]
            
            # Add government metadata if available
            government_metadata = affected_law_row.get('_government_metadata', {})
            if government_metadata and government_metadata.get('government_info'):
                commit_msg_parts.append(government_metadata['government_info'])
            
            commit_msg = '\n'.join(commit_msg_parts)
            
            # Check if this is an NPB version or individual law
            is_npb = affected_law_row.get('_is_npb', False)
            
            if is_npb:
                # Get NPB consolidated content
                logger.info(f"Fetching NPB consolidated content for version {affected_law_id} ({affected_law_code})...")
                vsebina = pisrs_client.get_law_content(affected_law_id, is_npb=True)
            else:
                # Get individual law content (fallback)
                logger.info(f"Fetching individual law content for {affected_law_id} ({affected_law_code})...")
                vsebina = pisrs_client.get_law_content(affected_law_id, is_npb=False)
            
            if not vsebina or not vsebina.strip():
                logger.warning(f"Empty or no content for law {affected_law_id}, skipping")
                skipped_count += 1
                continue
            
            # Log content info for debugging
            content_length = len(vsebina)
            content_hash = hash(vsebina) % 10000  # Simple hash for comparison
            logger.info(f"Got content for {affected_law_id}: {content_length} chars, hash={content_hash}")
                
            # Clean up the content
            vsebina_clean = re.sub(r"( |\n|\r)+", " ", vsebina)

            try:
                soup = bs(vsebina_clean, features="html.parser")
                prettyHTML = soup.prettify()
            except Exception as e:
                logger.warning(f"Failed to parse HTML for {affected_law_id}: {e}")
                skipped_count += 1
                continue

            # Write file and commit
            try:
                output_file = Path(data_location + law_code + ".html")
                output_file.write_text(prettyHTML, encoding='utf-8')

                # Get preparing ministry from the government metadata
                preparing_ministry = None
                if government_metadata and government_metadata.get('responsible_ministry'):
                    preparing_ministry = government_metadata['responsible_ministry']

                if not preparing_ministry:
                    raise ValueError(f"No responsible ministry found for law {affected_law_id}")

                # Get the responsible minister for this law's date
                minister = get_responsible_minister(affected_law_date, preparing_ministry)

                # Create commit with minister as committer
                repo.git.add(all=True)

                # Set environment variables for git commit
                commit_env = {
                    'GIT_COMMITTER_NAME': minister['name'],
                    'GIT_COMMITTER_EMAIL': f"{minister['name'].replace(' ', '.').lower()}@gov.si",
                    'GIT_COMMITTER_DATE': affected_law_date.strftime('%Y-%m-%d %H:%M:%S %z'),
                    'GIT_AUTHOR_NAME': minister['name'],
                    'GIT_AUTHOR_EMAIL': f"{minister['name'].replace(' ', '.').lower()}@gov.si",
                    'GIT_AUTHOR_DATE': affected_law_date.strftime('%Y-%m-%d %H:%M:%S %z')
                }

                repo.git.commit(date=affected_law_date, m=commit_msg, env=commit_env)

                logger.info(f"Committed {affected_law_id} as {minister['name']} ({minister.get('ministry', 'Government')})")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to write/commit {affected_law_id}: {e}")
                skipped_count += 1
                continue
                
        except Exception as e:
            logger.error(f"Unexpected error processing law {affected_law_row.get('ID', 'unknown')}: {e}")
            skipped_count += 1
            continue
    
    # Summary
    logger.info(f"Processing complete: {processed_count} laws processed, {skipped_count} skipped")
    if processed_count > 0:
        logger.info(f"Git repository created at: {data_location}")
    else:
        logger.warning("No laws were successfully processed")


# Note: Legacy functions removed - now using PISRS API client directly


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Slovenian legal documents into git repositories using PISRS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --law-id ZAKO4697 --output-dir ./repos/tax-law
  %(prog)s --law-id ZAKO1234 --output-dir /tmp/my-law-repo
  %(prog)s  # Uses defaults (ZAKO4697, /tmp/slovenian_laws/)

Note: This tool now uses the PISRS API directly and downloads only the required
data for the specified law, making it much faster than previous bulk approaches.
        """
    )
    parser.add_argument(
        "--law-id",
        type=str,
        default="ZAKO4697",
        help="ID of the law to process (default: ZAKO4697)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for the git repository (default: /tmp/slovenian_laws/)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        main(law_id=args.law_id, output_dir=args.output_dir)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error("Please check your PISRS_API_KEY and network connectivity")
        sys.exit(1)
