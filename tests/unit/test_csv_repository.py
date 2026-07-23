import pathlib
import pytest
from src.core.dataclasses.monster_data import MonsterData
from src.data_collection.repositories.csv_repository import LocalCsvRepository

def test_csv_repository_save_and_load(tmp_path):
    """Test that data can be serialized to CSV and deserialized accurately."""
    
    test_path = tmp_path
    test_file = "test_monsters.csv"

    repository = LocalCsvRepository(data_path=test_path, default_file_name=test_file)
    
    sample_monsters = [
        MonsterData(
            monster_name="Rathalos", 
            classification="Flying Wyvern", 
            first_appearance="Monster Hunter", 
            is_flagship=True, 
            elements=["Fire"], 
            rank=21
        )
    ]

    # Act: Save and then Load the data
    repository.save(sample_monsters)
    loaded_monsters = repository.load()

    # Assert: Verify the data matches perfectly
    assert len(loaded_monsters) == 1
    assert loaded_monsters[0].monster_name == "Rathalos"
    assert loaded_monsters[0].is_flagship is True
    assert "Fire" in loaded_monsters[0].elements
    assert loaded_monsters[0].rank == 21