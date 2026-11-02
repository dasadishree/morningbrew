import json
from datetime import datetime
from email.utils import parsedate_to_datetime
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "morningbrew.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

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

    cursor.execute("PRAGMA table_info(newsletters)")
    columns = {row[1] for row in cursor.fetchall()}
    for column in ("raw_content", "summary", "summary_sent"):
        if column in columns:
            cursor.execute(f"ALTER TABLE newsletters DROP COLUMN {column}")

    connection.commit()
    connection.close()

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

def get_latest_todays_newsletter():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, newsletter_date, subject, clean_content
        FROM newsletters
        WHERE clean_content IS NOT NULL AND clean_content != ''
    """)
    rows = cursor.fetchall()
    connection.close()

    today =datetime.now().astimezone().date()
    dated_rows=[]

    for row in rows:
        try:
            parsed_date=parsedate_to_datetime(row[1])
            if parsed_date.astimezone().date() ==today:
                dated_rows.append((parsed_date, row))
        except(TypeError, ValueError):
            continue
    if not dated_rows:
        return None
    
    return max(dated_rows, key=lambda item: item[0])[1]

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

def mark_quiz_sent(quiz_id):
    connection=get_connection()
    cursor=connection.cursor()
    cursor.execute(
        "UPDATE quizzes SET slack_sent = 1 WHERE id = ?",
        (quiz_id,),
    )
    connection.commit()
    connection.close()