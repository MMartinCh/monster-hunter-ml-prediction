import logging
from typing import List, Optional

from src.core.dataclasses import QuestItem #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.data_collection.scrapers.partial import ( #type:ignore
    TriQuestScraper,
    FourQuestScraper,
    FreedomQuestScraper,
    FUQuestScraper,
    GenerationsQuestScraper,
    RiseQuestScraper,
    WildsQuestScraper,
    WorldQuestScraper,
)

logger = logging.getLogger(__name__)

class CompleteQuestScraper(AbstractWebScraper[QuestItem]):
    """Pipeline calling all PartialQuestScraper classes and merging them into a complete quest dataset."""

    def __init__(
        self,
        tri_quest_scraper: Optional[TriQuestScraper] = None,
        four_quest_scraper: Optional[FourQuestScraper] = None,
        freedom_quest_scraper: Optional[FreedomQuestScraper] = None,
        fu_quest_scraper: Optional[FUQuestScraper] = None,
        generations_quest_scraper: Optional[GenerationsQuestScraper] = None,
        rise_quest_scraper: Optional[RiseQuestScraper] = None, 
        wilds_quest_scraper: Optional[WildsQuestScraper] = None, 
        world_quest_scraper: Optional[WorldQuestScraper] = None,
    ) -> None:

        self.scrapers: List[AbstractWebScraper[QuestItem]] = [
            tri_quest_scraper or TriQuestScraper(),
            four_quest_scraper or FourQuestScraper(),
            freedom_quest_scraper or FreedomQuestScraper(),
            fu_quest_scraper or FUQuestScraper(),
            generations_quest_scraper or GenerationsQuestScraper(),
            rise_quest_scraper or RiseQuestScraper(),
            world_quest_scraper or WorldQuestScraper(),
            wilds_quest_scraper or WildsQuestScraper(),
        ]

    def scrape(self) -> List[QuestItem]:
        """Scrape quests from all main line games and return a flat list of QuestItems."""
        return [
            quest 
            for scraper in self.scrapers 
            for quest in scraper.scrape()
        ]