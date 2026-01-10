from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from os import getenv
from dotenv import load_dotenv
from json import loads

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=getenv("api_key")
)

ALLOWED_DIFFICULTIES = ["Easy", "Medium", "Hard", "Impossible", "No Brainer"]

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
    except Exception as e:
        return f"Error generating response: {str(e)}"

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
    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    try:
        data = request.json
        if not data or "language" not in data or "difficulty" not in data:
            return jsonify({"error": "Missing language or difficulty"}), 400

        langy = data["language"]
        dify = data["difficulty"]

        if dify not in ALLOWED_DIFFICULTIES:
            return jsonify({"error": "Invalid difficulty selected"}), 400

        words = get_standard_response(
            "you are a language tutor, return the answer as just a python list of the words as strings",
            "give us 5 vocab words in " + langy + " in difficulty " + dify
        )

        questions = get_json_response(
            """you are a language tutor, use different answers on each question, and all the correct answers are different numbers [it cant be the number 1 for all of them]. return 5 multiple choice questions you come up with in json format:
            {'q1':'question text','q1a':['a','b','c','d']}""",
            "come up with multiple choice questions with 4 answers only one answer being the correct translation. the questions will ask users to translate english words into "
            + langy + " words using this list of words " + words
        )

        if "error" in questions:
            return jsonify({"error": questions["error"]}), 500

        return jsonify({"questions": questions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        if not data or "questions" not in data or "answers" not in data:
            return jsonify({"error": "Missing questions or answers"}), 400

        questions = data["questions"]
        answers = data["answers"]

        result = get_standard_response(
            "You are a language tutor, can you tell me if the answers I got are right? The questions are provided in dictinory format with the first question being under key q1 and the answers being under q1a. At the end will be a list of all the answers I chose.",
            str(questions) + " questions are done, here is list of answers " + str(answers)
        )

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
