"""
PISRS API client for targeted law data retrieval.

This module provides functions to retrieve specific laws and their relationships
on-demand, rather than downloading bulk data dumps.
"""

import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()


class PISRSClient:
    """Client for PISRS API with targeted data retrieval."""
    
    def __init__(self):
        self.api_key = os.getenv('PISRS_API_KEY')
        if not self.api_key:
            raise ValueError("PISRS_API_KEY not found in environment variables")
        
        self.base_url = "https://pisrs.si/extapi"
        self.headers = {'X-API-Key': self.api_key}
    
    def get_law_by_moped_id(self, moped_id: str) -> Optional[Dict]:
        """Get specific law by its MOPED ID."""
        try:
            url = f"{self.base_url}/predpis/register-predpisov"
            params = {'mopedID': moped_id, 'pageSize': 1}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                law_data = data['data'][0]
                
                # Convert API data to expected format
                return {
                    'ID': law_data.get('mopedId', ''),
                    'KRATICA': law_data.get('kratica', ''),
                    'NASLOV': law_data.get('naziv', ''),
                    'D_SPREJEMA': self._convert_date(law_data.get('datumSprejetja')),
                    'DATUMOBJ': self._convert_date(law_data.get('datumObjave')),
                    'OSNOVNI': law_data.get('osnovni', False),
                    'EVA': law_data.get('eva', ''),
                    'EPA': law_data.get('epa', ''),
                    'SOP': law_data.get('sop', ''),
                    'CITAT': law_data.get('citat', ''),
                    '_raw': law_data  # Keep raw data for relationship extraction
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get law {moped_id}: {e}")
            return None
    
    def get_historical_npb_versions(self, moped_id: str) -> List[Dict]:
        """Get all historical NPB (consolidated text) versions of a law."""
        try:
            # First get the target law to get its EPA/SOP/EVA identifiers and metadata
            target_law = self.get_law_by_moped_id(moped_id)
            if not target_law or not target_law.get('_raw'):
                logger.warning(f"Target law {moped_id} not found")
                return []
            
            raw_data = target_law['_raw']
            epa = raw_data.get('epa')
            sop = raw_data.get('sop') 
            eva = raw_data.get('eva')
            
            # Extract government/ministry metadata
            government_metadata = {
                'responsible_ministry': None,
                'adopting_body': None,
                'government_info': ''
            }
            
            if 'organOdgovorenZaPripravo' in raw_data and raw_data['organOdgovorenZaPripravo']:
                ministry_info = raw_data['organOdgovorenZaPripravo'][0] if isinstance(raw_data['organOdgovorenZaPripravo'], list) else raw_data['organOdgovorenZaPripravo']
                government_metadata['responsible_ministry'] = ministry_info.get('naziv', '')
            
            if 'organKiJeSprejelOzIzdalAkt' in raw_data:
                government_metadata['adopting_body'] = raw_data['organKiJeSprejelOzIzdalAkt'].get('naziv', '')
            
            # Create government info string
            gov_parts = []
            if government_metadata['responsible_ministry']:
                gov_parts.append(f"Prepared by: {government_metadata['responsible_ministry']}")
            if government_metadata['adopting_body']:
                gov_parts.append(f"Adopted by: {government_metadata['adopting_body']}")
            government_metadata['government_info'] = ' | '.join(gov_parts)
            
            if not any([epa, sop, eva]):
                logger.warning(f"No EPA/SOP/EVA identifiers found for law {moped_id}")
                return []
            
            # Search for NPB versions using the most reliable identifier (EPA worked best in tests)
            search_params = []
            if epa:
                search_params.append(('epa', epa))
            if sop:
                search_params.append(('sop', sop))
            if eva:
                search_params.append(('eva', eva))
            
            npb_versions = []
            url = f"{self.base_url}/npb"
            
            for param_name, param_value in search_params:
                try:
                    params = {param_name: param_value, 'pageSize': 100}
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'data' in data and data['data']:
                        npb_versions = data['data']
                        logger.info(f"Found {len(npb_versions)} NPB versions using {param_name}")
                        break  # Use the first successful search
                        
                except Exception as e:
                    logger.warning(f"NPB search by {param_name} failed: {e}")
                    continue
            
            if not npb_versions:
                logger.warning(f"No NPB versions found for law {moped_id}")
                return []
            
            # Sort by date (oldest first) and convert to expected format
            npb_versions.sort(key=lambda x: x.get('datumDokumenta', ''))
            
            # Get amendment information to map NPB versions to actual amendments
            amendments = raw_data.get('posegiVPredpis', [])
            
            result = []
            for i, npb in enumerate(npb_versions):
                # Extract version info from stevilkaDokumenta 
                stevilka = npb.get('stevilkaDokumenta', '')
                version_number = i + 1  # NPB sequence number
                
                # Try to determine the actual amendment name
                amendment_name = self._determine_amendment_name(npb, version_number, amendments, target_law['KRATICA'])
                
                # Convert NPB data to format compatible with main script
                npb_entry = {
                    'ID': str(npb.get('id')),  # Use NPB ID as the law ID
                    'KRATICA': amendment_name,  # Use actual amendment name instead of parent
                    'NASLOV': npb.get('naziv', ''),
                    'D_SPREJEMA': self._convert_date(npb.get('datumDokumenta')),
                    'DATUMOBJ': self._convert_date(npb.get('datumDokumenta')),
                    'OSNOVNI': True,  # NPB versions are consolidated texts
                    # Remove meaningless inherited identifiers
                    'CITAT': '',
                    '_raw': npb,
                    '_is_npb': True,  # Flag to indicate this is an NPB version
                    '_government_metadata': government_metadata,  # Add government metadata
                    '_amendment_name': amendment_name,  # Store for commit messages
                    '_version_number': version_number
                }
                result.append(npb_entry)
            
            logger.info(f"Found {len(result)} historical NPB versions for {moped_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get NPB versions for {moped_id}: {e}")
            return []
    
    def get_law_content(self, law_id: str, is_npb: bool = False) -> Optional[str]:
        """Get the content of a law by ID. If is_npb=True, law_id is treated as an NPB ID."""
        try:
            if is_npb:
                # law_id is already an NPB internal ID, use it directly
                logger.debug(f"Getting NPB consolidated content using NPB ID {law_id}")
                content = self._get_content_by_id(int(law_id))
                
                if content:
                    return content
                else:
                    logger.warning(f"No content returned for NPB ID {law_id}")
                    return None
            else:
                # Original behavior for individual law content
                law_data = self.get_law_by_moped_id(law_id)
                if not law_data or not law_data.get('_raw'):
                    logger.warning(f"No law data found for {law_id}")
                    return None
                
                internal_id = law_data['_raw'].get('id')
                if not internal_id:
                    logger.warning(f"No internal ID found for law {law_id}")
                    return None
                
                logger.debug(f"Getting original content for law {law_id} using internal ID {internal_id}")
                content = self._get_content_by_id(internal_id)
                
                if content:
                    return content
                else:
                    logger.warning(f"No content returned for law {law_id} (internal ID: {internal_id})")
                    return None
            
        except Exception as e:
            logger.error(f"Failed to get content for law {law_id}: {e}")
            return None
    
    # Note: NPB finding removed - we now get original historical content directly
    
    def _get_content_by_id(self, content_id: int) -> Optional[str]:
        """Get content text by internal ID."""
        try:
            url = f"{self.base_url}/besedilo/{content_id}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to get content for ID {content_id}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting content for ID {content_id}: {e}")
            return None
    
    def _law_affects_target(self, law_data: Dict, target_law_data: Dict) -> bool:
        """Check if a law affects the target law based on relationships."""
        target_moped_id = target_law_data.get('mopedId', '')
        target_kratica = target_law_data.get('kratica', '')
        
        if not target_moped_id:
            return False
        
        # Check relationship fields in the law data
        relationship_fields = ['vplivaNaPredpise', 'posegaVPredpise']
        
        for field in relationship_fields:
            if field in law_data and law_data[field]:
                relationships = law_data[field]
                if not isinstance(relationships, list):
                    relationships = [relationships]
                
                for rel in relationships:
                    if isinstance(rel, dict):
                        related_id = rel.get('mopedID', '')
                        if related_id == target_moped_id:
                            return True
        
        # Also check by KRATICA similarity for amendments
        law_kratica = law_data.get('kratica', '')
        if law_kratica and target_kratica:
            # Check if this looks like an amendment (contains target KRATICA)
            if target_kratica in law_kratica and law_kratica != target_kratica:
                return True
        
        return False
    
    def _convert_date(self, date_str: str) -> str:
        """Convert date from YYYY-MM-DD to DD.MM.YY format."""
        if date_str and date_str != 'null':
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%d.%m.%y')
            except:
                return date_str
        return ''
    
    def _parse_date(self, date_str: str) -> str:
        """Convert DD.MM.YY back to YYYY-MM-DD for sorting."""
        if date_str and '.' in date_str:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, '%d.%m.%y')
                return dt.strftime('%Y-%m-%d')
            except:
                return date_str
        return date_str
    
    def _determine_amendment_name(self, npb_data: Dict, version_number: int, amendments: List[Dict], base_kratica: str) -> str:
        """
        Determine the actual amendment name for an NPB version.
        
        Args:
            npb_data: NPB version data
            version_number: Sequential number of this NPB version
            amendments: List of amendments from posegiVPredpis
            base_kratica: Base law abbreviation (e.g., "ZDoh-2")
        
        Returns:
            Amendment name like "ZDoh-2A", "ZDoh-2B", etc., or base name for original
        """
        if version_number == 1:
            # First version is the original law
            return base_kratica
        
        # Try to match by date proximity with amendments
        npb_date_str = npb_data.get('datumDokumenta', '')
        if not npb_date_str:
            return f"{base_kratica}-v{version_number}"
        
        try:
            from datetime import datetime
            npb_date = datetime.strptime(npb_date_str, '%Y-%m-%d')
        except:
            return f"{base_kratica}-v{version_number}"
        
        # Look for amendment that was adopted close to this NPB date
        # NPB versions are created after amendments are adopted and consolidated
        closest_amendment = None
        min_days_diff = float('inf')
        
        for amendment in amendments:
            amendment_name = amendment.get('naziv', '')
            
            # Extract KRATICA from amendment name if possible
            # e.g., "Zakon o spremembah... (ZDoh-2A)" -> "ZDoh-2A"  
            import re
            kratica_match = re.search(r'\(([^)]+)\)$', amendment_name)
            if kratica_match:
                kratica = kratica_match.group(1)
                
                # Basic heuristic: map NPB versions to amendments sequentially
                # This assumes NPB versions are created in the same order as amendments
                if version_number <= len(amendments):
                    target_amendment_idx = version_number - 2  # -1 for 0-indexing, -1 for skipping original
                    if 0 <= target_amendment_idx < len(amendments):
                        target_amendment = amendments[target_amendment_idx]
                        target_name = target_amendment.get('naziv', '')
                        target_kratica_match = re.search(r'\(([^)]+)\)$', target_name)
                        if target_kratica_match:
                            return target_kratica_match.group(1)
        
        # Fallback: generate based on version number
        if version_number == 2:
            return f"{base_kratica}A"
        elif version_number == 3:
            return f"{base_kratica}B"
        elif version_number == 4:
            return f"{base_kratica}C"
        else:
            # For later versions, use letters: D, E, F, ..., Z, AA, AB, etc.
            letter_idx = version_number - 2  # Start from A for version 2
            if letter_idx < 26:
                letter = chr(ord('A') + letter_idx)
                return f"{base_kratica}{letter}"
            else:
                # Handle beyond Z: AA, AB, AC, etc.
                first_letter = chr(ord('A') + (letter_idx - 26) // 26)
                second_letter = chr(ord('A') + (letter_idx - 26) % 26)
                return f"{base_kratica}{first_letter}{second_letter}"


# Global client instance
pisrs_client = PISRSClient()