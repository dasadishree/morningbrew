import os
import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# authenticate w gmail
def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)

# gets recent emails
def find_morning_brew_emails(service, max_results=10):
    query = "from:crew@morningbrew.com"
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

def get_message(service, message_id):
    return(
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full"
        )
        .execute()
    )

def decode_body(data):
    """Decode Gmail's base64url encoded message body"""
    if not data:
        return ""
    
    decoded=base64.urlsafe_b64decode(data+"=" * (-len(data) %4))
    return decoded.decode("utf-8", errors="replace")

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

def get_headers(payload):
    headers ={}
    for header in payload.get("headers", []):
        name = header["name"].lower()
        headers[name] = header["value"]

    return headers

if __name__ == "__main__":
    service = get_gmail_service()
    messages = find_morning_brew_emails(service)
    print("Found", len(messages), "Morning Brew emails.")
    for message in messages:
        full_message = get_message(service, message["id"])
        headers = get_headers(full_message["payload"])
        print("\n"+"="*60)
        print("ID:", message["id"])
        print("Date:", headers.get("date"))
        print("Subject:", headers.get("subject"))
        body = extract_body(full_message["payload"])
        if body:
            mime_type, content = body
            print("MIME type:", mime_type)
            print("Characters:", len(content))