
# Headline-Harvester

Professional web scraper for automated news headline extraction from RSS feeds and websites.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with default configuration
python news_scraper.py
```

# Features

· Multi-source support (RSS & HTML)
· JSON and TXT output formats
· Configurable scraping parameters
· Error handling with retry logic
· Comprehensive logging

# Configuration

Edit config.json to customize:

```json
{
    "target_urls": ["https://feeds.bbci.co.uk/news/rss.xml"],
    "timeout": 15,
    "max_retries": 3,
    "output_format": "both"
}
```

# Usage Examples

```bash
# Custom configuration
python news_scraper.py --config config.json

# Single URL
python news_scraper.py --url "https://rss.cnn.com/rss/edition.rss"

# Output format
python news_scraper.py --output json
```

# Output

Generates timestamped files:

· news_headlines_YYYYMMDD_HHMMSS.txt
· news_headlines_YYYYMMDD_HHMMSS.json

# Dependencies

· requests
· beautifulsoup4
· lxml
· urllib3


