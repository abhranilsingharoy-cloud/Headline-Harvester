import requests
from bs4 import BeautifulSoup

def scrape_news_headlines():
    # URL of the news website to scrape
    # We'll use NPR's news section for this example.
    URL = 'https://www.npr.org/sections/news/'
    
    # --- Step 1: Use requests to fetch HTML ---
    try:
        print(f"Fetching headlines from {URL}...")
        response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        
        # Raise an exception if the request was unsuccessful (e.g., 404 Not Found)
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch URL. {e}")
        return

    # --- Step 2: Use BeautifulSoup to parse tags ---
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all the headline tags.
    # NOTE: Your image hints at <h2> or <title>. For this specific site (NPR),
    # the main headlines are in <h3> tags with a class of "title".
    # This selector is the part you must change for different websites.
    headline_tags = soup.find_all('h3', class_='title')
    
    if not headline_tags:
        print("Error: Could not find any headlines. The website's structure may have changed.")
        return
        
    headlines = []
    for tag in headline_tags:
        # Get the text from the tag and remove any extra whitespace
        headline_text = tag.get_text(strip=True)
        headlines.append(headline_text)

    # --- Step 3: Save the titles in a .txt file ---
    output_file = 'headlines.txt'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for headline in headlines:
                f.write(headline + '\n') # Write each headline on a new line
                
        print(f"\nSuccessfully scraped {len(headlines)} headlines.")
        print(f"Headlines saved to: {output_file}")

    except IOError as e:
        print(f"Error: Could not write to file {output_file}. {e}")

# Run the function when the script is executed
if __name__ == "__main__":
    scrape_news_headlines()
