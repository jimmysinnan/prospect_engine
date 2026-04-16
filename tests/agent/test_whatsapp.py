# tests/agent/test_whatsapp.py
import pytest
from unittest.mock import patch, MagicMock
from modules.agent.channels.whatsapp import send_whatsapp, fetch_replies, _normalize_number

def test_normalize_number_adds_prefix():
    assert _normalize_number("+33612345678") == "whatsapp:+33612345678"

def test_normalize_number_keeps_existing_prefix():
    assert _normalize_number("whatsapp:+33612345678") == "whatsapp:+33612345678"

@patch("modules.agent.channels.whatsapp.Client")
@patch.dict("os.environ", {
    "TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "token",
    "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
})
def test_send_whatsapp_calls_twilio(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(sid="SM123")

    result = send_whatsapp("+33612345678", "Bonjour !")
    assert result == "SM123"
    mock_client.messages.create.assert_called_once()

@patch.dict("os.environ", {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""})
def test_send_whatsapp_raises_without_credentials():
    with pytest.raises(ValueError, match="TWILIO"):
        send_whatsapp("+33612345678", "Bonjour !")

@patch("modules.agent.channels.whatsapp.Client")
@patch.dict("os.environ", {
    "TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "token"
})
def test_fetch_replies_returns_list(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.messages.list.return_value = []

    result = fetch_replies()
    assert isinstance(result, list)

@patch.dict("os.environ", {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""})
def test_fetch_replies_returns_empty_without_credentials():
    result = fetch_replies()
    assert result == []
