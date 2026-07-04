from dataclasses import dataclass

@dataclass(frozen=True)
class RankingScraperItem:
    """DTO retrieved by RankingScraper."""
    monster_name: str
    rank: int