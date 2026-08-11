import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin

import pandas as pd

from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.dataclasses import QuestItem #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class WorldQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH World/ Icebreak.
    To be called via QuestScraper class.
    """
    FEXTRALIFE_URL = r"https://monsterhunterworld.wiki.fextralife.com"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "world"
    QUEST_DATA_PATH = DATA_PATH / "world_quests.csv"
    QUEST_BASE_PATH = DATA_PATH / "stock" / "quest_base.csv"
    QUEST_MONSTERS_PATH = DATA_PATH / "stock" / "quest_monsters.csv"
    PROCESSED_STOCK_PATH = DATA_PATH / "stock" / "processed_stock_data.csv"
    MONSTER_LIST_PATH = DATA_PATH / "helper" / "world_monsters.json"
    MONSTER_HP_PATH = DATA_PATH / "helper" / "world_monster_hp.json"

    @cached_property
    @file_cache("MONSTER_LIST_PATH")
    def monster_links(self) -> Dict[str,str]:
        return self._scrape_monster_links()

    @cached_property
    @file_cache("MONSTER_HP_PATH", overwrite=True)
    def monster_hp(self) -> Dict[str,Dict[str,float]]:
        return self._scrape_monster_hp()
    
    @cached_property
    @file_cache("PROCESSED_STOCK_PATH")
    def processed_stock_data(self) -> pd.DataFrame:
        return self._load_stock_quest_data()

    @cached_property
    @file_cache("QUEST_DATA_PATH")
    def quest_data(self) -> pd.DataFrame:
        return self.scrape_quest_data()

    @property
    def _stock_quest_base(self) -> pd.DataFrame:
        return pd.read_csv(self.QUEST_BASE_PATH, index_col=False)

    @property
    def _stock_quest_monsters(self) -> pd.DataFrame:
        return pd.read_csv(self.QUEST_MONSTERS_PATH, index_col=False).rename(columns={"base_id": "id"})

    def scrape(self) -> List[QuestItem]:
        """Loads quest data from @gatheringhallstudios' quest databases and Fextralife (for base hp) 
        and extracts information as QuestItems.
        """
        worlds_quest_data = []

        df_quests = self.load_world_quest_data()

        # TODO: convert to new format
        for monster in self.monster_links.keys():
            monster_data = {}
            df_monster = df_quests[df_quests["monster_name"] == monster]

            monster_data["monster_name"] = monster
            monster_data["has_assignment"] = "assigned" in df_monster["category"].tolist()
            monster_data["initial_quest"] = df_monster["stars"].min()

            for rank in ["lr", "hr", "mr"]:
                monster_data[f"{rank}_reward"] = df_monster.loc[df_monster["rank"] == rank, "zenny"].mean()
                monster_data[f"{rank}_hp"] = df_monster.loc[df_monster["rank"] == rank, "hp"].mean()

            worlds_quest_data.append(self.convert_to_quest_item(monster_data))

        return worlds_quest_data
    
    def _load_stock_quest_data(self) -> pd.DataFrame:
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

    def _scrape_monster_hp(self) -> Dict[str,Dict[str,float]]:
        """Scrape LR, HR and MR hp for all monsters and return as pd df."""
        rank_mapping = {"Low Rank":"LR", "High Rank":"HR", "Master Rank":"MR", "HP":"MR", "Health":"MR"} #HACK

        all_monster_hp = {}
        for monster, link in self.monster_links.items():
            monster_hp = {}
            try:
                soup = self.retrieve_soup(link)
                hp_cell = soup.find(
                    lambda tag: tag.name == "li" 
                    and ("HP" in tag.text or "Health" in tag.text)
                    )

                has_sublist = hp_cell.find("ul")
                if has_sublist:
                    hp_li = [hp.text.strip() for hp in has_sublist.find_all("li") if hp.text.strip()]
                else:
                    hp_li = [hp_cell.text.strip()]

                print(f"Has sublist - {has_sublist}: {hp_li}")

                for li in hp_li:
                    if ":" not in li:
                        continue
                    rank_raw, hp_row = li.split(":", 1)
                    rank = rank_mapping.get(rank_raw, "Unique")
                    match = re.search(r"([\d,]+)\s*\(solo\)", hp_row.lower())
                    hp = int(match.group(1).replace(",", "")) if match else None

                    monster_hp[rank] = hp

                all_monster_hp[monster] = monster_hp

            except AttributeError:
                logger.warning(f"No Hp found for {monster}!")

            except KeyboardInterrupt:
                logger.info(f"WORLDS MONSTER HP scraping manually interrupted.")
                return all_monster_hp

        return all_monster_hp

    def _scrape_monster_links(self) -> Dict[str,str]:
        link = urljoin(self.FEXTRALIFE_URL, "Large+Monsters")
        soup = self.retrieve_soup(link)
        div = soup.select_one('div#tagged-pages-container')
        return {
            monster.text.strip(): urljoin(self.FEXTRALIFE_URL, monster["href"])
            for monster in div.find_all("a", href=True)
            if monster.text.strip()
        }