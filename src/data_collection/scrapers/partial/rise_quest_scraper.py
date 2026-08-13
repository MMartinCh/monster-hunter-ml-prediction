import json
import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd

from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.helpers import file_cache #type:ignore
from src.core.dataclasses import QuestItem # type:ignore

logger = logging.getLogger(__name__)

class RiseQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Rise/ Sunbreak.
    To be called via QuestScraper class.
    """
    def __init__(self, overwrite: bool = False, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.overwrite = overwrite

    BASE_URL = r"https://mhrise.mhrice.info/monster.html"
    KEY_QUEST_URL = r"https://monsterhunterrise.wiki.fextralife.com/Hub+Quests"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "rise"
    MONSTER_DATA_PATH = DATA_PATH / "monster_page_data.json"
    QUEST_DATA_PATH = DATA_PATH / "raw_quest_data.json"
    KEY_QUEST_PATH =  DATA_PATH / "helper" / "key_quests.txt"
    MONSTER_LINK_PATH = DATA_PATH / "helper" / "monster_links.txt"
    QUEST_LINK_PATH = DATA_PATH / "helper" / "quest_links.txt"

    @cached_property
    @file_cache("MONSTER_LINK_PATH")
    def monster_links(self) -> List[str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache("QUEST_LINK_PATH")
    def quest_links(self) -> Set[str]:
        return set(self._scrape_quest_links())

    @cached_property
    @file_cache("KEY_QUEST_PATH")
    def key_quests(self) -> Set[str]:
        return set(self._scrape_key_quests())

    @cached_property
    @file_cache("MONSTER_DATA_PATH")
    def monster_page_data(self) -> Dict[str,Dict[str,float]]:
        return self.scrape_monster_page_data()

    @cached_property
    @file_cache("QUEST_DATA_PATH")
    def quest_data(self) -> List[Dict[str,Any]]:
        return self.scrape_quest_data()

    def scrape(self) -> List[QuestItem]:
        """Get all Quest info for MH Rise/ Sunbreak and return list of structured quest data."""
        return[
            QuestItem(
                title=quest["title"],
                id=quest["id"],
                rank=quest["rank"],
                level=quest["level"],
                is_assignment=quest["is_assignment"],
                is_event=quest["is_event"],
                targets=quest["targets"],
                target_hp=self._calculate_target_hp(quest),
                reward_zenny=quest["reward_zenny"],
                reward_points=quest["reward_rank_points"],
                )
            for quest in self.quest_data
            ]

    def scrape_monster_page_data(self) -> Dict[str,Dict[str,float]]:
            """Scrape all data from all data from Monster pages. Save to csv and return df."""
            logger.info(f"No MONSTER PAGE DATA found at {self.MONSTER_DATA_PATH}. Start scraping from {self.BASE_URL}")

            monster_page_data = {}
            for link in self.monster_links:
                try:
                    monster_page_soup = self.retrieve_soup(link)
    
                    header = monster_page_soup.find("h1")
                    monster_name = header.find("span", class_="mh-lang", lang="en").text.strip()
    
                    size_column = monster_page_soup.find("span", string="Size")
                    size_info = size_column.find_next_sibling("span").text.strip()
                    monster_size = float(size_info.split("(")[0])
    
                    base_hp_column = monster_page_soup.find("span", string=re.compile("Base HP"))
                    base_hp_info = base_hp_column.find_next_sibling("span").text.strip() 
                    hp_from_string = re.findall(r"(?<=R\) )\d+", base_hp_info)
                    lr_base_hp, mr_base_hp = map(int, hp_from_string)
    
                    monster_page_data[monster_name] = {
                        "monster_size": monster_size,
                        "lr_base_hp": lr_base_hp,
                        "mr_base_hp": mr_base_hp
                    }
    
                except AttributeError:
                    logger.warning(f"Different data structure for {link}! Skip entry...")
                except KeyboardInterrupt:
                    logger.warning(f"RISE MONSTER INFO SCRAPING manually interrupted. Save data to {self.QUEST_DATA_PATH}.")
                    return monster_page_data

            return monster_page_data

    def scrape_quest_data(self) -> List[Dict[str,Any]]:
        """Get all quest links from specific Monster page and loop through each quest using get_quest_data-function."""
        quest_data = []
        for quest in self.quest_links:
            try:
                quest_data.append(self._extract_quest_data(quest))
            except AttributeError:
                logger.warning(f"Different data structure for {quest}! Skip entry...")
            except KeyboardInterrupt:
                logger.warning(f"RISE QUEST SCRAPING manually interrupted. Save data to {self.QUEST_DATA_PATH}.")
                return quest_data

        return quest_data

    def _extract_quest_data(self, quest: str) -> Dict[str,Any] | None:
        quest_soup = self.retrieve_soup(quest)

        quest_id_match = re.search(r"(\d+).html", quest)
        quest_id = quest_id_match.group(1) if quest_id_match else None
        quest_title = quest_soup.select_one("span.lang-default.mh-lang[lang='en'] span").text.strip()

        header = quest_soup.find("h1")
        quest_category = header.find("span", class_=True).text.strip()
        match = re.search(r"(?P<rank>[a-zA-Z]+)(?P<level>\d+)", quest_category)
        quest_rank, quest_level = "", None
        if match:
            quest_rank = match.group("rank").upper()
            quest_level = match.group("level")

        is_event = header.find("span", class_="mh-quest-event tag") is not None

        basic_info = quest_soup.find("section", id="s-basic")
        reward_zenny = int(basic_info.find("span", string=re.compile("Reward money")).find_next_sibling("span").text.replace("z","").strip()) # HACK: use regex
        reward_rank_points = int(basic_info.find("span", string=re.compile("Reward rank point")).find_next_sibling("span").text.replace("z","").strip())

        target_section = quest_soup.find("section", id="s-stats")
        target_table = target_section.find("tbody")

        targets_hp_scaling = {
            name_span.get_text().strip(): float(match.group(1))
            for row in target_table.select("tr:has(div.mh-quest-monster > span.is-primary.tag)")
            if (tag := row.select_one("div.mh-quest-monster > span.is-primary.tag")) and "Target" in tag.get_text()
            if (name_span := row.select_one("span.lang-default.mh-lang[lang='en']")) is not None
            if (match := next((m for td in row.find_all("td")[1:] if (m := re.search(r"x(\d+\.\d+)", td.get_text()))), None)) is not None
            }

        is_assignment = quest_title in self.key_quests

        return {
            "id": quest_id,
            "title": quest_title,
            "rank": quest_rank,
            "level": quest_level,
            "reward_zenny": reward_zenny,
            "reward_rank_points": reward_rank_points, 
            "targets": list(targets_hp_scaling.keys()),
            "targets_hp_scaling": json.dumps(targets_hp_scaling),
            "is_assignment": is_assignment,
            "is_event": is_event,
            "is_village_quest": quest_rank == "VI"
            }

    def _calculate_target_hp(self, quest_data: Dict[str,Any]) -> Dict[str,float]:
        """Read target hp scaling from table, multiply with base hp and return dict of targets and their quest hp."""
        targets_hp_scaling: Dict[str,float] = json.loads(quest_data.get("targets_hp_scaling", "{}"))
        quest_rank = quest_data.get("quest_rank", "")
        quest_rank = "LR" if quest_rank != "MR" else quest_rank

        targets_final_hp = {}
        for target, scaling in targets_hp_scaling.items():
            target_data: Dict[str,float] = self.monster_page_data.get(target, {})
            target_base = target_data.get(f"{quest_rank.lower()}_base_hp", None)
            if not target_base:
                continue

            targets_final_hp[target] = target_base * scaling

        return targets_final_hp

    def _scrape_monster_links(self) -> List[str]:
        """"Find all Monster page links from Monster overview page."""
        logger.info(f"No MONSTER LINKS found at {self.MONSTER_LINK_PATH}. Start scraping from {self.BASE_URL}")
        
        soup = self.retrieve_soup(self.BASE_URL)
        monster_table = soup.find("ul", class_="mh-list-monster")
        _monster_links = [urljoin(self.BASE_URL, a["href"]) for a in monster_table.find_all("a", href=True) if a["href"]]

        return _monster_links

    def _scrape_quest_links(self) -> Set[str]:
        """Scrape all quest links through monster pages."""
        quest_links = set()
        for monster in self.monster_links:
            monster_soup = self.retrieve_soup(monster, polite=False)

            quest_section = monster_soup.find("section", id="s-quest")
            quest_rows = quest_section.select("tr:not(.mh-non-target):not(.mh-hidden) a[href^='quest/']") 
            found_links = [urljoin(self.BASE_URL, a["href"].strip()) for a in quest_rows if a.has_attr("href")]
            quest_links.update(found_links)

        return quest_links

    def _scrape_key_quests(self) -> Set[str]:
        """Scrape all key quests from Fextralife Wiki, if not previously initiated and save."""
        logger.info(f"No KEY QUEST found at {self.KEY_QUEST_PATH}. Start scraping from {self.KEY_QUEST_URL}")
        soup = self.retrieve_soup(self.KEY_QUEST_URL)

        key_quest_tags = soup.select("p:has(img[title='key_quests_mhrise_wiki_guide_50px']) a")
        _key_quests = {a.text.strip() for a in key_quest_tags if a.text.strip()}

        return _key_quests 