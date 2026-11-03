import json
from email.utils import parsedate_to_datetime
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "morningbrew.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# creates tables
def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_message_id TEXT UNIQUE NOT NULL,
            newsletter_date TEXT,
            subject TEXT,
            clean_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            newsletter_id INTEGER NOT NULL,
            quiz_json TEXT NOT NULL,
            slack_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
        )
    """)

    connection.commit()
    connection.close()

# prevents saving same email twice
def newsletter_exists(gmail_message_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM newsletters
        WHERE gmail_message_id = ?
        """,
        (gmail_message_id,),
    )
    result = cursor.fetchone()
    connection.close()
    return result is not None

# stores new newsletters
def save_newsletter(
        gmail_message_id,
        newsletter_date,
        subject,
        clean_content,
):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO newsletters (
            gmail_message_id,
            newsletter_date,
            subject,
            clean_content
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            gmail_message_id,
            newsletter_date,
            subject,
            clean_content,
        ),
    )

    connection.commit()
    connection.close()

# parses dates to sort
def _parsed_newsletter_date(value):
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None

# finds newsletters still needing quizzes
def get_newsletters_awaiting_quiz():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            n.id,
            n.newsletter_date,
            n.subject,
            n.clean_content,
            COALESCE((
                SELECT slack_sent
                FROM quizzes
                WHERE newsletter_id = n.id
                ORDER BY id DESC
                LIMIT 1
            ), 0)
        FROM newsletters n
        WHERE n.clean_content IS NOT NULL AND n.clean_content != ''
    """)
    rows = cursor.fetchall()
    connection.close()

    dated = []
    for row in rows:
        parsed = _parsed_newsletter_date(row[1])
        if parsed is not None:
            dated.append((parsed, row))

    if not dated:
        return []

    sent_dates = [parsed for parsed, row in dated if row[4]]
    if sent_dates:
        cutoff = max(sent_dates)
        pending = [
            (parsed, row)
            for parsed, row in dated
            if parsed > cutoff and not row[4]
        ]
    else:
        newest = max(dated, key=lambda item: item[0])
        pending = [] if newest[1][4] else [newest]

    pending.sort(key=lambda item: item[0])
    return [row[:4] for _, row in pending]

# checks if a quiz was alreayd generated
def get_quiz(newsletter_id):
    connection=get_connection()
    cursor=connection.cursor()
    cursor.execute(
        """
        SELECT id, quiz_json, slack_sent
        FROM quizzes
        WHERE newsletter_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (newsletter_id,),
    )
    result = cursor.fetchone()
    connection.close()
    return result

# saves quizes
def save_quiz(newsletter_id, quiz):
    connection=get_connection()
    cursor=connection.cursor()
    cursor.execute(
        """
            INSERT INTO quizzes (newsletter_id, quiz_json)
            VALUES (?, ?)
        """,
        (newsletter_id, json.dumps(quiz)),
    )
    quiz_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return quiz_id

# marks successufl slasck posts
def mark_quiz_sent(quiz_id):
    connection=get_connection()
    cursor=connection.cursor()
    cursor.execute(
        "UPDATE quizzes SET slack_sent = 1 WHERE id = ?",
        (quiz_id,),
    )
    connection.commit()
    connection.close()