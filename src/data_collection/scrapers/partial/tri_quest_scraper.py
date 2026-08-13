from src.core.interfaces.abstract_web_scraper import AbstractWebScraper
from src.core.dataclasses.quest_data import QuestItem

class TriQuestScraper(AbstractWebScraper[QuestItem]):
        """Partial Scraper Class that scrapes quest data for MH Tri/ Tri Ultimate.
        To be called via QuestScraper class."""
        ...