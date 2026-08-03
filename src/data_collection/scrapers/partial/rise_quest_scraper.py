import json
import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List
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
    DEFAULT_MONSTER_DATA_PATH = DATA_PATH / "monster_page_data.json"
    DEFAULT_QUEST_DATA_PATH = DATA_PATH / "quest_data.json"
    DEFAULT_KEY_QUEST_PATH =  DATA_PATH / "helper" / "key_quests.txt"
    DEFAULT_MONSTER_LINK_PATH = DATA_PATH / "helper"  / "monster_links.txt"

    @cached_property
    @file_cache("DEFAULT_MONSTER_LINK_PATH")
    def monster_links(self) -> List[str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache("DEFAULT_KEY_QUEST_PATH")
    def key_quests(self) -> List[str]:
        return self._scrape_key_quests()

    @cached_property
    @file_cache("DEFAULT_MONSTER_DATA_PATH", overwrite=True)
    def monster_page_data(self) -> List[Dict[str,Any]]:
        return self.scrape_monster_page_data()

    @cached_property
    @file_cache("DEFAULT_QUEST_DATA_PATH", overwrite=True)
    def quest_data(self) -> List[Dict[str,Any]]:
        return self.scrape_quest_data()

    def scrape(self) -> List[QuestItem]:
        """Get all Quest info for MH Rise/ Sunbreak and return list of structured quest data."""

        # TODO: extract unique monster names, process their data and pack as QuestItem
        pass
        

    def scrape_monster_page_data(self) -> List[Dict[str,Any]]:
            """Scrape all data from all data from Monster pages. Save to csv and return df."""
            logger.info(f"No MONSTER PAGE DATA found at {self.DEFAULT_MONSTER_DATA_PATH}. Start scraping from {self.BASE_URL}")

            monster_page_data = []
            for link in self.monster_links:
                try:
                    monster_page_soup = self.retrieve_soup(link)
    
                    header = monster_page_soup.find("h1")
                    monster_name = header.find("span", class_="mh-lang", lang="en").text.strip()
    
                    size_column = monster_page_soup.find("span", string="Size")
                    size_info = size_column.find_next_sibling("span").text.strip() #type:ignore
                    monster_size = float(size_info.split("(")[0])
    
                    base_hp_column = monster_page_soup.find("span", string=re.compile("Base HP"))
                    base_hp_info = base_hp_column.find_next_sibling("span").text.strip() #type:ignore
                    hp_from_string = re.findall(r"(?<=R\) )\d+", base_hp_info)
                    lr_base_hp, mr_base_hp = map(int, hp_from_string)
    
                    monster_page_info = {
                        "monster_name": monster_name,
                        "monster_size": monster_size,
                        "lr_base_hp": lr_base_hp,
                        "mr_base_hp": mr_base_hp
                    }
    
                    print(monster_page_info)
    
                    monster_page_data.append(monster_page_info)
    
                except AttributeError:
                    logger.warning(f"Different data structure for {link}! Skip entry...")
                except KeyboardInterrupt:
                    logger.warning(f"RISE MONSTER INFO SCRAPING manually interrupted. Save data to {self.DEFAULT_QUEST_DATA_PATH}.")
                    return monster_page_data

            return monster_page_data

    def scrape_quest_data(self) -> List[Dict[str,Any]]:
        """Get all quest links from specific Monster page and loop through each quest using get_quest_data-function."""
        logger.info(f"No QUEST DATA found at {self.DEFAULT_QUEST_DATA_PATH}. Start scraping from {self.BASE_URL}")

        monster_quest_data = []
        scraped_quests = set()
        for monster in self.monster_links:
            monster_soup = self.retrieve_soup(monster)

            quest_section = monster_soup.find("section", id="s-quest")
            quest_rows = quest_section.select("tr:not(.mh-non-target):not(.mh-hidden) a[href^='quest/']") #type:ignore
            quest_links = [urljoin(self.BASE_URL, a["href"].strip()) for a in quest_rows if a.has_attr("href")] #type:ignore

            for quest in quest_links:
                if quest in scraped_quests:
                    logger.info(f"Quest {quest} skipped for quest already scraped.")
                    continue
                else:
                    scraped_quests.add(quest)

                try:
                    quest_info = self._extract_quest_data(quest)
                    if monster_quest_data:
                        monster_quest_data.append(quest_info)

                except AttributeError:
                        logger.warning(f"Different data structure for {quest}! Skip entry...")
                except KeyboardInterrupt:
                    logger.warning(f"RISE QUEST SCRAPING manually interrupted. Save data to {self.DEFAULT_QUEST_DATA_PATH}.")
                    return monster_quest_data

        return monster_quest_data

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

        is_assigned = quest_title in self.key_quests

        return {
            "id": quest_id,
            "title": quest_title,
            "rank": quest_rank,
            "level": quest_level,
            "reward_zenny": reward_zenny,
            "reward_rank_points": reward_rank_points, 
            "targets": list(targets_hp_scaling.keys()),
            "targets_hp_scaling": json.dumps(targets_hp_scaling),
            "is_assigned": is_assigned,
            "is_event": is_event,
            "is_village_quest": quest_rank == "VI"
            }

    def _calculate_target_hp(self) -> Dict[str, Dict[str, float]]:
        """Read target hp scaling from table, multiply with base hp and return dict of targets and their quest hp."""
        target_hp_scaling_for_quest = [
            {
                "quest_title": quest["title"],
                "quest_rank": quest["rank"],
                "targets_with_hp_scaling": json.loads(quest["targets_with_hp"]) 
            }
            for quest in self.quest_data
        ]

        monster_base_hp = {item["monster"]: item for item in self.monster_page_data}

        all_final_monster_hp_for_quest = {}
        
        for entry in target_hp_scaling_for_quest:
            quest_title = entry["quest_title"]
            quest_rank = entry["quest_rank"]
            
            quest_rank = "LR" if quest_rank not in ["LR", "HR"] else quest_rank
            targets_with_hp_scaling = entry["targets_with_hp_scaling"]

            quest_with_target_hp = {}
            for monster, scaling in targets_with_hp_scaling.items():
                monster_data = monster_base_hp.get(monster)
                if not monster_data:
                    logger.warning(f"No Monster data found for {monster}. Skip HP calculation.")
                    continue

                base_hp = monster_data.get(f"{quest_rank.lower()}_base_hp")                
                target_hp = base_hp * scaling 
                quest_with_target_hp[monster] = target_hp
                
            all_final_monster_hp_for_quest[quest_title] = quest_with_target_hp

        return all_final_monster_hp_for_quest

    def _scrape_monster_links(self) -> List[str]:
        """"Find all Monster page links from Monster overview page."""
        logger.info(f"No MONSTER LINKS found at {self.DEFAULT_MONSTER_LINK_PATH}. Start scraping from {self.BASE_URL}")
        
        soup = self.retrieve_soup(self.BASE_URL)
        monster_table = soup.find("ul", class_="mh-list-monster")
        _monster_links = [urljoin(self.BASE_URL, a["href"]) for a in monster_table.find_all("a", href=True) if a["href"]]

        self.DEFAULT_MONSTER_LINK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DEFAULT_MONSTER_LINK_PATH, "w", encoding="utf-8") as f:
            for link in _monster_links:
                print(link, file=f)

        logger.info(f"Scraped MONSTER LINKS saved to {self.DEFAULT_MONSTER_LINK_PATH}")
        return _monster_links

    def _scrape_key_quests(self) -> List[str]:
        """Scrape all key quests from Fextralife Wiki, if not previously initiated and save."""
        logger.info(f"No KEY QUEST found at {self.DEFAULT_KEY_QUEST_PATH}. Start scraping from {self.KEY_QUEST_URL}")
        soup = self.retrieve_soup(self.KEY_QUEST_URL)

        key_quest_tags = soup.select("p:has(img[title='key_quests_mhrise_wiki_guide_50px']) a")
        _key_quests = [a.text.strip() for a in key_quest_tags if a.text.strip()]

        self.DEFAULT_KEY_QUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DEFAULT_KEY_QUEST_PATH, "w", encoding="utf-8") as f:
            for quest in _key_quests:
                print(quest, file=f)

        logger.info(f"Scraped KEY QUESTS saved to {self.DEFAULT_KEY_QUEST_PATH}")
        return _key_quests 