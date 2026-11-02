import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_slack_message(message):
    webhook_url = os.getenv("SLACK+WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL not found in .env")
    response = requests.post(
        webhook_url,
        json={"text": message},
        timeout=15
    )
    response.raise_for_status()
    if response.text != "ok":
        raise Exception(f"Slack returned: {response.text}")
    
    print("message susccessfully sent to slack!")