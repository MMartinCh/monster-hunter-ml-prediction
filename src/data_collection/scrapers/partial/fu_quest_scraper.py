import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, sync_playwright

from src.core.helpers import file_cache #type:ignore
from src.core.interfaces.abstract_web_scraper import AbstractWebScraper #type:ignore
from src.core.dataclasses.quest_data import QuestItem #type:ignore

class FUQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Four Ultimate.
    To be called via QuestScraper class."""

    KIRANICO_URL = r"https://kiranico.com/en/mh4u/quest"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "four_ultimate"
    QUEST_DATA_PATH = DATA_PATH / "fu_quest_data.json"
    QUEST_LINKS_PATH = DATA_PATH / "helpers" / "fu_quest_links.txt"

    @cached_property
    @file_cache("QUEST_DATA_PATH")
    def quest_data(self) -> List[Dict[str,Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            _quest_data = [
                self.scrape_quest(quest, browser) 
                for quest in self.quest_links
                ]
            browser.close()
            return _quest_data
    
    @cached_property
    @file_cache("QUEST_LINKS_PATH")
    def quest_links(self) -> List[str]:
        return self._scrape_quest_links()

    def scrape(self) -> List[QuestItem]:
        return []

    def scrape_quest(self, link:str, browser:Browser) -> Dict[str,Any]:
        soup = self.retrieve_rendered_soup(browser, link)
        div = soup.select_one("div.col-sm-3")

        h1_tag = soup.find("h1")
        title = h1_tag.get_text(strip=True) if h1_tag else ""

        quest_type = self._get_quest_attribute(div, "Type")
        if not quest_type in ["Hunting", "Slaying", "Special"]:
            return {"title":title, "type":"no hunt"}

        hub_tags = div.find("td", colspan="2", string=True).text.strip().split(" ")
        hub = hub_tags[0]
        level = int(hub_tags[1])

        raw_reward = self._get_quest_attribute(div, "Reward")
        zenny = int(raw_reward.replace(",","").replace("z","")) if raw_reward and raw_reward.replace(",","").replace("z","").strip().isdigit() else 0
        raw_hrp = self._get_quest_attribute(div, "HRP")
        points = int(raw_hrp) if raw_hrp and raw_hrp.strip().isdigit() else 0

        return {
            "title": h1_tag.get_text(strip=True),
            "hub": hub,
            "rank": self._match_rank(hub, level),
            "level": level,
            "type": quest_type,
            "is_key": h1_tag.find("span", string="Key") is not None,
            "is_urgent": h1_tag.find("span", string="Urgent") is not None,
            "is_event": hub == "Event",
            "map": self._get_quest_attribute(div, "Map"),
            "targets": [
                target.text.strip()
                for target in div.find_all(
                    "a", string=True, href=re.compile(r"monster"))
                ],
            "zenny": zenny,
            "points": points,
        }

    def _get_quest_attribute(self, soup: BeautifulSoup, attribute: str) -> str | None:
        col = soup.find("td", string=attribute)
        return col.find_next("td").get_text(strip=True) if col else None #type:ignore

    def _match_rank(self, hub:str, level:int) -> str:
        rank = "LR"
        if hub == "Caravan" and level > 6:
            rank = "HR"
        elif hub in ["Guild", "Event"]:
            if level > 3:
                rank = "HR"
            elif level > 7:
                rank = "MR"
        return rank

    def _scrape_quest_links(self) -> List[str]:
        return [
            row.get("href")
            for row in self.retrieve_soup(self.KIRANICO_URL).find_all(
                "a", string=True, href=re.compile(r"^https://kiranico.com/en/mh4u/quest/\w*/\d+/*")
                )
        ]

    