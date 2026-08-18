import logging
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from time import sleep
from typing import List, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, sync_playwright

logger = logging.getLogger(__name__)

class AbstractWebScraper[T](ABC):
    """Abstract base class for all web based scrapers"""

    def __init__(self, 
                 url: Optional[str] = None, 
                 headers: Optional[dict] = None
                 ) -> None:
        
        self.url = url
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

    ROOT_PATH = Path(__file__).resolve().parents[3]
    DATA_PATH = ROOT_PATH / "data"

    @abstractmethod
    def scrape(self) -> List[T]:
        """Scrape data and return list of structured entries."""
        pass

    def retrieve_soup(self, url: Optional[str] = None, polite: bool = True) -> BeautifulSoup | None:
        """Fetches html from url and returns a BeautifulSoup object."""

        if url is None:
            url = self.url

        if polite:
            sleep(1.0)

        try:
            logger.info(f"Retrieving SOUP from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10) #type:ignore
            
            if response.status_code == 200:
                logger.debug(f"Request successful!: {response.status_code}")
                return BeautifulSoup(response.text, "html.parser")
            
            logger.warning(f"Request failed with status: {response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error occurred while fetching {url}: {e}")
            return None

    def retrieve_rendered_soup(self, browser: Browser, url: str) -> BeautifulSoup:
            logger.info(f"Retrieving RENDERED SOUP from: {url}")
            page = browser.new_page()
            try:
                page.goto(url, wait_until="load")
                return BeautifulSoup(page.content(), "html.parser")
            finally:
                page.close()