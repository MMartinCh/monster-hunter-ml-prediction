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

class FourQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Four Ultimate.
    To be called via QuestScraper class."""

    GAME = "Four Ultimate"
    GEN = 4

    QUEST_URL = r"https://kiranico.com/en/mh4u/quest"
    MONSTER_URL = r"https://kiranico.com/en/mh4u/monster"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "four_ultimate"
    QUEST_DATA_PATH = DATA_PATH / "fu_quest_data.json"
    MONSTER_DATA_PATH = DATA_PATH / "fu_monster_data.json"
    QUEST_LINKS_PATH = DATA_PATH / "helpers" / "fu_quest_links.txt"
    MONSTER_LINKS_PATH = DATA_PATH / "helpers" / "fu_monster_links.txt"

    @cached_property
    @file_cache("QUEST_DATA_PATH")
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
    @file_cache("MONSTER_DATA_PATH")
    def monster_data(self) -> List[Dict[str,Any]]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            _monster_data = [
                monster for link in self.monster_links
                if (monster := self.scrape_monster(browser, link))
                ]
            browser.close()
            return _monster_data
    
    @cached_property
    @file_cache("QUEST_LINKS_PATH")
    def quest_links(self) -> List[str]:
        return self._scrape_links("quest")

    @cached_property
    @file_cache("MONSTER_LINKS_PATH")
    def monster_links(self) -> List[str]:
        return self._scrape_links("monster")

    def scrape(self) -> List[QuestItem]:
        hp_lookup = {
            monster: hp
            for monster_dict in self.monster_data
            if (monster := monster_dict.get("monster_name"))
            and (hp := {
                "base": monster_dict.get("base_hp"),
                "lr": monster_dict.get("lr_hp"),
                "hr": monster_dict.get("hr_hp"),
                "mr": monster_dict.get("mr_hp")
            })
        }

        complete_data = []
        for quest in self.quest_data:
            if not quest.get("targets"):
                continue

            rank = quest.get("rank")
            target_hp = {}
            for target in quest.get("targets", []):
                if monster_hp := hp_lookup.get(target):
                    if hp_value := monster_hp.get(rank.lower() if rank else ""):
                        target_hp[target] = hp_value
                    elif base_hp := monster_hp.get("base"):
                        target_hp[target] = base_hp

            complete_data.append(
                QuestItem(
                    title=quest.get("title"),
                    game=self.GAME,
                    generation=self.GEN,
                    rank=rank,
                    level=quest.get("level"),
                    is_assignment=quest.get("is_urgent"),
                    is_event=quest.get("is_event"),
                    targets=quest.get("targets"),
                    target_hp=target_hp,
                    reward_zenny=quest.get("zenny"),
                    reward_points=quest.get("points"),
                )
            )

        return complete_data

    def scrape_quest(self, browser:Browser, link:str) -> Dict[str,Any]:
        soup = self.retrieve_rendered_soup(browser, link)
        div = soup.select_one("div.col-sm-3")

        h1_tag = soup.find("h1")
        title = "".join([element for element in h1_tag.contents if isinstance(element, str)]).strip()

        targets = [
                target.text.strip()
                for target in div.find_all(
                    "a", string=True, href=re.compile(r"monster")
                    )
                ] 
        quest_type = self._get_quest_attribute(div, "Type")
        if not quest_type in ["Hunting", "Slaying", "Special"] or targets is None:
            return {}

        hub_tags = div.find("td", colspan="2", string=True).text.strip().split(" ")
        hub = hub_tags[0]
        level = int(hub_tags[1])

        raw_reward = self._get_quest_attribute(div, "Reward")
        zenny = int(raw_reward.replace(",","").replace("z","")) if raw_reward and raw_reward.replace(",","").replace("z","").strip().isdigit() else 0
        raw_hrp = self._get_quest_attribute(div, "HRP")
        points = int(raw_hrp) if raw_hrp and raw_hrp.strip().isdigit() else 0

        return {
            "title": title,
            "hub": hub,
            "rank": self._match_rank(hub, level, title),
            "level": level,
            "type": quest_type,
            "is_key": h1_tag.find("span", string="Key") is not None,
            "is_urgent": h1_tag.find("span", string="Urgent") is not None,
            "is_event": hub == "Event",
            "map": self._get_quest_attribute(div, "Map"),
            "targets": targets,
            "zenny": zenny,
            "points": points,
        }

    def scrape_monster(self, browser:Browser, link:str) -> Dict[str,Any]:
        soup = self.retrieve_rendered_soup(browser, link)

        monster_name = "".join(
            element for element in soup.find("h1") 
            if isinstance(element, str)
            ).strip()

        hp_header = soup.find("h5", string="HP")
        hp_table = hp_header.find_next("table")

        size_header = soup.find("h5", string="Crown Sizes")
        size_table = size_header.find_next("table")

        return {
            "monster_name": monster_name,
            "base_hp": float(self._get_quest_attribute(hp_table, "Base HP", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "lr_hp": float(self._get_quest_attribute(hp_table, "Low", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "hr_hp": float(self._get_quest_attribute(hp_table, "High", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "mr_hp": float(self._get_quest_attribute(hp_table, "G", "0").replace("HP","").replace(",","").strip()), #type:ignore
            "small_size": float(self._get_quest_attribute(size_table, "Miniature", "0").replace("<","").replace(">","")), #type:ignore
            "large_size": float(self._get_quest_attribute(size_table, "Large", "0").replace("<","").replace(">","")), #type:ignore
            "max_size": float(self._get_quest_attribute(hp_table, "King", "0").replace("<","").replace(">","")), #type:ignore
        }

    def _get_quest_attribute(self, soup: BeautifulSoup, attribute: str, default:Any = None) -> Any | None:
        col = soup.find("td", string=re.compile(attribute))
        return col.find_next("td").get_text(strip=True) if col else default #type:ignore

    def _match_rank(self, hub:str, level:int, title:str) -> str:
        rank = "LR"
        if hub == "Caravan":
            if level > 6:
                rank = "HR"
            elif level == 10 and "Advanced" in title:
                rank = "MR"
        elif hub in ["Guild", "Event"]:
            if level > 3:
                rank = "HR"
            elif level > 7:
                rank = "MR"
        return rank

    def _scrape_links(self, type_: str) -> List[str]:
        if not type_.lower() in ["monster", "quest"]:
            raise AttributeError(f"Type {type_} no suitable category. Try MONSTER or QUEST...")

        url = getattr(self, f"{type_.upper()}_URL")
        soup = self.retrieve_soup(url)
        return [
            link
            for row in soup.find_all(
                    "a", 
                    string=True, 
                    href=re.compile(rf"^https://kiranico.com/en/mh4u/{type_.lower()}/\d+/.*")
                    )
                    if (link := row.get("href"))
        ]

