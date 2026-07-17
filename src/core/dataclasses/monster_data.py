from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True) 
class MonsterData:
    """Domain model representing a single monster's raw and engineered traits."""
    monster_name: str

    # Meta data
    first_appearance: Optional[str] = None
    latest_appearance: Optional[str] = None
    generation: Optional[int] = None

    quest_levels: List[int] = field(default_factory=list)
    classification: Optional[str] = None

    is_flagship: Optional[bool] = False
    is_subspecies: Optional[bool] = False
    is_variant: Optional[bool] = False

    # Gameplay data
    difficulty: Optional[str] = None

    base_hp: Optional[int] = None
    size: Optional[float] = None
    weaknesses: List[str] = field(default_factory=list)
    elements: List[str] = field(default_factory=list)
    ailments: List[str] = field(default_factory=list)

    habitats: List[str] = field(default_factory=list)
    
    # Target variable (y)
    rank: Optional[int] = None


@dataclass(frozen=True)
class RankingScraperItem:
    """DTO retrieved by RankingScraper."""
    monster_name: str
    rank: int

@dataclass(frozen=True)
class MHWikiItem:
    """DTO retrieved from the Monster Hunter Wiki - Monster Overview site and recursive Monster links."""
    monster_name: str

    first_appearance: Optional[str] = None
    latest_appearance: Optional[str] = None

    classification: Optional[str] = None
    elements: List[str] = field(default_factory=list)
    ailments: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    size: Optional[float] = None
    habitats: List[str] = field(default_factory=list)

    is_flagship: Optional[bool] = False
    is_subspecies: Optional[bool] = False
    is_variant: Optional[bool] = False
    is_final_boss: Optional[bool] = False
    has_theme: Optional[bool] = False