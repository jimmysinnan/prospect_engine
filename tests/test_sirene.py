import pytest
from unittest.mock import patch, Mock
from modules.sirene import search_companies, _parse_company, _match_taille

MOCK_API_RESPONSE = {
    "results": [
        {
            "nom_complet": "MARTIN & ASSOCIES CONSEIL",
            "activite_principale": "6630Z",
            "activite_principale_libelle": "Gestion de fonds",
            "date_creation": "2024-03-15",
            "tranche_effectif_salarie": "11",
            "dirigeants": [{"prenoms": "Jean", "nom": "Martin"}],
            "siege": {
                "siret": "12345678901234",
                "libelle_commune": "Lyon",
                "departement": "69",
                "adresse": "10 rue de la Paix, 69006 Lyon"
            }
        }
    ],
    "total_results": 1
}

def test_parse_company_returns_expected_fields():
    item = MOCK_API_RESPONSE["results"][0]
    company = _parse_company(item)
    assert company["siret"] == "12345678901234"
    assert company["societe"] == "MARTIN & ASSOCIES CONSEIL"
    assert company["ville"] == "Lyon"
    assert company["nom"] == "Jean Martin"
    assert company["source"] == "SIRENE"
    assert isinstance(company["anciennete_mois"], int)

def test_parse_company_missing_siege_returns_none():
    result = _parse_company({"nom_complet": "Test", "siege": {}})
    assert result is None

def test_match_taille_tpe():
    assert _match_taille("NN", "0") is True
    assert _match_taille("01", "0") is True
    assert _match_taille("11", "0") is False

def test_match_taille_pme():
    assert _match_taille("11", "1") is True
    assert _match_taille("21", "1") is True
    assert _match_taille("31", "1") is False

def test_match_taille_unknown_code():
    assert _match_taille("99", "0") is False

@patch("modules.sirene.requests.get")
def test_search_companies_returns_list(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_API_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    results = search_companies(secteur="gestion de fonds", departement="69", nb=1)
    assert len(results) == 1
    assert results[0]["siret"] == "12345678901234"

@patch("modules.sirene.requests.get")
def test_search_companies_handles_api_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("timeout")
    results = search_companies(secteur="test", nb=10)
    assert results == []

@patch("modules.sirene.requests.get")
def test_search_companies_filters_by_age(mock_get):
    mock_resp = Mock()
    old_item = {**MOCK_API_RESPONSE["results"][0], "date_creation": "2022-01-01"}
    mock_resp.json.return_value = {"results": [old_item], "total_results": 1}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    results = search_companies(secteur="test", nb=10, age_max_mois=12)
    assert results == []
