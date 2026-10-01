from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

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
            flash(
                "Registration failed. Please try again.",
                "error"
            )
            return redirect(url_for("register"))

        # -------------------------------------------------
        # CREATE PROFILE
        # -------------------------------------------------

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
        flash(
            "Please enter your email and password.",
            "error"
        )
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
            flash(
                "Invalid email or password.",
                "error"
            )
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
# CREATE QUIZ PAGE
# =========================================================

@app.route("/create-quiz")
def create_quiz():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("create_quiz.html")


# =========================================================
# CREATE QUIZ API
# =========================================================

@app.route("/api/create-quiz", methods=["POST"])
def create_quiz_api():

    try:

        # -------------------------------------------------
        # CHECK LOGIN
        # -------------------------------------------------

        if "user_id" not in session:
            return jsonify({
                "success": False,
                "error": "You must be logged in to create a quiz."
            }), 401

        # -------------------------------------------------
        # GET JSON DATA
        # -------------------------------------------------

        data = request.get_json(silent=True)

        print("========================================")
        print("CREATE QUIZ REQUEST")
        print("DATA:", data)
        print("========================================")

        if not data:
            return jsonify({
                "success": False,
                "error": "No quiz data received."
            }), 400

        # -------------------------------------------------
        # GET QUIZ INFORMATION
        # -------------------------------------------------

        title = str(
            data.get("title", "")
        ).strip()

        game_mode = str(
            data.get("game_mode", "classic")
        ).strip()

        questions = data.get(
            "questions",
            []
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not title:
            return jsonify({
                "success": False,
                "error": "Quiz title is required."
            }), 400

        if not questions:
            return jsonify({
                "success": False,
                "error": "Please add at least one question."
            }), 400

        if not isinstance(questions, list):
            return jsonify({
                "success": False,
                "error": "Invalid questions format."
            }), 400

        # -------------------------------------------------
        # CREATE QUIZ IN SUPABASE
        # -------------------------------------------------

        quiz_data = {
            "title": title,
            "game_mode": game_mode
        }

        quiz_result = (
            supabase
            .table("quizzes")
            .insert(quiz_data)
            .execute()
        )

        print("QUIZ RESULT:", quiz_result.data)

        if not quiz_result.data:
            return jsonify({
                "success": False,
                "error": "Could not create quiz in Supabase."
            }), 500

        quiz = quiz_result.data[0]

        quiz_id = quiz.get("id")

        if not quiz_id:
            return jsonify({
                "success": False,
                "error": "Quiz ID was not returned by Supabase."
            }), 500

        # -------------------------------------------------
        # PREPARE QUESTIONS
        # -------------------------------------------------

        question_rows = []

        for index, question in enumerate(questions, start=1):

            question_type = str(
                question.get(
                    "question_type",
                    "multiple_choice"
                )
            ).strip()

            question_text = str(
                question.get(
                    "question_text",
                    ""
                )
            ).strip()

            correct_answer = str(
                question.get(
                    "correct_answer",
                    ""
                )
            ).strip()

            option_a = str(
                question.get(
                    "option_a",
                    ""
                )
            ).strip()

            option_b = str(
                question.get(
                    "option_b",
                    ""
                )
            ).strip()

            option_c = str(
                question.get(
                    "option_c",
                    ""
                )
            ).strip()

            option_d = str(
                question.get(
                    "option_d",
                    ""
                )
            ).strip()

            # Timer
            try:
                timer = int(
                    question.get(
                        "timer",
                        30
                    )
                )
            except (ValueError, TypeError):
                timer = 30

            # Make sure timer is reasonable
            if timer <= 0:
                timer = 30

            # Validate question
            if not question_text:
                return jsonify({
                    "success": False,
                    "error": f"Question {index} has no question text."
                }), 400

            if not correct_answer:
                return jsonify({
                    "success": False,
                    "error": f"Question {index} has no correct answer."
                }), 400

            # Add question row
            question_rows.append({
                "quiz_id": quiz_id,
                "question_type": question_type,
                "question_text": question_text,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_answer": correct_answer,
                "timer": timer
            })

        # -------------------------------------------------
        # INSERT ALL QUESTIONS
        # -------------------------------------------------

        question_result = (
            supabase
            .table("questions")
            .insert(question_rows)
            .execute()
        )

        print(
            "QUESTION RESULT:",
            question_result.data
        )

        # -------------------------------------------------
        # CHECK QUESTION INSERT
        # -------------------------------------------------

        if not question_result.data:

            # Delete quiz if questions failed
            try:
                (
                    supabase
                    .table("quizzes")
                    .delete()
                    .eq("id", quiz_id)
                    .execute()
                )
            except Exception as cleanup_error:
                print(
                    "CLEANUP ERROR:",
                    cleanup_error
                )

            return jsonify({
                "success": False,
                "error": (
                    "Quiz was created but "
                    "questions could not be saved."
                )
            }), 500

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Quiz created successfully!",
            "quiz_id": quiz_id,
            "question_count": len(
                question_result.data
            )
        }), 201

    except Exception as e:

        print("========================================")
        print("CREATE QUIZ ERROR:")
        print(str(e))
        print("========================================")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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

    return render_template(
        "leaderboard.html"
    )


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "reports.html"
    )


# =========================================================
# ANIMALS
# =========================================================

@app.route("/animals")
def animals():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "animals.html"
    )


# =========================================================
# API TEST
# =========================================================

@app.route("/api/test")
def api_test():

    return jsonify({
        "success": True,
        "message": "QuizUp Flask API is working!"
    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
