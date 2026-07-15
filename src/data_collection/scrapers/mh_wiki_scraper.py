import logging
import requests

from bs4 import BeautifulSoup
from pathlib import Path
from typing import List

from src.core.dataclasses.mh_wiki_item import MHWikiItem
from src.core.interfaces.abstract_wiki_scraper import AbstractWikiScraper
from src.data.repositories.csv_repository import LocalCsvRepository

logger = logging.getLogger(__name__)

class MHWikiScraper(AbstractWebScraper):
    def __init__(self,
                 monsters_to_scrape: List[str] = None,
                 url: str = r"https://monsterhunterwiki.org/wiki/Monster_List#Large_Monsters"
                 ):
        
        self.url = url
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

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

    def scrape_monster(self, url: str) -> MHWikiItem:
        pass
    
    def retrieve_soup(self) -> str:
            logger.info(f"Trying to connect to MH Wiki Monster Overview page: {self.url}")
            response = requests.get(self.url, headers= self.headers)

            if response.status_code == 200:
                logger.info(f"Request successfull: {response.status_code}")

                html = response.text

                return BeautifulSoup(html, "html.parser")
            
            else:
                logger.warning(f"Request failed!: {response.status_code}")
                return "Fail"
