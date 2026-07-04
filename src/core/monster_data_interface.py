from abc import ABC, abstractmethod
from typing import List
from src.core.monster_data import MonsterData

class AbstractMonsterRepository(ABC):
    """Interface for saving and retrieving monster datasets."""
    
    @abstractmethod
    def save(self, monsters: List[MonsterData]) -> None:
        """Persist a list of MonsterData objects."""
        pass

    @abstractmethod
    def load(self) -> List[MonsterData]:
        """Retrieve all persisted MonsterData objects."""
        pass