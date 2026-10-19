from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

app = Flask(__name__)

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================
# HOME AND PAGE ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/create-quiz")
def create_quiz():
    return render_template("create_quiz.html")


@app.route("/join-game")
def join_game():
    return render_template("join_game.html")


@app.route("/play")
def play():
    return render_template("play_quiz.html")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/animals")
def animals():
    return render_template("animals.html")


# =========================
# CREATE QUIZ API
# =========================

@app.route("/api/create-quiz", methods=["POST"])
def api_create_quiz():
    quiz_id = None

    try:
        data = request.get_json(silent=True) or {}

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

        # Save the quiz using existing database columns.
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
            return jsonify({
                "error": "Quiz could not be saved."
            }), 500

        quiz_id = quiz_result.data[0]["id"]

        # Prepare all questions for insertion.
        question_rows = []

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

            if question_type not in (
                "multiple_choice",
                "true_false",
                "jumbled",
                "type_answer"
            ):
                raise ValueError(
                    f"Question {index} has an invalid type."
                )

            # Store choices and timer in the existing JSONB column.
            choices = {
                "A": str(item.get("option_a", "")).strip(),
                "B": str(item.get("option_b", "")).strip(),
                "C": str(item.get("option_c", "")).strip(),
                "D": str(item.get("option_d", "")).strip(),
                "timer": int(item.get("timer", 30) or 0)
            }

            question_rows.append({
                "quiz_id": quiz_id,
                "question": question_text,
                "question_type": question_type,
                "correct_answer": correct_answer,
                "choices": choices
            })

        # Insert all questions.
        supabase.table("questions").insert(
            question_rows
        ).execute()

        return jsonify({
            "message": "Quiz created successfully!",
            "quiz_id": quiz_id
        }), 201

    except ValueError as error:
        # Remove the quiz if validation failed after quiz creation.
        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception(
                    "Could not clean up incomplete quiz."
                )

        return jsonify({"error": str(error)}), 400

    except Exception:
        app.logger.exception("Create quiz failed.")

        # Avoid leaving an empty quiz if saving questions failed.
        if quiz_id is not None:
            try:
                supabase.table("quizzes").delete().eq(
                    "id", quiz_id
                ).execute()
            except Exception:
                app.logger.exception(
                    "Could not clean up incomplete quiz."
                )

        return jsonify({
            "error": (
                "Could not save the quiz. "
                "Check the Render logs for details."
            )
        }), 500


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
