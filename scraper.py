"""
News Headline Scraper
Author: Your Name
Description: Automated web scraper for extracting top news headlines
"""

import requests
from bs4 import BeautifulSoup
import datetime
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsHeadlineScraper:
    """
    A professional web scraper for extracting news headlines from target websites
    """
    
    def __init__(self, target_url, headers=None):
        self.target_url = target_url
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
        """
        Extract headlines from BBC News.
        This version uses stable selectors that BBC uses across pages.
        """
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # BBC stable selector for headline text
            elements = soup.select("a.gs-c-promo-heading")

            headlines = []
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 5:
                    headlines.append(text)

            logger.info(f"Extracted {len(headlines)} headlines")
            return headlines
        
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return []
    
    def save_headlines_to_file(self, headlines, filename=None):
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_headlines_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write("News Headlines Extraction Report\n")
                file.write(f"Source: {self.domain}\n")
                file.write(f"Extraction Date: {datetime.datetime.now()}\n")
                file.write(f"Total Headlines: {len(headlines)}\n")
                file.write("=" * 60 + "\n\n")
                
                for i, headline in enumerate(headlines, 1):
                    file.write(f"{i}. {headline}\n")
                
                file.write("\nEnd of extraction\n")
            
            logger.info(f"Headlines successfully saved to: {filename}")
            return filename
            
        except IOError as e:
            logger.error(f"Failed to save headlines to file: {e}")
            return None



def main():
    """ Main execution function """
    
    TARGET_URL = "https://www.bbc.com/news"
    
    scraper = NewsHeadlineScraper(TARGET_URL)
    
    html_content = scraper.fetch_html_content()
    
    if html_content:
        headlines = scraper.extract_headlines(html_content)
        
        if headlines:
            output_file = scraper.save_headlines_to_file(headlines)
            print(f"\n✔ Scraping completed successfully")
            print(f"✔ Output file: {output_file}")
            print(f"✔ Extracted {len(headlines)} headlines from {scraper.domain}\n")
        else:
            print("⚠ No headlines found. BBC may have changed its HTML structure.")
    else:
        print("❌ Failed to retrieve webpage content.")

if __name__ == "__main__":
    main()
