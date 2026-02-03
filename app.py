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

DIFFICULTIES = ["no brainer", "easy", "medium", "hard", "impossible"]

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

    # IMPORTANT FIX:
    # We force the model to include correct answer keys: q1c..q5c
    questions = get_json_response(
        """You are a language tutor.

Return EXACTLY this JSON format (valid JSON):
{
  "q1": "question text",
  "q1a": ["ans1","ans2","ans3","ans4"],
  "q1c": 1,

  "q2": "question text",
  "q2a": ["ans1","ans2","ans3","ans4"],
  "q2c": 2,

  "q3": "question text",
  "q3a": ["ans1","ans2","ans3","ans4"],
  "q3c": 3,

  "q4": "question text",
  "q4a": ["ans1","ans2","ans3","ans4"],
  "q4c": 4,

  "q5": "question text",
  "q5a": ["ans1","ans2","ans3","ans4"],
  "q5c": 1
}

Rules:
- q#a must always have exactly 4 options.
- q#c must be an integer 1-4 representing the correct option number.
- The correct answer positions should not all be the same number.
""",
        f"Come up with multiple choice questions with 4 answers only one answer being the correct translation. "
        f"The questions will ask users to translate English words into {lang} words using this list of words {words}."
    )

    # basic validation fallback (still minimal)
    for i in range(1, 6):
        if f"q{i}" not in questions or f"q{i}a" not in questions or f"q{i}c" not in questions:
            return jsonify({"error": "Question generation failed. Please try again."}), 500

    session["questions"] = questions
    session["difficulty"] = difficulty
    session["conversation"] = []

    return jsonify(questions)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data.get("answers", [])
    questions = session.get("questions", {})
    correct = 0

    # score correctly using q1c..q5c
    for i in range(5):
        q_key = f"q{i+1}"
        correct_key = f"q{i+1}c"

        chosen = answers[i] if i < len(answers) else None
        correct_option = questions.get(correct_key)

        # store conversation
        session["conversation"].append({
            "question": questions.get(q_key),
            "chosen": chosen,
            "correct": str(correct_option)
        })

        # count correct
        if chosen is not None and str(chosen) == str(correct_option):
            correct += 1

    # difficulty recommendation logic (same as before but fixed)
    current_index = DIFFICULTIES.index(session["difficulty"])
    recommended = session["difficulty"]

    if correct <= 1 and current_index > 0:
        recommended = DIFFICULTIES[current_index - 1]
    elif correct >= 4 and current_index < len(DIFFICULTIES) - 1:
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
