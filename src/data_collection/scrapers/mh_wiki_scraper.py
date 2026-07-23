import logging
import re
import beepy

from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

from src.core.dataclasses import MHWikiItem
from src.core.interfaces import AbstractWebScraper

logger = logging.getLogger(__name__)

class MHWikiScraper(AbstractWebScraper[MHWikiItem]):
    def __init__(self, 
                 monsters_to_scrape: Optional[List[str]] = None, 
                 url: str = r"https://monsterhunterwiki.org/wiki/Monster_List"
                 ):
        
        super().__init__(url = url)
        self.monsters_to_scrape = monsters_to_scrape

    def scrape(self) -> List[MHWikiItem]:
        soup = self.retrieve_soup()
        scraping_monsters = self.monsters_to_scrape if self.monsters_to_scrape else self.get_monster_links(soup)

        logger.info("Start scraping from MH Wiki.")

        wiki_data = []
        try:
            for relative_link in scraping_monsters:
                monster_data = self.get_monster_info(relative_link)
                if monster_data is not None:
                    wiki_data.append(monster_data)
            
            logger.info(f"MH Wiki successfully scraped! {len(wiki_data)} entries collected.")
            return wiki_data
            
        except KeyboardInterrupt:
            logger.warning(f"Manually interrupted with keybord interrupt!")
            return wiki_data

    def get_monster_info(self, link: str) -> MHWikiItem:
        soup = self.retrieve_soup(f"https://monsterhunterwiki.org/{link}")

        name_from_link = link.split("/")[-1]
        monster_info = {}

        try:
            info_table = soup.find("table", class_ = "wikitable monster-game-info")

            monster_info["monster_name"] = info_table.find("span", class_ = "custom-gallery").get("data-monster").strip()
            
            for attribute in ["Original", "Latest", "Classification"]:
                row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
                monster_info[attribute.lower()] = row.find("td").text.strip()

            for attribute in ["Elements", "Status Effects", "Weakest To"]:
                row = info_table.find("th", string=re.compile(attribute)).find_parent("tr")
                containers = row.find_all("span", typeof="mw:File")
                monster_info[attribute.lower()] = [c.find("a").get("title").strip() for c in containers]

            size_table = soup.find("table", class_="wikitable", align="right", style="margin: 0rem 0rem 1rem 1rem; max-width:450px; clear:both;")

            size_dimensions = []
            for attribute in ["Length", "Height", "Foot Size"]:
                row = size_table.find("th", string=re.compile(attribute)).find_parent("tr")
                size_dimensions.append(row.find("td").text)
            monster_info["size"] = size_dimensions

            row_habitats = size_table.find("th", string=re.compile("Habitats")).find_parent("tr").find_next_sibling("tr")
            monster_info["habitats"] = [h.text.strip() for h in row_habitats.find_all("a")]

            label_header = soup.find("h3", string="Categories")
            label_table = label_header.find_next_sibling("div", class_="mw-portlet-body")
            labels = [label.text for label in label_table.find_all("li")]
            for label in ["Flagship Monsters", "Subspecies", "Variants", "Deviants", "Rare Species", "Collaboration Monsters", "Final Boss Monsters", "Monsters with Themes"]:
                monster_info[label] = label in labels
            
            logger.info(f"Data successfully scraped for {name_from_link}")
            
            return MHWikiItem(
                monster_name=monster_info.get("monster_name"),
                first_appearance=monster_info.get("original"),
                latest_appearance=monster_info.get("latest"),
                classification=monster_info.get("classification"),
                elements=monster_info.get("elements", []),
                ailments=monster_info.get("status effects", []),
                weaknesses=monster_info.get("weakest to", []),
                size=monster_info["size"],
                habitats=monster_info.get("habitats", []),
                is_flagship=monster_info.get("Flagship Monsters", False),
                is_subspecies=monster_info.get("Subspecies", False),
                is_variant=monster_info.get("Variants", False),
                is_deviant=monster_info.get("Deviants", False),
                is_rare_species=monster_info.get("Rare Species", False),
                is_collaboration=monster_info.get("Collaboration Monsters", False),
                is_final_boss=monster_info.get("Final Boss Monsters", False),
                has_theme=monster_info.get("Monsters with Themes", False)
            )

        except AttributeError as e:
            logger.warning(f"Attribute not found: {e}. Article suspected as category headline: {name_from_link}")

    def get_monster_links(self, soup: BeautifulSoup) -> List[str]:
        logger.info("Extracting Monster Links from MH Wiki...")
        
        start_headline = soup.find("span", class_="mw-headline", id="Large_Monsters")

        if not start_headline:
            logger.warning("Start headline not found!")
            return []
        
        logger.debug(f"Start headline found: {start_headline}")

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
            
            if relative_link not in monster_urls:
                monster_urls.append(relative_link)

        logger.debug(f"Monster urls extracted! {len(monster_urls)} elements found.")
    
        return monster_urls