import pathlib
import pytest

from src.data_collection.scrapers.ranking_scraper import RankingScraper

def test_ranking_scraper_with_local_html(mocker):
    with open("tests/fixtures/sample_ranking.txt", "r", encoding="utf-8") as f:
        fake_html = f.read()
        
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.text = fake_html
    
    mocker.patch("src.core.interfaces.abstract_web_scraper.requests.get", return_value=mock_response)
    
    scraper = RankingScraper(url="https://fake-capcom-site.com")
    result = scraper.scrape()
    
    assert len(result) == 20
    assert result[0].monster_name == "Zinogre"
    assert result[0].rank == 1
    assert result[-1].monster_name == "Crimson Glow Valstrax"
    assert result[-1].rank == 20