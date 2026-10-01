from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

# Secret key para sa Flask session
app.secret_key = "quizup-flask-session-key-change-this"


# =========================================================
# SUPABASE
# =========================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    # Ipakita ang registration page
    if request.method == "GET":
        return render_template("register.html")

    # Kunin ang data mula sa form
    full_name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "student")

    # Basic validation
    if not full_name or not email or not password:
        flash("Please complete all required fields.", "error")
        return redirect(url_for("register"))

    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("register"))

    try:

        # -------------------------------------------------
        # CREATE USER IN SUPABASE AUTHENTICATION
        # -------------------------------------------------

        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        user = auth_response.user

        if not user:
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for("register"))

        # -------------------------------------------------
        # CREATE PROFILE
        # -------------------------------------------------

        # Gamitin ang Auth user's UUID bilang profile ID
        profile_data = {
            "id": str(user.id),
            "username": email.split("@")[0],
            "full_name": full_name,
            "role": role
        }

        supabase.table("profiles").upsert(
            profile_data,
            on_conflict="id"
        ).execute()

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        flash(
            "Account created successfully! You can now login.",
            "success"
        )

        return redirect(url_for("login"))

    except Exception as e:

        print("REGISTER ERROR:", e)

        flash(
            "Registration failed. Please check your information and try again.",
            "error"
        )

        return redirect(url_for("register"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Ipakita ang login page
    if request.method == "GET":
        return render_template("login.html")

    # Kunin ang login information
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter your email and password.", "error")
        return redirect(url_for("login"))

    try:

        # -------------------------------------------------
        # LOGIN THROUGH SUPABASE AUTH
        # -------------------------------------------------

        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user = auth_response.user

        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # -------------------------------------------------
        # SAVE USER INFORMATION IN FLASK SESSION
        # -------------------------------------------------

        session["user_id"] = str(user.id)
        session["email"] = user.email

        return redirect(url_for("dashboard"))

    except Exception as e:

        print("LOGIN ERROR:", e)

        flash(
            "Login failed. Please check your email and password.",
            "error"
        )

        return redirect(url_for("login"))


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    return redirect(url_for("home"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# =========================================================
# CREATE QUIZ
# =========================================================

@app.route("/create-quiz")
def create_quiz():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("create_quiz.html")


# =========================================================
# JOIN GAME
# =========================================================

@app.route("/join-game")
def join_game():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("join_game.html")


# =========================================================
# PLAY QUIZ
# =========================================================

@app.route("/play")
def play():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("play_quiz.html")


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/leaderboard")
def leaderboard():

    return render_template("leaderboard.html")


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("reports.html")


# =========================================================
# ANIMALS
# =========================================================

@app.route("/animals")
def animals():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("animals.html")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
