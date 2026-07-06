import pathlib
import pytest
from src.core.dataclasses.monster_data import MonsterData
from src.data.repositories.csv_repository import LocalCsvRepository

def test_csv_repository_save_and_load(tmp_path):
    """Test that data can be serialized to CSV and deserialized accurately."""
    # Arrange: Setup a temporary path and sample data using pytest's tmp_path fixture
    test_file = tmp_path / "test_monsters.csv"
    repository = LocalCsvRepository(file_path=test_file)
    
    sample_monsters = [
        MonsterData(
            name="Rathalos", 
            species="Flying Wyvern", 
            generation=1, 
            is_flagship=True, 
            elements=["Fire"], 
            anniversary_rank=21
        )
    ]

    # Act: Save and then Load the data
    repository.save(sample_monsters)
    loaded_monsters = repository.load()

    # Assert: Verify the data matches perfectly
    assert len(loaded_monsters) == 1
    assert loaded_monsters[0].name == "Rathalos"
    assert loaded_monsters[0].is_flagship is True
    assert "Fire" in loaded_monsters[0].elements
    assert loaded_monsters[0].anniversary_rank == 21