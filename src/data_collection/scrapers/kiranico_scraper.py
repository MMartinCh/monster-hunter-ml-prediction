import re
import logging
import numpy as np

from bs4 import BeautifulSoup
from typing import List

from src.core.interfaces import AbstractWebScraper
from src.core.dataclasses import WikiQuestItem

logger = logging.getLogger(__name__)

class KiranicoScraper(AbstractWebScraper[WikiQuestItem]):
    """Scraper class to scrape quest info from Kiranico pages to different MH games from Wilds to Tri Ultimate."""

    def scrape(self) -> List[WikiQuestItem]:
        """Scrape quests from Monster Hunter main line games in order of sales: Worlds -> Rise -> Wilds... Keep first entry only."""
        pass

    def scrape_worlds(self) -> List[WikiQuestItem]:
        WORLDS_URL = r"https://mhworld.kiranico.com/en/monsters"
        worlds_data = []

        soup = self.retrieve_soup(WORLDS_URL)
        table = soup.find("table", class_="table table-padded")
        monster_links = [row.find("a").get("href") for row in table.find_all("tr")]

        return monster_links


    def scrape_wilds(self) -> List[WikiQuestItem]:
        WILDS_URL = r"https://mhwilds.kiranico.com/data/quests"
        wilds_data = []

        soup = self.retrieve_soup(WILDS_URL)
        table = soup.find("table", class_="w-full caption-bottom text-sm")
        rows = table.find_all("tr")

        unique_monsters = set()
        for row in rows:
            for a in row.find_all("a", href=re.compile(r"/data/monsters/")):
                unique_monsters.add(a.text.strip())

        # Collect all quest data
        all_quests_for_monsters = {monster_name:[] for monster_name in unique_monsters}
        for quest in rows:
            quest_data = {}
            cells = quest.find_all("td")

            quest_data["quest_title"] = cells[0].text.strip()
            quest_data["quest_reward"] = int(cells[1].text.strip().replace(",","").replace("HRP",""))

            quest_monsters = [a.text.strip() for a in cells[2].find_all("a") if a.text.strip()]
            quest_monster = quest_monsters[0] if quest_monsters else None

            quest_monster_hp = [div.text.strip() for div in cells[3].find_all("div") if div.text.strip()]
            quest_data["quest_monster_hp"] = int(quest_monster_hp[0].replace(",","").replace("HP","")) if quest_monster_hp else None

            quest_data["quest_level"] = int(re.search(r"\d★", quest_data.get("quest_title")).group().replace("★",""))
            quest_data["is_assignment"] = "Assignment" in quest_data.get("quest_title")

            match quest_data.get("quest_level"):
                case level if level <= 3:
                    quest_data["quest_rank"] = "Low"
                case level if level <= 6:
                    quest_data["quest_rank"] = "High"
                case level if level > 6:
                    quest_data["quest_rank"] = "Master"
                case _:
                    quest_data["quest_rank"] = "Unknown"

            if quest_monster is not None:
                all_quests_for_monsters[quest_monster].append(quest_data)

        for monster, quests in all_quests_for_monsters.items():
            monster_data={}
            monster_data["monster_name"] = monster
            monster_data["game_appearances"] = monster_data.get("game_appearances", 0) + 1
            monster_data["quest_appearances"] = len(quests)
            monster_data["has_assignment"] = any(quest["is_assignment"] for quest in quests)
            monster_data["initial_quest"] = min(quest["quest_level"] for quest in quests)

            rank_mapping = {"lr":"Low", "hr":"High", "mr":"Master"}
            for rank in ["lr", "hr", "mr"]:
                monster_data[f"{rank}_hp"] = np.mean([quest["quest_monster_hp"] for quest in quests if quest["quest_rank"] == rank_mapping[rank]])
                monster_data[f"{rank}_reward"] = np.mean([quest["quest_reward"] for quest in quests if quest["quest_rank"] == rank_mapping[rank]])

            wilds_data.append(self.convert_to_quest_item(monster_data))
        
        return wilds_data

    def convert_to_quest_item(self, data: dict) -> WikiQuestItem:
        return WikiQuestItem(
            monster_name=data.get("monster_name"),
            total_game_appearances=data.get("game_appearances", 0),
            total_quest_appearances=data.get("quest_appearances", 0),    
            has_assignment=data.get("has_assignment", False),
            initial_quest=data.get("initial_quest"),
            lr_hp=data.get("lr_hp"),
            hr_hp=data.get("hr_hp"),               
            mr_hp=data.get("mr_hp"),
            lr_reward=data.get("lr_reward"),
            hr_reward=data.get("hr_reward"),               
            mr_reward=data.get("mr_reward")
        )