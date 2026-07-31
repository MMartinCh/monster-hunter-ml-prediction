import json
import logging
import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd

from src.core.interfaces import AbstractWebScraper # type: ignore
from src.core.dataclasses import QuestItem # type: ignore

logger = logging.getLogger(__name__)

class RiseQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Rise/ Sunbreak.
    To be called via QuestScraper class.
    """
    BASE_URL = r"https://mhrise.mhrice.info/monster.html"
    KEY_QUEST_URL = r"https://monsterhunterrise.wiki.fextralife.com/Hub+Quests"

    # helpers
    DEFAULT_KEY_QUEST_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\helper\key_quests.txt")
    DEFAULT_MONSTER_LINK_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\helper\monster_links.txt")
    # datasets
    DEFAULT_MONSTER_DATA_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\monster_page_data.csv")
    DEFAULT_QUEST_DATA_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\quest_data.csv")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def monster_links(self) -> List[str]:
        if self.DEFAULT_MONSTER_LINK_PATH.exists():
            logger.info(f"Read MONSTER LINKS from disk at {self.DEFAULT_MONSTER_LINK_PATH}")
            with open(self.DEFAULT_MONSTER_LINK_PATH) as f:
                return[link.strip() for link in f]
        return self.scrape_monster_links()

    @cached_property
    def key_quests(self) -> List[str]:
        if self.DEFAULT_KEY_QUEST_PATH.exists():
            logger.info(f"Read KEY QUESTS from disk at {self.DEFAULT_KEY_QUEST_PATH}")
            with open(self.DEFAULT_KEY_QUEST_PATH, "r", encoding="utf-8") as f:
                return [quest.strip() for quest in f]
        return self.scrape_key_quests()

    @cached_property
    def monster_page_data(self) -> pd.DataFrame:
        if self.DEFAULT_MONSTER_DATA_PATH.exists():
            logger.info(f"Read MONSTER PAGE DATA from disk at {self.DEFAULT_MONSTER_DATA_PATH}")
            return pd.read_csv(self.DEFAULT_MONSTER_DATA_PATH, index_col="monster_name")
        return self.scrape_monster_page_info()

    @cached_property
    def quest_data(self) -> pd.DataFrame:
        if self.DEFAULT_QUEST_DATA_PATH.exists():
            logger.info(f"Read QUEST DATA from disk at {self.DEFAULT_QUEST_DATA_PATH}")
            return pd.read_csv(self.DEFAULT_QUEST_DATA_PATH, index_col="title")
        return self.scrape_quest_data()

    def scrape_monster_links(self) -> List[str]:
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

    def scrape_key_quests(self) -> List[str]:
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

    def scrape_monster_page_info(self) -> pd.DataFrame:
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
    
            df = pd.DataFrame(monster_page_data)
            df.to_csv(self.DEFAULT_MONSTER_DATA_PATH, index=False)

            logger.info(f"Scraped MONSTER DATA saved to {self.DEFAULT_MONSTER_DATA_PATH}")
            return df

    def scrape_quest_data(self) -> pd.DataFrame:
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
                    quest_soup = self.retrieve_soup(quest)

                    quest_title = quest_soup.select_one("span.lang-default.mh-lang[lang='en'] span").text.strip()

                    header = quest_soup.find("h1")
                    quest_category = header.find("span", class_=True).text.strip()
                    match = re.search(r"(?P<rank>[a-zA-Z]+)(?P<level>\d+)", quest_category)
                    quest_rank, quest_level = None, None
                    if match:
                        quest_rank = match.group("rank").upper()
                        quest_rank = "LR" if quest_rank == "VI" else quest_rank # transform Village quests to Low Rank
                        quest_level = match.group("level")

                    if quest_rank == "A":
                        logger.info(f"Quest {quest_title} skipped for ANOMALY QUEST.")
                        continue

                    basic_info = quest_soup.find("section", id="s-basic")
                    quest_reward = int(basic_info.find("span", string=re.compile("Reward money")).find_next_sibling("span").text.replace("z","").strip()) # HACK: use regex

                    target_section = quest_soup.find("section", id="s-stats")
                    target_table = target_section.find("tbody")

                    targets_hp_scaling = {
                        name_span.get_text().strip(): float(match.group(1))
                        for row in target_table.select("tr:has(div.mh-quest-monster > span.is-primary.tag)")
                        if (tag := row.select_one("div.mh-quest-monster > span.is-primary.tag")) and "Target" in tag.get_text()
                        if (name_span := row.select_one("span.lang-default.mh-lang[lang='en']")) is not None
                        if (match := next((m for td in row.find_all("td")[1:] if (m := re.search(r"x(\d+\.\d+)", td.get_text()))), None)) is not None
                    }

                    targets_with_hp = []
                    collected_targets = []
                    for target_monster in targets_hp_scaling.keys():
                        try:
                            relative_quest_rank = "lr" if quest_rank == "HR" else quest_rank.lower() #type:ignore

                            base_hp = self.monster_page_data.at[target_monster, f"{relative_quest_rank}_base_hp"] #type:ignore
                            hp_scaling = targets_hp_scaling.get(target_monster, 1)
                            target_hp = base_hp * hp_scaling #type:ignore

                            target_count = collected_targets.count(target_monster)
                            final_name = f"{target_monster}_{target_count}" if target_count else target_monster

                            collected_targets.append(target_monster)
                            targets_with_hp.append({final_name: target_hp})

                        except (KeyError, AttributeError) as e:
                            logger.warning(f"Error when calculating TARGET HP for {e}. Default at NONE...")

                    is_assigned = quest_title in self.key_quests

                    quest_info ={
                        "title": quest_title,
                        "rank": quest_rank,
                        "level": quest_level,
                        "reward": quest_reward,
                        "targets_with_hp": json.dumps(targets_with_hp),
                        "is_assigned": is_assigned
                    }
                    monster_quest_data.append(quest_info)
                    print(quest_info)

                except AttributeError:
                    logger.warning(f"Different data structure for {quest}! Skip entry...")

        df = pd.DataFrame(monster_quest_data)
        df.to_csv(self.DEFAULT_QUEST_DATA_PATH, index=False)

        logger.info(f"Scraped QUEST DATA saved to {self.DEFAULT_QUEST_DATA_PATH}")
        return df

    # main scraping section
    def scrape(self) -> List[QuestItem]:
        """ Get all quest info from mhrise.info."""
        rise_quest_info = []

        overview_soup = self.retrieve_soup(self.BASE_URL)
        monster_table = overview_soup.find("ul", class_="mh-list-monster")
        monster_links = [urljoin(self.BASE_URL, a["href"]) for a in monster_table.find_all("a", href=True) if a["href"]]

        for link in monster_links:
            try:
                monster_soup = self.retrieve_soup(link)
                monster_name = monster_soup.select_one('span.lang-default.mh-lang[lang="en"]').get_text(strip=True)
                #monster_base_hps = self.get_monster_page_info(monster_soup)
                monster_quests = self.get_quests_for_monster(monster_soup)

            except KeyboardInterrupt:
                logger.warning("Rise HP scraping manually interrupted.")
                return rise_quest_info

            except Exception as e:
                logger.warning(f"Failure for extracting {link}: {e}")

        return rise_quest_info