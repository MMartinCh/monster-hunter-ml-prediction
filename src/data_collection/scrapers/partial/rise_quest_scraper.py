import logging
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.interfaces import AbstractWebScraper # type: ignore
from src.core.dataclasses import QuestItem # type: ignore

logger = logging.getLogger(__name__)

class RiseQuestScraper(AbstractWebScraper[QuestItem]):
    """Partial Scraper Class that scrapes quest data for MH Rise/ Sunbreak.
    To be called via QuestScraper class.
    """
    BASE_URL = r"https://mhrise.mhrice.info/monster.html"
    KEY_QUEST_URL = r"https://monsterhunterrise.wiki.fextralife.com/Hub+Quests"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key_quests: List[str] | None = None

    @property
    def key_quests(self) -> List[str]:
        if self._key_quests is None:
            self._key_quests = self._scrape_key_quests()
        return self._key_quests

    def _scrape_key_quests(self) -> List[str]:
        """Scrape all key quests from Fextralife Wiki, if not previously initiated."""
        soup = self.retrieve_soup(self.KEY_QUEST_URL)
        key_quest_tags = soup.select("p:has(img[title='key_quests_mhrise_wiki_guide_50px']) a")
        return [a.text.strip() for a in key_quest_tags if a.text.strip()]

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

    def get_monster_page_info(self, soup: BeautifulSoup) -> Dict[str, float|None]:
        # Get base hps
        base_hp_column = soup.find("span", string=re.compile("Base HP"))
        base_hp_info = base_hp_column.find_next_sibling("span").text.strip() #type:ignore

        hps_from_string = re.findall(r"(?<=R\) )\d+", base_hp_info)
        lr_base_hp, mr_base_hp = map(int, hps_from_string)

        # Get size
        size_column = soup.find("span", string="Size")
        size_info = size_column.find_next_sibling("span").text.strip() #type:ignore
        monster_size = float(size_info.split("(")[0])

        print(monster_size)

        return {
            "monster_size": monster_size or None,
            "lr_base_hp": lr_base_hp or None,
            "mr_base_hp": mr_base_hp or None
            }

    def get_quests_for_monster(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        monster_quest_data = []

        quest_section = soup.find("section", id="s-quest")
        quest_rows = quest_section.select("tr:not(.mh-non-target):not(.mh-hidden) a[href^='quest/']")
        quest_links = [urljoin(self.BASE_URL, a["href"]) for a in quest_rows if a.has_attr("href")]

        for link in quest_links:
            quest_data = {}
            quest_soup = self.retrieve_soup(link)

            quest_data["name"] = quest_soup.select_one("span.lang-default.mh-lang[lang='en'] span").text.strip()
            quest_data["is_assigned"] = quest_data["name"] in self.key_quests

            # TODO: scrape data from quest page - reward, hp,

            print(quest_data)
            monster_quest_data.append(quest_data)

        return monster_quest_data