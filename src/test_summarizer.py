from src.ai.summarizer import summarize_newsletter
from src.database.db import get_unsammarized_newsletters

newsletters = get_unsammarized_newsletters()

if not newsletters:
    print("No unsammarized newsletters found.")
    exit()

newsletter = newsletters[0]

newsletter_id, gmail_id, date, subject, content=newsletter

print("="*60)
print("Subject:", subject)
print("Generating summary...")
print("="*60)

summary = summarize_newsletter(content)
print("\nSUMMARY:\n")
print(summary)