import csv
import pathlib
from typing import List
from src.core.interfaces.repository_interface import AbstractMonsterRepository
from src.core.dataclasses.monster_data import MonsterData

class LocalCsvRepository(AbstractMonsterRepository):
    """Handles persistence using flat CSV files."""
    
    def __init__(self, file_path: pathlib.Path):
        self.file_path = file_path / "mh_repository.csv"

    def save(self, monsters: List[MonsterData]) -> None:
        # Ensure the directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not monsters:
            return

        # Extract field names dynamically from the dataclass
        headers = list(monsters[0].__dict__.keys())

        with open(self.file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for monster in monsters:
                # Convert lists to comma-separated strings for CSV compatibility
                row = monster.__dict__.copy()
                #row["elements"] = ",".join(row["elements"])
                #row["ailments"] = ",".join(row["ailments"])
                writer.writerow(row)

    def load(self) -> List[MonsterData]:
        if not self.file_path.exists():
            return []

        monsters = []
        with open(self.file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                monsters.append(
                    MonsterData(
                        name=row["name"],
                        species=row["species"],
                        generation=int(row["generation"]),
                        is_flagship=row["is_flagship"] == "True",
                        elements=row["elements"].split(",") if row["elements"] else [],
                        ailments=row["ailments"].split(",") if row["ailments"] else [],
                        base_hp=int(row["base_hp"]) if row["base_hp"] else None,
                        anniversary_rank=int(row["anniversary_rank"]) if row["anniversary_rank"] else None,
                    )
                )
        return monsters