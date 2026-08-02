import logging
import re
from functools import cached_property
from pathlib import Path
from typing import List

import pandas as pd

from src.core.interfaces import AbstractWebScraper
from src.core.dataclasses import QuestItem
from src.core.helpers import file_cache

logger = logging.getLogger(__name__)

class WorldQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH World/ Icebreak.
    To be called via QuestScraper class.
    """
    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "world"
    DEFAULT_QUEST_DATA_PATH = DATA_PATH / "world_quests.csv"
    DEFAULT_QUEST_BASE_PATH = DATA_PATH / "stock" / "quest_base.csv"
    DEFAULT_QUEST_MONSTERS_PATH = DATA_PATH / "stock" / "quest_monsters.csv"
    DEFAULT_PROCESSED_STOCK_PATH = DATA_PATH / "stock" / "processed_stock_data.csv"
    DEFAULT_MONSTER_HP_PATH = DATA_PATH / "helper" / "world_monster_hp.csv"

    @property
    def stock_quest_base(self) -> pd.DataFrame:
        return pd.read_csv(self.DEFAULT_QUEST_BASE_PATH, index_col=False)

    @property
    def stock_quest_monsters(self) -> pd.DataFrame:
        return pd.read_csv(self.DEFAULT_QUEST_MONSTERS_PATH, index_col=False).rename(columns={"base_id": "id"})

    @cached_property
    def monster_list(self) -> List[str]:
        small_monsters = ['Jagras', 'Kestodon', 'Gajau', 'Vespoid', 'Hornetaur', 'Raphinos', 'Gastodon',
                                        'Girros', 'Barnos', 'Gajalaka', 'Wulg', 'Boaboa', 'Mosswine', 'Shamos'] # HACK: repeated boilerplate
        df = pd.read_csv(self.DEFAULT_QUEST_MONSTERS_PATH)
        unique_monsters = set(df[~df["monster_en"].isin(small_monsters)]["monster_en"].tolist())
        return list(unique_monsters)

    @cached_property
    @file_cache("DEFAULT_MONSTER_HP_PATH")
    def monster_hp(self) -> pd.DataFrame:
        return self.scrape_world_monster_hp(self.monster_list)

    @cached_property
    @file_cache("DEFAULT_PROCESSED_STOCK_PATH")
    def processed_stock_data(self) -> pd.DataFrame:
        return self.load_stock_quest_data()

    @cached_property
    @file_cache("DEFAULT_QUEST_DATA_PATH")
    def quest_data(self) -> pd.DataFrame:
        return self.scrape_quest_data()

    def scrape(self) -> List[QuestItem]:
        """Loads quest data from @gatheringhallstudios' quest databases and Fextralife (for base hp) 
        and extracts information as QuestItems.
        """
        worlds_quest_data = []

        df_quests = self.load_world_quest_data()
        world_monsters = df_quests["monster_name"].unique().tolist()

        # TODO: convert to new format
        for monster in world_monsters:
            monster_data = {}
            df_monster = df_quests[df_quests["monster_name"] == monster]

            monster_data["monster_name"] = monster
            monster_data["game_appearances"] = 1
            monster_data["quest_appearances"] = df_monster["quantity"].sum()
            monster_data["has_assignment"] = "assigned" in df_monster["category"].tolist()
            monster_data["initial_quest"] = df_monster["stars"].min()

            for rank in ["lr", "hr", "mr"]:
                monster_data[f"{rank}_reward"] = df_monster.loc[df_monster["rank"] == rank, "zenny"].mean()
                monster_data[f"{rank}_hp"] = df_monster.loc[df_monster["rank"] == rank, "hp"].mean()

            worlds_quest_data.append(self.convert_to_quest_item(monster_data))

        return worlds_quest_data

    def merge(self) -> pd.DataFrame:
        """Merge individual data subsets and return as pd df."""
        return pd.DataFrame()
    
    def load_stock_quest_data(self) -> pd.DataFrame:
        """Merges baseline database files for Monster Hunter World, transforms it into suitable format and loads it as DataFrame.
        """
        df_merged = pd.merge(self.stock_quest_monsters, self.stock_quest_base, how="outer", on="id")

        small_monsters = [
            'Jagras', 'Kestodon', 'Gajau', 'Vespoid', 'Hornetaur', 'Raphinos', 'Gastodon',                                    
            'Girros', 'Barnos', 'Gajalaka', 'Wulg', 'Boaboa', 'Mosswine', 'Shamos'
            ]
        df_objective_filtered = df_merged[df_merged["is_objective"] == True]
        df_large_filtered = df_objective_filtered[~df_objective_filtered["monster_en"].isin(small_monsters)]

        df_large_filtered.rename(columns={"monster_en":"monster_name"}, inplace=True)
        df_large_filtered["rank"] = df_large_filtered["rank"].str.lower()
        #df_large_filtered.loc[df_large_filtered['rank'] == 'mr', 'stars'] += 9

        return df_large_filtered

    def scrape_world_monster_hp(self, monsters: List[str]) -> pd.DataFrame:
        """Scrape LR, HR and MR hp for all monsters and return as pd df."""
        fextralife_url = r"https://monsterhunterworld.wiki.fextralife.com"
        world_monster_hp = []
        rank_mapping = {"Low Rank":"lr", "High Rank":"hr", "Master Rank":"mr", "HP":"mr", "Health":"mr"}

        for monster in monsters:
            relative_link = monster.strip().replace(" ","+")
            absolute_link = f"{fextralife_url}/{relative_link}"
            
            try:
                soup = self.retrieve_soup(absolute_link)
                hp_cell = soup.find(lambda tag: tag.name == "li" and "HP" in tag.text)

                has_sublist = hp_cell.find("ul")

                if has_sublist:
                    hp_li = [hp.text.strip() for hp in has_sublist.find_all("li") if hp.text.strip()]
                else:
                    hp_li = [hp_cell.text.strip()]

                for li in hp_li:
                    if ":" not in li:
                        continue
                    rank, hp_row = li.split(":", 1)
                    match = re.search(r"([\d,]+)\s*\(solo\)", hp_row.lower())
                    hp = int(match.group(1).replace(",", "")) if match else None

                    world_monster_hp.append({
                        "monster_name": monster,
                        "rank": rank_mapping.get(rank.strip(), "mr"),
                        "hp": hp
                        })

            except AttributeError:
                logger.warning(f"No Hp found for {absolute_link}!")

        df_world_hp = pd.DataFrame(world_monster_hp)

        return df_world_hp
    