import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.database.db import (
    initialize_database,
    get_latest_todays_newsletter,
    save_quiz,
    mark_quiz_sent,
)
from src.notifications.slack import send_slack_message
load_dotenv()

MODEL="gemini-3.8-flash"

def generate_quiz(content):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options=types.HttpOptions(timeout=30000, retry_options=types.HttpRetryOptions(attempts=1),),)
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
    # make sure formatted right
    questions=quiz["questions"]
    if len(questions)!=10:
        raise ValueError("gemini didnt return exactly 10 questions")
    for question in questions:
        if set(question["choices"].keys()) != {"A", "B", "C", "D"}:
            raise ValueError("A question doesnt have 4 choices")
        if question["answer"] not in {"A", "B", "C", "D"}:
            raise ValueError("A question has an invalid answer.")
        
    return quiz

def format_slack_quiz(subject, quiz):
    message = f"*Morning Brew Daily Quiz*\n_{subject}_\n\n"
    for number, question in enumerate(quiz["questions"], start=1):
        message+=f"*{number}. {question['question']}*\n"
        for letter, choice in question["choices"].items():
            message+=f"• {letter}. {choice}\n"
        message+="\n"
    message+="*Answer Key*\n"
    answers = []

    for number, question in enumerate(quiz["questions"], start=1):
        answers.append(f"{number}) {question['answer']}")
    message+= "     ".join(answers)
    return message

def main():
    initialize_database()
    newsletter=get_latest_todays_newsletter()
    if newsletter is None:
        print("No newsletter from today found. Run the Gmail reader first:")
        print("python3 -m src.gmail.reader")
        return
    newsletter_id, newsletter_date, subject, content = newsletter
    print("generating a new quiz...")
    quiz=generate_quiz(content)
    quiz_id=save_quiz(newsletter_id, quiz)
    message=format_slack_quiz(subject,quiz)
    send_slack_message(message)
    mark_quiz_sent(quiz_id)
    print("new quiz posted!")

if __name__ == "__main__":
    main()