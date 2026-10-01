from flask import Flask, render_template
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY


# =========================
# FLASK APP
# =========================

app = Flask(__name__)


# =========================
# SUPABASE
# =========================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# LOGIN
# =========================

@app.route("/login")
def login():
    return render_template("login.html")


# =========================
# REGISTER
# =========================

@app.route("/register")
def register():
    return render_template("register.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =========================
# CREATE QUIZ
# =========================

@app.route("/create-quiz")
def create_quiz():
    return render_template("create_quiz.html")


# =========================
# JOIN GAME
# =========================

@app.route("/join-game")
def join_game():
    return render_template("join_game.html")


# =========================
# PLAY QUIZ
# =========================

@app.route("/play")
def play():
    return render_template("play_quiz.html")


# =========================
# LEADERBOARD
# =========================

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


# =========================
# REPORTS
# =========================

@app.route("/reports")
def reports():
    return render_template("reports.html")


# =========================
# ANIMAL PLAYERS
# =========================

@app.route("/animals")
def animals():
    return render_template("animals.html")


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )