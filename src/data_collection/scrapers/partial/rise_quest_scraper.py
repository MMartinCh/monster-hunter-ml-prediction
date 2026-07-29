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

    DEFAULT_MONSTER_INFO_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\monster_page_data.csv")
    DEFAULT_KEY_QUEST_PATH = Path(r"C:\Users\Martin\Desktop\monster-hunter-ml-prediction\data\subsets\rise\key_quests.txt")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def monster_base_hp_data(self) -> List[Dict[str,int]]:
        if self.DEFAULT_MONSTER_INFO_PATH.exists():
            df = pd.read_csv(self.DEFAULT_HP_PATH)
        else:
            df = self.get_monster_page_info()

        return df[["monster_name", "lr_base_hp", "mr_base_hp"]].to_dict(orient="records")

        
    def _get_monster_base_hp_data(self, file_path: Path = Path("default path")) -> List[Dict[str,int]]:
        if not file_path.exists():
            monster_base_hp_data = pd.read_csv()
        else:
            ... # TODO  add scraper code and save to csv at file path
        return monster_base_hp_data

    @cached_property
    def key_quests(self) -> List[str]:
        if self.DEFAULT_KEY_QUEST_PATH.exists():
            logger.info("Loading key_quests.txt from disc.")
            with open(self.DEFAULT_KEY_QUEST_PATH, "r", encoding="utf-8") as f:
                return [quest.strip() for quest in f]
            
        return self._scrape_key_quests()

    def _scrape_key_quests(self) -> List[str]:
        """Scrape all key quests from Fextralife Wiki, if not previously initiated and save."""
        logger.info(f"key_quests.txt not found in default directory. Scraping key quests...")
        soup = self.retrieve_soup(self.KEY_QUEST_URL)

        key_quest_tags = soup.select("p:has(img[title='key_quests_mhrise_wiki_guide_50px']) a")
        _key_quests = [a.text.strip() for a in key_quest_tags if a.text.strip()]

        self.DEFAULT_KEY_QUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DEFAULT_KEY_QUEST_PATH, "w", encoding="utf-8") as f:
            for quest in _key_quests:
                print(quest, file=f)

        return _key_quests 

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

    def get_monster_page_info(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Scrape all data from all data from Monster pages. Save to csv and return df."""
        monster_page_data = []
        monster_page_info = {}

        monster_overview_soup = self.retrieve_soup(self.BASE_URL)
        monster_table = monster_overview_soup.find("ul", class_="mh-list-monster")
        monster_links = [urljoin(self.BASE_URL, a["href"]) for a in monster_table.find_all("a", href=True) if a["href"]]

        for link in monster_links:
            monster_page_soup = self.retrieve_soup(link)

            monster_page_info["monster_name"] = ...

            base_hp_column = soup.find("span", string=re.compile("Base HP"))
            base_hp_info = base_hp_column.find_next_sibling("span").text.strip() #type:ignore
            hps_from_string = re.findall(r"(?<=R\) )\d+", base_hp_info)
            monster_page_info["lr_base_hp"] = int(hps_from_string[0])
            monster_page_info["mr_base_hp"] = int(hps_from_string[1])

            # Get size
            size_column = soup.find("span", string="Size")
            size_info = size_column.find_next_sibling("span").text.strip() #type:ignore
            monster_page_info["monster_size"] = float(size_info.split("(")[0])

            monster_page_data.append(monster_page_info)

            df = pd.DataFrame(monster_page_data)
            df.to_csv(self.DEFAULT_MONSTER_INFO_PATH)

        return df

    def get_quests_for_monster(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Get all quest links from specific Monster page and loop through each quest using get_quest_data-function."""
        monster_quest_data = []

        quest_section = soup.find("section", id="s-quest")
        quest_rows = quest_section.select("tr:not(.mh-non-target):not(.mh-hidden) a[href^='quest/']") #type:ignore
        quest_links = [a["href"].strip() for a in quest_rows if a.has_attr("href")] #type:ignore

        for relative_link in quest_links:
            link = urljoin(self.BASE_URL, relative_link)
            monster_quest_data.append(self.get_quest_data(link))

        return monster_quest_data

    def get_quest_data(self, link: str) -> Dict[str, Any]:
        """Extract complete quest data from individual quest page."""
        quest_soup = self.retrieve_soup(link)
        quest_data = {}

        quest_id_match = re.findall(r"\d+(?=.html)", link)
        quest_data["id"] = quest_id_match[0] if quest_id_match else None

        quest_data["name"] = quest_soup.select_one("span.lang-default.mh-lang[lang='en'] span").text.strip()
        quest_data["level"] = ...
        quest_data["rank"] = ...

        basic_info = quest_soup.find("section", id="s-basic")
        quest_data["map"] = ... 
        quest_data["requirement"] = ...
        quest_data["zenny"] = int(basic_info.find("span", string=re.compile("Reward money")).find_next_sibling("span").text.replace("z","").strip()) # HACK: use regex
        quest_data["village_points"] = int(basic_info.find("span", string=re.compile("Reward village point")).find_next_sibling("span").text.strip())
        quest_data["rank_points"] = int(basic_info.find("span", string=re.compile("Reward rank point")).find_next_sibling("span").text.strip())

        quest_data["targets"] = ...
        quest_data["target_hp"] = ...

        quest_data["is_assigned"] = quest_data["name"] in self.key_quests
        quest_data["is_event"] = ...

        print(quest_data)

        return quest_data