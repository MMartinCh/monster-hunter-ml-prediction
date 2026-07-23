import pytest
from bs4 import BeautifulSoup
from src.data_collection.scrapers import MHWikiScraper

def test_ranking_scraper_with_local_html(mocker):
    with open("tests/fixtures/sample_wiki.txt", "r", encoding="utf-8") as f:
        fake_html = f.read()
        
    scraper = MHWikiScraper()

    def dynamic_soup_mock(url=None, *args, **kwargs):
        if url is None or "Monster_List" in url:
            return BeautifulSoup(fake_html, "html.parser")
            
        monster_name = "Generic Monster"
        classification = "Bird Wyvern"
        if "Chatacabra" in url:
            monster_name = "Chatacabra"
            classification = "Amphibian"

        monster_info_html = f"""
        <table class="wikitable monster-game-info">
            <tr><td><span class="custom-gallery" data-monster="{monster_name}"></span></td></tr>
            <tr><th>Original</th><td>Monster Hunter Wilds</td></tr>
            <tr><th>Latest</th><td>Monster Hunter Wilds</td></tr>
            <tr><th>Classification</th><td>{classification}</td></tr>
            <tr><th>Elements</th><td><span typeof="mw:File"><a title="Fire"></a></span></td></tr>
            <tr><th>Status Effects</th><td><span typeof="mw:File"><a title="Poison"></a></span></td></tr>
            <tr><th>Weakest To</th><td><span typeof="mw:File"><a title="Water"></a></span></td></tr>
        </table>
        
        <table class="wikitable" align="right" style="margin: 0rem 0rem 1rem 1rem; max-width:450px; clear:both;">
            <tr><th>Length</th><td>1500.0 cm</td></tr>
            <tr><th>Height</th><td>400.0 cm</td></tr>
            <tr><th>Foot Size</th><td>100.0 cm</td></tr>
            <tr><th>Habitats</th><td>Header-Zeile</td></tr>
            <tr><td><a href="/wiki/Forest">Forest</a></td></tr>
        </table>
        
        <h3>Categories</h3>
        <div class="mw-portlet-body">
            <ul>
        """
        
        if "Berserk_Tetsucabra" in url:  
            monster_info_html += "<li>Subspecies</li>"
        elif "Drilltusk_Tetsucabra" in url:  
            monster_info_html += "<li>Variants</li>"
            
        monster_info_html += """
            </ul>
        </div>
        """
        return BeautifulSoup(monster_info_html, "html.parser")

    mocker.patch.object(scraper, "retrieve_soup", side_effect=dynamic_soup_mock)

    result = scraper.scrape()
    for i, entry in enumerate(result):
        print(f"{i}: {entry}")

        assert len(result) == 11
        assert result[1].monster_name == "Chatacabra"
        assert result[1].classification == "Amphibian"
        assert result[4].is_subspecies is True
        assert result[4].is_variant is False        
        assert result[5].is_subspecies is False
        assert result[5].is_variant is True
