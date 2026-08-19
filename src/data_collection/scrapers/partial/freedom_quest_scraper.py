import json
import logging
import re
import requests
from functools import cached_property
from typing import Any, Dict, List

from src.core.helpers import file_cache #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_data import QuestItem #type:ignore

logger = logging.getLogger(__name__)

class FreedomQuestScraper(AbstractWebScraper[QuestItem]):
    """Scrapes quests for Freedom/ Freedom Unit and returns list of quest items."""
    GAME = "Freedom Unite"
    GEN = 2

    SOURCE_REPO = r"Kolyn090/mhfu-db/refs/heads/main/Quests/"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "freedom"
    CACHE_DATA = DATA_PATH / "freedom_cache_data.json" 
    QUEST_DATA_PATH = DATA_PATH / "freedom_quest_data.json"

    @cached_property
    @file_cache("QUEST_DATA_PATH")
    def quest_data(self) -> List[Dict[str,Any]]:
        return []

    @cached_property
    @file_cache("CACHE_DATA")
    def cached_quest_data(self) -> List[Dict[str,Any]]:
        return self.fetch_quest_data()

    @cached_property
    def raw_cache_data(self) -> Dict[str, List[Dict[str, Any]]]:
        return self._fetch_handler_data_from_github() 

    def scrape(self) -> List[QuestItem]:
        return [
            QuestItem(
                title=quest.get("name"),
                game=self.GAME,
                generation=self.GEN,
                rank=self._match_rank(handler = quest.get("handler")),
                level=quest.get("difficulty"),
                is_assignment=quest.get("quest-type", "").strip() == "key",
                targets=quest.get("difficulty"),
                reward_zenny=quest.get("reward")
            )
            for quest in self.cached_quest_data
        ]

    def _match_rank(self, handler) -> str:
        match handler:
            case "Elder":
                rank = "LR"
            case "Nekoht":
                rank = "HR"
            case "Guild_LR":
                rank = "LR"
            case "Guild_HR":
                rank = "HR"
            case "Guild_MR":
                rank = "MR"
            case _:
                rank = f"unknown: {handler}"
        return rank

    def fetch_quest_data(self) -> List[Dict[str, Any]]:
        return [
            {**quest, "handler": handler}
            for handler, quest_list in self.raw_cache_data.items()
            for quest in quest_list
            if isinstance(quest, dict) 
        ]

    def _fetch_handler_data_from_github(self) -> Dict[str, List[Dict[str, Any]]]:
        files_to_fetch = {
            "Elder" : "elder.json",
            "Nekoht" : "nekoht.json",
            "Guild_LR" : "gal-1.json",
            "Guild_HR" : "gal-2.json",
            "Guild_MR" : "gal-3.json",
        }

        raw_quest_data = {}
        for handler, file in files_to_fetch.items():
            url = f"https://raw.githubusercontent.com/{self.SOURCE_REPO}/{file}"
            response = requests.get(url)
            logger.info(f"Fetching data from {url}...")

            if response.status_code == 200:
                raw_quest_data[handler] = response.json()
            else:
                logger.warning(f"Issue with fetching {handler}-data: {response.status_code}")

        return raw_quest_data