import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd

from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.dataclasses import QuestItem #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class WorldQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH World/ Icebreak.
    To be called via QuestScraper class.
    """
    BASE_URL = r"https://mhw.poedb.tw/eng/monsters/large"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "world"
    DATA_QUEST_PATH = DATA_PATH / "world_quests.csv"
    DATA_MONSTER_PATH = DATA_PATH / "world_monsters.csv"
    HELPER_MONSTER_LINKS = DATA_PATH / "helper" / "world_monster_links.json"
    HELPER_QUEST_LINKS = DATA_PATH / "helper" / "world_quest_links.json"

    @cached_property
    @file_cache("HELPER_MONSTER_LINKS")
    def monster_links(self) -> Dict[str,str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache("HELPER_QUEST_LINKS")
    def quest_links(self) -> Dict[str,List[str]]:
        return self._scrape_quest_links_from_monster()

    @cached_property
    @file_cache("DATA_MONSTER_PATH")
    def monster_data(self) -> Dict[str,Dict[str,Any]]:
        return {
            monster : self.scrape_monster_data(link)
            for monster, link in self.monster_links.items()
        }

    @cached_property
    @file_cache("HELPER_QUEST_LINKS")
    def quest_data(self) -> List[Dict[str,Any]]:
        ...

    def scrape(self) -> List[QuestItem]:
        """Extract quest data from Base Url."""
        worlds_quest_data = []

        return worlds_quest_data

    def scrape_quest_data(self, link: str) -> Dict[str,Any]:
        soup = self.retrieve_soup(link)
        table_info = soup.select_one("div.card")
        table_header = table_info.select_one("div.card-header")

        level_match = re.search(r"(M?★)(\d+)(.+)", table_header.text)
        if not level_match:
            logger.warning(f"Level format not matching for {link}!")
            return {}

        level = int(level_match.group(2))
        rank_str = level_match.group(1).strip()
        rank = "MR"
        if not "M" in rank_str:
            if level > 5:
                rank = "HR"
            else:
                rank = "LR"

        table_monsters = table_info.find_next_sibling("div", class_="card")
        monsters_and_hp = {
            row.find("a", href=True).text.strip():
            int(row.find_all("td")[3].text)
            for row in table_monsters.find("tbody").find_all("tr")
            if "solo" in row.find_all("td")[1].text.lower()
        }

        return {
            "id_": self._get_row_attribute(table_info, "Quest ID"),
            "title": level_match.group(3).strip(),
            "rank": rank,
            "level": level, 
            "map": self._get_row_attribute(table_info, "Map"),
            "zenny": int(self._get_row_attribute(table_info, "Reward Money")),
            "points": int(self._get_row_attribute(table_info, "HRReward")),
            "conditions": self._get_row_attribute(table_info, "Conditions"),
            "monsters_and_hp": monsters_and_hp,
            }

    def scrape_monster_data(self, link: str) -> Dict[str,Any]:
        soup = self.retrieve_soup(link)
        table_header = soup.select_one("div.card-header")
        table_body = soup.select_one("table.table.table-striped")

        return {
            "name": table_header.get_text(strip=True), 
            "ecology": self._get_row_attribute(table_body, "Ecology"),
            "base_hp": int(self._get_row_attribute(table_body, "Base HP").replace(",","")),
            "threat": int(self._get_row_attribute(table_body, "Threat Level")),
            "habitats": [
                habitat.text.strip()
                for habitat in self._get_row_attribute(table_body, "Ecology", next="a", text_=False)
                ],
            "size": re.search(r"Base: (\d+\.\d*)", self._get_row_attribute(table_body, "Size")).group(1), #type:ignore
        }
    
    def _get_row_attribute(self, table: BeautifulSoup, attribute: str, next: str = "td", text_: bool = True) -> Any:
        row = table.find("th", string=re.compile(attribute))
        if not row:
            return None
        return row.find_next(next).text.strip() if text_ else row.find_next(next) #type:ignore

    def _scrape_monster_links(self) -> Dict[str,str]:
        soup = self.retrieve_soup(self.BASE_URL)
        return {
            a.text.strip(): urljoin(self.BASE_URL, a.get("href"))
            for a in soup.select("div.list-group.d-flex.flex-row.flex-wrap a.list-group-item[href]")
        }

    def _scrape_quest_links_from_monster(self) -> Dict[str,List[str]]:
        quest_links = {}
        for monster, link in self.monster_links.items():
            soup = self.retrieve_soup(link)
            quest_header = soup.find(
                lambda tag: tag.name == "div" 
                and "card-header" in tag.get("class", []) 
                and "Quest" in tag.get_text()
            )
            quest_table = quest_header.find_next("tbody")
            quest_links[monster] = [
                urljoin(self.BASE_URL, row.find("a", href=True).get("href"))
                for row in quest_table.find_all("tr")
                ]
        return quest_links
        