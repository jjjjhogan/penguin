from flask import Flask, render_template, request, session, redirect, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = "penguin_secret"

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
# LANGUAGE GAME
# ========================

@app.route("/language")
def language():
    if "username" not in session:
        return redirect("/login")
    return render_template("index.html")

# ========================
# FLAPPY GAME
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

    if not os.path.exists("language_leaderboard.json"):
        data = []
    else:
        with open("language_leaderboard.json","r") as f:
            data = json.load(f)

    data = sorted(data, key=lambda x: x["xp"], reverse=True)

    return render_template("leaderboard.html", leaderboard=data)

# ========================

if __name__ == "__main__":
    app.run(debug=True)