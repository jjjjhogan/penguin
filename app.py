from flask import Flask, render_template, request, session, redirect, jsonify
import json

app = Flask(__name__)
app.secret_key = "penguin_secret"

FLAPPY_FILE = "flappy_scores.json"

def load_flappy():
    try:
        with open(FLAPPY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_flappy(data):
    with open(FLAPPY_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    if "username" not in session:
        return redirect("/login")
    return render_template("home.html", username=session["username"])

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

@app.route("/flappy")
def flappy():
    if "username" not in session:
        return redirect("/login")
    return render_template("flappy.html")

@app.route("/submit_flappy_score", methods=["POST"])
def submit_flappy_score():
    if "username" not in session:
        return jsonify({"status":"no_user"})

    score = request.json.get("score")
    user = session["username"]

    data = load_flappy()
    data.append({"user":user,"score":score})

    data = sorted(data, key=lambda x: x["score"], reverse=True)[:5]
    save_flappy(data)

    return jsonify({"status":"saved"})

@app.route("/get_flappy_leaderboard")
def get_flappy_leaderboard():
    return jsonify(load_flappy())

if __name__ == "__main__":
    app.run(debug=True)