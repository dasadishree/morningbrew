from src.database.db import get_connection

connection=get_connection()
cursor=connection.cursor()

cursor.execute("""
    SELECT
        id,
        gmail_message_id,
        newsletter_date,
        subject,
        LENGTH(raw_content),
        LENGTH(clean_content)           
    FROM newsletters
    ORDER BY newsletter_date DESC
""")
newsletters = cursor.fetchall()
print(f"Total newsletter in database: {len(newsletters)}")

for newsletter in newsletters:
    newsletter_id, gmail_id, date, subject, raw_length, clean_length = newsletter
    print("\n"+"="*60)
    print("Database ID:", newsletter_id)
    print("Gmail ID:", gmail_id)
    print("Date:", date)
    print("Subject:", subject)
    print("Raw content length:", raw_length)
    print("Clean content length:", clean_length)

connection.close()