import logging
import sys

from pathlib import Path

from src.data_collection.scrapers import MHWikiScraper, RankingScraper, KiranicoScraper
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
    MODE = "TEST"

    logger.info(f"Start session | Data Path: {DATA_PATH} | Mode: {MODE}")

    repository = LocalCsvRepository(DATA_PATH)
    merger = DataMerger()
    ranking_scraper = RankingScraper()
    wiki_scraper = MHWikiScraper()
    kiranico_scraper = KiranicoScraper()

    # Get Data: Scraping or Loading
    match MODE:
        case "SCRAPE":
            ranking_data = ranking_scraper.scrape()
            wiki_data = wiki_scraper.scrape()
            kiranico_data = kiranico_scraper.scrape()

            repository.save(ranking_data, "ranking_data.csv")
            repository.save(wiki_data, "wiki_data.csv")
            repository.save(kiranico_data, "kiranico_data.csv")
    
        case "LOAD":
            ranking_data = repository.load("ranking_data.csv")
            wiki_data = repository.load("wiki_data.csv")

        case "TEST":
            test_data = kiranico_scraper.scrape_worlds()
            for i, monster in enumerate(test_data):
                print(f"{i+1}: {monster}")

            #repository.save(test_data, "kiranico_test.csv")

    # Merge data
    #merged_data = merger.merge(ranking_data, wiki_data)

    # Save data
    #repository.save(merged_data, file_name="attempt_merge.csv")