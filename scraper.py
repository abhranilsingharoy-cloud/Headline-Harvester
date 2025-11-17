"""
News Headline Scraper
Author: Your Name
Description: A flexible, automated web scraper for extracting top news headlines.
"""

import requests
from bs4 import BeautifulSoup
import datetime
import logging
from urllib.parse import urlparse, urljoin
import os
import sys
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsHeadlineScraper:
    """
    A professional web scraper for extracting news headlines from target websites
    using a provided list of CSS selectors.
    """
    
    def __init__(self, target_url, selectors, headers=None):
        """
        Initializes the scraper.
        
        Args:
            target_url (str): The URL of the website to scrape.
            selectors (list): A list of CSS selector strings to find headlines.
            headers (dict, optional): Custom headers for requests.
        """
        if not isinstance(selectors, list) or not selectors:
            raise ValueError("selectors must be a non-empty list of strings")
            
        self.target_url = target_url
        self.selectors = selectors
        self.domain = urlparse(target_url).netloc
        self.headers = headers or {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0 Safari/537.36'
            )
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_html_content(self):
        """Fetches the HTML content from the target URL."""
        try:
            logger.info(f"Fetching content from: {self.target_url}")
            response = self.session.get(self.target_url, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            logger.info("Successfully retrieved webpage content")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch content: {e}")
            return None
    
    def extract_headlines(self, html_content):
        """Extracts headlines and URLs from the HTML content."""
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            headlines_data = set()

            for selector in self.selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    url = elem.get('href')

                    if not text or len(text) <= 5 or not url:
                        continue
                        
                    absolute_url = urljoin(self.target_url, url)
                    
                    if absolute_url.startswith('http'):
                        headlines_data.add((text, absolute_url))

            logger.info(f"Extracted {len(headlines_data)} unique headlines")
            
            return [{'text': text, 'url': url} for text, url in headlines_data]
        
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return []
    
    def save_headlines_to_file(self, headlines, filename=None):
        """Saves the extracted headlines and URLs to a text file."""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_headlines_{self.domain}_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write("News Headlines Extraction Report\n")
                file.write(f"Source: {self.domain} ({self.target_url})\n")
                file.write(f"Extraction Date: {datetime.datetime.now()}\n")
                file.write(f"Total Headlines: {len(headlines)}\n")
                file.write("=" * 60 + "\n\n")
                
                for i, item in enumerate(headlines, 1):
                    file.write(f"{i}. {item['text']}\n")
                    file.write(f"   Link: {item['url']}\n\n")
                
                file.write("End of extraction\n")
            
            logger.info(f"Headlines successfully saved to: {filename}")
            return filename
            
        except IOError as e:
            logger.error(f"Failed to save headlines to file: {e}")
            return None


def main():
    """ Main execution function """
    
    TARGET_URL = "https://www.bbc.com/news"
    
    BBC_SELECTORS = [
        "a.gs-c-promo-heading",
        "a.nw-o-link-promo__link",
        "a.gs-o-link-promo__link"
    ]
    
    scraper = NewsHeadlineScraper(TARGET_URL, BBC_SELECTORS)
    
    html_content = scraper.fetch_html_content()
    
    if html_content:
        headlines = scraper.extract_headlines(html_content)
        
        if headlines:
            output_file = scraper.save_headlines_to_file(headlines)
            print(f"\n✔ Scraping completed successfully")
            print(f"✔ Output file: {output_file}")
            print(f"✔ Extracted {len(headlines)} unique headlines from {scraper.domain}\n")
            
            # Auto-open the file after saving
            if output_file:
                try:
                    if sys.platform.startswith("win"):   # Windows
                        os.startfile(output_file)
                    elif sys.platform == "darwin":      # macOS
                        subprocess.run(["open", output_file])
                    else:                               # Linux
                        subprocess.run(["xdg-open", output_file])
                except Exception as e:
                    print(f"⚠ Could not open file automatically: {e}")
        else:
            print(f"⚠ No headlines found. The selectors for {scraper.domain} may be outdated.")
    else:
        print("❌ Failed to retrieve webpage content.")

if __name__ == "__main__":
    main()
