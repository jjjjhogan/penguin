from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from os import getenv
from json import loads
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = "penguin-secret-key"

client = OpenAI(api_key=getenv("api_key"))

# Difficulty order
DIFFICULTIES = ["No Brainer", "Easy", "Medium", "Hard", "Impossible"]

# In-memory storage
leaderboard = []   # [{username, score, difficulty}]
daily_visits = {}  # {date: count}

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

# --------- ROUTES ----------

@app.route("/")
def home():
    today = str(date.today())
    daily_visits[today] = daily_visits.get(today, 0) + 1

    return render_template("home.html", visits=daily_visits[today])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["username"] = username
            return redirect("/play")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/play")
def play():
    if "username" not in session:
        return redirect("/login")
    return render_template("index.html", difficulties=DIFFICULTIES, username=session["username"])

@app.route("/leaderboard")
def leaderboard_page():
    # Sort by score descending
    sorted_board = sorted(leaderboard, key=lambda x: x["score"], reverse=True)
    return render_template("leaderboard.html", leaderboard=sorted_board)

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    lang = data["language"]
    difficulty = data["difficulty"]

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
""",
        f"Translate English words into {lang} using this list {words}"
    )

    session["questions"] = questions
    session["difficulty"] = difficulty

    return jsonify(questions)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data["answers"]
    questions = session.get("questions", {})

    # We still approximate correctness (same as before)
    correct = 0
    for a in answers:
        if a == "1":
            correct += 1

    # Difficulty adjustment
    current_index = DIFFICULTIES.index(session["difficulty"])
    new_index = current_index

    if correct <= 1 and current_index > 0:
        new_index -= 1
    elif correct >= 4 and current_index < len(DIFFICULTIES) - 1:
        new_index += 1

    recommended = DIFFICULTIES[new_index]

    # Save to leaderboard
    leaderboard.append({
        "username": session["username"],
        "score": correct,
        "difficulty": session["difficulty"]
    })

    return jsonify({
        "correct": correct,
        "recommended": recommended
    })

if __name__ == "__main__":
    app.run(debug=True)
