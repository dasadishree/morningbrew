from src.database.db import get_unsummarized_newsletters

newsletters = get_unsummarized_newsletters()
print(f"Found {len(newsletters)} unsummarized newsletters.")

for newsletter in newsletters:
    newsletter_id, gmail_id, date, subject, clean_content = newsletter
    print("\n"+"="*60)
    print("Database ID:", newsletter_id)
    print("Gmail ID:", gmail_id)
    print("Date:", date)
    print("Subject:", subject)
    print("Content preview:")
    print(clean_content[:500])