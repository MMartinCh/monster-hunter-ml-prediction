import logging
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, sync_playwright

from src.core.helpers import file_cache #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_data import QuestItem #type:ignore

logger = logging.getLogger(__name__)

class FreedomQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Freedom.
    To be called via QuestScraper class."""

    GAME = "Freedom"
    GEN = 1

    VILLAGE_QUEST_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Village_Quests"
    GUILD_QUEST_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Guild_Quests"
    MONSTER_URL = r"https://monsterhunter.fandom.com/wiki/MHF1:_Monsters"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "freedom"
    QUEST_DATA_PATH = DATA_PATH / "freedom_quest_data.json"
    MONSTER_LIST_PATH = DATA_PATH / "helpers" / "monster_list.txt"

    @cached_property
    @file_cache("QUEST_DATA_PATH")
    def quest_data(self) -> List[Dict[str,Any]]:
        soup = self.retrieve_soup(self.QUEST_URL)
        quest_tables = soup.find_all("table", class_="themetable")
        return [
            quest 
            for table in quest_tables
            if (quest := self.scrape_quest(table))
        ]

    @cached_property
    @file_cache("MONSTER_LIST_PATH", overwrite=True)
    def monster_list(self) -> List[str]:
        return self._scrape_monster_list()

    def scrape(self) -> List[QuestItem]:
        return []

    def scrape_quest(self, table = BeautifulSoup) -> Dict[str,Any] | None:
        return {}

    def _match_rank(self, hub:str, level:int) -> str:
        rank = ""
        return rank

    def _scrape_monster_list(self) -> List[str]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            soup = self.retrieve_rendered_soup(browser=browser, url=self.MONSTER_URL)
            start_header = soup.find("span", class_="mw-headline", id="Large_Monsters", string="Large Monsters")

            t1 = start_header.find_next("table")
            t2 = t1.find_next("table") if t1 else None
            tables = [t for t in (t1, t2) if t]

            browser.close()

        return [
            title
            for table in tables
            for a in table.find_all("a", href=True, title=True)
            if a.find("font")
            and (title := a.get("title", "").strip())
        ]