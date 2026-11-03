# Morning Brew quiz
My teacher assigns weekely quizzes based off of current events so made a Slack bot to give myself practice questions based on the newsletter he pulls from (morningbrew.org (or maybe its .com))

Every hour, while you are logged into this Mac, the script checks Gmail. When a new Morning Brew issue arrives, it writes a 10-question multiple-choice quiz and posts it to Slack. Each issue is posted once.

```bash
python3 -m src.quiz.generate
```