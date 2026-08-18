import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, sync_playwright

from src.core.helpers import file_cache #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_data import QuestItem #type:ignore

logger = logging.getLogger(__name__)

class TriQuestScraper(AbstractWebScraper[QuestItem]):
        """Partial Scraper Class that scrapes quest data for MH Tri/ Tri Ultimate.
        To be called via QuestScraper class."""

        GAME = "Tri Ultimate"
        GEN = 3

        QUEST_URL = r"https://kiranico.com/en/mh3u/quest"

        TRI_DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "tri_ultimate"
        TRI_QUEST_DATA_PATH = TRI_DATA_PATH / "tri_quest_data.json"
        TRI_QUEST_LINKS_PATH = TRI_DATA_PATH / "helpers" / "tri_quest_links.txt"

        @cached_property
        @file_cache("TRI_QUEST_DATA_PATH")
        def quest_data(self) -> List[Dict[str,Any]]:
                with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        _quest_data = [
                                quest for link in self.quest_links
                                if (quest := self.scrape_quest(browser, link))
                        ]
                        browser.close()
                return _quest_data

        @cached_property
        @file_cache("TRI_QUEST_LINKS_PATH", overwrite=False)
        def quest_links(self) -> List[str]:
                return self._scrape_quest_links()

        def scrape(self) -> List[QuestItem]:
                return [
                        QuestItem(
                                title=quest.get("title"),
                                game=self.GAME,
                                generation=self.GEN,
                                rank=quest.get("rank"),
                                level=quest.get("level"),
                                is_assignment=quest.get("is_urgent"),
                                is_event=quest.get("is_event"),
                                targets=quest.get("targets"),
                                reward_zenny=quest.get("zenny"),
                                reward_points=quest.get("points"),
                        )
                        for quest in self.quest_data
                ]

        def scrape_quest(self, browser:Browser, link:str) -> Dict[str,Any]:
                soup = self.retrieve_rendered_soup(browser, link)
                div = soup.select_one("div.col-sm-3")
        
                h1_tag = soup.find("h1")
                title = h1_tag.find(text=True, recursive=False).strip() if h1_tag else ""
        
                targets = [
                        target.text.strip()
                        for target in div.find_all(
                            "a", string=True, href=re.compile(r"monster")
                            )
                        ] 
                quest_type = self._get_quest_attribute(div, "Type")
                if not targets or quest_type not in ["Hunt", "Slay", "Special", "Endurance"]:
                        logger.info(f"No hunting quest: {title}, quest_type: {quest_type}")
                        return {}

                is_urgent = h1_tag.find("span", string="Urgent") is not None
        
                hub_tags = div.find("td", colspan="2", string=True).text.strip().split(" ")
                hub = hub_tags[0]
                level = int(hub_tags[1])
        
                raw_reward = self._get_quest_attribute(div, "Reward")
                zenny = int(raw_reward.replace(",","").replace("z","")) if raw_reward and raw_reward.replace(",","").replace("z","").strip().isdigit() else 0

                raw_hrp = self._get_quest_attribute(div, "HRP")
                points = int(raw_hrp) if raw_hrp and raw_hrp.strip().isdigit() else 0

                quest_dict =  {
                    "title": title,
                    "hub": hub,
                    "rank": self._match_rank(hub, level, is_urgent),
                    "level": level,
                    "type": quest_type,
                    "is_key": h1_tag.find("span", string="Key") is not None,
                    "is_urgent": is_urgent,
                    "is_event": hub == "Event",
                    "map": self._get_quest_attribute(div, "Map"),
                    "targets": targets,
                    "zenny": zenny,
                    "points": points,
                }

                print(quest_dict)

                return quest_dict

        def _get_quest_attribute(self, soup: BeautifulSoup, attribute: str, default:Any = None) -> Any | None:
                col = soup.find("td", string=re.compile(attribute))
                return col.find_next("td").get_text(strip=True) if col else default #type:ignore

        def _match_rank(self, hub:str, level:int, is_urgent:bool) -> str:
                rank = "LR"
                if hub == "Village" and level > 5:
                        rank = "HR"
                        if level == 9 and is_urgent:
                                rank = "MR"
                elif hub in ["Port", "Event"]:
                        if level > 5:
                                rank = "MR"
                        elif level > 2:
                                rank = "HR"
                        
                return rank

        def _scrape_quest_links(self) -> List[str]:
                soup = self.retrieve_soup(self.QUEST_URL)
                return [
                        link
                        for row in soup.find_all(
                                "a", 
                                string=True, 
                                href=re.compile(r"quest/\w*/\d+")
                                )
                                if (link := row.get("href"))
                ]