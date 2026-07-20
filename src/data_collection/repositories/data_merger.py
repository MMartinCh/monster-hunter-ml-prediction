import logging
import pandas as pd
from src.core import RankingScraperItem, MHWikiItem

logger = logging.getLogger(__name__)

class DataMerger():
    """Merges data from multiple DTOs into combined DF."""

    def merge(self, 
              ranking_data: list[RankingScraperItem] = None, 
              wiki_data: list[MHWikiItem] = None,
              ) -> pd.DataFrame:
        
        df_ranking = pd.DataFrame(ranking_data)
        df_wiki = pd.DataFrame(wiki_data)
        # add further dfs

        logger.info(f"Merging DFs...")

        return pd.merge(df_ranking, df_wiki, on="monster_name", how="outer")
