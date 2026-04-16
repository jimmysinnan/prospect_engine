import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from modules.scoring import score_lead, score_leads_batch, SYSTEM_PROMPT

MOCK_LEAD = {
    "siret": "12345678901234",
    "societe": "Martin & Associés Conseil",
    "secteur": "Gestion de fonds",
    "ville": "Lyon",
    "anciennete_mois": 8,
    "signaux": ["Création récente (Bodacc)"],
    "effectifs_code": "11",
}

MOCK_AI_RESPONSE = {
    "score": 82,
    "signaux": ["Création récente", "Potentiel patrimonial fort"],
    "message_linkedin": "Bonjour,\n\nVotre cabinet à Lyon a retenu mon attention.\n\nDisponible 20 min ?",
    "message_email": "Bonjour,\n\nJe vous contacte concernant votre situation patrimoniale.\n\nCordialement",
    "priorite": 1,
    "raison": "Entreprise récente avec CA potentiel significatif dans un secteur favorable."
}

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_returns_expected_fields(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(MOCK_AI_RESPONSE))]
    mock_client.messages.create.return_value = mock_message

    result = score_lead(MOCK_LEAD)

    assert result["score"] == 82
    assert result["priorite"] == 1
    assert "message_linkedin" in result
    assert "message_email" in result
    assert isinstance(result["signaux"], list)

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_merges_existing_signals(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        **MOCK_AI_RESPONSE, "signaux": ["Signal IA"]
    }))]
    mock_client.messages.create.return_value = mock_message

    lead = {**MOCK_LEAD, "signaux": ["Bodacc signal"]}
    result = score_lead(lead)
    assert "Bodacc signal" in result["signaux"]
    assert "Signal IA" in result["signaux"]

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_fallback_on_invalid_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not json")]
    mock_client.messages.create.return_value = mock_message

    result = score_lead(MOCK_LEAD)
    assert result["score"] == 30
    assert "message_linkedin" in result

def test_score_lead_raises_without_api_key():
    import os
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            score_lead(MOCK_LEAD)

@patch("modules.scoring.score_lead")
def test_score_leads_batch_calls_progress(mock_score):
    mock_score.side_effect = lambda l, p=None: {**l, "score": 50, "priorite": 2,
        "signaux": [], "message_linkedin": "", "message_email": "", "raison": ""}
    leads = [MOCK_LEAD.copy(), MOCK_LEAD.copy()]
    progress_calls = []
    score_leads_batch(leads, progress_callback=lambda i, t: progress_calls.append((i, t)))
    assert progress_calls == [(1, 2), (2, 2)]
