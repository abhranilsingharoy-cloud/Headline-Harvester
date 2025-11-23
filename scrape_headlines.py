import requests
from bs4 import BeautifulSoup

# Step 1: Fetch the webpage
url = "https://www.bbc.com/news"
response = requests.get(url)
response.raise_for_status()  # ensure success

# Step 2: Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

# Step 3: Extract headlines (BBC uses <h2>)
headlines = [h.get_text(strip=True) for h in soup.find_all("h2")]

# Step 4: Save to a text file
with open("headlines.txt", "w", encoding="utf-8") as f:
    for idx, title in enumerate(headlines, start=1):
        f.write(f"{idx}. {title}\n")

print("Headlines scraped and saved to headlines.txt")
