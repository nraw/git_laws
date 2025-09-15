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
        # Get all laws affecting the target law (including the law itself)
        affected_laws_data = pisrs_client.get_laws_affecting_law(law_id)
        
        if not affected_laws_data:
            logger.error(f"Law ID '{law_id}' not found or no related laws found")
            logger.error("Please check that the law ID is correct")
            sys.exit(1)
        
        # Filter for laws that start with "ZAKO" and have dates
        affected_laws_data = [
            law for law in affected_laws_data 
            if law['ID'].startswith("ZAKO") and law['D_SPREJEMA']
        ]
        
        if not affected_laws_data:
            logger.warning(f"No processable laws found for {law_id}")
            logger.info("This may indicate the law ID is not a ZAKO-type law or has no date")
            return
        
        # Convert to DataFrame for compatibility with existing code
        affected_laws = pd.DataFrame(affected_laws_data)
        affected_laws["date_accepted"] = pd.to_datetime(affected_laws["D_SPREJEMA"], format="%d.%m.%y")
        affected_laws = affected_laws.sort_values("date_accepted")
        
        logger.info(f"Found {len(affected_laws)} laws to process")
        
        # Get law code for the target law
        target_law = affected_laws[affected_laws.ID == law_id]
        if len(target_law) == 0:
            logger.error(f"Target law {law_id} not found in affected laws")
            sys.exit(1)
        
        law_code = target_law.iloc[0].KRATICA
        logger.info(f"Processing law {law_id} ({law_code})")
        
    except Exception as e:
        logger.error(f"Error fetching law data for {law_id}: {e}")
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
            commit_msg = (
                affected_law_code + " - " + affected_law_id + " - " + affected_law_title
            )
            affected_law_date = affected_law_row["date_accepted"]
            
            # Get law content from API
            logger.info(f"Fetching content for law {affected_law_id}...")
            vsebina = pisrs_client.get_law_content(affected_law_id)
            
            if not vsebina or not vsebina.strip():
                logger.warning(f"Empty or no content for law {affected_law_id}, skipping")
                skipped_count += 1
                continue
                
            # Clean up the content
            vsebina_clean = re.sub(r"( |\n|\r)+", " ", vsebina)

            try:
                soup = bs(vsebina_clean)
                prettyHTML = soup.prettify()
            except Exception as e:
                logger.warning(f"Failed to parse HTML for {affected_law_id}: {e}")
                skipped_count += 1
                continue

            # Write file and commit
            try:
                output_file = Path(data_location + law_code + ".html")
                output_file.write_text(prettyHTML, encoding='utf-8')
                
                repo.git.add(all=True)
                repo.git.commit(date=affected_law_date, m=commit_msg)
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
        default="/tmp/slovenian_laws/",
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
