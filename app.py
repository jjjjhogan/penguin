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

@app.route("/set_penguin_color", methods=["POST"])
def set_penguin_color():

    if "username" not in session:
        return jsonify({"error": "not logged in"}), 401

    data = request.get_json()
    color = data.get("color")

    leaderboard = load_language()

    user = session["username"]

    if user not in leaderboard:
        return jsonify({"error": "user not found"}), 404

    # update color
    leaderboard[user]["penguin"]["color"] = color

    save_language(leaderboard)

    return jsonify({"success": True})

def load_language():
    if not os.path.exists(LANG_FILE):
        return {}
    with open(LANG_FILE, "r") as f:
        return json.load(f)

def save_language(data):
    with open(LANG_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/penguin")
def penguin():
    if "username" not in session:
        return redirect("/")

    leaderboard = load_language()
    user = leaderboard.get(session["username"])

    return render_template("penguin.html", user=user)

@app.route("/penguin_talk", methods=["POST"])
def penguin_talk():

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Say a short fun language fact in a random language with translation."
            }
        ]
    )

    return jsonify({
        "message": response.choices[0].message.content
    })

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")

    if not username:
        return redirect("/")

    session["username"] = username
    leaderboard = load_language()


    if username not in leaderboard:
        leaderboard[username] = {
            "score": 0,
            "xp": 0,
            "level": 1,
            "penguin": {
                "color": "#000000",
                "outfit": "none"
            }
        }
    save_language(leaderboard)
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
    language = data.get("language", "").strip()
    difficulty = data.get("difficulty")

    # 👇 Make No-Brainer easier
    if difficulty == "no-brainer":
        prompt_text = f"Create 5 VERY EASY beginner English to {language} translation questions. Use simple words like cat, dog, house."
    else:
        prompt_text = f"Create 5 {difficulty} difficulty English to {language} translation questions."

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Return JSON: {questions:[{question:'',options:['','','',''],answer:0}]}"
            },
            {
                "role": "user",
                "content": prompt_text
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

    user = session["username"]

    if user not in leaderboard:
        leaderboard[user] = {
            "score": 0,
            "xp": 0,
            "level": 1,
            "penguin": {
                "color": "#000000",
                "outfit": "none"
            }
        }

    leaderboard[user]["score"] += correct
    leaderboard[user]["xp"] += correct

    # LEVEL UP (20 xp per level)
    if(leaderboard[user]["xp"]p >= 20):
        xp -= 20
    leaderboard[user]["level"] = new_level

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

@app.route("/start_conversation", methods=["POST"])
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


if __name__ == "__main__":
    app.run(debug=True)