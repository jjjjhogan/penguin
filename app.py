from flask import Flask, render_template, request, jsonify, session, redirect
import json
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = "penguin_secret_key"

client = OpenAI(api_key=os.getenv('api_key'))

LANG_FILE = "language_leaderboard.json"


def load_language():
    if not os.path.exists(LANG_FILE):
        return {}

    try:
        with open(LANG_FILE, "r") as f:
            return json.loads(f)
    except:
        return {}


def save_language(data):
    with open(LANG_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")

    if not username:
        return redirect("/")

    session["username"] = username
    return redirect("/home")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")

    return render_template("home.html", username=session["username"])


@app.route("/language")
def language():
    if "username" not in session:
        return redirect("/")

    return render_template("language.html")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@app.route("/flappy")
def flappy():
    return render_template("flappy.html")


@app.route("/start_language", methods=["POST"])
def start_language():

    if "username" not in session:
        return jsonify({"error": "not logged in"}), 401

    data = request.get_json()

    language = data.get("language")
    difficulty = data.get("difficulty")

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Return exactly 5 language questions in JSON format {questions:[{question:'',options:['','','',''],answer:0}]}"
            },
            {
                "role": "user",
                "content": f"Create 5 {difficulty} English to {language} translation questions."
            }
        ]
    )

    questions_json = json.loads(response.choices[0].message.content)

    session["questions"] = questions_json["questions"]

    return jsonify(questions_json)


@app.route("/submit_language", methods=["POST"])
def submit_language():

    if "questions" not in session:
        return jsonify({"error": "no questions"}), 400

    data = request.get_json()
    answers = data.get("answers", [])

    questions = session["questions"]

    correct = 0
    feedback = []

    for i, q in enumerate(questions):

        user = answers[i] if i < len(answers) else -1
        correct_answer = q["answer"]

        if user == correct_answer:
            correct += 1
            feedback.append({"status": "correct"})
        else:
            feedback.append({"status": "wrong", "correct": q["options"][correct_answer]})

    xp = correct
    leaderboard = load_language()
    print('debug: ' +str(type(leaderboard)))
    print(leaderboard)
    username = session["username"]

    if username not in leaderboard:
        leaderboard[username] = {"xp": 0, "level": 1}

    leaderboard[username]["xp"] += xp

    while leaderboard[username]["xp"] >= 20:
        leaderboard[username]["xp"] -= 20
        leaderboard[username]["level"] += 1

    save_language(leaderboard)

    return jsonify({
        "correct": correct,
        "xp": xp,
        "feedback": feedback
    })


@app.route("/language_leaderboard", methods=["GET"])
def language_leaderboard():
    leaderboard = load_language()
    return jsonify(leaderboard)


if __name__ == "__main__":
    app.run(debug=True)