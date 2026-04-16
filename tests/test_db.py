import pytest
from modules.db import Database


@pytest.fixture
def db():
    return Database(":memory:")


def test_create_session(db):
    session_id = db.create_session()
    assert isinstance(session_id, int)
    assert session_id > 0


def test_insert_lead(db):
    session_id = db.create_session()
    lead = {
        "siret": "12345678901234", "nom": "Jean Martin",
        "societe": "Martin & Associés", "secteur": "Expertise comptable",
        "ville": "Lyon", "email": "jean@martin.fr", "tel": "+33612345678",
        "score": 75, "priorite": 1, "signaux": ["Création récente"], "source": "SIRENE"
    }
    lead_id = db.insert_lead(session_id, lead)
    assert lead_id > 0


def test_get_leads_by_session(db):
    session_id = db.create_session()
    lead = {"siret": "111", "nom": "A", "societe": "B", "secteur": "C",
            "ville": "D", "email": "", "tel": "", "score": 50,
            "priorite": 2, "signaux": [], "source": "SIRENE"}
    db.insert_lead(session_id, lead)
    leads = db.get_leads_by_session(session_id)
    assert len(leads) == 1
    assert leads[0]["nom"] == "A"


def test_update_lead_status(db):
    session_id = db.create_session()
    lead_id = db.insert_lead(session_id, {"siret": "1", "nom": "X", "societe": "Y",
        "secteur": "Z", "ville": "W", "email": "", "tel": "",
        "score": 0, "priorite": 3, "signaux": [], "source": "SIRENE"})
    db.update_lead_status(lead_id, "sent")
    leads = db.get_leads_by_session(session_id)
    assert leads[0]["status"] == "sent"


def test_insert_and_get_conversations(db):
    session_id = db.create_session()
    lead_id = db.insert_lead(session_id, {"siret": "1", "nom": "X", "societe": "Y",
        "secteur": "Z", "ville": "W", "email": "", "tel": "",
        "score": 0, "priorite": 3, "signaux": [], "source": "SIRENE"})
    db.insert_conversation(lead_id, "email", "agent", "Bonjour !", 0)
    db.insert_conversation(lead_id, "email", "prospect", "Merci, intéressé.", 45)
    convs = db.get_conversations(lead_id)
    assert len(convs) == 2
    assert convs[0]["role"] == "agent"
    assert convs[1]["score_maturite"] == 45


def test_get_all_sessions(db):
    db.create_session()
    db.create_session()
    sessions = db.get_all_sessions()
    assert len(sessions) == 2


def test_update_session(db):
    session_id = db.create_session()
    db.update_session(session_id, nb_leads=150, nb_sent=42)
    sessions = db.get_all_sessions()
    assert sessions[0]["nb_leads"] == 150
    assert sessions[0]["nb_sent"] == 42
