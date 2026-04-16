import pytest
from unittest.mock import patch, MagicMock
from modules.google_maps import (
    search_places, _normalize_phone, _extract_city,
    _extract_departement, _types_to_label, _parse_place
)


def test_normalize_phone_international():
    assert _normalize_phone("+596 696 12 34 56") == "+596696123456"


def test_normalize_phone_empty():
    assert _normalize_phone("") == ""


def test_extract_city_standard():
    assert _extract_city("12 Rue Schoelcher, 97200 Fort-de-France, Martinique") == "Fort-de-France"


def test_extract_city_fallback():
    assert _extract_city("Some Place, Paris, France") == "Paris"


def test_extract_departement_972():
    assert _extract_departement("5 rue Victor Hugo, 97200 Fort-de-France, Martinique") == "972"


def test_extract_departement_75():
    assert _extract_departement("10 rue de Rivoli, 75001 Paris, France") == "75"


def test_types_to_label_known():
    assert _types_to_label(["accounting", "establishment"]) == "Expertise comptable"


def test_types_to_label_unknown():
    label = _types_to_label(["notary", "establishment"])
    assert isinstance(label, str) and len(label) > 0


def test_parse_place_builds_lead():
    place = {
        "place_id": "abc",
        "name": "Cabinet Dupont",
        "formatted_address": "5 rue X, 97200 Fort-de-France, Martinique",
        "types": ["accounting", "establishment"],
        "business_status": "OPERATIONAL",
        "rating": 4.5,
        "user_ratings_total": 12,
    }
    detail = {
        "name": "Cabinet Dupont",
        "international_phone_number": "+596 696 00 11 22",
        "website": "https://cabinet-dupont.fr",
        "formatted_address": "5 rue X, 97200 Fort-de-France, Martinique",
        "types": ["accounting", "establishment"],
    }
    lead = _parse_place(place, detail)
    assert lead["societe"] == "Cabinet Dupont"
    assert lead["tel"] == "+596696001122"
    assert lead["website"] == "https://cabinet-dupont.fr"
    assert lead["source"] == "Google Maps"
    assert lead["ville"] == "Fort-de-France"
    assert lead["departement"] == "972"


@patch("modules.google_maps.requests.get")
@patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": "test-key"})
def test_search_places_returns_leads(mock_get):
    # Mock text search response
    search_response = MagicMock()
    search_response.json.return_value = {
        "status": "OK",
        "results": [
            {
                "place_id": "place1",
                "name": "Cabinet Martin",
                "formatted_address": "1 rue X, 97200 Fort-de-France, Martinique",
                "types": ["accounting"],
                "business_status": "OPERATIONAL",
                "rating": 4.2,
                "user_ratings_total": 8,
            }
        ],
    }
    search_response.raise_for_status = MagicMock()

    # Mock details response
    detail_response = MagicMock()
    detail_response.json.return_value = {
        "result": {
            "name": "Cabinet Martin",
            "international_phone_number": "+596 596 60 12 34",
            "website": "https://cabinet-martin.fr",
            "formatted_address": "1 rue X, 97200 Fort-de-France, Martinique",
            "types": ["accounting"],
        }
    }
    detail_response.raise_for_status = MagicMock()

    mock_get.side_effect = [search_response, detail_response]

    leads = search_places("expert comptable", "Martinique", nb=5)
    assert len(leads) == 1
    assert leads[0]["tel"] == "+596596601234"
    assert leads[0]["source"] == "Google Maps"


@patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": ""})
def test_search_places_raises_without_api_key():
    with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
        search_places("comptable", "Paris", nb=5)
