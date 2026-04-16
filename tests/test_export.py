import pytest
from modules.export import leads_to_csv

SAMPLE_LEADS = [
    {
        "score": 82, "nom": "Jean Martin", "societe": "Martin Conseil",
        "secteur": "Gestion de fonds", "ville": "Lyon", "siret": "12345678901234",
        "email": "jean@martin.fr", "tel": "+33612345678", "source": "SIRENE",
        "anciennete_mois": 8, "signaux": ["Création récente"], "status": "new",
        "message_linkedin": "Bonjour Jean,", "message_email": "Objet: ..."
    },
    {
        "score": 45, "nom": "Sophie Dubois", "societe": "Dubois SAS",
        "secteur": "Comptabilité", "ville": "Paris", "siret": "98765432109876",
        "email": "", "tel": "", "source": "Bodacc",
        "anciennete_mois": 24, "signaux": [], "status": "sent",
        "message_linkedin": "", "message_email": ""
    }
]

def test_leads_to_csv_returns_bytes():
    result = leads_to_csv(SAMPLE_LEADS)
    assert isinstance(result, bytes)

def test_leads_to_csv_contains_headers():
    result = leads_to_csv(SAMPLE_LEADS).decode("utf-8-sig")
    assert "Score" in result
    assert "Nom" in result
    assert "SIRET" in result

def test_leads_to_csv_contains_data():
    result = leads_to_csv(SAMPLE_LEADS).decode("utf-8-sig")
    assert "Jean Martin" in result
    assert "82" in result
    assert "Lyon" in result

def test_leads_to_csv_handles_list_signals():
    lead = {**SAMPLE_LEADS[0], "signaux": ["Signal A", "Signal B"]}
    result = leads_to_csv([lead]).decode("utf-8-sig")
    assert "Signal A" in result

def test_leads_to_csv_handles_json_string_signals():
    lead = {**SAMPLE_LEADS[0], "signaux": '["Signal A", "Signal B"]'}
    result = leads_to_csv([lead]).decode("utf-8-sig")
    assert "Signal A" in result

def test_leads_to_csv_empty_list():
    result = leads_to_csv([])
    assert isinstance(result, bytes)
