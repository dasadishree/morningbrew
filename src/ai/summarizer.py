import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
def summarize_newsletter(content):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"""
You summarize Morning Brew newsletters for a busy reader.
Create a concise but informative summary. 
Focus on:
- the most important stories
- important facts and numbers
- major business, technology, finance, or cultural developments
- useful takeaways

Use 4-6 bullet points.
Do not add information that is not present in the newsletter.

NEWSLETTER:
{content}
""",
    )
    
    return response.text