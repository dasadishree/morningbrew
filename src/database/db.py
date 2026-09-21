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
            raw_content TEXT,
            clean_content TEXT,
            summary TEXT,
            summary_sent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
        raw_content,
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
            raw_content,
            clean_content
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            gmail_message_id,
            newsletter_date,
            subject,
            raw_content,
            clean_content,
        ),
    )

    connection.commit()
    connection.close()