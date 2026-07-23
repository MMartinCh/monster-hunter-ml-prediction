import re
import logging

from bs4 import BeautifulSoup
from typing import List

from src.core.interfaces import AbstractWebScraper
from src.core.dataclasses import WikiQuestItem

logger = logging.getLogger(__name__)

class KiranicoQuestScraper(AbstractWebScraper[WikiQuestItem]):
    """Scraper class to scrape quest info from Kiranico pages to different MH games from Wilds to Tri Ultimate."""
    
    def __init__(self, url: str = r"https://kiranico.com/"):
        self.url = url

    def scrape(self) -> List[WikiQuestItem]:
        pass

    def scrape_wilds(self):
        WILDS_URL = r"https://mhwilds.kiranico.com/data/quests"
        soup = self.retrieve_soup(WILDS_URL)
        rows = soup.find_all("tr", class_='"border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"')

        # Find unique monsters first
        unique_monsters = set()
        for row in rows:
            for a in row.find_all("a", href=re.compile(r"/data/monsters/")):
                unique_monsters.add(a.text)
        
        return unique_monsters


            
