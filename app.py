
import os
import logging

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash,
)
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    app.secret_key = "change-this-to-a-long-random-secret-before-deploying"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("RENDER") is not None
)

logging.basicConfig(level=logging.INFO)


# ==========================================
# SUPABASE CONNECTION
# ==========================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter your email and password.", "error")
        return render_template("login.html"), 400

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user = result.user

        if not user:
            flash("Login failed. Please check your credentials.", "error")
            return render_template("login.html"), 401

        # Store only the user ID and email in the Flask session.
        session.clear()
        session["user_id"] = str(user.id)
        session["user_email"] = user.email or email

        return redirect(url_for("dashboard"))

    except Exception:
        app.logger.exception("Login failed")
        flash(
            "Login failed. Check your email and password, "
            "or verify your Supabase Auth configuration.",
            "error"
        )
        return render_template("login.html"), 401


# ==========================================
# REGISTER
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    full_name = (
        request.form.get("full_name")
        or request.form.get("name")
        or ""
    ).strip()

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not full_name or not email or not password:
        flash("Please complete all required fields.", "error")
        return render_template("register.html"), 400

    if len(password) < 6:
        flash("Your password must be at least 6 characters.", "error")
        return render_template("register.html"), 400

    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })

        user = result.user

        if not user:
            flash(
                "Registration could not be completed. Please try again.",
                "error"
            )
            return render_template("register.html"), 400

        # Supabase may require email verification before login.
        if result.session:
            session.clear()
            session["user_id"] = str(user.id)
            session["user_email"] = user.email or email

            return redirect(url_for("dashboard"))

        flash(
            "Registration successful! Check your email to verify "
            "your account before logging in.",
            "success"
        )
        return redirect(url_for("login"))

    except Exception:
        app.logger.exception("Registration failed")
        flash(
            "Registration failed. The email may already be registered, "
            "or Supabase Auth needs to be checked.",
            "error"
        )
        return render_template("register.html"), 400


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("dashboard.html")


# ==========================================
# CREATE QUIZ PAGE
# ==========================================

@app.route("/create-quiz")
def create_quiz():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("create_quiz.html")


# ==========================================
# JOIN GAME
# ==========================================

@app.route("/join-game")
def join_game():
    return render_template("join_game.html")


# ==========================================
# PLAY QUIZ
# ==========================================

@app.route("/play")
def play():
    return render_template("play_quiz.html")


# ==========================================
# LEADERBOARD
# ==========================================

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


# ==========================================
# REPORTS
# ==========================================

@app.route("/reports")
def reports():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("reports.html")


# ==========================================
# ANIMALS
# ==========================================

@app.route("/animals")
def animals():
    return render_template("animals.html")


# ==========================================
# CREATE QUIZ API
# ==========================================

@app.route("/api/create-quiz", methods=["POST"])
def api_create_quiz():
    if not session.get("user_id"):
        return jsonify({
            "error": "Please log in before creating a quiz."
        }), 401

    quiz_id = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request data."
            }), 400

        title = str(data.get("title", "")).strip()
        game_mode = str(
            data.get("game_mode", "classic")
        ).strip()
        questions = data.get("questions", [])

        if not title:
            return jsonify({
                "error": "Please enter a quiz title."
            }), 400

        if game_mode not in ("classic", "team", "accuracy"):
            return jsonify({
                "error": "Invalid game mode."
            }), 400

        if not isinstance(questions, list) or not questions:
            return jsonify({
                "error": "Please add at least one question."
            }), 400

        question_rows = []

        allowed_types = {
            "multiple_choice",
            "true_false",
            "jumbled",
            "type_answer"
        }

        for index, item in enumerate(questions, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Question {index} has invalid data."
                )

            question_text = str(
                item.get("question_text", "")
            ).strip()

            question_type = str(
                item.get("question_type", "")
            ).strip()

            correct_answer = str(
                item.get("correct_answer", "")
            ).strip()

            if not question_text or not correct_answer:
                raise ValueError(
                    f"Question {index} needs a question "
                    "and a correct answer."
                )

            if question_type not in allowed_types:
                raise ValueError(
                    f"Question {index} has an invalid type."
                )

            try:
                timer = int(item.get("timer", 30))
            except (ValueError, TypeError):
                timer = 30

            timer = max(5, min(timer, 300))

            choices = {
                "A": str(item.get("option_a", "")).strip(),
                "B": str(item.get("option_b", "")).strip(),
                "C": str(item.get("option_c", "")).strip(),
                "D": str(item.get("option_d", "")).strip(),
                "timer": timer
            }

            if question_type == "multiple_choice":
                options = [
                    choices["A"],
                    choices["B"],
                    choices["C"],
                    choices["D"]
                ]

                if not all(options):
                    raise ValueError(
                        f"Question {index} needs all four choices."
                    )

                if correct_answer.casefold() not in [
                    option.casefold() for option in options
                ]:
                    raise ValueError(
                        f"Question {index}: the correct answer "
                        "must match one of the choices."
                    )

            elif question_type == "true_false":
                if correct_answer.casefold() not in {"true", "false"}:
                    raise ValueError(
                        f"Question {index}: answer must be True or False."
                    )

                correct_answer = (
                    "True"
                    if correct_answer.casefold() == "true"
                    else "False"
                )

                choices = {
                    "A": "True",
                    "B": "False",
                    "timer": timer
                }

            question_rows.append({
                "quiz_id": None,
                "question": question_text,
                "question_type": question_type,
                "correct_answer": correct_answer,
                "choices": choices
            })

        # Insert quiz using the columns confirmed in your database.
        quiz_result = (
            supabase.table("quizzes")
            .insert({
                "title": title,
                "description": "",
                "game_mode": game_mode
            })
            .execute()
        )

        if not quiz_result.data:
            raise RuntimeError("Supabase did not return the saved quiz.")

        quiz_id = quiz_result.data[0]["id"]

        for row in question_rows:
            row["quiz_id"] = quiz_id

        # Insert every question linked to this quiz.
        supabase.table("questions").insert(
            question_rows
        ).execute()

        return jsonify({
            "success": True,
            "message": "Quiz created successfully!",
            "quiz_id": quiz_id
        }), 201

    except ValueError as error:
        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception("Quiz cleanup failed")

        return jsonify({
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Create quiz failed")

        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception("Quiz cleanup failed")

        return jsonify({
            "error": (
                "Could not save the quiz. "
                "Check the Render logs for the detailed error."
            )
        }), 500


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "QuizUp"
    }), 200


# ==========================================
# RUN LOCAL SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
