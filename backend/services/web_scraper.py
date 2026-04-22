# backend/services/web_scraper.py

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Tuple
import re

class CreditCardWebScraper:
    """Scrapes credit card information from websites"""
    
    def __init__(self):
        """Initialize scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_card_from_url(self, url: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Scrape credit card information from a URL
        
        Args:
            url: URL to credit card page
            
        Returns:
            (success, card_data, error_message)
        """
        print(f"🌐 Fetching webpage: {url}")
        
        try:
            # Fetch the webpage
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            print("✅ Page fetched successfully")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract card data using pattern matching
            return self._extract_with_patterns(soup, text_content, url)
                
        except requests.RequestException as e:
            return False, None, f"Failed to fetch webpage: {str(e)}"
        except Exception as e:
            return False, None, f"Error scraping page: {str(e)}"
    
    def _extract_with_patterns(
        self, 
        soup: BeautifulSoup, 
        text: str, 
        url: str
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        Extract card data using pattern matching
        """
        print("🔍 Extracting card information...")
        
        card_data = {}
        
        # ============================================
        # Extract Card Name
        # ============================================
        print("  📝 Extracting card name...")
        
        # Try meta tags first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            card_data['name'] = og_title['content'].strip()
        else:
            # Fall back to title tag
            title = soup.find('title')
            if title:
                card_data['name'] = title.get_text().strip()
        
        if 'name' in card_data:
            # Clean up title
            card_data['name'] = card_data['name'].split('|')[0].strip()
            card_data['name'] = card_data['name'].split('-')[0].strip()
            card_data['name'] = re.sub(r'\s*Credit Card.*', '', card_data['name'], flags=re.IGNORECASE)
            print(f"    ✅ Found: {card_data['name']}")
        else:
            print(f"    ❌ Could not find card name")
        
        # ============================================
        # Extract Issuer from URL
        # ============================================
        print("  🏦 Extracting issuer...")
        
        issuer_map = {
            'chase.com': 'Chase',
            'americanexpress.com': 'American Express',
            'amex': 'American Express',
            'capitalone.com': 'Capital One',
            'citi.com': 'Citi',
            'discover.com': 'Discover',
            'wellsfargo.com': 'Wells Fargo',
            'bankofamerica.com': 'Bank of America',
            'usbank.com': 'U.S. Bank',
        }
        
        card_data['issuer'] = 'Unknown'
        for domain, issuer in issuer_map.items():
            if domain in url.lower():
                card_data['issuer'] = issuer
                print(f"    ✅ Found: {issuer}")
                break
        
        # ============================================
        # Extract Annual Fee
        # ============================================
        print("  💰 Extracting annual fee...")
        
        # Check for "no annual fee" first
        if re.search(r'\$0\s*(?:intro\s*)?annual fee', text, re.IGNORECASE):
            card_data['annual_fee'] = 0
            print(f"    ✅ Found: $0 (no annual fee)")
        elif re.search(r'no annual fee', text, re.IGNORECASE):
            card_data['annual_fee'] = 0
            print(f"    ✅ Found: $0 (no annual fee)")
        else:
            # Look for fee amount
            fee_patterns = [
                r'\$(\d+)\s*annual fee',
                r'annual fee[:\s]*\$(\d+)',
                r'\$(\d+)\s*per year',
                r'(\d+)\s*dollar annual fee',
            ]
            
            found_fee = False
            for pattern in fee_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    card_data['annual_fee'] = int(match.group(1))
                    print(f"    ✅ Found: ${card_data['annual_fee']}")
                    found_fee = True
                    break
            
            if not found_fee:
                card_data['annual_fee'] = 0  # Default to 0
                print(f"    ⚠️  Could not find, defaulting to $0")
        
        # ============================================
        # Extract Rewards
        # ============================================
        print("  🎁 Extracting rewards...")
        
        card_data['rewards'] = {'default': 1}
        
        # Common reward patterns
        reward_patterns = {
            'dining': [
                r'(\d+)x?\s*points?\s*(?:per\s*dollar\s*)?on\s*dining',
                r'(\d+)x?\s*(?:points?\s*)?at\s*restaurants',
                r'earn\s*(\d+)x?\s*(?:points?\s*)?(?:on\s*)?dining',
            ],
            'travel': [
                r'(\d+)x?\s*points?\s*(?:per\s*dollar\s*)?on\s*travel',
                r'(\d+)x?\s*(?:points?\s*)?on\s*(?:flights?|hotels?)',
                r'earn\s*(\d+)x?\s*(?:points?\s*)?(?:on\s*)?travel',
            ],
            'groceries': [
                r'(\d+)x?\s*points?\s*(?:per\s*dollar\s*)?(?:at\s*)?(?:on\s*)?(?:U\.?S\.?\s*)?supermarkets?',
                r'(\d+)x?\s*points?\s*(?:per\s*dollar\s*)?on\s*groceries',
                r'earn\s*(\d+)x?\s*(?:points?\s*)?at\s*grocery stores',
            ],
            'gas': [
                r'(\d+)x?\s*points?\s*(?:per\s*dollar\s*)?at\s*gas\s*stations?',
                r'(\d+)x?\s*(?:points?\s*)?on\s*gas',
            ],
        }
        
        for category, patterns in reward_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    rate = float(match.group(1))
                    card_data['rewards'][category] = rate
                    print(f"    ✅ {category}: {rate}x")
                    break
        
        # Look for general "everything" rate
        everything_patterns = [
            r'(\d+\.?\d*)%\s*cash\s*back\s*on\s*(?:all|every)',
            r'(\d+)x?\s*points?\s*on\s*(?:all|every)',
            r'earn\s*(\d+\.?\d*)%\s*back',
        ]
        
        for pattern in everything_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rate = float(match.group(1))
                if '%' in pattern:
                    rate = rate  # Cash back percentage
                card_data['rewards']['default'] = rate
                print(f"    ✅ default: {rate}x")
                break
        
        if len(card_data['rewards']) == 1:
            print(f"    ⚠️  Only found default rate, might need manual review")
        
        # ============================================
        # Point Value (default to 1 cent)
        # ============================================
        card_data['point_value'] = 0.01  # Standard 1 cent per point
        
        # Check if it's a specific transfer partner card
        if 'sapphire' in card_data.get('name', '').lower():
            card_data['point_value'] = 0.0125  # Chase UR portal is 1.25 cents
        elif 'venture' in card_data.get('name', '').lower():
            card_data['point_value'] = 0.01  # 1 cent per mile
        
        print(f"  💎 Point value: {card_data['point_value']} (${card_data['point_value']*100} cents)")
        
        # ============================================
        # Extract Benefits
        # ============================================
        print("  🎯 Extracting benefits...")
        
        card_data['benefits'] = []
        
        # Look for monetary benefits
        benefit_patterns = [
            r'\$(\d+)\s*(?:annual\s*)?(?:travel|hotel|airline|uber|dining|statement)\s*credit',
            r'\$(\d+)\s*in\s*(?:travel|dining|statement)\s*credits?',
            r'up\s*to\s*\$(\d+)\s*(?:in\s*)?(?:travel|dining|airline)\s*(?:fee\s*)?credits?',
        ]
        
        for pattern in benefit_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                benefit = match.group(0)
                if benefit not in card_data['benefits']:
                    card_data['benefits'].append(benefit)
                    print(f"    ✅ {benefit}")
        
        # Look for text-based benefits
        text_benefits = [
            'no foreign transaction fees?',
            'TSA PreCheck',
            'Global Entry',
            'airport lounge access',
            'priority boarding',
            'free checked bags?',
            'travel (?:and purchase )?protection',
            'rental car insurance',
            'extended warranty',
        ]
        
        for pattern in text_benefits:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                benefit = match.group(0)
                if benefit not in card_data['benefits']:
                    card_data['benefits'].append(benefit)
                    print(f"    ✅ {benefit}")
        
        if not card_data['benefits']:
            print(f"    ⚠️  No benefits found")
        
        # ============================================
        # Validation
        # ============================================
        print("\n🔍 Validating extracted data...")
        
        if not card_data.get('name'):
            return False, None, "Could not extract card name from page"
        
        print("✅ Extraction complete!\n")
        
        return True, card_data, ""


