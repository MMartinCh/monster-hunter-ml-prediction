from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from src.core.dataclasses.monster_data import MonsterData

class AbstractMonsterRepository[T](ABC):
    """Interface for saving and retrieving monster datasets."""
    ROOT_PATH = Path(__file__).resolve().parents[3]
    DATA_PATH = ROOT_PATH / "data"
    
    @abstractmethod
    def save(self, monsters: List[T]) -> None:
        """Persist a list of MonsterData objects."""
        pass

    @abstractmethod
    def load(self) -> List[T]:
        """Retrieve all persisted MonsterData objects."""
        pass