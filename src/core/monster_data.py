from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True) 
class MonsterData:
    """Domain model representing a single monster's raw and engineered traits."""
    name: str
    species: str
    generation: int
    is_flagship: bool
    elements: List[str] = field(default_factory=list)
    ailments: List[str] = field(default_factory=list)
    base_hp: Optional[int] = None
    
    # Target variable (y)
    anniversary_rank: Optional[int] = None