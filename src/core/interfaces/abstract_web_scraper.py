from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Optional

import logging
import requests

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

    @abstractmethod
    def scrape(self) -> List[T]:
        """Scrape data and return list of structured entries."""
        pass

    def retrieve_soup(self, url: Optional[str] = None) -> BeautifulSoup | None:
        """Fetches html from url and returns a BeautifulSoup object."""

        if url is None:
            url = self.url

        try:
            logger.info(f"Retrieving soup from: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Request successful!: {response.status_code}")
                return BeautifulSoup(response.text, "html.parser")
            
            logger.warning(f"Request failed with status: {response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error occurred while fetching {url}: {e}")
            return None