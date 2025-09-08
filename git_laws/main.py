import argparse
import re
import sys
from pathlib import Path

import bson
import pandas as pd
from bs4 import BeautifulSoup as bs
from git import Repo
from loguru import logger
from markdownify import markdownify
from tqdm import tqdm


def validate_data_files():
    """Validate that all required data files exist and are accessible."""
    required_files = [
        "data/vplivana.csv",
        "data/osnovni.csv", 
        "data/vsebina.bson/pisrs/vsebina.bson"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("Missing required data files:")
        for file_path in missing_files:
            logger.error(f"  - {file_path}")
        logger.error("\nPlease ensure you have downloaded the required data files:")
        logger.error("- osnovni.csv and vplivana.csv from: https://podatki.gov.si/dataset/osnovni-podatki-o-predpisih-rs")
        logger.error("- vsebina.bson from: https://podatki.gov.si/dataset/neuradna-preciscena-besedila-predpisov")
        sys.exit(1)
    
    logger.info("All required data files found")


def main(law_id=None, output_dir=None):
    """Main function to process Slovenian legal documents into git repositories."""
    logger.info("Starting git-laws processing")
    
    # Validate required data files exist
    validate_data_files()
    
    try:
        # Load CSV data files
        logger.info("Loading CSV data files")
        vpliva_na = pd.read_csv("data/vplivana.csv")
        osnovni_raw = pd.read_csv("data/osnovni.csv")
        osnovni = osnovni_raw.dropna(subset=["D_SPREJEMA"]).copy()
        osnovni["date_accepted"] = pd.to_datetime(osnovni["D_SPREJEMA"], format="%d.%m.%y")
        
        # Load BSON data file with error handling
        logger.info("Loading BSON law content data")
        with open("data/vsebina.bson/pisrs/vsebina.bson", "rb") as f:
            try:
                laws = bson.decode_all(f.read())
                logger.info(f"Successfully loaded {len(laws)} laws from BSON data")
            except bson.InvalidBSON as e:
                logger.error(f"Failed to decode BSON data: {e}")
                logger.error("The vsebina.bson file may be corrupted. Please re-download it.")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Unexpected error reading BSON data: {e}")
                sys.exit(1)
                
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except pd.errors.EmptyDataError as e:
        logger.error(f"CSV file is empty or corrupted: {e}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading data files: {e}")
        sys.exit(1)

    if law_id is None:
        law_id = "ZAKO4697"
    
    # Validate the law ID exists
    try:
        law_code = get_law_code(law_id, osnovni)
        logger.info(f"Processing law {law_id} ({law_code})")
    except IndexError:
        logger.error(f"Law ID '{law_id}' not found in the dataset")
        logger.error("Please check that the law ID is correct and exists in osnovni.csv")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error retrieving law code for {law_id}: {e}")
        sys.exit(1)
    
    # Find affected laws
    affected_ids = vpliva_na[vpliva_na.VPLIVA_NA == law_id]
    affected = osnovni[
        ((osnovni.ID.isin(affected_ids.ID)) & (osnovni.KRATICA.str.contains(law_code)))
        | (osnovni.ID == law_id)
    ]
    affected_laws = affected[affected.ID.str.startswith("ZAKO")].sort_values(
        "date_accepted"
    )
    
    if len(affected_laws) == 0:
        logger.warning(f"No laws found that affect {law_id}")
        logger.info("This may be normal if the law has no amendments or related laws")
        return
        
    logger.info(f"Found {len(affected_laws)} laws to process")

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
            
            # Get law content with error handling
            affected_law = get_law(affected_law_id, laws)
            if not affected_law:
                skipped_count += 1
                continue
                
            # Process law content
            vsebina = affected_law["vsebina"]
            if not vsebina or not vsebina.strip():
                logger.warning(f"Empty content for law {affected_law_id}, skipping")
                skipped_count += 1
                continue
                
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


def get_law(affected_law_id, laws):
    """Retrieve law content by ID from the laws dataset."""
    try:
        laws_list = [law["idPredpisa"] for law in laws]
        if affected_law_id in laws_list:
            law_number = laws_list.index(affected_law_id)
            law = laws[law_number]
            
            # Validate that the law has required fields
            if not isinstance(law, dict):
                logger.warning(f"Invalid law data structure for {affected_law_id}")
                return None
                
            if "vsebina" not in law:
                logger.warning(f"No content field found for law {affected_law_id}")
                return None
                
            return law
        else:
            logger.warning(f"No law available for {affected_law_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving law {affected_law_id}: {e}")
        return None


def get_law_code(law_id, osnovni):
    """Get law code/abbreviation from law ID."""
    try:
        matching_laws = osnovni[osnovni.ID == law_id]
        if len(matching_laws) == 0:
            raise IndexError(f"Law ID {law_id} not found")
        law_code = matching_laws.iloc[0].KRATICA
        if pd.isna(law_code) or not law_code.strip():
            raise ValueError(f"Empty or invalid law code for {law_id}")
        return law_code
    except IndexError:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        raise Exception(f"Error getting law code for {law_id}: {e}")


def get_law_id(law_code, osnovni):
    """Get law ID from law code/abbreviation."""
    try:
        matching_laws = osnovni[osnovni.KRATICA == law_code]
        if len(matching_laws) == 0:
            raise IndexError(f"Law code {law_code} not found")
        law_id = matching_laws.iloc[0].ID
        if pd.isna(law_id) or not law_id.strip():
            raise ValueError(f"Empty or invalid law ID for code {law_code}")
        return law_id
    except IndexError:
        raise  # Re-raise to be handled by caller
    except Exception as e:
        raise Exception(f"Error getting law ID for code {law_code}: {e}")


def get_markdown(vsebina):
    """Convert HTML content to markdown format."""
    try:
        if not vsebina or not vsebina.strip():
            logger.warning("Empty content provided to get_markdown")
            return ""
        vsebina_md = markdownify(vsebina)
        return vsebina_md
    except Exception as e:
        logger.error(f"Error converting to markdown: {e}")
        return ""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Slovenian legal documents into git repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --law-id ZAKO4697 --output-dir ./repos/tax-law
  %(prog)s --law-id ZAKO1234 --output-dir /tmp/my-law-repo
  %(prog)s  # Uses defaults (ZAKO4697, /tmp/slovenian_laws/)
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
        logger.error("Please check the error message above and ensure all data files are properly downloaded")
        sys.exit(1)
