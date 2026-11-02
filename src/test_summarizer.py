from src.ai.summarizer import summarize_newsletter
from src.database.db import get_unsummarized_newsletters, save_summary

newsletters = get_unsummarized_newsletters()

if not newsletters:
    print("No unsummarized newsletters found.")
    exit()

newsletter = newsletters[0]

newsletter_id, gmail_id, date, subject, content = newsletter

print("="*60)
print("Subject:", subject)
print("Generating summary...")
print("="*60)

summary = summarize_newsletter(content)
print("\nSUMMARY:\n")
print(summary)
save_summary(newsletter_id, summary)
print("\nsummary saved to db!")