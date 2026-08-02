import itertools
import logging
from functools import cached_property

import pandas as pd
from bs4 import BeautifulSoup
from typing import List

from src.core.dataclasses import RankingScraperItem #type:ignore
from src.core.interfaces import AbstractWebScraper #type:ignore
from src.core.helpers import file_cache #type:ignore

logger = logging.getLogger(__name__)

class RankingScraper(AbstractWebScraper[RankingScraperItem]):
    """Scrapes monster names and rankings from MH 20th anniversary website."""
    RANKING_URL = r"https://www.monsterhunter.com/20th/en/vote-monster/result/"

    DATA_PATH = AbstractWebScraper.DATA_PATH / "subsets" / "general"
    DEFAULT_PARTIAL_RANKING_PATH = DATA_PATH / "partial" / "partial_ranking_data.json"
    DEFAULT_RANKING_RESULTS_PATH = DATA_PATH / "ranking_data.csv"

    @property
    def top_3(self) -> List[RankingScraperItem]:
        return self._get_top_3()

    @cached_property
    @file_cache("DEFAULT_PARTIAL_RANKING_PATH")
    def ranks_4_to_228(self) -> List[RankingScraperItem]:
        return self._get_4_to_228()

    def scrape(self) -> List[RankingScraperItem]:
        logger.info("Start scraping Official Capcom Fan Ranking.")
        monster_rankings = []

        monster_rankings.extend(self.top_3)
        monster_rankings.extend(self.ranks_4_to_228)

        return monster_rankings
    
    def _get_top_3(self) -> List[RankingScraperItem]:
        top_3 = [
            {"monster_name": "Zinogre", "rank": 1},
            {"monster_name": "Nergigante", "rank": 2},
            {"monster_name": "Lagiacrus", "rank": 3}
            ]

        return [RankingScraperItem(**entry) for entry in top_3]
    
    def _get_4_to_228(self) -> List[RankingScraperItem]:
        top_4_to_bottom = []

        soup = self.retrieve_soup(self.RANKING_URL)
        ranking = soup.find('div', class_= 'ranking')

        li_top_20_tags = ranking.find_all('li', class_ = 'no-4-18')
        li_bottom_tags = ranking.find_all('li', class_ = 'no-img')

        for li in itertools.chain(li_top_20_tags, li_bottom_tags):
            name_div = li.find('div', class_ = 'name')
            rank_div = li.find('div', class_ = 'no')

            try:
                name = name_div.text.strip()
                rank = int(rank_div.text.split('.')[-1].strip())

                rank_dict = {"monster_name": name, "rank": rank}

                top_4_to_bottom.append(RankingScraperItem(**rank_dict))

            except AttributeError:
                logger.warning(f"No text for scraped item Nr. {rank} found!")

        logger.info(f"Ranks 4 to 229 successfully scraped! {len(top_4_to_bottom)} items scraped.")
        return top_4_to_bottom