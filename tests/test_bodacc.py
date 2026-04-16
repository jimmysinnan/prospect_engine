import pytest
from unittest.mock import patch, Mock
from modules.bodacc import get_signals_for_siret, enrich_leads

MOCK_BODACC_RESPONSE = {
    "records": [
        {"fields": {"typeavis_lib": "Vente et cession", "dateparution": "2024-01-15"}},
        {"fields": {"typeavis_lib": "Immatriculation", "dateparution": "2024-01-10"}},
    ]
}

@patch("modules.bodacc.requests.get")
def test_get_signals_cession(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_BODACC_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    signals = get_signals_for_siret("12345678901234")
    assert any("Cession" in s for s in signals)

@patch("modules.bodacc.requests.get")
def test_get_signals_creation(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "records": [{"fields": {"typeavis_lib": "Immatriculation"}}]
    }
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    signals = get_signals_for_siret("12345678901234")
    assert any("Création" in s for s in signals)

@patch("modules.bodacc.requests.get")
def test_get_signals_handles_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("timeout")
    signals = get_signals_for_siret("99999999999999")
    assert signals == []

@patch("modules.bodacc.requests.get")
def test_enrich_leads_adds_signals(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {"records": [
        {"fields": {"typeavis_lib": "Vente et cession"}}
    ]}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    leads = [{"siret": "12345678901234", "signaux": ["Création récente"]}]
    enriched = enrich_leads(leads)
    assert len(enriched[0]["signaux"]) > 1

@patch("modules.bodacc.requests.get")
def test_enrich_leads_skips_empty_siret(mock_get):
    leads = [{"siret": "", "signaux": []}]
    enriched = enrich_leads(leads)
    mock_get.assert_not_called()
    assert enriched[0]["signaux"] == []
