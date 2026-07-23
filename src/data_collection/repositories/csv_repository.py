import csv
import logging
import sys

import pandas as pd

from pathlib import Path
from typing import List, get_type_hints

from src.core.interfaces import AbstractMonsterRepository
from src.core.dataclasses import MonsterData

logger = logging.getLogger(__name__)

class LocalCsvRepository(AbstractMonsterRepository):
    """Handles persistence using flat CSV files."""
    
    def __init__(self, data_path: Path, default_file_name: str = "mh_repository.csv") -> None:
        self.DATA_PATH = data_path
        self.default_file_name = default_file_name

    def save(self, monsters: List[MonsterData] | pd.DataFrame, file_name: str = None) -> None:
        file_name = self.default_file_name if file_name is None else file_name
        file_path = self.DATA_PATH / file_name

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if type(monsters) is pd.DataFrame:
            monsters.to_csv(file_path, index=False)
            return

        monsters = [m for m in monsters if m is not None]        
        if not monsters:
            logger.warning("No monsters found for saving!")
            return

        # Extract field names dynamically from the dataclass
        headers = list(monsters[0].__dict__.keys())

        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for monster in monsters:    
                row = {
                    key: ", ".join(sorted(val)) if isinstance(val, list) else val 
                    for key, val in monster.__dict__.items()
                }
                writer.writerow(row)

        logger.info(f"Data successfully saved to: {file_path}!")

    def load(self, file_name: str = None) -> List[MonsterData]:
        file_name = self.default_file_name if file_name is None else file_name
        file_path = self.DATA_PATH / file_name

        logger.info(f"Loading data: {file_path}")

        monsters = []
        if not file_path.exists():
            return monsters

        type_hints = get_type_hints(MonsterData)

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                monster_kwargs = {}
                
                for field_name, expected_type in type_hints.items():
                    val = row.get(field_name)
                    
                    if val is None or val == "":
                        if "bool" in str(expected_type):
                            monster_kwargs[field_name] = False
                        elif "list" in str(expected_type).lower():
                            monster_kwargs[field_name] = []
                        else:
                            monster_kwargs[field_name] = None
                        continue

                    type_str = str(expected_type).lower()
                    
                    if "list" in type_str:
                        clean_items = [item.strip() for item in val.split(",") if item.strip()]
                        if "int" in type_str:
                            monster_kwargs[field_name] = [int(i) for i in clean_items if i.isdigit()]
                        elif "float" in type_str:
                            monster_kwargs[field_name] = [float(i) for i in clean_items]
                        else:
                            monster_kwargs[field_name] = clean_items
                            
                    elif "bool" in type_str:
                        monster_kwargs[field_name] = val.lower() in ("true", "1", "yes")
                        
                    elif "int" in type_str:
                        monster_kwargs[field_name] = int(val) if val.isdigit() else None
                        
                    elif "float" in type_str:
                        try:
                            monster_kwargs[field_name] = float(val)
                        except ValueError:
                            monster_kwargs[field_name] = None
                            
                    else:
                        monster_kwargs[field_name] = val

                monsters.append(MonsterData(**monster_kwargs))

        return monsters
