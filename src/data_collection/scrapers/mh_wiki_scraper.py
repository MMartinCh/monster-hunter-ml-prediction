import logging
import re

from bs4 import BeautifulSoup
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from src.core.dataclasses import MHWikiItem
from src.core.interfaces import AbstractWebScraper

logger = logging.getLogger(__name__)

class MHWikiScraper(AbstractWebScraper[MHWikiItem]):
    def __init__(self, 
                 monsters_to_scrape: List[str] = None, 
                 url: str = r"https://monsterhunterwiki.org/wiki/Monster_List"
                 ):
        
        super().__init__(url = url)
        self.monsters_to_scrape = monsters_to_scrape

    def scrape(self) -> List[MHWikiItem]:
        wiki_data = []
        
        soup = self.retrieve_soup()

        if not self.monsters_to_scrape:
             ...

        for monster in self.monsters_to_scrape:
            monster_link = soup.find(monster)
            monster_data = self.scrape_monster(monster_link)

            wiki_data.append(monster_data)
            
        return wiki_data

    def get_monster_info(self, soup: BeautifulSoup) -> MHWikiItem:
        info_table = soup.find("table", class_ = "wikitable monster-game-info")

        monster_info = {}

        monster_info["monster_name"] = info_table.find("span", class_ = "custom-gallery").get("data-monster").strip()
        
        for attribute in ["Original", "Latest", "Classification"]:
            row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
            monster_info[attribute.lower()] = row.find("td").text.strip()

        for attribute in ["Elements", "Status Effects", "Weakest To"]:
            row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
            containers = row.find_all("span", typeof="mw:File")
            monster_info[attribute.lower()] = [c.find("a").get("title").strip() for c in containers]

        size_table = soup.find("table", class_="wikitable", align="right", style="margin: 0rem 0rem 1rem 1rem; max-width:450px; clear:both;")
        print(size_table)

        size_dimensions = []
        for attribute in ["Length", "Height", "Foot Size"]:
            row = size_table.find("th", string=re.compile(attribute)).find_parent("tr")
            size_dimensions.append(row.find("td").text)
        monster_info["size"] = size_dimensions

        row_habitats = size_table.find("th", string=re.compile("Habitats")).find_parent("tr").find_next_sibling("tr")
        print(row_habitats)
        monster_info["habitats"] = [h.text.strip() for h in row_habitats.find_all("a")]

        return MHWikiItem(*monster_info.values())

    def get_monster_links(self, soup: BeautifulSoup) -> List[str]:
        logger.info("Extracting Monster Links from soup...")
        
        base_url = "https://monsterhunterwiki.org"
        start_headline = soup.find("span", class_="mw-headline", id="Large_Monsters")

        if not start_headline:
            logger.warning("Start headline not found!")
            return []
        
        logger.info(f"Start headline found: {start_headline}")

        start_h2 = start_headline.find_parent("h2")
        scrape_range = []
        for sibling in start_h2.next_siblings:
            if sibling.name == "h2":
                break
            if sibling.name is not None:
                scrape_range.append(sibling)

        monster_urls = []
        pattern = re.compile(r"^/wiki/(?!(?:MH[a-zA-Z0-9]*)(?:$|_))([^:]+)$")

        for el in scrape_range:
            a_tag = el.find("a", href=pattern)
            relative_link = a_tag["href"]
            full_link = f"{base_url}{relative_link}"
            
            if full_link not in monster_urls:
                monster_urls.append(full_link)

        logger.info(f"Monster urls extracted! {len(monster_urls)} elements found.")
    
        return monster_urls