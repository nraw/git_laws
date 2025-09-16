"""
Web scraper to extract historical Slovenian minister information from gov.si
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger


class SlowenianMinisterScraper:
    """Scrape minister information from Slovenian government websites."""

    def __init__(self):
        self.base_url = "https://www.gov.si"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_historical_governments(self) -> List[Dict]:
        """Scrape the main historical governments page to get government list."""
        url = f"{self.base_url}/drzavni-organi/vlada/o-vladi/pretekle-vlade/"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            governments = []

            # Look for list items containing government information
            # Pattern: <li>[Number. Government Name](/path/) (dates) predsednik vlade Name</li>
            list_items = soup.find_all('li')

            for li in list_items:
                # Get all the text content from this list item
                li_text = li.get_text(strip=True)

                # Look for government links within this list item
                links = li.find_all('a', href=True)

                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)

                    # Check if this looks like a government page link
                    if ('/pretekle-vlade/' in href and
                        ('vlada' in link_text.lower() or re.match(r'\d+\.', link_text))):

                        # Parse the full list item text for complete info
                        gov_info = self._parse_government_list_item(li_text, href, link_text)
                        if gov_info:
                            governments.append(gov_info)
                            logger.info(f"Found government: {gov_info['number']} - {gov_info['pm']}")

            return governments

        except Exception as e:
            logger.error(f"Error scraping historical governments: {e}")
            return []

    def _parse_government_list_item(self, li_text: str, href: str, link_text: str) -> Optional[Dict]:
        """Parse government information from complete list item text."""
        # Pattern: "1. Vlada Republike Slovenije (16. 5. 1990 - 14. 5. 1992) predsednik vlade Lojze Peterle"

        # Extract government number from link text
        number_match = re.match(r'(\d+)\.', link_text)
        if not number_match:
            return None

        gov_number = int(number_match.group(1))

        # Extract date range - look for (date - date) pattern
        date_pattern = r'\(([^)]+)\)'
        date_match = re.search(date_pattern, li_text)
        date_range = date_match.group(1).strip() if date_match else ""

        # Extract PM name - look for "predsednik vlade" pattern
        pm_pattern = r'predsednik\s+vlade\s+([^(\n]+?)(?:\s*\(|$)'
        pm_match = re.search(pm_pattern, li_text, re.IGNORECASE)
        pm_name = pm_match.group(1).strip() if pm_match else ""

        return {
            'number': gov_number,
            'date_range': date_range,
            'pm': pm_name,
            'url': self.base_url + href if href.startswith('/') else href,
            'link_text': link_text,
            'raw_text': li_text
        }

    def _parse_government_link_text(self, text: str, href: str) -> Optional[Dict]:
        """Parse government information from link text. (Legacy method)"""
        # Look for patterns like "1. vlada (16. 5. 1990 - 14. 5. 1992)"
        pattern = r'(\d+)\.\s*vlada.*?\((.+?)\)'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            gov_number = match.group(1)
            date_range = match.group(2).strip()

            # Extract PM name - usually after the date range
            pm_pattern = r'vlada[^(]*\([^)]*\)\s*(.+?)(?:\s*-|$)'
            pm_match = re.search(pm_pattern, text, re.IGNORECASE)
            pm_name = pm_match.group(1).strip() if pm_match else ""

            return {
                'number': int(gov_number),
                'date_range': date_range,
                'pm': pm_name,
                'url': self.base_url + href if href.startswith('/') else href,
                'raw_text': text
            }

        return None

    def scrape_government_details(self, government_info: Dict) -> Dict:
        """Scrape detailed information from a specific government page."""
        url = government_info['url']

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            details = government_info.copy()
            details['ministers'] = []
            details['ministries'] = {}

            # Look for minister information in various possible structures
            ministers = self._extract_ministers_from_page(soup)
            details['ministers'] = ministers

            # Look for coalition information
            coalition_info = self._extract_coalition_info(soup)
            if coalition_info:
                details['coalition'] = coalition_info

            # Look for time period information if not already parsed
            if not details.get('start_date') or not details.get('end_date'):
                period_info = self._extract_period_info(soup, details.get('date_range', ''))
                details.update(period_info)

            logger.info(f"Scraped {len(ministers)} ministers for government {details['number']}")
            return details

        except Exception as e:
            logger.error(f"Error scraping government {government_info['number']} at {url}: {e}")
            return government_info

    def _extract_ministers_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract minister information from a government page."""
        ministers = []

        # Pattern 1: Look for bold text followed by minister details
        # Structure: **Name Surname** minister for [ministry] – elected date – function ceased date
        bold_elements = soup.find_all(['strong', 'b'])

        for bold in bold_elements:
            bold_text = bold.get_text(strip=True)

            # Check if this looks like a minister name (at least 2 words, proper capitalization)
            if self._looks_like_minister_name(bold_text):
                # Look for the text that follows this bold element
                following_text = self._get_following_text(bold)

                if following_text:
                    minister_info = self._parse_minister_entry(bold_text, following_text)
                    if minister_info:
                        ministers.append(minister_info)

        # Pattern 2: Look for structured text patterns mentioning ministers
        all_text = soup.get_text()
        minister_entries = self._extract_ministers_from_full_text(all_text)
        ministers.extend(minister_entries)

        # Pattern 3: Table with ministers
        tables = soup.find_all('table')
        for table in tables:
            ministers.extend(self._extract_ministers_from_table(table))

        # Pattern 4: List items containing minister info
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            ministers.extend(self._extract_ministers_from_list(list_elem))

        # Remove duplicates
        unique_ministers = []
        seen = set()
        for minister in ministers:
            key = (minister['name'], minister.get('ministry', ''))
            if key not in seen:
                seen.add(key)
                unique_ministers.append(minister)

        return unique_ministers

    def _looks_like_minister_name(self, text: str) -> bool:
        """Check if text looks like a minister name."""
        if not text:
            return False

        words = text.split()
        if len(words) < 2:
            return False

        # Check for proper capitalization
        for word in words:
            if not word[0].isupper():
                return False

        # Exclude common non-name patterns
        exclude_patterns = ['VLADA', 'MINISTRSTVO', 'MINISTRI', 'PREDSEDNIK', 'KOALICIJA']
        if any(pattern in text.upper() for pattern in exclude_patterns):
            return False

        return True

    def _get_following_text(self, element) -> str:
        """Get text that follows a specific element."""
        following_text = ""

        # Get the parent and look for text after this element
        parent = element.parent
        if parent:
            # Get all text from parent
            parent_text = parent.get_text()

            # Find where our element text appears and get what follows
            element_text = element.get_text()
            element_pos = parent_text.find(element_text)

            if element_pos >= 0:
                following_text = parent_text[element_pos + len(element_text):].strip()

        return following_text

    def _parse_minister_entry(self, name: str, following_text: str) -> Optional[Dict]:
        """Parse minister entry from name and following text."""
        # Pattern: "minister for [ministry] – elected date – function ceased date"

        # Look for ministry information
        ministry_patterns = [
            r'ministr[a-z]*\s+za\s+([^–\n]+)',  # "minister za finance"
            r'minister\s+for\s+([^–\n]+)',      # "minister for finance"
            r'([^–\n]*ministr[a-z]*[^–\n]*)',   # any text containing "ministr"
        ]

        ministry = ""
        for pattern in ministry_patterns:
            match = re.search(pattern, following_text, re.IGNORECASE)
            if match:
                ministry = match.group(1).strip()
                break

        # Look for date information
        start_date = ""
        end_date = ""

        # Pattern for dates: "elected 3. 12. 2004" or "izvoljen 3. 12. 2004"
        start_patterns = [
            r'(?:izvoljen|elected)\s+(\d+\.\s*\d+\.\s*\d{4})',
            r'nastopil\s+funkcijo\s+(\d+\.\s*\d+\.\s*\d{4})',
        ]

        for pattern in start_patterns:
            match = re.search(pattern, following_text, re.IGNORECASE)
            if match:
                start_date = match.group(1).strip()
                break

        # Pattern for end dates: "function ceased 21. 11. 2008" or "prenehala funkcija 21. 11. 2008"
        end_patterns = [
            r'(?:prenehala?\s+funkcij[ao]|function\s+ceased)\s+(\d+\.\s*\d+\.\s*\d{4})',
            r'končal\s+(?:mandat|funkcijo)\s+(\d+\.\s*\d+\.\s*\d{4})',
        ]

        for pattern in end_patterns:
            match = re.search(pattern, following_text, re.IGNORECASE)
            if match:
                end_date = match.group(1).strip()
                break

        if ministry or start_date:  # At least one piece of useful info
            return {
                'name': name,
                'ministry': ministry,
                'start_date': start_date,
                'end_date': end_date,
                'source': 'bold_pattern'
            }

        return None

    def _extract_ministers_from_full_text(self, text: str) -> List[Dict]:
        """Extract ministers from full page text using patterns."""
        ministers = []

        # Split text into lines for easier processing
        lines = text.split('\n')

        # Look for patterns like "Name Surname minister za ..." across multiple lines
        current_minister = None
        current_text = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line contains a person name (at least 2 capitalized words)
            words = line.split()
            if (len(words) >= 2 and
                all(word[0].isupper() for word in words[:2]) and
                not any(exclude in line.upper() for exclude in ['VLADA', 'MINISTRI', 'PREDSEDNIK'])):

                # This might be a minister name, check if next lines contain ministry info
                potential_minister = ' '.join(words[:3])  # Take first 3 words as potential name

                # Look ahead in the next few lines for ministry information
                lookahead_text = line
                for next_line_idx in range(1, min(3, len(lines))):
                    if line != lines[-1]:  # Not last line
                        lookahead_text += " " + lines[lines.index(line) + next_line_idx].strip()

                if 'ministr' in lookahead_text.lower():
                    minister_info = self._parse_minister_text_entry(potential_minister, lookahead_text)
                    if minister_info:
                        ministers.append(minister_info)

        return ministers

    def _parse_minister_text_entry(self, name: str, text: str) -> Optional[Dict]:
        """Parse minister from text entry."""
        # Look for ministry
        ministry_patterns = [
            r'ministr[a-z]*\s+za\s+([^,\n\-–]+)',
            r'([^,\n\-–]*ministr[a-z]*[^,\n\-–]*)',
        ]

        ministry = ""
        for pattern in ministry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ministry = match.group(1).strip()
                break

        if ministry:
            return {
                'name': name,
                'ministry': ministry,
                'source': 'text_pattern'
            }

        return None

    def _extract_ministers_from_table(self, table) -> List[Dict]:
        """Extract ministers from table structure."""
        ministers = []

        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # Assume first column is ministry, second is minister name
                ministry_text = cells[0].get_text(strip=True)
                minister_text = cells[1].get_text(strip=True)

                if ministry_text and minister_text and 'ministr' in ministry_text.lower():
                    ministers.append({
                        'ministry': ministry_text,
                        'name': minister_text,
                        'source': 'table'
                    })

        return ministers

    def _extract_ministers_from_list(self, list_elem) -> List[Dict]:
        """Extract ministers from list structure."""
        ministers = []

        items = list_elem.find_all('li')
        for item in items:
            text = item.get_text(strip=True)
            minister_info = self._parse_minister_text(text)
            if minister_info:
                minister_info['source'] = 'list'
                ministers.append(minister_info)

        return ministers

    def _extract_ministers_from_text(self, text: str) -> List[Dict]:
        """Extract ministers from plain text."""
        ministers = []

        # Look for patterns like "Minister za finance: Ime Priimek"
        patterns = [
            r'[Mm]inistr[a-z]*\s+za\s+([^:]+):\s*([^,\n]+)',
            r'([^:]+\s+minister[a-z]*):\s*([^,\n]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                ministry = match[0].strip()
                name = match[1].strip()

                if name and len(name.split()) >= 2:  # At least first and last name
                    ministers.append({
                        'ministry': f"Ministrstvo za {ministry}",
                        'name': name,
                        'source': 'text'
                    })

        return ministers

    def _parse_minister_text(self, text: str) -> Optional[Dict]:
        """Parse minister information from text line."""
        # Common patterns for minister listings
        patterns = [
            r'([^-]+)\s*-\s*(.+)',  # "Ministry - Name"
            r'(.+?):\s*(.+)',       # "Ministry: Name"
        ]

        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                ministry_part = match.group(1).strip()
                name_part = match.group(2).strip()

                # Check if this looks like ministry info
                if 'ministr' in ministry_part.lower() and name_part:
                    return {
                        'ministry': ministry_part,
                        'name': name_part
                    }

        return None

    def _extract_coalition_info(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract coalition information from page."""
        text = soup.get_text()

        # Look for coalition keywords
        coalition_keywords = ['koalicija', 'coalition', 'stranke', 'parties']

        for keyword in coalition_keywords:
            if keyword in text.lower():
                # Try to find relevant paragraph
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text()
                    if keyword in p_text.lower():
                        return p_text.strip()

        return None

    def _extract_period_info(self, soup: BeautifulSoup, date_range: str) -> Dict:
        """Extract and parse period information."""
        info = {}

        if date_range:
            # Parse date range like "16. 5. 1990 - 14. 5. 1992"
            parts = date_range.split('-')
            if len(parts) == 2:
                start_str = parts[0].strip()
                end_str = parts[1].strip()

                start_date = self._parse_slovenian_date(start_str)
                end_date = self._parse_slovenian_date(end_str)

                if start_date:
                    info['start_date'] = start_date.strftime('%Y-%m-%d')
                if end_date:
                    info['end_date'] = end_date.strftime('%Y-%m-%d')

        return info

    def _parse_slovenian_date(self, date_str: str) -> Optional[datetime]:
        """Parse Slovenian date format."""
        # Handle formats like "16. 5. 1990"
        date_str = date_str.strip()

        # Remove extra spaces
        date_str = re.sub(r'\s+', ' ', date_str)

        patterns = [
            r'(\d+)\.\s*(\d+)\.\s*(\d{4})',  # "16. 5. 1990"
            r'(\d+)\.\s*(\d+)\.\s*(\d{2})',  # "16. 5. 90"
        ]

        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))

                # Handle 2-digit years
                if year < 100:
                    year += 1900 if year > 50 else 2000

                try:
                    return datetime(year, month, day)
                except ValueError:
                    continue

        return None

    def scrape_all_governments(self, output_file: str = "slovenian_ministers.json") -> Dict:
        """Scrape all historical governments and save to file."""
        logger.info("Starting to scrape Slovenian historical governments")

        # Get list of governments
        governments = self.scrape_historical_governments()
        if not governments:
            logger.error("No governments found to scrape")
            return {}

        # Scrape details for each government
        detailed_governments = []
        for gov in governments:
            logger.info(f"Scraping government {gov['number']}: {gov['pm']}")
            details = self.scrape_government_details(gov)
            detailed_governments.append(details)

            # Be nice to the server
            time.sleep(1)

        # Structure the data
        result = {
            'scrape_date': datetime.now().isoformat(),
            'source': 'https://www.gov.si/drzavni-organi/vlada/o-vladi/pretekle-vlade/',
            'governments': detailed_governments,
            'total_governments': len(detailed_governments)
        }

        # Save to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Scraped {len(detailed_governments)} governments, saved to {output_path}")
        return result


def main():
    """Main function to run the scraper."""
    scraper = SlowenianMinisterScraper()
    result = scraper.scrape_all_governments("data/slovenian_ministers.json")

    if result and 'total_governments' in result:
        print(f"Scraped {result['total_governments']} governments")
        for gov in result.get('governments', []):
            print(f"Government {gov['number']}: {len(gov.get('ministers', []))} ministers")
    else:
        print("Failed to scrape governments")


if __name__ == "__main__":
    main()