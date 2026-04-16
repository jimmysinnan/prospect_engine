# tests/agent/test_qualifier.py
import pytest
import json
from unittest.mock import patch, MagicMock
from modules.db import Database
from modules.agent.conversation import ConversationManager
from modules.agent.qualifier import qualify_response

@pytest.fixture
def db():
    return Database(":memory:")

@pytest.fixture
def setup(db):
    sid = db.create_session()
    lead_id = db.insert_lead(sid, {
        "siret": "1", "nom": "Jean Martin", "societe": "Martin SAS",
        "secteur": "Comptabilité", "ville": "Lyon", "email": "j@m.fr",
        "tel": "+336", "score": 70, "priorite": 1, "signaux": [], "source": "SIRENE"
    })
    manager = ConversationManager(db)
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    lead = db.get_leads_by_session(sid)[0]
    return lead, manager

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_returns_reply(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "action": "reply",
        "score_maturite": 45,
        "message": "Merci pour votre retour. Quelle est votre principale priorité ?",
        "raison": "Prospect intéressé mais besoin d'en savoir plus"
    }))]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Intéressé, dites m'en plus.", manager)
    assert result["action"] == "reply"
    assert result["score_maturite"] == 45
    assert isinstance(result["message"], str)

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_returns_propose_rdv(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "action": "propose_rdv",
        "score_maturite": 75,
        "message": "Parfait ! Voici mon lien : https://calendly.com/test",
        "raison": "Prospect qualifié"
    }))]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Oui je suis très intéressé.", manager)
    assert result["action"] == "propose_rdv"
    assert result["score_maturite"] >= 60

def test_qualify_archives_after_max_turns(db):
    sid = db.create_session()
    lead_id = db.insert_lead(sid, {
        "siret": "1", "nom": "X", "societe": "Y", "secteur": "Z", "ville": "W",
        "email": "", "tel": "", "score": 50, "priorite": 2, "signaux": [], "source": "SIRENE"
    })
    manager = ConversationManager(db)
    # Simulate 4 agent turns already done
    for i in range(4):
        manager.add_agent_reply(lead_id, "email", f"Message {i}", 30)

    lead = db.get_leads_by_session(sid)[0]
    result = qualify_response(lead, "Réponse", manager)
    assert result["action"] == "archive"

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_fallback_on_bad_json(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="invalid json")]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Intéressé.", manager)
    assert result["action"] in ("reply", "propose_rdv", "archive")
    assert "message" in result
