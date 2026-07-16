import itertools
import logging
import sys

from bs4 import BeautifulSoup
from typing import List

from src.core.dataclasses import RankingScraperItem
from src.core.interfaces import AbstractWebScraper

logger = logging.getLogger(__name__)

class RankingScraper(AbstractWebScraper[RankingScraperItem]):
    """Scrapes monster names and rankings from MH 20th anniversary website."""
    def __init__(self, url: str = "https://www.monsterhunter.com/20th/en/vote-monster/result/") -> None:
        self.url = url
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def scrape(self):
        logger.info("RankingScraper - initiate scraping...")

        monster_rankings = []

        soup = self.retrieve_soup()

        monster_rankings.extend(self.get_top_3())
        monster_rankings.extend(self.get_4_to_228(soup))

        logger.info(f"All Monster Ranks successfully scraped! {len(monster_rankings)} items scraped in total!")

        return monster_rankings
    
    def get_top_3(self) -> List[RankingScraperItem]:
        logger.info("Fetch Top 3...")

        top_3 = []

        top_3_data = [
            {"monster_name": "Zinogre", "rank": 1},
            {"monster_name": "Nergigante", "rank": 2},
            {"monster_name": "Lagiacrus", "rank": 3}
            ]
        
        for monster in top_3_data:
            top_3.append(RankingScraperItem(**monster))

        logger.info("Top 3 retrieved.")

        return top_3
    
    def get_4_to_228(self, soup: BeautifulSoup) -> List[RankingScraperItem]:
        logger.info("Scrape ranks 4 to 229...")

        top_4_to_bottom = []

        ranking = soup.find('div', class_ = 'ranking')

        li_top_20_tags = ranking.find_all('li', class_ = 'no-4-18')
        li_bottom_tags = ranking.find_all('li', class_ = 'no-img')

        for li in itertools.chain(li_top_20_tags, li_bottom_tags):
            name_div = li.find('div', class_ = 'name')
            rank_div = li.find('div', class_ = 'no')

            try:
                name = name_div.text.strip()
                rank = rank_div.text.split('.')[-1]

                rank_dict = {"monster_name": name, "rank": rank}
                rank_dict = RankingScraperItem(**rank_dict)
                
                top_4_to_bottom.append(rank_dict)

            except AttributeError:
                logger.warning(f"No text for scraped item Nr. {rank} found!")

        logger.info(f"Ranks 4 to 229 successfully scraped! {len(top_4_to_bottom)} items scraped.")

        return top_4_to_bottom