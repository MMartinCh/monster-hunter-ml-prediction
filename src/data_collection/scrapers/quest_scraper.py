import logging
from typing import List

from src.core.dataclasses import QuestItem
from src.core.interfaces import AbstractWebScraper
from src.data_collection.scrapers.partial import RiseQuestScraper, WildsQuestScraper, WorldQuestScraper

logger = logging.getLogger(__name__)

class CompleteQuestScraper(AbstractWebScraper[QuestItem]):
    """Pipeline calling all PartialQuestScraper classes and merging them to complete quest info dataset."""

    # TODO: Add column to db, from where the monster was scraped.
    # TODO: gather data from all quests, transform later

    def __init__(self,
                rise_quest_scraper: RiseQuestScraper, 
                wilds_quest_scraper: WildsQuestScraper, 
                world_quest_scraper: WorldQuestScraper
                ) -> None:

        self.rise_quest_scraper = rise_quest_scraper
        self.wilds_quest_scraper = wilds_quest_scraper
        self.world_quest_scraper = world_quest_scraper

    def scrape(self) -> List[QuestItem]:
        """Scrape quests from Monster Hunter main line games in order of sales: World -> Rise -> Wilds... 
        Keep first entry for in-game data only. Sum up meta-data.
        """

        # TODO: complete all quest scrapers

        world_data = self.world_quest_scraper.scrape()
        rise_data = self.rise_quest_scraper.scrape()
        wilds_data = self.wilds_quest_scraper.scrape()

    def merge_quest_data(self, quest_data_arrays: List[List[QuestItem]]) -> List[QuestItem]:
        """Merges quest data for every game into a unified list of QuestItem objects."""
        # TODO: implement function to merge individual QuestItems
        return ...