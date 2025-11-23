#!/usr/bin/env python3
"""
news_scraper.py

A professional, configurable web scraper to collect headlines (or other text)
from public news pages. Features:
 - CLI with argparse
 - Configurable CSS selector (default: "h2")
 - Robust requests session with retries and timeout
 - Logging with INFO/DEBUG
 - Save results to a .txt file
"""

from typing import List
import argparse
import logging
import sys
import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


DEFAULT_USER_AGENT = "news-scraper/1.0 (+https://example.com)"
DEFAULT_SELECTOR = "h2"
DEFAULT_OUTPUT = "headlines.txt"
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 0.3


def make_session(retries: int = DEFAULT_RETRIES, backoff: float = DEFAULT_BACKOFF, timeout: int = DEFAULT_TIMEOUT, user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
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
        if not text:
            continue
        if dedupe:
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
    logging.info("Saving %d headlines to %s", len(headlines), out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        for i, t in enumerate(headlines, start=1):
            f.write(f"{i}. {t}\n")


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
    p = argparse.ArgumentParser(description="Scrape headlines (or any text) from a web page using a CSS selector.")
    p.add_argument("--url", "-u", required=True, help="Target URL to scrape")
    p.add_argument("--selector", "-s", default=DEFAULT_SELECTOR, help=f"CSS selector to extract elements (default: {DEFAULT_SELECTOR})")
    p.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help=f"Output text file (default: {DEFAULT_OUTPUT})")
    p.add_argument("--limit", "-n", type=int, default=0, help="Maximum number of headlines to save (0 for no limit)")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout seconds (default: {DEFAULT_TIMEOUT})")
    p.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help=f"Number of request retries for transient errors (default: {DEFAULT_RETRIES})")
    p.add_argument("--backoff", type=float, default=DEFAULT_BACKOFF, help=f"Backoff factor between retries (default: {DEFAULT_BACKOFF})")
    p.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="Custom User-Agent header")
    p.add_argument("--dedupe/--no-dedupe", dest="dedupe", default=True, help="Remove duplicate headlines (default: enabled)")
    p.add_argument("--log", default="INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log)

    session = make_session(retries=args.retries, backoff=args.backoff, user_agent=args.user_agent)
    try:
        html = fetch_html(session, args.url, timeout=args.timeout)
    except Exception:
        logging.exception("Exiting due to fetch failure.")
        return 2

    try:
        headlines = parse_headlines(html, selector=args.selector, dedupe=args.dedupe, limit=args.limit)
    except Exception:
        logging.exception("Parsing error.")
        return 3

    if not headlines:
        logging.warning("No headlines extracted. Try a different selector with --selector.")
    try:
        save_headlines(headlines, args.output)
    except Exception:
        logging.exception("Failed to save output.")
        return 4

    logging.info("Done. Saved %d headlines.", len(headlines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
