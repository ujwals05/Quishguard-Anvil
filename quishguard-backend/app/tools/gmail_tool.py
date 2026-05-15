"""
gmail_tool.py
─────────────
Gmail API: authenticate, fetch emails, download image attachments.

FIRST TIME SETUP:
  1. Google Cloud Console → Enable Gmail API
  2. Create OAuth2 credentials → Desktop App → download as credentials.json
  3. Place credentials.json in project root
  4. Run once:  python -m app.tools.gmail_tool
     → Opens browser, you sign in → token.json is saved automatically
"""

import os
import base64
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}


# ── Auth ───────────────────────────────────────────────────────────────────

def get_gmail_service():
    """Returns authenticated Gmail API service. Handles token refresh automatically."""
    creds = None

    if os.path.exists(settings.GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(settings.GMAIL_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(settings.GMAIL_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"credentials.json not found. "
                    "Download from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.GMAIL_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(settings.GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── Fetch emails ───────────────────────────────────────────────────────────

def fetch_unread_emails(max_results: int = 10) -> list[dict]:
    """Fetch unread emails from inbox. Returns list of parsed email dicts."""
    try:
        service = get_gmail_service()
        result = service.users().messages().list(
            userId="me", q="is:unread", maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        emails = []
        for m in messages:
            parsed = _parse_email(service, m["id"])
            if parsed:
                emails.append(parsed)

        logger.info(f"Fetched {len(emails)} unread emails")
        return emails

    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        return []


def fetch_email_by_id(message_id: str) -> Optional[dict]:
    """Fetch a single email by Gmail message ID."""
    try:
        service = get_gmail_service()
        return _parse_email(service, message_id)
    except Exception as e:
        logger.error(f"Failed to fetch email {message_id}: {e}")
        return None


def _parse_email(service, message_id: str) -> Optional[dict]:
    try:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        attachments = _get_attachment_metadata(msg["payload"])

        return {
            "id":          message_id,
            "thread_id":   msg.get("threadId"),
            "sender":      headers.get("From", ""),
            "subject":     headers.get("Subject", "(no subject)"),
            "date":        headers.get("Date", ""),
            "snippet":     msg.get("snippet", ""),
            "attachments": attachments,
        }
    except Exception as e:
        logger.error(f"Error parsing email {message_id}: {e}")
        return None


def _get_attachment_metadata(payload: dict) -> list[dict]:
    """Recursively walk MIME tree and collect image attachment metadata."""
    attachments = []
    for part in payload.get("parts", []):
        if part.get("mimeType", "").startswith("multipart/"):
            attachments.extend(_get_attachment_metadata(part))
            continue
        body = part.get("body", {})
        att_id = body.get("attachmentId")
        filename = part.get("filename", "")
        if att_id and filename:
            attachments.append({
                "attachment_id": att_id,
                "filename":      filename,
                "mime_type":     part.get("mimeType", ""),
            })
    return attachments


# ── Download attachments ───────────────────────────────────────────────────

def download_attachment(
    message_id: str,
    attachment_id: str,
    filename: str,
    save_dir: str = "/tmp/quishguard_attachments",
) -> Optional[str]:
    """Download one attachment. Returns saved file path or None."""
    try:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        service = get_gmail_service()

        att = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()

        file_bytes = base64.urlsafe_b64decode(att["data"])
        save_path = os.path.join(save_dir, filename)

        with open(save_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Saved attachment: {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        return None


def download_all_image_attachments(
    email: dict,
    save_dir: str = "/tmp/quishguard_attachments",
) -> list[str]:
    """Download all image attachments from an email. Returns list of file paths."""
    saved = []
    for att in email.get("attachments", []):
        if att.get("mime_type", "") in IMAGE_MIME_TYPES:
            path = download_attachment(
                message_id=email["id"],
                attachment_id=att["attachment_id"],
                filename=att["filename"],
                save_dir=save_dir,
            )
            if path:
                saved.append(path)
    return saved


# ── Gmail Watch (Pub/Sub push) ─────────────────────────────────────────────

def setup_gmail_watch(topic_name: str) -> Optional[dict]:
    """
    Register Gmail push notifications via Google Pub/Sub.
    Call once to start receiving webhooks when new emails arrive.

    topic_name: "projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC_NAME"
    """
    try:
        service = get_gmail_service()
        response = service.users().watch(
            userId="me",
            body={
                "topicName": topic_name,
                "labelIds": ["INBOX"],
                "labelFilterAction": "include",
            },
        ).execute()
        logger.info(f"Gmail watch active, expires: {response.get('expiration')}")
        return response
    except HttpError as e:
        logger.error(f"Failed to set up Gmail watch: {e}")
        return None


def get_history(history_id: str) -> list[str]:
    """
    Fetch new Gmail message IDs since a given historyId.
    Called from webhook when a Pub/Sub notification arrives.
    """
    try:
        service = get_gmail_service()
        response = service.users().history().list(
            userId="me",
            startHistoryId=history_id,
            historyTypes=["messageAdded"],
        ).execute()

        ids = []
        for record in response.get("history", []):
            for m in record.get("messagesAdded", []):
                ids.append(m["message"]["id"])
        return ids

    except HttpError as e:
        logger.error(f"Failed to get history: {e}")
        return []


# ── Manual test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running Gmail OAuth flow and fetching emails...")
    emails = fetch_unread_emails(max_results=3)
    for e in emails:
        print(f"\n📧 From: {e['sender']}")
        print(f"   Subject: {e['subject']}")
        print(f"   Attachments: {len(e['attachments'])}")
        for a in e["attachments"]:
            print(f"      - {a['filename']} ({a['mime_type']})")