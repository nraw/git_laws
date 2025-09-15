"""
Data downloader for Slovenian legal documents.

This module provides functionality to automatically download the required data files
from the Slovenian government's open data portal (OPSI) and PISRS system.
"""

import json
import os
import tarfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bson
import pandas as pd
import requests
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

# Load environment variables
load_dotenv()


def create_data_directory():
    """Create the data directory if it doesn't exist."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def download_file(url, filepath, description="Downloading file"):
    """Download a file from URL with progress bar."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as file, tqdm(
            desc=description,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    progress_bar.update(len(chunk))
        
        logger.info(f"Successfully downloaded: {filepath}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False


def download_csv_from_pisrs_api():
    """
    Download CSV data from PISRS API using the correct endpoints.
    
    This function uses the official PISRS API to get basic regulation data (osnovni) 
    and relationship data (vplivana) from the register of regulations.
    """
    data_dir = create_data_directory()
    
    # Get API key from environment
    api_key = os.getenv('PISRS_API_KEY')
    if not api_key:
        logger.error("PISRS_API_KEY not found in environment variables")
        logger.error("Please set PISRS_API_KEY in your .env file")
        return False
    
    # Correct base URL from pisrs.json
    base_url = "https://pisrs.si/extapi"
    success_count = 0
    
    # Correct authentication method from pisrs.json
    headers = {
        'X-API-Key': api_key
    }
    
    # Get basic regulation data (osnovni)
    logger.info("Downloading basic regulation data (osnovni.csv)...")
    try:
        # Use the register-predpisov endpoint to get all regulations data
        osnovni_url = f"{base_url}/predpis/register-predpisov"
        osnovni_data = []
        page = 1
        page_size = 1000  # Maximum allowed by API
        
        while True:
            params = {
                'pageSize': page_size,
                'page': page
            }
            
            logger.info(f"Fetching page {page} of osnovni data...")
            response = requests.get(osnovni_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have data
            if 'data' not in data or not data['data']:
                break
            
            osnovni_data.extend(data['data'])
            
            # Check if we've reached the end
            if len(data['data']) < page_size:
                break
            
            page += 1
            
            # Safety limit to prevent infinite loops
            if page > 100:  # Max 100k records
                logger.warning("Reached safety limit of 100 pages for osnovni data")
                break
        
        if osnovni_data:
            # Convert API data to expected CSV format
            # Map API fields to expected CSV column names
            converted_data = []
            for item in osnovni_data:
                # Convert date format from YYYY-MM-DD to DD.MM.YY
                def convert_date(date_str):
                    if date_str and date_str != 'null':
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(date_str, '%Y-%m-%d')
                            return dt.strftime('%d.%m.%y')
                        except:
                            return date_str
                    return ''
                
                converted_item = {
                    'ID': item.get('mopedId', ''),
                    'KRATICA': item.get('kratica', ''),
                    'NASLOV': item.get('naziv', ''),
                    'D_SPREJEMA': convert_date(item.get('datumSprejetja')),
                    'DATUMOBJ': convert_date(item.get('datumObjave')),
                    'OSNOVNI': item.get('osnovni', False),
                    'EVA': item.get('eva', ''),
                    'EPA': item.get('epa', ''),
                    'SOP': item.get('sop', ''),
                    'CITAT': item.get('citat', ''),
                }
                converted_data.append(converted_item)
            
            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(converted_data)
            osnovni_path = data_dir / "osnovni.csv"
            df.to_csv(osnovni_path, index=False, encoding='utf-8')
            logger.info(f"Successfully downloaded osnovni.csv with {len(converted_data)} records")
            success_count += 1
        else:
            logger.error("No osnovni data received from API")
            
    except Exception as e:
        logger.error(f"Failed to download osnovni data: {e}")
    
    # For vplivana (relationship data), we need to construct it from the osnovni data
    # by looking at relationships between regulations
    logger.info("Constructing relationship data (vplivana.csv)...")
    try:
        if osnovni_data:
            vplivana_data = []
            
            # Process relationships from osnovni data
            for regulation in osnovni_data:
                reg_moped_id = regulation.get('mopedId')  # Use mopedId as the main identifier
                if reg_moped_id:
                    # Check for related regulations based on the actual API fields
                    # From the debug output, we can see fields like:
                    # vplivaNaPredpise, vpliviNaPredpis, posegaVPredpise, posegiVPredpis
                    
                    related_fields = [
                        ('vplivaNaPredpise', 'VPLIVA_NA'),
                        ('vpliviNaPredpis', 'VPLIVI_NA'),
                        ('posegaVPredpise', 'POSEGA_V'),
                        ('posegiVPredpis', 'POSEGI_V')
                    ]
                    
                    for field_name, relation_type in related_fields:
                        if field_name in regulation and regulation[field_name]:
                            related_items = regulation[field_name]
                            if isinstance(related_items, list):
                                for related_item in related_items:
                                    if isinstance(related_item, dict) and 'mopedID' in related_item:
                                        vplivana_data.append({
                                            'ID': reg_moped_id,
                                            'VPLIVA_NA': related_item['mopedID'],
                                            'TIP_VPLIVA': relation_type
                                        })
                            elif isinstance(related_items, dict) and 'mopedID' in related_items:
                                vplivana_data.append({
                                    'ID': reg_moped_id,
                                    'VPLIVA_NA': related_items['mopedID'],
                                    'TIP_VPLIVA': relation_type
                                })
            
            if vplivana_data:
                # Convert to DataFrame and save as CSV
                df_vplivana = pd.DataFrame(vplivana_data)
                vplivana_path = data_dir / "vplivana.csv"
                df_vplivana.to_csv(vplivana_path, index=False, encoding='utf-8')
                logger.info(f"Successfully created vplivana.csv with {len(vplivana_data)} relationships")
                success_count += 1
            else:
                # Create empty vplivana.csv with proper headers
                df_vplivana = pd.DataFrame(columns=['ID', 'VPLIVA_NA', 'TIP_VPLIVA'])
                vplivana_path = data_dir / "vplivana.csv"
                df_vplivana.to_csv(vplivana_path, index=False, encoding='utf-8')
                logger.info("Created empty vplivana.csv (no relationships found in data)")
                success_count += 1
        else:
            logger.error("Cannot create vplivana data without osnovni data")
            
    except Exception as e:
        logger.error(f"Failed to create vplivana data: {e}")
    
    return success_count >= 2


def download_bson_data():
    """
    Download BSON data containing law content using PISRS API.
    """
    data_dir = create_data_directory()
    
    # Get API key from environment
    api_key = os.getenv('PISRS_API_KEY')
    if not api_key:
        logger.error("PISRS_API_KEY not found in environment variables")
        return False
    
    # Correct authentication method from pisrs.json
    headers = {
        'X-API-Key': api_key
    }
    
    # Correct base URL from pisrs.json
    base_url = "https://pisrs.si/extapi"
    
    # Try to get content data using the NPB (Neuradna prečiščena besedila) endpoint
    logger.info("Downloading legal content data (vsebina.bson)...")
    
    try:
        # Use the NPB endpoint to get consolidated text data
        npb_url = f"{base_url}/npb"
        content_data = []
        page = 1
        page_size = 1000
        
        while True:
            params = {
                'pageSize': page_size,
                'page': page
            }
            
            logger.info(f"Fetching page {page} of content data...")
            response = requests.get(npb_url, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have data
            if 'data' not in data or not data['data']:
                break
            
            # For each regulation, get its content using the besedilo endpoint
            for item in data['data']:
                if 'id' in item:
                    try:
                        content_url = f"{base_url}/besedilo/{item['id']}"
                        content_response = requests.get(content_url, headers=headers, timeout=30)
                        if content_response.status_code == 200:
                            # The besedilo endpoint returns HTML directly, not JSON
                            html_content = content_response.text
                            
                            # Structure the data similar to the expected BSON format
                            # Use the NPB item's ID as a string (since that's what the main script expects)
                            content_item = {
                                'idPredpisa': str(item['id']),  # Convert to string
                                'vsebina': html_content,
                                'naslov': item.get('naziv', ''),
                                'kratica': item.get('stevilkaDokumenta', ''),
                                'metadata': item
                            }
                            content_data.append(content_item)
                            
                        if len(content_data) % 100 == 0:
                            logger.info(f"Downloaded content for {len(content_data)} regulations...")
                            
                    except Exception as e:
                        logger.warning(f"Failed to get content for regulation {item.get('id', 'unknown')}: {e}")
                        continue
            
            # Check if we've reached the end
            if len(data['data']) < page_size:
                break
            
            page += 1
            
            # Safety limit to prevent infinite loops
            if page > 50:  # Max 50k content records
                logger.warning("Reached safety limit of 50 pages for content data")
                break
        
        if content_data:
            # Create directory structure and save as BSON
            bson_dir = data_dir / "vsebina.bson" / "pisrs"
            bson_dir.mkdir(parents=True, exist_ok=True)
            bson_path = bson_dir / "vsebina.bson"
            
            # Write as BSON format
            with open(bson_path, 'wb') as f:
                for item in content_data:
                    f.write(bson.encode(item))
            
            logger.info(f"Successfully downloaded vsebina.bson with {len(content_data)} content records")
            return True
        else:
            logger.error("No content data received from API")
            return False
            
    except Exception as e:
        logger.error(f"Failed to download content data: {e}")
        return False


def extract_archive(archive_path, extract_to):
    """Extract downloaded archive files."""
    try:
        logger.info(f"Extracting {archive_path}")
        
        if str(archive_path).endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
        elif str(archive_path).endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                
        logger.info(f"Successfully extracted {archive_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract {archive_path}: {e}")
        return False


def convert_json_to_bson(json_file, bson_file):
    """Convert JSON file to BSON format if needed."""
    try:
        logger.info(f"Converting {json_file} to BSON format")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure directory exists
        bson_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write as BSON
        with open(bson_file, 'wb') as f:
            if isinstance(data, list):
                for item in data:
                    f.write(bson.encode(item))
            else:
                f.write(bson.encode(data))
        
        logger.info(f"Successfully converted to BSON: {bson_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert JSON to BSON: {e}")
        return False


def fallback_manual_instructions():
    """Provide fallback instructions if automatic download fails."""
    logger.warning("Automatic download failed. Please download files manually:")
    logger.warning("")
    logger.warning("1. Basic regulation data (osnovni.csv and vplivana.csv):")
    logger.warning("   Visit: https://podatki.gov.si/dataset/osnovni-podatki-o-predpisih-rs")
    logger.warning("   Look for CSV download options or API access")
    logger.warning("")
    logger.warning("2. Legal content data (vsebina.bson):")
    logger.warning("   Visit: https://podatki.gov.si/dataset/neuradna-preciscena-besedila-predpisov")
    logger.warning("   Look for BSON or JSON download options")
    logger.warning("")
    logger.warning("3. Alternative approach:")
    logger.warning("   Contact PISRS support or check their API documentation at:")
    logger.warning("   https://pisrs.si/swagger")
    logger.warning("")
    logger.warning("Expected file structure:")
    logger.warning("data/")
    logger.warning("├── osnovni.csv")
    logger.warning("├── vplivana.csv")
    logger.warning("└── vsebina.bson/")
    logger.warning("    └── pisrs/")
    logger.warning("        └── vsebina.bson")


def download_all_data():
    """
    Main function to download all required data files.
    
    Returns:
        bool: True if all files were downloaded successfully, False otherwise.
    """
    logger.info("Starting automatic data download...")
    
    csv_success = download_csv_from_pisrs_api()
    bson_success = download_bson_data()
    
    if csv_success and bson_success:
        logger.info("All data files downloaded successfully!")
        return True
    
    elif csv_success:
        logger.warning("CSV files downloaded, but BSON data failed")
        fallback_manual_instructions()
        return False
    
    elif bson_success:
        logger.warning("BSON data downloaded, but CSV files failed")
        fallback_manual_instructions()
        return False
    
    else:
        logger.error("Failed to download any data files automatically")
        fallback_manual_instructions()
        return False


if __name__ == "__main__":
    download_all_data()