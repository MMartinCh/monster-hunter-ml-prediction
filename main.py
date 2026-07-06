import logging
import sys

from pathlib import Path

from src.data.scrapers.mh_wiki_scraper import MHWikiScraper
from src.data.scrapers.ranking_scraper import RankingScraper
from src.data.repositories.csv_repository import LocalCsvRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    ranking_scraper = RankingScraper()
    wiki_scraper = MHWikiScraper()

    csv_repository = LocalCsvRepository(Path(r"C:\Users\Moritz\Desktop\mh_project\data"))

    soup = wiki_scraper.retrieve_soup()

    print(soup)



    # ranking = ranking_scraper.scrape_ranking()
    # csv_repository.save(ranking)

    # for item in ranking:
    #     print(item)