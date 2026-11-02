import json
import os

from dotenv import load_dotenv
from google import genai

from src.database.db import (
    get_latest_todays_newsletter,
    get_quiz,
    save_quiz,
    mark_quiz_sent,
)
from src.notifications.slack import send_slack_message
load_dotenv()

MODEL="gemini-3.8-flash"

def generate_quiz(content):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
        Create exactly 10 multiple choice questions about the important news in this Morning Brew newsletter.
        Avoid pulling from the "sponsored by" sections or the header / footer.
        Each question must have 4 answer choices (A, B, C, D) and use only information in this newsletter (no outside)
        Make questions specific and fact based
        Maybe include "all of the above" type questions if aspplicaitable or even just put that answer in as a trick like make varying answers
        Return ONLY valid JSON in this exact structure:
        {{
        "questions": [
            {{
            "question": "Question text",
            "choices": {{
                "A": "Choice A",
                "B": "Choice B",
                "C": "Choice C",
                "D": "Choice D"
            }},
            "answer": "A",
            "explanation": "Brief explanation"
            }}
        ]
        }}
        NEWSLETTER
        {content}
        """,
            config={"response_mime_type": "application/json"}
    )

    quiz=json.loads(response.text)
    questions=quiz["questions"]
    if len(questions)!=5:
        raise ValueError("gemini didnt return exactly 10 questions")
    for question in questions:
        if set(question["choices"].keys()) != {"A", "B", "C", "D"}:
            raise ValueError("A question doesnt have 4 choices")
        if question["answer"] not in {"A", "B", "C", "D"}:
            raise ValueError("A question has an invalid answer.")
        
    return quiz