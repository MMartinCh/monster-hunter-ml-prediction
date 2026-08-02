import logging
import re
from functools import cached_property
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from src.core.interfaces import AbstractWebScraper
from src.core.dataclasses import QuestItem
from src.core.helpers import file_cache

logger = logging.getLogger(__name__)

class WildsQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Wilds from Kiranico.
    To be called via QuestScraper class.
    """
    BASE_URL = r"https://mhwilds.kiranico.com/data/quests"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "wilds"
    DEFAULT_QUEST_DATA_PATH = DATA_PATH / "wilds_quests.csv"

    def scrape(self) -> List[QuestItem]:
        """Scrape all MH Wilds quests and return as structured quest data per quest."""
        pass

    def merge(self) -> pd.DataFrame:
        """Combine subsets to complete Pandas DF."""
        pass

    @cached_property
    @file_cache("DEFAULT_QUEST_DATA_PATH")
    def wilds_quest_data(self) -> pd.DataFrame:
        return self.scrape_quests()

    def scrape_quests(self) -> pd.DataFrame:
        """Scrapes quest and monster data from the Monster Hunter Wilds Kiranico database."""
        logger.info(f"No WILDS QUEST DATA found at {self.DEFAULT_QUEST_DATA_PATH}. Start scraping...")
        wilds_data = []

        soup = self.retrieve_soup(self.BASE_URL)
        table = soup.find("table", class_="w-full caption-bottom text-sm")
        quest_rows = table.find_all("tr")

        unique_monsters = set()
        for row in quest_rows:
            for link in row.find_all("a", href=re.compile(r"/data/monsters/")):
                unique_monsters.add(link.text.strip())

        # Collect all quest data mapped to monsters
        all_quests_for_monsters = {monster_name: [] for monster_name in unique_monsters}
        
        for row in quest_rows:
            quest_data = {}
            cells = row.find_all("td")

            quest_data["title"] = cells[0].text.strip()
            quest_data["reward"] = int(cells[1].text.strip().replace(",", "").replace("HRP", ""))

            monsters_in_quest = [link.text.strip() for link in cells[2].find_all("a") if link.text.strip()]
            primary_monster = monsters_in_quest[0] if monsters_in_quest else None

            monster_hp_divs = [div.text.strip() for div in cells[3].find_all("div") if div.text.strip()]
            quest_data["monster_hp"] = int(monster_hp_divs[0].replace(",", "").replace("HP", "")) if monster_hp_divs else None

            quest_data["level"] = int(re.search(r"\d★", quest_data.get("title")).group().replace("★", ""))
            quest_data["is_assignment"] = "Assignment" in quest_data.get("title")

            match quest_data.get("level"):
                case level if level <= 3:
                    quest_data["rank"] = "Low"
                case level if level <= 6:
                    quest_data["rank"] = "High"
                case level if level > 6:
                    quest_data["rank"] = "Master"
                case _:
                    quest_data["rank"] = "Unknown"

            if primary_monster is not None:
                all_quests_for_monsters[primary_monster].append(quest_data)

        # Process statistics per monster
        # TODO: new format - only quests
        for monster, quests in all_quests_for_monsters.items():
            monster_data = {
                "monster_name": monster,
                "game_appearances": 1,
                "quest_appearances": len(quests),
                "has_assignment": any(q["is_assignment"] for q in quests),
                "initial_quest": min(q["level"] for q in quests)
            }

            rank_mapping = {"lr": "Low", "hr": "High", "mr": "Master"}
            for rank_prefix, rank_name in rank_mapping.items():
                monster_data[f"{rank_prefix}_hp"] = np.mean(
                    [q["monster_hp"] for q in quests if q["rank"] == rank_name]
                )
                monster_data[f"{rank_prefix}_reward"] = np.mean(
                    [q["reward"] for q in quests if q["rank"] == rank_name]
                )

            wilds_data.append(self.convert_to_quest_item(monster_data))
        
        return wilds_data