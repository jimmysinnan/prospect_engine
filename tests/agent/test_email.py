import pytest
from unittest.mock import patch, MagicMock, call
from modules.agent.channels.email import send_email, _decode_header_str, _get_body

@patch("modules.agent.channels.email.smtplib.SMTP")
@patch.dict("os.environ", {
    "SMTP_HOST": "smtp.gmail.com", "SMTP_PORT": "587",
    "SMTP_USER": "test@gmail.com", "SMTP_PASS": "password"
})
def test_send_email_calls_smtp(mock_smtp_cls):
    mock_smtp = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

    result = send_email("prospect@example.com", "Test subject", "Bonjour !")
    assert result is True
    mock_smtp.send_message.assert_called_once()

@patch.dict("os.environ", {"SMTP_USER": "", "SMTP_PASS": ""})
def test_send_email_raises_without_credentials():
    with pytest.raises(ValueError, match="SMTP_USER"):
        send_email("to@example.com", "Subject", "Body")

def test_decode_header_str_plain():
    assert _decode_header_str("Hello World") == "Hello World"

def test_decode_header_str_encoded():
    # Encoded header (base64 UTF-8)
    encoded = "=?utf-8?b?Qm9uam91cg==?="
    assert _decode_header_str(encoded) == "Bonjour"

@patch("modules.agent.channels.email.imaplib.IMAP4_SSL")
@patch.dict("os.environ", {
    "IMAP_HOST": "imap.gmail.com",
    "SMTP_USER": "test@gmail.com",
    "SMTP_PASS": "password",
    "IMAP_FOLDER": "INBOX"
})
def test_fetch_replies_returns_list(mock_imap_cls):
    mock_imap = MagicMock()
    mock_imap_cls.return_value = mock_imap
    # No messages found
    mock_imap.search.return_value = ("OK", [b""])

    replies = fetch_replies_fn()
    assert isinstance(replies, list)

def fetch_replies_fn():
    from modules.agent.channels.email import fetch_replies
    return fetch_replies(since_hours=1)

@patch.dict("os.environ", {"SMTP_USER": "", "SMTP_PASS": ""})
def test_fetch_replies_returns_empty_without_credentials():
    from modules.agent.channels.email import fetch_replies
    result = fetch_replies()
    assert result == []
