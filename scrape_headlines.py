#!/usr/bin/env python3
"""
news_scraper.py

A professional, configurable web scraper to collect headlines.
Fixed to mimic a real browser to avoid 403 blocks.
"""

from typing import List
import argparse
import logging
import sys
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# FIX 1: Use a "Real" Browser User-Agent to avoid being blocked by news sites
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)
DEFAULT_SELECTOR = "h2"
DEFAULT_OUTPUT = "headlines.txt"
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 0.3


def make_session(retries: int = DEFAULT_RETRIES, backoff: float = DEFAULT_BACKOFF, user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    """
    Creates a robust session with retry logic and browser headers.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session


def fetch_html(session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    logging.info("Fetching %s", url)
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        
        # FIX 2: Verify content type is actually text/html
        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logging.warning("Warning: URL returned Content-Type: %s (Expected text/html)", content_type)

        logging.debug("Fetched %d bytes", len(resp.content))
        return resp.text
    except requests.RequestException as e:
        logging.error("Failed to fetch URL %s: %s", url, e)
        raise


def parse_headlines(html: str, selector: str = DEFAULT_SELECTOR, dedupe: bool = True, limit: int = 0) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(selector)
    logging.info("Found %d elements using selector '%s'", len(elements), selector)
    
    titles = []
    seen = set()
    
    for el in elements:
        text = el.get_text(separator=" ", strip=True)
        
        # Skip empty strings
        if not text:
            continue
            
        if dedupe:
            # Use lowercase key for case-insensitive deduplication
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            
        titles.append(text)
        if limit and len(titles) >= limit:
            break
            
    logging.info("Parsed %d unique headlines", len(titles))
    return titles


def save_headlines(headlines: List[str], out_path: str = DEFAULT_OUTPUT) -> None:
    if not headlines:
        logging.warning("No headlines to save.")
        return

    logging.info("Saving %d headlines to %s", len(headlines), out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            for i, t in enumerate(headlines, start=1):
                f.write(f"{i}. {t}\n")
    except IOError as e:
        logging.error("File I/O Error: %s", e)
        raise


def configure_logging(level: str):
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scrape headlines from a web page using a CSS selector.")
    p.add_argument("--url", "-u", required=True, help="Target URL to scrape")
    p.add_argument("--selector", "-s", default=DEFAULT_SELECTOR, help=f"CSS selector (default: {DEFAULT_SELECTOR})")
    p.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help=f"Output file (default: {DEFAULT_OUTPUT})")
    p.add_argument("--limit", "-n", type=int, default=0, help="Max headlines (0 for no limit)")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    p.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Retry attempts")
    p.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="Custom User-Agent header")
    p.add_argument("--dedupe", action=argparse.BooleanOptionalAction, default=True, help="Remove duplicates")
    p.add_argument("--log", default="INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log)

    # Pass retry settings to session creator
    session = make_session(retries=args.retries, user_agent=args.user_agent)
    
    try:
        html = fetch_html(session, args.url, timeout=args.timeout)
    except Exception:
        # Stack trace is already logged in fetch_html
        logging.info("Exiting due to fetch failure.")
        return 2

    try:
        headlines = parse_headlines(html, selector=args.selector, dedupe=args.dedupe, limit=args.limit)
    except Exception:
        logging.exception("Parsing error.")
        return 3

    if not headlines:
        print("No headlines found. Try changing the selector with --selector 'tag.class'")
        return 0

    try:
        save_headlines(headlines, args.output)
    except Exception:
        logging.exception("Failed to save output.")
        return 4

    print(f"Success! Saved {len(headlines)} headlines to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
