"""
News Headline Scraper
Author: [Your Name/Organization]
Date: [Current Date]
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
        """
        Initialize the scraper with target URL and request headers
        
        Args:
            target_url (str): URL of the news website to scrape
            headers (dict): Custom headers for HTTP requests
        """
        self.target_url = target_url
        self.domain = urlparse(target_url).netloc
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_html_content(self):
        """
        Retrieve HTML content from the target URL
        
        Returns:
            str: Raw HTML content
        """
        try:
            logger.info(f"Fetching content from: {self.target_url}")
            response = self.session.get(self.target_url, timeout=10)
            response.raise_for_status()
            logger.info("Successfully retrieved webpage content")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch content: {e}")
            return None
    
    def extract_headlines(self, html_content, tag='h2', class_=None):
        """
        Parse HTML and extract headlines based on specified tags and classes
        
        Args:
            html_content (str): HTML content to parse
            tag (str): HTML tag containing headlines (h1, h2, h3, etc.)
            class_ (str): CSS class name for filtering specific elements
            
        Returns:
            list: Extracted headline texts
        """
        if not html_content:
            return []
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Build CSS selector based on parameters
            selector = tag
            if class_:
                selector = f"{tag}.{class_}" if '.' not in class_ else f"{tag}[class*='{class_}']"
            
            headline_elements = soup.select(selector)
            headlines = [elem.get_text().strip() for elem in headline_elements]
            
            # Clean and filter headlines
            cleaned_headlines = [
                headline for headline in headlines 
                if headline and len(headline) > 10  # Filter out very short texts
            ]
            
            logger.info(f"Extracted {len(cleaned_headlines)} headlines")
            return cleaned_headlines
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return []
    
    def save_headlines_to_file(self, headlines, filename=None):
        """
        Save extracted headlines to a text file with timestamp
        
        Args:
            headlines (list): Headlines to save
            filename (str): Custom output filename
            
        Returns:
            str: Path to the saved file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_headlines_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                # Write header information
                file.write(f"News Headlines Extraction Report\n")
                file.write(f"Source: {self.domain}\n")
                file.write(f"Extraction Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Total Headlines: {len(headlines)}\n")
                file.write("=" * 60 + "\n\n")
                
                # Write headlines with numbering
                for i, headline in enumerate(headlines, 1):
                    file.write(f"{i}. {headline}\n")
                
                file.write(f"\nEnd of extraction - {len(headlines)} headlines captured")
            
            logger.info(f"Headlines successfully saved to: {filename}")
            return filename
            
        except IOError as e:
            logger.error(f"Failed to save headlines to file: {e}")
            return None

def main():
    """
    Main execution function demonstrating the scraper usage
    """
    # Configuration - Update these parameters based on target website
    TARGET_URL = "https://example-news-website.com"  # Replace with actual news website
    HEADLINE_TAG = "h2"  # HTML tag containing headlines
    HEADLINE_CLASS = "headline"  # CSS class for headlines (adjust as needed)
    
    # Initialize scraper
    scraper = NewsHeadlineScraper(TARGET_URL)
    
    # Execute scraping workflow
    html_content = scraper.fetch_html_content()
    
    if html_content:
        headlines = scraper.extract_headlines(
            html_content, 
            tag=HEADLINE_TAG, 
            class_=HEADLINE_CLASS
        )
        
        if headlines:
            output_file = scraper.save_headlines_to_file(headlines)
            print(f"Scraping completed successfully. Output file: {output_file}")
            print(f"Extracted {len(headlines)} headlines from {scraper.domain}")
        else:
            print("No headlines were extracted. Please check the HTML structure.")
    else:
        print("Failed to retrieve webpage content.")

if __name__ == "__main__":
    main()
