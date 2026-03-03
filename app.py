from flask import Flask, render_template, request, session, redirect, jsonify
from openai import OpenAI
from os import getenv
from dotenv import load_dotenv
from json import loads
import json

app = Flask(__name__)
app.secret_key = "penguin_secret"

load_dotenv()
client = OpenAI(api_key=getenv("api_key"))

FLAPPY_FILE = "flappy_scores.json"
LANG_FILE = "language_scores.json"

# =========================
# LOAD / SAVE FUNCTIONS
# =========================

def load_file(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return []

def save_file(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# =========================
# OPENAI HELPERS
# =========================

def get_standard_response(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ]
    )
    return response.choices[0].message.content

def get_json_response(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ]
    )
    return loads(response.choices[0].message.content)

# =========================
# AUTH
# =========================

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

# =========================
# HOME
# =========================

@app.route("/")
def home():
    if "username" not in session:
        return redirect("/login")
    return render_template("home.html", username=session["username"])

# =========================
# LANGUAGE PAGE
# =========================

@app.route("/language")
def language():
    if "username" not in session:
        return redirect("/login")
    return render_template("index.html")

# =========================
# START LANGUAGE GAME
# =========================

@app.route("/start_language", methods=["POST"])
def start_language():

    data = request.json
    langy = data.get("lang")
    dify = data.get("diffy")

    words = get_standard_response(
        "return a python list of 5 vocabulary words only",
        f"give 5 vocab words in {langy} difficulty {dify}"
    )

    questions = get_json_response(
        """Return JSON:
        {
        "q1": "question text",
        "q1a": ["a","b","c","d"],
        "q1correct": 2
        }
        Repeat for q1 to q5.
        """,
        f"Create 5 multiple choice translation questions into {langy} using {words}"
    )

    session["questions"] = questions

    return jsonify({"questions":questions})

# =========================
# SUBMIT LANGUAGE ANSWERS
# =========================

@app.route("/submit_language", methods=["POST"])
def submit_language():

    answers = request.json.get("answers")
    questions = session.get("questions")
    username = session.get("username")

    results = []
    score = 0

    for i in range(1,6):
        correct = questions[f"q{i}correct"]
        user_answer = answers[i-1]

        is_correct = str(correct) == str(user_answer)

        if is_correct:
            score += 1

        results.append({
            "question": questions[f"q{i}"],
            "choices": questions[f"q{i}a"],
            "correct": correct,
            "user": user_answer,
            "is_correct": is_correct
        })

    # Save leaderboard
    data = load_file(LANG_FILE)
    data.append({"user":username,"score":score})
    data = sorted(data, key=lambda x: x["score"], reverse=True)[:5]
    save_file(LANG_FILE, data)

    return jsonify({
        "score":score,
        "results":results
    })

# =========================
# LANGUAGE LEADERBOARD
# =========================

@app.route("/language_leaderboard")
def get_language_leaderboard():
    return jsonify(load_file(LANG_FILE))

# =========================
# FLAPPY
# =========================

@app.route("/flappy")
def flappy():
    if "username" not in session:
        return redirect("/login")
    return render_template("flappy.html")

@app.route("/submit_flappy_score", methods=["POST"])
def submit_flappy_score():
    score = request.json.get("score")
    user = session["username"]

    data = load_file(FLAPPY_FILE)
    data.append({"user":user,"score":score})
    data = sorted(data, key=lambda x: x["score"], reverse=True)[:5]
    save_file(FLAPPY_FILE, data)

    return jsonify({"status":"saved"})

@app.route("/get_flappy_leaderboard")
def get_flappy_leaderboard():
    return jsonify(load_file(FLAPPY_FILE))

if __name__ == "__main__":
    app.run(debug=True)