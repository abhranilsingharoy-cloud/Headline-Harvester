#!/usr/bin/env python3
"""
scrape_headlines.py

Advanced, production-ready web scraper to extract top headlines from a news site.

Features:
- Robust HTTP session with retries and backoff
- Configurable CSS selectors (supports multiple selectors)
- Deduplication and basic text normalization
- CLI with arguments and optional config file
- Logging and graceful error handling
- Outputs to a .txt file (one headline per line)
"""

from __future__ import annotations
import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, Set

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------
# Configuration dataclass
# -----------------------
@dataclass
class ScraperConfig:
    url: str
    selectors: List[str] = field(default_factory=lambda: ["h1", "h2", ".headline", ".top-story"])
    output_file: str = "headlines.txt"
    user_agent: str = "Mozilla/5.0 (compatible; HeadlineScraper/1.0; +https://example.com/bot)"
    timeout: int = 10
    max_headlines: Optional[int] = None  # None => no limit
    verify_ssl: bool = True
    retries: int = 3
    backoff_factor: float = 0.5

# -----------------------
# Logging setup
# -----------------------
def setup_logging(level: str = "INFO") -> None:
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt)

# -----------------------
# HTTP fetching with retries
# -----------------------
def create_session(config: ScraperConfig) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=config.retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=config.backoff_factor,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": config.user_agent})
    return session

def fetch_html(session: requests.Session, url: str, timeout: int, verify: bool) -> str:
    logging.info("Fetching URL: %s", url)
    try:
        resp = session.get(url, timeout=timeout, verify=verify)
        resp.raise_for_status()
        logging.debug("Response status: %s", resp.status_code)
        return resp.text
    except requests.RequestException as e:
        logging.error("Failed to fetch URL '%s': %s", url, e)
        raise

# -----------------------
# Parsing and cleaning
# -----------------------
def normalize_text(s: str) -> str:
    # Basic normalization: strip, collapse whitespace
    return " ".join(s.split()).strip()

def parse_headlines(html: str, selectors: List[str], limit: Optional[int] = None) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    seen: Set[str] = set()
    headlines: List[str] = []

    logging.info("Parsing HTML with selectors: %s", selectors)

    # Search in order of selectors
    for sel in selectors:
        # If selector is simple (h1,h2) use soup.find_all; CSS selectors otherwise
        elements = soup.select(sel)
        logging.debug("Selector '%s' returned %d elements", sel, len(elements))
        for el in elements:
            # Text extraction: prefer .get_text, fallback to .string
            text = el.get_text(separator=" ", strip=True) if el else ""
            if not text:
                continue
            text = normalize_text(text)
            if not text or text in seen:
                continue
            seen.add(text)
            headlines.append(text)
            if limit and len(headlines) >= limit:
                logging.info("Reached headline limit: %d", limit)
                return headlines

    # As a fallback: try generic title tag if no headlines found
    if not headlines:
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            title = normalize_text(title_tag.text)
            headlines.append(title)
            logging.info("No selector matches; falling back to <title>.")

    logging.info("Extracted %d unique headlines", len(headlines))
    return headlines

# -----------------------
# Persistence
# -----------------------
def save_headlines(headlines: List[str], filename: str) -> None:
    logging.info("Saving %d headlines to %s", len(headlines), filename)
    try:
        # Write safely (atomic write could be implemented if needed)
        with open(filename, "w", encoding="utf-8") as fh:
            for h in headlines:
                fh.write(h + "\n")
    except IOError as e:
        logging.error("Failed to write to file '%s': %s", filename, e)
        raise

# -----------------------
# CLI & Orchestration
# -----------------------
def load_config_file(path: str) -> dict:
    logging.info("Loading config file: %s", path)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def build_config_from_args(args: argparse.Namespace) -> ScraperConfig:
    if args.config:
        cfg_data = load_config_file(args.config)
        # Merge CLI overrides into config file values
        url = args.url or cfg_data.get("url")
        selectors = args.selectors or cfg_data.get("selectors", [])
        output_file = args.output or cfg_data.get("output_file", "headlines.txt")
        user_agent = args.user_agent or cfg_data.get("user_agent")
        timeout = args.timeout if args.timeout is not None else cfg_data.get("timeout", 10)
        max_headlines = args.max_headlines if args.max_headlines is not None else cfg_data.get("max_headlines")
        retries = args.retries if args.retries is not None else cfg_data.get("retries", 3)
        backoff_factor = args.backoff if args.backoff is not None else cfg_data.get("backoff_factor", 0.5)
    else:
        url = args.url
        selectors = args.selectors or []
        output_file = args.output
        user_agent = args.user_agent
        timeout = args.timeout
        max_headlines = args.max_headlines
        retries = args.retries
        backoff_factor = args.backoff

    if not url:
        logging.error("No URL provided. Use --url or provide it in the config file.")
        raise SystemExit(2)

    cfg = ScraperConfig(
        url=url,
        selectors=selectors or ["h1", "h2", ".headline", ".top-story"],
        output_file=output_file or "headlines.txt",
        user_agent=user_agent or ScraperConfig().user_agent,
        timeout=timeout or 10,
        max_headlines=max_headlines,
        verify_ssl=not args.insecure,
        retries=retries or 3,
        backoff_factor=backoff_factor or 0.5,
    )
    logging.debug("Built ScraperConfig: %s", cfg)
    return cfg

def parse_cli_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Advanced Web Scraper for News Headlines")
    p.add_argument("--url", "-u", help="URL of the news page to scrape")
    p.add_argument("--selectors", "-s", nargs="+", help="CSS selectors to locate headlines (in order)")
    p.add_argument("--output", "-o", help="Output .txt file name (default: headlines.txt)", default="headlines.txt")
    p.add_argument("--max-headlines", "-m", type=int, help="Maximum number of headlines to collect")
    p.add_argument("--user-agent", help="Custom User-Agent string")
    p.add_argument("--timeout", type=int, help="Request timeout in seconds", default=10)
    p.add_argument("--retries", type=int, help="Number of retries for requests", default=3)
    p.add_argument("--backoff", type=float, help="Backoff factor between retries", default=0.5)
    p.add_argument("--config", "-c", help="Optional JSON config file")
    p.add_argument("--insecure", action="store_true", help="Disable SSL verification (not recommended)")
    p.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    return p.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> None:
    args = parse_cli_args(argv)
    setup_logging(args.log_level)

    try:
        cfg = build_config_from_args(args)
    except SystemExit:
        raise
    except Exception as e:
        logging.exception("Failed to build configuration: %s", e)
        raise SystemExit(1)

    session = create_session(cfg)

    try:
        html = fetch_html(session, cfg.url, cfg.timeout, cfg.verify_ssl)
        headlines = parse_headlines(html, cfg.selectors, limit=cfg.max_headlines)
        if not headlines:
            logging.warning("No headlines extracted. Exiting with no output.")
            raise SystemExit(0)
        save_headlines(headlines, cfg.output_file)
        logging.info("Done. Wrote %d headlines to %s", len(headlines), cfg.output_file)
    except Exception as e:
        logging.exception("An error occurred during scraping: %s", e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
