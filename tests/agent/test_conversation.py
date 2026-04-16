import pytest
from modules.db import Database
from modules.agent.conversation import ConversationManager
from modules.agent.prompts import get_outreach_message


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture
def manager(db):
    return ConversationManager(db)


@pytest.fixture
def lead_id(db):
    sid = db.create_session()
    return db.insert_lead(sid, {
        "siret": "1", "nom": "Jean Martin", "societe": "Martin SAS",
        "secteur": "CGP", "ville": "Lyon", "email": "j@m.fr", "tel": "+336",
        "score": 75, "priorite": 1, "signaux": [], "source": "SIRENE"
    })


def test_start_conversation_creates_agent_message(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    convs = db.get_conversations(lead_id)
    assert len(convs) == 1
    assert convs[0]["role"] == "agent"
    assert convs[0]["canal"] == "email"


def test_start_conversation_sets_lead_status_sent(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    session_id = db.conn.execute(
        "SELECT session_id FROM leads WHERE id=?", (lead_id,)
    ).fetchone()[0]
    leads = db.get_leads_by_session(session_id)
    assert leads[0]["status"] == "sent"
    assert leads[0]["mode"] == "agent"


def test_add_prospect_reply(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    manager.add_prospect_reply(lead_id, "email", "Intéressé, dites m'en plus.")
    convs = db.get_conversations(lead_id)
    assert len(convs) == 2
    assert convs[1]["role"] == "prospect"


def test_get_turn_count(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Message 1")
    manager.add_prospect_reply(lead_id, "email", "Réponse 1")
    manager.add_agent_reply(lead_id, "email", "Message 2", score_maturite=40)
    assert manager.get_turn_count(lead_id) == 2


def test_format_history_for_prompt(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    manager.add_prospect_reply(lead_id, "email", "Bonjour, je suis intéressé.")
    history = manager.format_history_for_prompt(lead_id)
    assert "CGP:" in history
    assert "Prospect:" in history
    assert "Bonjour Jean," in history


def test_get_outreach_message_linkedin():
    msg = get_outreach_message("linkedin", "cgp", "Jean Martin", "CGP", "Lyon")
    assert "Jean Martin" in msg
    assert "Lyon" in msg


def test_get_outreach_message_email():
    msg = get_outreach_message("email", "cgp", "Sophie Dubois", "Comptabilité", "Paris")
    assert "Sophie Dubois" in msg
