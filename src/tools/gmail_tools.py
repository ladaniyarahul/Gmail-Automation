# src/tools/gmail_tools.py

"""
Gmail tools for the Gmail AI Agent (real Gmail API integration).

This module defines tools that:
- Fetch unread emails from Gmail.
- Send replies to specific emails.
- Apply labels to emails (creating labels if needed).

Authentication:
- Uses OAuth2 credentials stored in a local 'token.json' file.
- 'token.json' must contain a valid refreshable access token with the
  Gmail scope 'https://www.googleapis.com/auth/gmail.modify'.

You can obtain 'token.json' using the standard Gmail API Python quickstart
flow and then mount/place it inside the container or project root.
"""

from __future__ import annotations

import base64
import os
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow



# ---------------------------------------------------------
# Gmail API Setup
# ---------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")



def _get_gmail_service():
    """
    Create and return an authenticated Gmail API service client.

    This tries to load 'token.json'. If missing/invalid, it will run
    OAuth using 'credentials.json' and then save a new 'token.json'.
    """
    creds = None

    # 1) Try to load existing token.json
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except ValueError:
            # e.g. missing refresh_token, client_id, client_secret
            creds = None

    # 2) If no valid creds, refresh or run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise RuntimeError(
                    f"Gmail credentials file '{CREDENTIALS_FILE}' not found or invalid.\n"
                    "Download OAuth client credentials from Google Cloud Console as "
                    "'credentials.json' or set GMAIL_CREDENTIALS_FILE env var."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 3) Save new token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service



def _extract_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
    """
    Find a header by name (case-insensitive) in a Gmail message's header list.
    """
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def _decode_body(payload: Dict[str, Any]) -> str:
    """
    Decode the plain text body of a Gmail message payload.

    Note: This is a simplified version focusing on 'text/plain'.
    For more complex multi-part messages, this can be extended.
    """
    body = ""

    if "parts" in payload:
        # Multi-part message: look for text/plain part
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    body_bytes = base64.urlsafe_b64decode(data.encode("utf-8"))
                    body = body_bytes.decode("utf-8", errors="ignore")
                    break
    else:
        # Single-part message
        data = payload.get("body", {}).get("data")
        if data:
            body_bytes = base64.urlsafe_b64decode(data.encode("utf-8"))
            body = body_bytes.decode("utf-8", errors="ignore")

    return body


def _ensure_label(service, user_id: str, label_name: str) -> str:
    """
    Ensure that a label with the given name exists.

    If it exists, return its ID.
    If not, create it and then return the new ID.
    """
    labels_resp = service.users().labels().list(userId=user_id).execute()
    labels = labels_resp.get("labels", [])

    for label in labels:
        if label.get("name") == label_name:
            return label["id"]

    # Label not found, create it
    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId=user_id, body=label_body).execute()
    return created["id"]


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------


@tool
def fetch_unread_emails(limit: int = 20) -> Dict[str, Any]:
    """
    Fetch a list of unread emails from Gmail.

    Args:
        limit: Maximum number of emails to fetch.

    Returns:
        A dictionary with key "emails" containing a list of email dicts:
        Each email includes:
            - id
            - thread_id
            - subject
            - sender
            - snippet
            - body
    """
    service = _get_gmail_service()
    user_id = "me"

    # List unread messages in the inbox
    response = (
        service.users()
        .messages()
        .list(
            userId=user_id,
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=limit,
        )
        .execute()
    )

    messages = response.get("messages", [])
    emails: List[Dict[str, Any]] = []

    for msg_meta in messages:
        msg_id = msg_meta["id"]
        msg = (
            service.users()
            .messages()
            .get(userId=user_id, id=msg_id, format="full")
            .execute()
        )

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        subject = _extract_header(headers, "Subject") or ""
        sender = _extract_header(headers, "From") or ""
        snippet = msg.get("snippet", "")
        body = _decode_body(payload)

        emails.append(
            {
                "id": msg_id,
                "thread_id": msg.get("threadId"),
                "subject": subject,
                "sender": sender,
                "snippet": snippet,
                "body": body,
            }
        )

    return {"emails": emails}


@tool
def send_reply(email_id: str, reply_text: str) -> str:
    """
    Send a reply to a specific email.

    Args:
        email_id: Gmail message ID of the email to reply to.
        reply_text: Text content of the reply.

    Returns:
        A string describing the result.
    """
    service = _get_gmail_service()
    user_id = "me"

    # Get the original message metadata
    original = (
        service.users()
        .messages()
        .get(
            userId=user_id,
            id=email_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "To"],
        )
        .execute()
    )

    headers = original.get("payload", {}).get("headers", [])
    subject = _extract_header(headers, "Subject") or ""
    from_header = _extract_header(headers, "From") or ""
    # Gmail will automatically set the From to the authenticated user.
    # We set "To" to the original sender:
    to_addr = from_header

    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    # Build MIME email
    message = MIMEText(reply_text)
    message["To"] = to_addr
    message["Subject"] = subject
    # Threading headers (optional but recommended)
    message["In-Reply-To"] = original.get("id")
    message["References"] = original.get("id")

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    send_body = {
        "raw": encoded_message,
        "threadId": original.get("threadId"),
    }

    sent = (
        service.users()
        .messages()
        .send(userId=user_id, body=send_body)
        .execute()
    )

    return f"Reply sent. New message id={sent.get('id')} in thread {sent.get('threadId')}"


@tool
def apply_label(email_id: str, label: str) -> str:
    """
    Apply a label to a specific email.

    Args:
        email_id: Gmail message ID of the email.
        label: Label name to apply (e.g., 'Client', 'Billing', 'Personal', 'Spam').

    Returns:
        A string describing the result.
    """
    service = _get_gmail_service()
    user_id = "me"

    label_id = _ensure_label(service, user_id, label)

    body = {
        "addLabelIds": [label_id],
        "removeLabelIds": [],  # keep empty unless you want to remove labels
    }

    updated = (
        service.users()
        .messages()
        .modify(userId=user_id, id=email_id, body=body)
        .execute()
    )

    return f"Label '{label}' applied to email_id={email_id}, new labelIds={updated.get('labelIds')}"
