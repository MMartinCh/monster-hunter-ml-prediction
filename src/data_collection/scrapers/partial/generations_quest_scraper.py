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
                return [
                        QuestItem(
                                title=quest.get("title"),
                                quest_id=quest.get("id_"),
                                rank=quest.get("rank"),
                                level=quest.get("level"),
                                is_assignment=quest.get("is_urgent"),
                                is_event=quest.get("is_event"),
                                targets=quest.get("targets"),
                                target_hp=quest.get("targets_hp"),
                                reward_zenny=quest.get("zenny"),
                                reward_points=quest.get("hr_points"),
                        )
                        for quest in self.quest_data
                        if quest.get("hub") in ["Village", "Hub"]
                ]

        def scrape_quest(self, link: str) -> Dict[str, Any]:
                soup = self.retrieve_soup(link, polite=False)

                header_tag = soup.find("h2", string=True)
                header_text = header_tag.text.strip()
                header_data = self._match_header(header_text)

                tag_div = header_tag.find_next("div")

                reward_raw = header_tag.find_next("div", class_="card-footer text-muted").text.split("/")
                rewards = [
                        float(match.group(1).replace(",",""))
                        for reward in reward_raw
                        if (match := re.search(r"([\d,]+\.?\d*)", reward)) is not None
                ]

                monster_header = soup.find("h5", string="Monster")
                monster_table = monster_header.find_next("div", class_="row")
                monster_hp = {}
                if monster_table:
                        monster_hp = {
                                monster.text.strip(): 
                                float(match.group(1).replace(",", "")) #type:ignore
                                for row in monster_table.find_all("tr")
                                if (monster := row.find("a", href=True, string=True)) is not None
                                and (hp_cell := row.find(lambda tag: tag.name == "td" and tag.text and "HP" in tag.text)) is not None
                                and (match := re.search(r"([\d,]+\.?\d*)", hp_cell.text)) is not None
                        }
                        print(monster_hp)

                return {
                        "id_": link.split("/")[-1],
                        "title": header_data.get("title"),
                        "rank": header_data.get("rank"),
                        "level": header_data.get("level"),
                        "hub": header_data.get("hub"),
                        "map": tag_div.find("a", href=True, string=True).text.strip(),
                        "is_urgent": tag_div.find("span", string="Urgent") is not None,
                        "is_key": tag_div.find("span", string="Key") is not None,
                        "is_event": "DLC" in header_text,
                        "targets": [key for key in monster_hp.keys()],
                        "targets_hp": monster_hp,
                        "zenny": rewards[0],
                        "points": rewards[1],
                        "hr_points": rewards[2],
                }

        def _match_header(self, header: str) -> Dict[str,str|int]:
                header_match = re.search(r"(\w+)\s*(G?\d+★?) // (.*)", header)
                if not header_match:
                        hub, title = header.split("//")
                        rank = "unknown"
                        level = 0

                else:
                        hub = header_match.group(1)
                        rank_tag = header_match.group(2)
                        title = header_match.group(3)

                        level_match = re.search(r"(\d+)", rank_tag)
                        level = int(level_match.group(1)) if level_match else 0

                        rank = "G"
                        is_village = "Village" in hub
                        if is_village:
                                rank = "HR" if level > 6 else "LR"
                        elif not is_village and not "G" in rank_tag:
                                rank = "HR" if level > 3 else "LR"
                
                return {
                        "title": title.strip(),
                        "hub": hub.strip(),
                        "rank": rank,
                        "level": level,
                }

        def scrape_monster(self, link: str) -> Dict[str,Any]:
                soup = self.retrieve_soup(link, polite=False)

                size_header = soup.find("h5", string=re.compile("Size"))
                size_text = size_header.text.strip() if size_header else ""
                size = None
                match = re.search(r"([\d,]+\.?\d*)", size_text)
                if match:
                    size = float(match.group(1).replace(",",""))

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