import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
def summarize_newsletter(content):
    response = client.responses.create(
        model="gpt-5.5",
        instructions=(
            "You summarize Morning Brew newsletters for a busy reader. "
            "Create a concise but informative summary. "
            "Focus on the most important facts, stories, numbers, and takeaways."
            "Use 4-6 bullet points. "
            "Do not add information that is not present in the newsletter."
        ),
        input=content,
    )
    return response.output_text