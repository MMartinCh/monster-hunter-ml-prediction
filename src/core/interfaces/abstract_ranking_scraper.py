from abc import ABC, abstractmethod
from typing import List
from src.core.dataclasses.ranking_scraper_item import RankingScraperItem

class AbstractRankingScraper(ABC):
    """Interface for scraping fan rating data from MH 20th anniversary website."""

    @abstractmethod
    def scrape_ranking(self) -> List[RankingScraperItem]:
        """Scrape fan ratings and monster names from url."""
        pass