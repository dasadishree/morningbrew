import fcntl
import json
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.database.db import (
    initialize_database,
    get_newsletters_awaiting_quiz,
    get_quiz,
    save_quiz,
    mark_quiz_sent,
)
from src.gmail.reader import save_new_newsletters
from src.notifications.slack import send_slack_message
load_dotenv()

HACKCLUB_URL = "https://ai.hackclub.com/proxy/v1/chat/completions"
MODELS = ("qwen/qwen3.6-flash", "google/gemini-3.6-flash")

# grneerate 10 questions
def generate_quiz(content):
    api_key = os.getenv("HACKCLUB_API_KEY")
    if not api_key:
        raise ValueError("HACKCLUB_API_KEY not found in .env")
    last_error = None
    for model in MODELS:
        for attempt in range(1, 3):
            try:
                return _request_quiz(api_key, content, model)
            except (requests.RequestException, TimeoutError, json.JSONDecodeError, ValueError, KeyError) as exc:
                last_error = exc
                print(f"{model} attempt {attempt} failed: {exc}")
                if attempt == 1:
                    time.sleep(3)
    raise last_error


def _quiz_prompt(content):
    return f"""
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
            }}
        ]
        }}
        NEWSLETTER
        {content}
        """


def _completion_text(payload):
    message = payload["choices"][0]["message"]
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return content


def _extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("model did not return JSON")
    return text[start : end + 1]


def _request_quiz(api_key, content, model):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": _quiz_prompt(content)}],
        "temperature": 0.4,
    }
    response = requests.post(
        HACKCLUB_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={**body, "response_format": {"type": "json_object"}},
        timeout=90,
    )
    if response.status_code == 400:
        response = requests.post(
            HACKCLUB_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout=90,
        )
    response.raise_for_status()
    quiz = json.loads(_extract_json(_completion_text(response.json())))
    # make sure formatted right
    questions=quiz["questions"]
    if len(questions)!=10:
        raise ValueError("gemini didnt return exactly 10 questions")
    for question in questions:
        question["choices"] = _normalize_choices(question.get("choices"))
        answer = str(question.get("answer", "")).strip().upper()
        answer = answer[:1]
        if answer not in {"A", "B", "C", "D"}:
            raise ValueError("A question has an invalid answer.")
        question["answer"] = answer

    return quiz

# consisntent choice formatitng
def _normalize_choices(choices):
    letters = ("A", "B", "C", "D")
    if isinstance(choices, list):
        if len(choices) != 4:
            raise ValueError("A question doesnt have 4 choices")
        return {letter: str(choice) for letter, choice in zip(letters, choices)}
    if not isinstance(choices, dict):
        raise ValueError("A question doesnt have 4 choices")
    normalized = {}
    for key, value in choices.items():
        label = str(key).strip().upper()
        if not label or label[0] not in letters or label[0] in normalized:
            continue
        if len(label) == 1 or not label[1].isalpha():
            normalized[label[0]] = value
    if set(normalized) != set(letters):
        raise ValueError("A question doesnt have 4 choices")
    return {letter: normalized[letter] for letter in letters}

# formats quiz for slack
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

# genernate save and post
def post_quiz(newsletter):
    newsletter_id, _, subject, content = newsletter
    existing = get_quiz(newsletter_id)
    if existing:
        quiz_id, quiz_json, slack_sent = existing
        if slack_sent:
            print("Quiz already sent:", subject)
            return
        quiz = json.loads(quiz_json)
        print("Sending the saved quiz:", subject)
    else:
        print("Generating a quiz:", subject)
        quiz = generate_quiz(content)
        quiz_id = save_quiz(newsletter_id, quiz)

    message = format_slack_quiz(subject, quiz)
    send_slack_message(message)
    mark_quiz_sent(quiz_id)
    print("Quiz posted:", subject)

def main():
    lock_path = Path.home() / "Library" / "Logs" / "morningbrew" / "quiz.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Quiz check already running.")
        return

    try:
        save_new_newsletters()
        pending = get_newsletters_awaiting_quiz()
        if not pending:
            print("No new newsletter to quiz.")
            return
        for newsletter in pending:
            post_quiz(newsletter)
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()

if __name__ == "__main__":
    main()