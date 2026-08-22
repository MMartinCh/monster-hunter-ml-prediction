import logging
import re
from functools import cached_property
from pathlib import Path
from typing import cast, Any, Dict, List

from bs4 import BeautifulSoup, Tag
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
    @file_cache("QUEST_DATA_PATH", overwrite=True)
    def quest_data(self) -> List[Dict[str,Any]]:
        _quest_data = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            for url in [self.VILLAGE_QUEST_URL, self.GUILD_QUEST_URL]:
                hub = "Village" if "Village" in url else "Guild"
                soup = self.retrieve_rendered_soup(browser, url)
                quest_tables = soup.find_all("table", class_="themetable")
                _quest_data.extend([
                        quest 
                        for table in quest_tables
                        if (quest := self.scrape_quest(table, hub))
                    ])

            browser.close()
        return _quest_data

    @cached_property
    @file_cache("MONSTER_LIST_PATH")
    def monster_list(self) -> List[str]:
        return self._scrape_monster_list()

    def scrape(self) -> List[QuestItem]:
        return [
            QuestItem(
                title= quest.get("title"),
                quest_id= f"{self.GAME}_{i}",
                game= self.GAME,
                generation= self.GEN,
                rank= quest.get("rank"),
                level= quest.get("level"),
                is_assignment= quest.get("is_urgent"),
                targets= quest.get("objective"),
                reward_zenny= quest.get("zenny"),
                reward_points= quest.get("points"),
            ) for i, quest in enumerate(self.quest_data)
        ]

    def scrape_quest(self, table: Tag, hub: str) -> Dict[str, Any] | None:
        rows = cast(List[Tag], table.find_all("tr"))

        header_row = rows[0].find_all("th") 
        objective_row = cast(Tag, rows[1])

        targets = [
                target 
                for objective in cast(List[Tag], objective_row.find_all("a", href=True, title=True))
                if (target := objective.get("title"))
            ]
        if not targets: 
            return {}

        tab_header = cast(Tag, table.find_parent("div", class_="wds-tab__content"))
        tab_string = cast(Tag, tab_header.find("span", class_="mw-headline", id=True)).get_text(strip=True)
        rank_info = self._match_rank(tab_string, hub)

        return {
            "title": header_row[1].text.strip(),
            "hub": hub,
            "level": rank_info.get("level"), 
            "rank": rank_info.get("rank"),
            "objective": targets,
            "map": self._get_attribute(table, "Location"),
            "is_urgent": "Urgent" in header_row[0].get_text(strip=True),
            "is_key": "Key" in header_row[0].get_text(strip=True),
            "zenny": self._get_attribute(table, "Reward", "int"),
            "points": self._get_attribute(table, "HR Points", "int"),
        }

    def _get_attribute(self, section: Tag, attribute: str, type_: str = "str") -> str|int|None:
        th_match = section.find(
            lambda tag: tag.name == "th" and re.search(rf"\b{attribute}\b", tag.get_text(), re.IGNORECASE) #type:ignore
        )

        if not th_match:
            return None

        parent_tr = cast(Tag, th_match.find_parent("tr"))
        if not parent_tr:
            return None

        td_cell = parent_tr.find("td")
        if not td_cell:
            return None

        content = td_cell.get_text(strip=True)
        if type_ == "int":
            match = re.search(r"(\d+)", content)
            content = match.group(1) if match else 0

        return content

    def _match_rank(self, tab_string:str, hub: str) -> Dict[str,str|int]:
        level, rank = 0, "LR"
        match = re.search(r"(★+)", tab_string)
        if match:
            level = len(match.group(1))
        elif "Urgent" in tab_string:
            if hub == "Village":
                level = 6
            elif hub == "Guild":
                level = 9

        if hub != "Village":
            if level > 5:
                rank = "MR"
            elif level > 3:
                rank = "HR"
        
        return {
            "level": level,
            "rank": rank
        }

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