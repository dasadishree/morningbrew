# Morning Brew daily quiz

Checks Gmail for today's Morning Brew, writes a 10-question multiple-choice quiz from it, and posts that quiz to Slack once.

```bash
python3 -m src.quiz.generate
```

Running it again the same day does nothing if that quiz was already posted. Run it after the newsletter goes out (or on a daily schedule a little after Morning Brew usually arrives).

Needs a `.env` with `GEMINI_API_KEY` and `SLACK_WEBHOOK_URL`, plus Gmail `credentials.json`.
