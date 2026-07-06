from abc import ABC, abstractmethod
from typing import List
from src.core.dataclasses.mh_wiki_item import MHWikiItem

class AbstractWikiScraper(ABC):
    """Interface for the MH Wiki Scraper."""

    @abstractmethod
    def scrape_wiki(self) -> List[MHWikiItem]:
        """Scrapes MH Wiki and Monster links recursively."""
        pass