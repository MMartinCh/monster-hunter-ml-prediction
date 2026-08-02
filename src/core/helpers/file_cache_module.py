import json
import logging
import pandas as pd
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)

def file_cache(path_attr: str, dataclass_cls: type | None = None, index_col: str | None = None):
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
                    case ".json":
                        with open(path, "w", encoding="utf-8") as f:
                            if dataclass_cls and hasattr(data[0], "__dataclass_fields__"):
                                import dataclasses
                                json_data = [dataclasses.asdict(item) for item in data]
                            else:
                                json_data = data
                            json.dump(json_data, f, indent=4, ensure_ascii=False)
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
                case ".json":
                    with open(path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                        if dataclass_cls:
                            return [dataclass_cls(**item) for item in raw_data]
                        return raw_data
                case ".csv":
                    return pd.read_csv(path, index_col=index_col)
                case ".txt":
                    with open(path, "r", encoding="utf-8") as f:
                        return [line.strip() for line in f]
                case _:
                    raise ValueError(f"Unsupported file format: {file_ending}")

        return wrapper
    return decorator            

