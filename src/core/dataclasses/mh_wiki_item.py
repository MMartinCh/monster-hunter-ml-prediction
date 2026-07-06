from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class MHWikiItem:
    """DTO retrieved from the Monster Hunter Wiki - Monster Overview site and recursive Monster links."""
    monster_name: str
    first_appearance: str
    latest_appearance: str

    classification: str
    elements: List[str]
    status_effects: List[str]
    weaknesses: List[str]

    size: float
    habitats: List[str]

    is_subspecies: bool
    is_variant: bool
    is_flagship: bool