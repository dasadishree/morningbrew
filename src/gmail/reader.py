import os
import base64
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
        try:
            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        except Exception as e:
            print("Existing Gmail authentication expired:", e)
            print("YOu will need to sign in again")
            TOKEN_FILE.unlink(missing_ok=True)
            creds=None

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

def decode_body(data):
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
    initialize_database()
    
    service = get_gmail_service()
    messages = find_morning_brew_emails(service)
    print("Found", len(messages), "Morning Brew emails.")
    saved_count=0
    skipped_count=0

    for message in messages:
        
        metadata=get_message(
            service,
            message["id"],
            message_format="metadata"
        )
        headers=get_headers(metadata["payload"])
        print(headers.get("date"), "|", headers.get("subject"))

    if messages:
        print("\n"+"="*60)
        print("INSPECTING NEWEST NEWSLETTER")
        print("="*60)
        full_message=get_message(service, messages[0]["id"])
        headers=get_headers(full_message["payload"])
        print("Subject:", headers.get("subject"))
        body_result = extract_body(full_message["payload"])
        if body_result:
            mime_type, raw_content = body_result
            if mime_type == "text/html":
                clean_content = html_to_text(raw_content)
            else:
                clean_content = clean_plain_text(raw_content)
            
            print("\nEXTRAVCTED CONTENT:\n")
            print(clean_content)
        else:
            print("no readable content found")