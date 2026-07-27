import logging
import re
from pathlib import Path
from typing import List

import pandas as pd

from src.core.interfaces import AbstractWebScraper
from src.core.dataclasses import QuestItem

logger = logging.getLogger(__name__)

class WorldQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH World/ Icebreak.
    To be called via QuestScraper class.
    """

    def scrape(self) -> List[QuestItem]:
        """Loads quest data from @gatheringhallstudios' quest databases and Fextralife (for base hp) 
        and extracts information as QuestItems.
        """
        worlds_quest_data = []

        df_quests = self.load_world_quest_data()
        world_monsters = df_quests["monster_name"].unique().tolist()

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
    
    def load_world_quest_data(self, overwrite: bool = False, scrape_hp: bool = False) -> pd.DataFrame:
        """Merges baseline database files for Monster Hunter World, transforms it into suitable format and loads it as DataFrame.
        Optionally scrapes Monster hp from fextralife (through helper function scrape_world_monster_hp).
        """
        database_path = Path(__file__).resolve().parents[4] / "data" / "subsets" / "gatheringhallstudios"
        merged_filename = database_path / "mhw_quests_merged.csv"

        if not merged_filename.is_file() or overwrite:
            base_filename = database_path / "world_quest_base.csv"
            monsters_filename = database_path / "world_quest_monsters.csv"

            df_base = pd.read_csv(base_filename, index_col=False)
            df_monsters = pd.read_csv(monsters_filename, index_col=False).rename(columns={"base_id": "id"})
            df_merged = pd.merge(df_monsters, df_base, how="outer", on="id")

            small_monsters = ['Jagras', 'Kestodon', 'Gajau', 'Vespoid', 'Hornetaur', 'Raphinos', 'Gastodon',
                                'Girros', 'Barnos', 'Gajalaka', 'Wulg', 'Boaboa', 'Mosswine', 'Shamos']
            df_objective_filtered = df_merged[df_merged["is_objective"] == True]
            df_large_filtered = df_objective_filtered[~df_objective_filtered["monster_en"].isin(small_monsters)]

            df_large_filtered.rename(columns={"monster_en":"monster_name"}, inplace=True)
            df_large_filtered["rank"] = df_large_filtered["rank"].str.lower()
            df_large_filtered.loc[df_large_filtered['rank'] == 'mr', 'stars'] += 9

            df_complete = df_large_filtered.sort_values(by=["monster_name", "id"]).reset_index(drop=True)

            if scrape_hp or not "hp" in df_large_filtered.columns:
                world_monsters = df_large_filtered["monster_name"].unique().tolist()
                df_hp = self.scrape_world_monster_hp(world_monsters)

                df_complete = pd.merge(df_complete, df_hp, on=["monster_name", "rank"], how="left")

            df_complete.to_csv(merged_filename, index=False)

        return pd.read_csv(merged_filename, index_col=False)

    def scrape_world_monster_hp(self, monsters: List[str]) -> pd.DataFrame:
        fextralife_url = r"https://monsterhunterworld.wiki.fextralife.com"
        world_monster_hp = []
        rank_mapping = {"Low Rank":"lr", "High Rank":"hr", "Master Rank":"mr", "HP":"mr", "Health":"mr"}

        for monster in monsters:
            try:
                relative_link = monster.strip().replace(" ","+")
                absolute_link = f"{fextralife_url}/{relative_link}"

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
        df_world_hp.to_csv(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\test_hp.csv", index=False)

        return df_world_hp
    