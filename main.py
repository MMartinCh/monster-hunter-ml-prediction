import logging
import sys
from pathlib import Path

from src.data_collection.scrapers.partial import FUQuestScraper, GenerationsQuestScraper, RiseQuestScraper, WorldQuestScraper, WildsQuestScraper # type: ignore
from src.data_collection.scrapers import MHWikiScraper, RankingScraper, CompleteQuestScraper
from src.data_collection.scrapers.ranking_scraper import RankingScraper
from src.data_collection.repositories import DataMerger, LocalCsvRepository

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # Initiate classes
    DATA_PATH = Path(__file__).resolve().parent/ "data"
    MODE = "TEST"

    logger.info(f"Start session | Data Path: {DATA_PATH} | Mode: {MODE}")

    repository = LocalCsvRepository()
    merger = DataMerger()
    ranking_scraper = RankingScraper()
    wiki_scraper = MHWikiScraper()
    #quest_scraper = CompleteQuestScraper()

    # Get Data: Scraping or Loading
    match MODE:
        case "SCRAPE":
            ranking_data = ranking_scraper.scrape()
            wiki_data = wiki_scraper.scrape()
            quest_data = quest_scraper.scrape()

            repository.save(ranking_data, "ranking_data.csv")
            repository.save(wiki_data, "wiki_data.csv")
            repository.save(quest_data, "quest_data.csv")
    
        case "LOAD":
            ranking_data = repository.load("ranking_data.csv")
            wiki_data = repository.load("wiki_data.csv")

        case "TEST":

            test_scraper = FUQuestScraper()
            test_data = test_scraper.monster_data
            
            print("Test Results")
            print("="*30)
            for i, data in enumerate(test_data):
                print(i, ": ", data)

            #repository.save(test_data, file_name="gu_test_data.csv")

    # Merge data
    #merged_data = merger.merge(ranking_data, wiki_data)

    # Save data