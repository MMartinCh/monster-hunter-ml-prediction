import logging
import sys

from pathlib import Path

from src.data_collection.scrapers import MHWikiScraper
from src.data_collection.scrapers.ranking_scraper import RankingScraper
from src.data_collection.repositories import DataMerger, LocalCsvRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # Initiate classes
    DATA_PATH = Path(__file__).resolve().parent/"data"
    MODE = "LOAD"

    logger.info(f"Start session | Data Path: {DATA_PATH} | Mode: {MODE}")

    repository = LocalCsvRepository(DATA_PATH)
    merger = DataMerger()
    ranking_scraper = RankingScraper()
    wiki_scraper = MHWikiScraper()

    # Get Data: Scraping or Loading
    if MODE == "SCRAPE":
        ranking_data = ranking_scraper.scrape()
        wiki_data = wiki_scraper.scrape()

        repository.save(ranking_data, "ranking_data.csv")
        repository.save(wiki_data, "wiki_data.csv")
    
    else:
        ranking_data = repository.load("ranking_data.csv")
        wiki_data = repository.load("wiki_data.csv")

    # Merge data
    merged_data = merger.merge(ranking_data, wiki_data)

    # Save data
    repository.save(merged_data, file_name="attempt_merge.csv")