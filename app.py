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
    flash
)

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-only-change-this-secret-key"
)

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
# MY QUIZZES PAGE (HTML is built into app.py,
# so no extra template file is needed)
# ==========================================

MY_QUIZZES_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QuizUp - My Quizzes</title>
  <style>
    body { font-family: Arial, sans-serif; background:#f4f3ff; margin:0; color:#1e1b3a; }
    .nav { background:linear-gradient(90deg,#5b3fd6,#3b82f6); padding:16px 28px;
           display:flex; justify-content:space-between; align-items:center; }
    .nav .brand { color:#fff; font-size:22px; font-weight:bold; text-decoration:none; }
    .nav a.link { color:#fff; text-decoration:none; margin-left:18px; font-weight:bold; font-size:14px; }
    .wrap { max-width:900px; margin:30px auto; padding:0 16px; }
    .top { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }
    .card { background:#fff; border-radius:16px; padding:18px; margin:14px 0;
            box-shadow:0 2px 10px rgba(0,0,0,.06); }
    .card h3 { margin:0 0 4px; }
    .meta { color:#666; font-size:14px; }
    .btn { border:0; border-radius:10px; padding:8px 14px; cursor:pointer;
           background:#6d28d9; color:#fff; text-decoration:none; font-size:14px; display:inline-block; }
    .btn.red { background:#fee2e2; color:#b91c1c; }
    .qs { display:none; margin-top:12px; padding-left:18px; }
    .qs li { margin:8px 0; }
  </style>
</head>
<body>
  <div class="nav">
    <a class="brand" href="/dashboard">QuizUp</a>
    <div>
      <a class="link" href="/dashboard">Dashboard</a>
      <a class="link" href="/my-quizzes">My Quizzes</a>
      <a class="link" href="/join-game">Join Game</a>
      <a class="link" href="/leaderboard">Leaderboard</a>
      <a class="link" href="/reports">Reports</a>
      <a class="link" href="/logout">Logout</a>
    </div>
  </div>

  <div class="wrap">
    <div class="top">
      <h1>My Quizzes</h1>
      <a class="btn" href="/create-quiz">+ Create Quiz</a>
    </div>

    <div id="list">Loading...</div>
  </div>

  <script>
    const list = document.getElementById("list");

    function esc(s) {
      const d = document.createElement("div");
      d.textContent = s ?? "";
      return d.innerHTML;
    }

    async function loadQuizzes() {
      try {
        const res = await fetch("/api/my-quizzes");
        const data = await res.json();

        if (!res.ok) {
          list.textContent = data.error || "Something went wrong.";
          return;
        }

        if (!data.quizzes.length) {
          list.innerHTML = "<p>You have no quizzes yet. <a href='/create-quiz'>Create one</a>!</p>";
          return;
        }

        list.innerHTML = data.quizzes.map(q => `
          <div class="card">
            <h3>${esc(q.title)}</h3>
            <div class="meta">${esc(q.game_mode)} • ${(q.questions || []).length} question(s)</div>
            <div style="margin-top:10px">
              <button class="btn" onclick="toggleQs('${q.id}')">View Questions</button>
              <button class="btn red" onclick="deleteQuiz('${q.id}')">Delete</button>
            </div>
            <ol class="qs" id="qs-${q.id}">
              ${(q.questions || []).map(x => `
                <li>${esc(x.question)}<br>
                    <span class="meta">Answer: ${esc(x.correct_answer)}</span></li>
              `).join("")}
            </ol>
          </div>
        `).join("");
      } catch (e) {
        list.textContent = "Could not load quizzes.";
      }
    }

    function toggleQs(id) {
      const el = document.getElementById("qs-" + id);
      el.style.display = el.style.display === "block" ? "none" : "block";
    }

    async function deleteQuiz(id) {
      if (!confirm("Delete this quiz and all its questions?")) return;
      const res = await fetch("/api/quizzes/" + id, { method: "DELETE" });
      if (res.ok) loadQuizzes();
      else alert("Could not delete the quiz.");
    }

    loadQuizzes();
  </script>
</body>
</html>
'''


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

        if not result.user:
            flash("Login failed. Please try again.", "error")
            return render_template("login.html"), 401

        # Create a new session after successful login.
        session.clear()
        session["user_id"] = str(result.user.id)
        session["user_email"] = result.user.email or email

        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))

    except Exception:
        app.logger.exception("Login failed")

        flash(
            "Login failed. Check your email and password. "
            "If you registered recently, verify your email first.",
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
        flash(
            "Password must be at least 6 characters long.",
            "error"
        )
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

        if not result.user:
            flash("Registration failed. Please try again.", "error")
            return render_template("register.html"), 400

        # Supabase may require email verification.
        if result.session:
            session.clear()
            session["user_id"] = str(result.user.id)
            session["user_email"] = result.user.email or email

            flash("Registration successful!", "success")
            return redirect(url_for("dashboard"))

        flash(
            "Registration successful! Check your email "
            "to verify your account before logging in.",
            "success"
        )
        return redirect(url_for("login"))

    except Exception:
        app.logger.exception("Registration failed")

        flash(
            "Registration failed. The email may already exist, "
            "or Supabase Auth may need checking.",
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
        flash("Please log in first.", "error")
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
# MY QUIZZES (PAGE + API)
# ==========================================

@app.route("/my-quizzes")
def my_quizzes():

    if not session.get("user_id"):
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    # Returned as plain HTML (no Jinja processing).
    return MY_QUIZZES_HTML


@app.route("/api/my-quizzes")
def api_my_quizzes():

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        result = (
            supabase.table("quizzes")
            .select("*, questions(*)")
            .eq("host_id", session["user_id"])
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify({"quizzes": result.data or []}), 200

    except Exception:
        app.logger.exception("Load my quizzes failed")
        return jsonify({"error": "Could not load your quizzes."}), 500


@app.route("/api/quizzes/<quiz_id>", methods=["DELETE"])
def api_delete_quiz(quiz_id):

    if not session.get("user_id"):
        return jsonify({"error": "Please log in first."}), 401

    try:
        # Make sure the quiz belongs to the logged-in user.
        owned = (
            supabase.table("quizzes")
            .select("id")
            .eq("id", quiz_id)
            .eq("host_id", session["user_id"])
            .execute()
        )

        if not owned.data:
            return jsonify({"error": "Quiz not found."}), 404

        supabase.table("questions").delete().eq(
            "quiz_id", quiz_id
        ).execute()

        supabase.table("quizzes").delete().eq(
            "id", quiz_id
        ).execute()

        return jsonify({"success": True}), 200

    except Exception:
        app.logger.exception("Delete quiz failed")
        return jsonify({"error": "Could not delete the quiz."}), 500


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

                if correct_answer.casefold() not in {
                    "true", "false"
                }:
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
                "question": question_text,
                "question_type": question_type,
                "correct_answer": correct_answer,
                "choices": choices
            })

        # Save quiz (now linked to the logged-in user via host_id).
        quiz_result = (
            supabase.table("quizzes")
            .insert({
                "title": title,
                "description": "",
                "game_mode": game_mode,
                "host_id": session["user_id"]
            })
            .execute()
        )

        if not quiz_result.data:
            raise RuntimeError("Quiz was not returned after insertion.")

        quiz_id = quiz_result.data[0]["id"]

        # Link every question to its quiz.
        for row in question_rows:
            row["quiz_id"] = quiz_id

        # Save all questions.
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
