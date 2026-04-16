import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def send_whatsapp(to_number, message):
    """Send a WhatsApp message via Twilio. Returns message SID."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID et TWILIO_AUTH_TOKEN requis dans .env")

    client = Client(account_sid, auth_token)
    msg = client.messages.create(
        body=message,
        from_=from_number,
        to=_normalize_number(to_number)
    )
    return msg.sid


def fetch_replies(since_minutes=60):
    """Poll Twilio for inbound WhatsApp messages. Returns list of reply dicts."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

    if not account_sid or not auth_token:
        return []

    client = Client(account_sid, auth_token)
    since = datetime.utcnow() - timedelta(minutes=since_minutes)

    replies = []
    try:
        messages = client.messages.list(date_sent_after=since, direction="inbound")
        for msg in messages:
            replies.append({
                "from": msg.from_,
                "body": msg.body,
                "sid": msg.sid,
                "date_sent": msg.date_sent,
            })
    except Exception as e:
        logging.warning("Twilio fetch_replies error: %s", e)

    return replies


def _normalize_number(number):
    """Ensure number has whatsapp: prefix."""
    if number.startswith("whatsapp:"):
        return number
    return f"whatsapp:{number}"
