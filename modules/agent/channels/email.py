import smtplib
import imaplib
import email as email_lib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def send_email(to_address, subject, body):
    """Send a plain-text email via SMTP. Raises ValueError if credentials missing."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        raise ValueError("SMTP_USER et SMTP_PASS requis dans .env")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_address
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True


def fetch_replies(since_hours=1):
    """Fetch unread replies via IMAP polling. Returns list of reply dicts."""
    imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")
    imap_user = os.getenv("SMTP_USER", "")
    imap_pass = os.getenv("SMTP_PASS", "")
    imap_folder = os.getenv("IMAP_FOLDER", "INBOX")

    if not imap_user or not imap_pass:
        return []

    replies = []
    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(imap_user, imap_pass)
        mail.select(imap_folder)

        since_date = (datetime.now() - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
        _, msg_nums = mail.search(None, f"SINCE {since_date} UNSEEN")

        for num in (msg_nums[0].split() if msg_nums[0] else []):
            _, msg_data = mail.fetch(num, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)
            replies.append({
                "from": msg.get("From", ""),
                "subject": _decode_header_str(msg.get("Subject", "")),
                "body": _get_body(msg),
                "message_id": msg.get("Message-ID", ""),
                "in_reply_to": msg.get("In-Reply-To", ""),
            })

        mail.logout()
    except Exception:
        pass

    return replies


def _decode_header_str(header_str):
    if not header_str:
        return ""
    decoded, encoding = decode_header(header_str)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="replace")
    return str(decoded)


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""
