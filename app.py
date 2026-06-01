from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from openai import OpenAI
from dotenv import load_dotenv

import os
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = "penguin_secret_key"

# ================= DATABASE =================

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ================= OPENAI =================

client = OpenAI(api_key=os.getenv("api_key"))

# ================= MODELS =================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    score = db.Column(db.Integer, default=0)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

    penguin_color = db.Column(db.String(20), default="#000000")
    penguin_outfit = db.Column(db.String(50), default="none")

# ================= ROUTES =================

@app.route("/")
def root():
    return redirect("/login")

# ================= LOGIN =================

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/login_user", methods=["POST"])
def login_user():

    username = request.form["username"]
    print(username)

    if not username:
        return jsonify({"error": "No username"}), 400

    session["username"] = username

    user = User.query.filter_by(username=username).first()

    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    return redirect("/home")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= HOME =================

@app.route("/home")
def home():

    if "username" not in session:
        return redirect("/login")

    return render_template("home.html")

# ================= LANGUAGE GAME =================

@app.route("/language")
def language():

    if "username" not in session:
        return redirect("/login")

    return render_template("language.html")

@app.route("/start_language", methods=["POST"])
def start_language():

    data = request.get_json()

    language = data.get("language", "").strip()
    difficulty = data.get("difficulty")

    try:

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """
Return EXACT JSON:

{
  "questions":[
    {
      "question":"",
      "options":["","","",""],
      "answer":0
    }
  ]
}
"""
                },
                {
                    "role": "user",
                    "content": f"""
Create 5 {difficulty} multiple choice questions
for learning {language}.
"""
                }
            ]
        )

        questions_json = json.loads(
            response.choices[0].message.content
        )

        session["questions"] = questions_json["questions"]

        return jsonify(questions_json)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route("/submit_language", methods=["POST"])
def submit_language():

    if "questions" not in session:
        return jsonify({"error": "No questions"}), 400

    data = request.get_json()

    answers = data.get("answers", [])

    questions = session["questions"]

    correct = 0

    for i, q in enumerate(questions):

        if i < len(answers):

            if answers[i] == q["answer"]:
                correct += 1

    user = User.query.filter_by(
        username=session["username"]
    ).first()

    user.score += correct
    user.xp += correct

    user.level = user.xp // 20 + 1

    db.session.commit()

    return jsonify({
        "correct": correct,
        "xp": user.xp,
        "level": user.level
    })

# ================= LEADERBOARD =================

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/leaderboard_data")
def leaderboard_data():

    users = User.query.order_by(User.score.desc()).all()

    results = []

    for u in users:

        results.append({
            "username": u.username,
            "score": u.score,
            "level": u.level,
            "penguin_color": u.penguin_color
        })

    return jsonify(results)

# ================= PENGUIN =================

@app.route("/penguin")
def penguin():

    if "username" not in session:
        return redirect("/login")

    user = User.query.filter_by(
        username=session["username"]
    ).first()

    return render_template(
        "penguin.html",
        user=user
    )

@app.route("/set_penguin_color", methods=["POST"])
def set_penguin_color():

    data = request.get_json()

    color = data.get("color")

    user = User.query.filter_by(
        username=session["username"]
    ).first()

    user.penguin_color = color

    db.session.commit()

    return jsonify({"success": True})

@app.route("/penguin_talk", methods=["POST"])
def penguin_talk():

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
Say a short fun language fact
in a random language and
include English translation.
"""
            }
        ]
    )

    return jsonify({
        "message":
        response.choices[0].message.content
    })

def start_conversation():

    if "username" not in session:
        return jsonify({"error": "not logged in"}), 401

    data = request.get_json()
    language = data.get("language").strip()
    difficulty = data.get("difficulty")

    # difficulty control
    if difficulty == "easy":
        instruction = "short simple sentences"
    elif difficulty == "medium":
        instruction = "medium conversational sentences"
    else:
        instruction = "long detailed conversational sentences"

    try:

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return JSON: {prompts:[{english:'', target:''}]}"
                },
                {
                    "role": "user",
                    "content": f"Create 5 {instruction} translating English into {language}."
                }
            ]
        )

        prompts = json.loads(response.choices[0].message.content)

        session["conversation"] = prompts["prompts"]

        return jsonify(prompts)

    except Exception as e:
        print("Conversation error:", e)
        return jsonify({"error": "AI failed"}), 500

@app.route("/submit_conversation", methods=["POST"])
def submit_conversation():

    if "conversation" not in session:
        return jsonify({"error": "no prompts"}), 400

    data = request.get_json()
    answers = data.get("answers", [])

    prompts = session["conversation"]

    results = []

    try:

        for i, p in enumerate(prompts):

            user_answer = answers[i] if i < len(answers) else ""

            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "Grade from 0-10. Return JSON: {score: number, feedback: '', correction: ''}"
                    },
                    {
                        "role": "user",
                        "content": f"""
English: {p['english']}
Correct: {p['target']}
User: {user_answer}
"""
                    }
                ]
            )

            grade = json.loads(response.choices[0].message.content)
            results.append(grade)

        return jsonify({"results": results})

    except Exception as e:
        print("Grading error:", e)
        return jsonify({"error": "grading failed"}), 500


@app.route("/conversation")
def conversation():
    if "username" not in session:
        return redirect("/")
    return render_template("conversation.html")


@app.route("/flappy")
def flappy():
    return render_template("flappy.html")


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)