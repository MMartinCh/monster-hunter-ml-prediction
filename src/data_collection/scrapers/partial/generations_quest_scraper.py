import re
from functools import cached_property
from typing import Any, Dict, List
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.helpers import file_cache #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_data import QuestItem #type:ignore

class GenerationsQuestScraper(AbstractWebScraper[QuestItem]):
        """Partial Scraper Class that scrapes quest data for MH G/GU.
        To be called via QuestScraper class."""
        ...

        KIRANICO_URL = r"https://mhgu.kiranico.com/"

        DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "generations"
        GU_QUEST_DATA = DATA_PATH / "gu_quest_data.json"
        GU_MONSTER_DATA = DATA_PATH / "gu_monster_data.json"
        GU_QUEST_LINKS = DATA_PATH / "helpers" / "gu_quest_links.txt"
        GU_MONSTER_LINKS = DATA_PATH / "helpers" / "gu_monster_links.txt"

        @cached_property
        @file_cache("GU_QUEST_DATA")
        def quest_data(self) -> List[Dict[str,Any]]:
                return [
                        self.scrape_quest(quest) 
                        for quest in self.quest_links
                        ]

        @cached_property
        @file_cache("GU_MONSTER_DATA")
        def monster_data(self) -> List[Dict[str,Any]]:
                return [
                        self.scrape_monster(monster) 
                        for monster in self.monster_links
                        ]

        @cached_property
        @file_cache("GU_QUEST_LINKS")
        def quest_links(self) -> List[str]:
                return self.scrape_quest_links()

        @cached_property
        @file_cache("GU_MONSTER_LINKS")
        def monster_links(self) -> List[str]:
                return self.scrape_monster_links()

        def scrape(self) -> List[QuestItem]:
                return []

        def scrape_quest(self, link: str) -> Dict[str, Any]:
                soup = self.retrieve_soup(link)

                header = soup.find("h2", string=True).text.strip()
                header_match = re.search(r"(\w*)(G?\d+★?) // (.*)", header)
                if header_match:
                        hub = header_match.group(1)
                        level = header_match.group(2)
                        title = header_match.group(3)


                return {
                        "id_": ...,
                        "title": title,
                        "rank": ...,
                        "level": level,
                        "hub": hub,
                        "map": ...,
                        "targets": [],
                        "targets_hp": {},
                        "zenny": ...,
                        "points": ...,
                }

        def scrape_monster(self, link: str) -> Dict[str,Any]:
                soup = self.retrieve_soup(link, polite=False)

                size_header = soup.find("h5", string=re.compile("Size"))
                size_text = size_header.text.strip() if size_header else ""
                size = None
                match = re.search(r"(\d+\.?\d*)", size_text)
                if match:
                    size = float(match.group(1))

                map_header = soup.find("h5", string="Map List")
                map_table = map_header.find_next("table") if map_header else None
                maps = []
                if map_table:
                    maps = [
                        map_.text.strip() 
                        for map_ in map_table.find_all("a", href=True) 
                        if map_.text.strip()
                    ]

                return {
                        "name": soup.find("h2", string=True).text.strip(),
                        "size": size,
                        "maps": maps,
                        "quests": self._scrape_quest_links_for_monster(soup),
                }

        def scrape_quest_links(self) -> List[str]:
                quest_links = set()
                for link in self.monster_links:
                        soup = self.retrieve_soup(link)
                        quest_links.update(
                                self._scrape_quest_links_for_monster(soup)
                                )
                return list(quest_links)

        def _scrape_quest_links_for_monster(self, soup: BeautifulSoup) -> List[str]:
                header = soup.find("h5", string="Quest List")
                if not header:
                        return []
                table = header.find_next("table")
                if not table:
                        return []
                return [
                        row["href"] #type:ignore
                        for row in table.find_all("a", href=True) #type:ignore
                        ] 

        def scrape_monster_links(self) -> List[str]:
                soup = self.retrieve_soup(self.KIRANICO_URL)
                header = soup.find("p", string="Monster")
                table = header.find_next("table")
                return [
                        cell["href"] 
                        for cell in table.find_all("a", href=True)
                        ]