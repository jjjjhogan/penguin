from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
from os import getenv
from json import loads
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = "penguin-secret-key"

client = OpenAI(api_key=getenv("api_key"))

DIFFICULTIES = [
    "no brainer",
    "easy",
    "medium",
    "hard",
    "impossible"
]

leaderboard = []

def get_standard_response(system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception:
        return "[]"

def get_json_response(system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return loads(response.choices[0].message.content)
    except Exception:
        return {}

@app.route("/")
def home():
    today = str(date.today())
    if session.get("last_login") != today:
        session["last_login"] = today
        session["daily_logins"] = session.get("daily_logins", 0) + 1

    return render_template(
        "index.html",
        leaderboard=leaderboard,
        daily_logins=session.get("daily_logins", 1),
        difficulties=DIFFICULTIES
    )

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    lang = data.get("language")
    difficulty = data.get("difficulty")

    words = get_standard_response(
        "You are a language tutor. Return ONLY a Python list of words as strings.",
        f"Give 5 vocab words in {lang} difficulty {difficulty}"
    )

    questions = get_json_response(
        """You are a language tutor.
Return 5 multiple choice questions in JSON format:
{
 'q1':'question',
 'q1a':['a','b','c','d'],
 ...
}
Each question must have ONE correct answer.
""",
        f"Translate English words into {lang} using this list {words}"
    )

    session["questions"] = questions
    session["difficulty"] = difficulty
    session["conversation"] = []

    return jsonify(questions)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data.get("answers")
    questions = session.get("questions", {})
    correct = 0

    for i in range(5):
        session["conversation"].append({
            "question": questions.get(f"q{i+1}"),
            "chosen": answers[i]
        })

        if answers[i] == "1":  # model enforced randomization, placeholder correctness
            correct += 1

    current_index = DIFFICULTIES.index(session["difficulty"])
    recommended = session["difficulty"]

    if correct <= 1 and current_index > 0:
        recommended = DIFFICULTIES[current_index - 1]
    elif correct >= 3 and current_index < len(DIFFICULTIES) - 1:
        recommended = DIFFICULTIES[current_index + 1]

    # FIX: 4 or 5 ALWAYS goes up (unless already max)
    if correct >= 4 and current_index < len(DIFFICULTIES) - 1:
        recommended = DIFFICULTIES[current_index + 1]

    leaderboard.append({
        "score": correct,
        "difficulty": session["difficulty"]
    })

    return jsonify({
        "correct": correct,
        "recommended": recommended,
        "conversation": session["conversation"]
    })

if __name__ == "__main__":
    app.run(debug=True)
