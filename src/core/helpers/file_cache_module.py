import logging
import pandas as pd
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)

def file_cache(path_attr: str, index_col: str | None = None):
    def decorator(scrape_func):
        @wraps(scrape_func)
        def wrapper(self):
            path: Path = getattr(self, path_attr)
            data_name = path.stem.upper()
            file_ending = path.suffix

            if not path.exists():
                logger.info(f"{data_name} not found at {path}! Start scraping...")

                data = scrape_func(self)

                path.parent.mkdir(parents=True, exist_ok=True)
                match file_ending:
                    case ".csv":
                        data.to_csv(path, index=False)
                    case ".txt":
                        with open(path, "w", encoding="utf-8") as f:
                            for item in data:
                                print(item, file=f)
                    case _:
                        logger.warning(f"Unknown file ending {file_ending}. Data not saved.")

                logger.info(f"{data_name} succesfully scraped! Saving to {path}.")
                return data

            logger.info(f"Reading {data_name} from disk at {path}.")
            match file_ending:
                case ".csv":
                    return pd.read_csv(path, index_col=index_col)
                case ".txt":
                    with open(path, "r", encoding="utf-8") as f:
                        return [line.strip() for line in f]
                case _:
                    raise ValueError(f"Unsupported file format: {file_ending}")

        return wrapper
    return decorator            

