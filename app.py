from flask import Flask, render_template, request, session, redirect, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from os import getenv
import json
import os

# ========================
# SETUP
# ========================

app = Flask(__name__)
app.secret_key = "penguin_secret"

load_dotenv()
client = OpenAI(api_key=getenv("api_key"))

LANG_FILE = "language_leaderboard.json"

# ========================
# HELPER FUNCTIONS
# ========================


def load_language():
    if not os.path.exists(LANG_FILE):
        return {}

    try:
        with open(LANG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_language(data):
    try:
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving leaderboard:", e)
# ========================
# HOME
# ========================

@app.route("/")
def home():
    if "username" not in session:
        return redirect("/login")
    return render_template("home.html", username=session["username"])

# ========================
# LOGIN
# ========================

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form.get("username")
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ========================
# LANGUAGE PAGE
# ========================

@app.route("/language")
def language():
    if "username" not in session:
        return redirect("/login")
    return render_template("index.html")

# ========================
# START LANGUAGE GAME
# ========================

@app.route("/start_language", methods=["POST"])
def start_language():

    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400
    language = data.get("language")
    difficulty = data.get("difficulty")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a language tutor. Return exactly 5 multiple choice questions in JSON format with this structure: { 'questions': [ { 'question': '', 'options': ['a','b','c','d'], 'answer': 0 } ] }"
                },
                {
                    "role": "user",
                    "content": f"Create 5 {difficulty} difficulty vocabulary translation questions translating English into {language}."
                }
            ]
        )

        questions_json = json.loads(response.choices[0].message.content)

        session["questions"] = questions_json["questions"]

        return jsonify(questions_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================
# SUBMIT LANGUAGE ANSWERS
# ========================

@app.route("/submit_language", methods=["POST"])
def submit_language():

    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_answers = request.json.get("answers")
    questions = session.get("questions")

    if not questions:
        return jsonify({"error": "No active game"}), 400

    correct_count = 0
    feedback = []

    for i, question in enumerate(questions):
        correct_index = question["answer"]
        user_index = user_answers[i]

        if user_index == correct_index:
            correct_count += 1
            feedback.append({
                "question": question["question"],
                "status": "correct"
            })
        else:
            feedback.append({
                "question": question["question"],
                "status": "incorrect",
                "correct_answer": question["options"][correct_index]
            })

    # XP system (1 XP per correct answer)
    xp_gained = correct_count

    leaderboard = load_language()

    user_found = False
    for player in leaderboard:
        if player["user"] == session["username"]:
            player["xp"] += xp_gained
            player["level"] = player["xp"] // 20
            user_found = True
            break

    if not user_found:
        leaderboard.append({
            "user": session["username"],
            "xp": xp_gained,
            "level": xp_gained // 20
        })

    save_language(leaderboard)

    return jsonify({
        "correct": correct_count,
        "xp_gained": xp_gained,
        "feedback": feedback
    })

# ========================
# FLAPPY PAGE
# ========================

@app.route("/flappy")
def flappy():
    if "username" not in session:
        return redirect("/login")
    return render_template("flappy.html")

# ========================
# LANGUAGE LEADERBOARD
# ========================

@app.route("/language_leaderboard")
def language_leaderboard():
    if "username" not in session:
        return redirect("/login")

    leaderboard = load_language()
    leaderboard = sorted(leaderboard, key=lambda x: x["xp"], reverse=True)

    return render_template("leaderboard.html", leaderboard=leaderboard)

# ========================

if __name__ == "__main__":
    app.run(debug=True)