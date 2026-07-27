from typing import Any, Dict

from ....src.core.interfaces import AbstractWebScraper
from ....src.core.dataclasses import QuestItem

class PartialQuestScraper(AbstractWebScraper[QuestItem]):
    """Abstract Base Class for scrapers contributing to CompleteQuestScraper. 
    Adds helper class to convert dict to QuestItem dataclass format.
    """

    def convert_to_quest_item(self, data: Dict[str: Any]) -> QuestItem:
        """Helper to map processed dictionary data to a structured QuestItem dataclass."""
        return QuestItem(
            monster_name=data.get("monster_name"),
            total_game_appearances=data.get("game_appearances", 0),
            total_quest_appearances=data.get("quest_appearances", 0),    
            has_assignment=data.get("has_assignment", False),
            initial_quest=data.get("initial_quest"),
            lr_hp=data.get("lr_hp"),
            hr_hp=data.get("hr_hp"),               
            mr_hp=data.get("mr_hp"),
            lr_reward=data.get("lr_reward"),
            hr_reward=data.get("hr_reward"),               
            mr_reward=data.get("mr_reward")
        )