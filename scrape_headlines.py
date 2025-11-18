"""
Advanced News Headlines Scraper
Author: AI Assistant
Date: 2024
Description: Professional web scraper for extracting news headlines with advanced features
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NewsScraper:
    """Advanced web scraper for news headlines extraction"""
    
    def __init__(self, config_file: str = None):
        self.session = requests.Session()
        self.setup_session()
        self.config = self.load_config(config_file)
        
    def setup_session(self) -> None:
        """Configure HTTP session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'target_urls': [
                'https://feeds.bbci.co.uk/news/rss.xml',
                'https://rss.cnn.com/rss/edition.rss'
            ],
            'timeout': 10,
            'max_retries': 3,
            'retry_delay': 2,
            'output_format': 'both',  # txt, json, or both
            'selectors': {
                'rss': ['title', 'description'],
                'html': ['h1', 'h2', 'h3', '.headline', '.title']
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}. Using defaults.")
        
        return default_config
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _safe_get_text(self, element: Any) -> str:
        """Helper to safely extract text from a BS4 element"""
        if element:
            return element.get_text(strip=True)
        return ""

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch URL content with error handling and retries"""
        if not self.is_valid_url(url):
            logger.error(f"Invalid URL: {url}")
            return None
        
        for attempt in range(self.config['max_retries']):
            try:
                response = self.session.get(
                    url, 
                    timeout=self.config['timeout'],
                    allow_redirects=True
                )
                response.raise_for_status()
                logger.info(f"Successfully fetched {url}")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(self.config['retry_delay'])
                continue
        
        logger.error(f"All attempts failed for {url}")
        return None
    
    def parse_rss_feed(self, content: str, source: str) -> List[Dict[str, str]]:
        """Parse RSS feed content"""
        headlines = []
        try:
            # Try lxml first, fall back to html.parser if lxml is missing
            try:
                soup = BeautifulSoup(content, 'lxml-xml')
            except Exception:
                soup = BeautifulSoup(content, 'xml') 
                
            items = soup.find_all('item')
            
            for item in items:
                # FIX: Used helper method to avoid 'NoneType' errors
                title_text = self._safe_get_text(item.find('title'))
                
                headline_data = {
                    'title': title_text,
                    'description': self._safe_get_text(item.find('description')),
                    'link': self._safe_get_text(item.find('link')),
                    'pubDate': self._safe_get_text(item.find('pubDate')),
                    'source': source
                }
                if headline_data['title']:  # Only add if title exists
                    headlines.append(headline_data)
                    
            logger.info(f"Parsed {len(headlines)} headlines from RSS feed")
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            
        return headlines
    
    def parse_html_content(self, content: str, source: str) -> List[Dict[str, str]]:
        """Parse HTML content for headlines"""
        headlines = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try multiple selectors for headline extraction
            for selector in self.config['selectors']['html']:
                elements = soup.select(selector)
                
                for element in elements:
                    text = element.get_text().strip()
                    
                    if text and len(text) > 10:  # Basic validation
                        link = ''
                        # Try to find the link (href)
                        if element.name == 'a':
                            link_raw = element.get('href')
                        else:
                            # Search for an 'a' tag inside or as a parent
                            parent_link = element.find_parent('a')
                            child_link = element.find('a')
                            
                            link_raw = None
                            if parent_link:
                                link_raw = parent_link.get('href')
                            elif child_link:
                                link_raw = child_link.get('href')
                        
                        # FIX: Explicit string conversion for urljoin
                        if link_raw:
                            link = urljoin(source, str(link_raw))

                        headlines.append({
                            'title': text,
                            'link': link,
                            'source': source,
                            'type': 'html',
                            'selector': selector
                        })
            
            logger.info(f"Parsed {len(headlines)} headlines from HTML")
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            
        return headlines
    
    def scrape_url(self, url: str) -> List[Dict[str, str]]:
        """Scrape headlines from a single URL"""
        content = self.fetch_content(url)
        if not content:
            return []
        
        # Determine content type and parse accordingly
        if 'rss' in url.lower() or 'xml' in url.lower():
            return self.parse_rss_feed(content, url)
        else:
            return self.parse_html_content(content, url)
    
    def save_headlines_txt(self, headlines: List[Dict[str, str]], filename: str) -> None:
        """Save headlines to text file with formatting"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"NEWS HEADLINES SCRAPER REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Headlines: {len(headlines)}\n")
                f.write("=" * 80 + "\n\n")
                
                current_source = ""
                for headline in headlines:
                    if headline['source'] != current_source:
                        current_source = headline['source']
                        f.write(f"\nSOURCE: {current_source}\n")
                        f.write("-" * 60 + "\n")
                    
                    f.write(f"• {headline['title']}\n")
                    
                    if headline.get('description'):
                        f.write(f"  Desc: {headline['description']}\n")
                    
                    if headline.get('link'):
                        f.write(f"  Link: {headline['link']}\n")

                    if headline.get('pubDate'):
                        f.write(f"  Published: {headline['pubDate']}\n")
                    
                    f.write("\n")
            
            logger.info(f"Headlines saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to TXT file: {e}")
    
    def save_headlines_json(self, headlines: List[Dict[str, str]], filename: str) -> None:
        """Save headlines to JSON file with metadata"""
        try:
            output_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_headlines': len(headlines),
                    'sources': list(set(h['source'] for h in headlines))
                },
                'headlines': headlines
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Headlines saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to JSON file: {e}")
    
    def run_scraper(self) -> Dict[str, List[Dict[str, str]]]:
        """Main method to run the scraper"""
        logger.info("Starting news headlines scraping process...")
        
        all_headlines = []
        results = {}
        
        for url in self.config['target_urls']:
            logger.info(f"Scraping: {url}")
            headlines = self.scrape_url(url)
            all_headlines.extend(headlines)
            results[url] = headlines
            
            # Be respectful to servers
            time.sleep(1)
        
        # Save outputs based on configuration
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"news_headlines_{timestamp}"
        
        output_format = self.config.get('output_format', 'both')
        
        if output_format in ['txt', 'both']:
            self.save_headlines_txt(all_headlines, f"{base_filename}.txt")
        
        if output_format in ['json', 'both']:
            self.save_headlines_json(all_headlines, f"{base_filename}.json")
        
        logger.info(f"Scraping completed. Total headlines collected: {len(all_headlines)}")
        return results

def main():
    """Command line interface for the news scraper"""
    parser = argparse.ArgumentParser(description='Advanced News Headlines Scraper')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--url', '-u', help='Single URL to scrape (overrides config)')
    parser.add_argument('--output', '-o', choices=['txt', 'json', 'both'], 
                       help='Output format (overrides config)')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = NewsScraper(args.config)
    
    # Override config if command line arguments provided
    if args.url:
        scraper.config['target_urls'] = [args.url]
    
    if args.output:
        scraper.config['output_format'] = args.output
    
    try:
        results = scraper.run_scraper()
        
        # Print summary to console
        total_headlines = sum(len(headlines) for headlines in results.values())
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Sources processed: {len(results)}")
        print(f"Total headlines collected: {total_headlines}")
        
        for url, headlines in results.items():
            print(f"  - {url}: {len(headlines)} headlines")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
