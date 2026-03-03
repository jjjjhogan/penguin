from flask import Flask, render_template, request, session, redirect, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = "penguin_secret"

LANG_FILE = "language_leaderboard.json"

# ========================
# LOAD / SAVE LANGUAGE DATA
# ========================

def load_language():
    if not os.path.exists(LANG_FILE):
        return []
    with open(LANG_FILE, "r") as f:
        return json.load(f)

def save_language(data):
    with open(LANG_FILE, "w") as f:
        json.dump(data, f)

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
        session["username"] = request.form["username"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ========================
# LANGUAGE LEADERBOARD PAGE
# ========================

@app.route("/language_leaderboard")
def language_leaderboard():
    data = load_language()
    data = sorted(data, key=lambda x: x["xp"], reverse=True)
    return render_template("leaderboard.html", leaderboard=data)

# ========================
# LANGUAGE LEADERBOARD DATA FOR GRAPH
# ========================

@app.route("/language_leaderboard_data")
def language_leaderboard_data():
    data = load_language()
    data = sorted(data, key=lambda x: x["xp"], reverse=True)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)