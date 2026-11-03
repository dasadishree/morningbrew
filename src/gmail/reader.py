import base64
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.newsletter.parser import html_to_text, clean_plain_text
from src.database.db import initialize_database, newsletter_exists, save_newsletter

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# authenticate w gmail
def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())

    if creds and creds.valid:
        return build("gmail", "v1", credentials=creds)

    if not sys.stdin.isatty() and os.getenv("MORNINGBREW_LOGIN") != "1":
        raise RuntimeError(
            "Gmail needs a sign-in. In Terminal, from this project folder, run: "
            "python3 -m src.gmail.reader"
        )

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)

# gets recent emails
def find_morning_brew_emails(service, max_results=10):
    query = "from:crew@morningbrew.com in:anywhere"
    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=max_results
        )
        .execute()
    )

    return results.get("messages", [])

# retrieives email
def get_message(service, message_id, message_format="full"):
    request_args={
        "userId": "me",
        "id": message_id,
        "format": message_format
    }
    if message_format =="metadata":
        request_args["metadataHeaders"] = ["Date", "Subject"]
    return (
        service.users()
        .messages()
        .get(**request_args)
        .execute()
    )

# decodes gmails base64
def decode_body(data):
    if not data:
        return ""
    
    decoded=base64.urlsafe_b64decode(data+"=" * (-len(data) %4))
    return decoded.decode("utf-8", errors="replace")

# extracts email boidy
def extract_body(payload):
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    if body_data and mime_type in ("text/html", "text/plain"):
        return mime_type, decode_body(body_data)
    
    for part in payload.get("parts", []):
        result = extract_body(part)
        if result:
            return result
        
    return None

# gets date and subject
def get_headers(payload):
    headers ={}
    for header in payload.get("headers", []):
        name = header["name"].lower()
        headers[name] = header["value"]

    return headers

# processes and sdaves new emails
def save_new_newsletters(max_results=10):
    initialize_database()

    service = get_gmail_service()
    messages = find_morning_brew_emails(service, max_results=max_results)
    print("Found", len(messages), "Morning Brew emails.")
    saved_count = 0
    skipped_count = 0

    for message in messages:
        gmail_id=message["id"]
        if newsletter_exists(gmail_id):
            print("alr saved: ", gmail_id)
            skipped_count+=1
            continue

        full_message=get_message(service, gmail_id)
        headers=get_headers(full_message["payload"])
        newsletter_date = headers.get("date")
        subject =headers.get("subject", "Untitled Newsletter")
        body_result = extract_body(full_message["payload"])

        if not body_result:
            print("no reabale content: ", subject)
            continue

        mime_type, raw_content = body_result
        if mime_type == "text/html":
            clean_content = html_to_text(raw_content)
        else:
            clean_content = clean_plain_text(raw_content)
        
        if not clean_content.strip():
            print("empty newsletter:", subject)
            continue

        save_newsletter(
            gmail_id,
            newsletter_date,
            subject,
            clean_content,
        )
        saved_count+=1
        print("Saved:", subject)

    print("\nNew newsletters saved:", saved_count)
    print("Already saved:", skipped_count)
    return saved_count

if __name__ == "__main__":
    save_new_newsletters()