import logging
import sys

from pathlib import Path

from src.data_collection.scrapers import MHWikiScraper
from src.data_collection.scrapers.ranking_scraper import RankingScraper
from src.data_collection.repositories.csv_repository import LocalCsvRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    ranking_scraper = RankingScraper()
    wiki_scraper = MHWikiScraper()
    csv_repository = LocalCsvRepository(file_path=Path(r"C:\Users\Moritz\Desktop\mh_project\data"))

    wiki_soup = wiki_scraper.retrieve_soup()
    monster_links = wiki_scraper.get_monster_links(wiki_soup)

    example_entry = monster_links[1:10]
    print(example_entry)

    example_info = wiki_scraper.scrape()
    
    csv_repository.save(example_info)