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
    
    def get_laws_affecting_law(self, moped_id: str) -> List[Dict]:
        """Get all laws that affect the specified law."""
        try:
            # First get the target law to understand what affects it
            target_law = self.get_law_by_moped_id(moped_id)
            if not target_law:
                logger.warning(f"Target law {moped_id} not found")
                return []
            
            target_kratica = target_law['KRATICA']
            if not target_kratica:
                logger.warning(f"No KRATICA found for law {moped_id}")
                return [target_law]  # Return just the target law
            
            # Search for laws that mention this KRATICA in their relationships
            # This is more complex, so we'll use a broader search approach
            url = f"{self.base_url}/predpis/register-predpisov"
            
            affecting_laws = [target_law]  # Always include the target law itself
            
            # Search for amendments and related laws by KRATICA pattern
            # Laws that affect this one often have similar KRATICA patterns
            kratica_base = target_kratica.split('-')[0]  # Get base part before dash
            
            page = 1
            while page <= 10:  # Limit search to prevent excessive API calls
                params = {
                    'pageSize': 1000,
                    'page': page,
                    'osnovni': False  # Look for amendments/modifications (non-basic laws)
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if 'data' not in data or not data['data']:
                    break
                
                for law_data in data['data']:
                    law_kratica = law_data.get('kratica', '')
                    law_moped_id = law_data.get('mopedId', '')
                    
                    # Check if this law affects our target law
                    if self._law_affects_target(law_data, target_law['_raw']):
                        converted_law = {
                            'ID': law_moped_id,
                            'KRATICA': law_kratica,
                            'NASLOV': law_data.get('naziv', ''),
                            'D_SPREJEMA': self._convert_date(law_data.get('datumSprejetja')),
                            'DATUMOBJ': self._convert_date(law_data.get('datumObjave')),
                            'OSNOVNI': law_data.get('osnovni', False),
                            'EVA': law_data.get('eva', ''),
                            'EPA': law_data.get('epa', ''),
                            'SOP': law_data.get('sop', ''),
                            'CITAT': law_data.get('citat', ''),
                            '_raw': law_data
                        }
                        affecting_laws.append(converted_law)
                
                if len(data['data']) < 1000:
                    break
                
                page += 1
            
            # Remove duplicates and sort by date
            unique_laws = {}
            for law in affecting_laws:
                unique_laws[law['ID']] = law
            
            result = list(unique_laws.values())
            result = [law for law in result if law['D_SPREJEMA']]  # Only laws with dates
            
            # Sort by date
            result.sort(key=lambda x: self._parse_date(x['D_SPREJEMA']) if x['D_SPREJEMA'] else '1900-01-01')
            
            logger.info(f"Found {len(result)} laws affecting {moped_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get laws affecting {moped_id}: {e}")
            return []
    
    def get_law_content(self, law_id: str) -> Optional[str]:
        """Get the content (text) of a specific law by ID."""
        try:
            # First try to find NPB (consolidated text) for this law
            npb_id = self._find_npb_for_law(law_id)
            if npb_id:
                return self._get_content_by_id(npb_id)
            
            # If no NPB found, try to get basic law content
            # We need to search for the law first to get its internal ID
            law_data = self.get_law_by_moped_id(law_id)
            if law_data and law_data.get('_raw'):
                internal_id = law_data['_raw'].get('id')
                if internal_id:
                    return self._get_content_by_id(internal_id)
            
            logger.warning(f"No content found for law {law_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get content for law {law_id}: {e}")
            return None
    
    def _find_npb_for_law(self, moped_id: str) -> Optional[int]:
        """Find NPB (consolidated text) ID for a given law."""
        try:
            url = f"{self.base_url}/npb"
            
            # Search NPB by different criteria
            search_params = [
                {'stevilkaDokumenta': moped_id},
                # Could add more search strategies here
            ]
            
            for params in search_params:
                params.update({'pageSize': 100, 'page': 1})
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and len(data['data']) > 0:
                        # Return the most recent NPB
                        npb_items = sorted(data['data'], 
                                         key=lambda x: x.get('datumDokumenta', ''), 
                                         reverse=True)
                        return npb_items[0]['id']
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to find NPB for {moped_id}: {e}")
            return None
    
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


# Global client instance
pisrs_client = PISRSClient()