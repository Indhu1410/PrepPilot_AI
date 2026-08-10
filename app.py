"""
PrepPilot AI - AI Powered Interview Preparation Web Application
app.py - Main Flask application entry point.

Run with: python app.py
"""

import os
import json
import re
import random
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import models

# Optional: Gemini API integration.
# Set GEMINI_API_KEY as an environment variable to enable real AI evaluation.
# If not set, a smart local fallback evaluator is used instead so the app
# is fully functional out of the box for demonstration purposes.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_ENABLED = False
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_ENABLED = True
    except ImportError:
        GEMINI_ENABLED = False

app = Flask(__name__)
app.secret_key = "preppilot-ai-secret-key-change-in-production"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")

TOPICS = {
    "python": {"name": "Python", "icon": "bi-filetype-py", "color": "#3776AB"},
    "sql": {"name": "SQL", "icon": "bi-database", "color": "#F29111"},
    "html": {"name": "HTML", "icon": "bi-filetype-html", "color": "#E34F26"},
    "css": {"name": "CSS", "icon": "bi-filetype-css", "color": "#1572B6"},
    "javascript": {"name": "JavaScript", "icon": "bi-filetype-js", "color": "#F7DF1E"},
    "hr": {"name": "HR Interview", "icon": "bi-person-badge", "color": "#8B5CF6"},
}

MAX_ATTEMPTS = 3


# ---------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------- #

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def load_questions(topic):
    path = os.path.join(QUESTIONS_DIR, f"{topic}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_strong_password(password):
    if len(password) < 6:
        return False
    return bool(re.search(r"[A-Za-z]", password) and re.search(r"[0-9]", password))


def evaluate_answer_locally(question, correct_answer, user_answer):
    """
    Local fallback evaluator used when the Gemini API is not configured.
    Uses simple keyword-overlap heuristics to produce a reasonable score,
    correctness verdict, grammar/confidence estimate, and suggestions,
    so the app remains fully functional without external API keys.
    """
    if not user_answer or not user_answer.strip():
        return {
            "score": 0,
            "correctness": "Incorrect",
            "grammar": "N/A",
            "confidence": "Low",
            "suggestions": "You did not provide an answer. Try to explain the concept in your own words.",
            "better_answer": correct_answer
        }

    def keywords(text):
        words = re.findall(r"[a-zA-Z]+", text.lower())
        stopwords = {"the", "a", "an", "is", "are", "and", "or", "of", "to", "in",
                     "it", "that", "this", "for", "with", "as", "be", "on", "was"}
        return set(w for w in words if w not in stopwords and len(w) > 2)

    correct_kw = keywords(correct_answer)
    user_kw = keywords(user_answer)
    overlap = correct_kw & user_kw

    overlap_ratio = len(overlap) / max(len(correct_kw), 1)
    length_bonus = min(len(user_answer.split()) / 25, 1) * 10

    score = int(min(100, overlap_ratio * 90 + length_bonus))

    if score >= 70:
        correctness = "Correct"
        confidence = "High"
    elif score >= 40:
        correctness = "Partially Correct"
        confidence = "Medium"
    else:
        correctness = "Incorrect"
        confidence = "Low"

    word_count = len(user_answer.split())
    grammar = "Good" if word_count >= 8 else "Needs Improvement"

    if score >= 70:
        suggestions = "Great answer! You covered the key concepts clearly. Try adding a real-world example to make it even stronger."
    elif score >= 40:
        suggestions = "You are on the right track but missed some key points. Review the core concept again and be more specific."
    else:
        suggestions = "Your answer is missing important concepts. Revisit the topic fundamentals and try to structure your answer more clearly."

    return {
        "score": score,
        "correctness": correctness,
        "grammar": grammar,
        "confidence": confidence,
        "suggestions": suggestions,
        "better_answer": correct_answer
    }


def evaluate_answer_with_gemini(question, correct_answer, user_answer):
    """Evaluate the user's answer using the Gemini API (used only if configured)."""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
You are an expert technical interviewer. Evaluate the candidate's answer.

Question: {question}
Ideal/Reference Answer: {correct_answer}
Candidate's Answer: {user_answer}

Respond ONLY in valid JSON with these exact keys:
{{
  "score": <integer 0-100>,
  "correctness": "<Correct/Partially Correct/Incorrect>",
  "grammar": "<Good/Average/Needs Improvement>",
  "confidence": "<High/Medium/Low>",
  "suggestions": "<short constructive feedback, 1-2 sentences>",
  "better_answer": "<a concise ideal answer, 1-3 sentences>"
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception:
        return evaluate_answer_locally(question, correct_answer, user_answer)


def evaluate_answer(question, correct_answer, user_answer):
    if GEMINI_ENABLED:
        return evaluate_answer_with_gemini(question, correct_answer, user_answer)
    return evaluate_answer_locally(question, correct_answer, user_answer)


# ---------------------------------------------------------------- #
# Auth Routes
# ---------------------------------------------------------------- #

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("login"))

        user = models.get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            flash(f"Welcome back, {user['fullname']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not fullname or not email or not password or not confirm_password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))

        if not is_strong_password(password):
            flash("Password must be at least 6 characters and include letters and numbers.", "danger")
            return redirect(url_for("signup"))

        if models.get_user_by_email(email):
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)
        models.create_user(fullname, email, hashed_password)
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/google-login")
def google_login():
    # Placeholder route for Google OAuth integration.
    # To enable: configure a Google Cloud OAuth Client ID/Secret,
    # install 'Authlib' or 'google-auth-oauthlib', and redirect here
    # to Google's consent screen, then handle the callback to create/
    # log in the user via their verified Google email.
    flash("Google Sign-In is not configured yet. Please use email/password.", "info")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------- #
# Core App Routes
# ---------------------------------------------------------------- #

@app.route("/dashboard")
@login_required
def dashboard():
    stats = models.get_dashboard_stats(session["user_id"])
    return render_template("dashboard.html", stats=stats, topics=TOPICS)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = models.get_user_by_id(session["user_id"])

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            fullname = request.form.get("fullname", "").strip()
            if fullname:
                models.update_user_profile(session["user_id"], fullname)
                session["fullname"] = fullname
                flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_new_password = request.form.get("confirm_new_password", "")

            if not check_password_hash(user["password"], current_password):
                flash("Current password is incorrect.", "danger")
            elif new_password != confirm_new_password:
                flash("New passwords do not match.", "danger")
            elif not is_strong_password(new_password):
                flash("New password must be at least 6 characters with letters and numbers.", "danger")
            else:
                models.update_user_password(session["user_id"], generate_password_hash(new_password))
                flash("Password changed successfully.", "success")
            return redirect(url_for("profile"))

    user = models.get_user_by_id(session["user_id"])
    history = models.get_results_for_user(session["user_id"])
    return render_template("profile.html", user=user, history=history)


@app.route("/courses")
@login_required
def courses():
    return render_template("courses.html", topics=TOPICS)


@app.route("/interview/<topic>")
@login_required
def interview(topic):
    if topic not in TOPICS:
        flash("Invalid topic selected.", "danger")
        return redirect(url_for("courses"))

    questions = load_questions(topic)
    random.shuffle(questions)

    session["interview_topic"] = topic
    session["interview_questions"] = questions
    session["interview_index"] = 0
    session["interview_scores"] = []
    session["interview_correct"] = 0
    session["interview_wrong"] = 0

    return render_template(
        "interview.html",
        topic=topic,
        topic_name=TOPICS[topic]["name"],
        total_questions=len(questions),
        max_attempts=MAX_ATTEMPTS
    )


@app.route("/api/get_question")
@login_required
def api_get_question():
    index = session.get("interview_index", 0)
    questions = session.get("interview_questions", [])

    if index >= len(questions):
        return jsonify({"done": True})

    q = questions[index]
    return jsonify({
        "done": False,
        "index": index,
        "total": len(questions),
        "question": q["question"]
    })


@app.route("/api/submit_answer", methods=["POST"])
@login_required
def api_submit_answer():
    data = request.get_json(force=True)
    user_answer = data.get("answer", "")
    attempt_number = data.get("attempt", 1)

    index = session.get("interview_index", 0)
    questions = session.get("interview_questions", [])

    if index >= len(questions):
        return jsonify({"error": "No more questions."}), 400

    q = questions[index]
    evaluation = evaluate_answer(q["question"], q["answer"], user_answer)

    models.save_answer_attempt(
        session["user_id"], session.get("interview_topic", ""),
        q["question"], user_answer, evaluation["score"], evaluation["correctness"]
    )

    is_final_attempt = attempt_number >= MAX_ATTEMPTS
    passed = evaluation["correctness"] in ("Correct", "Partially Correct") and evaluation["score"] >= 50

    response = {
        "evaluation": evaluation,
        "passed": passed,
        "show_correct_answer": is_final_attempt and not passed,
        "correct_answer": q["answer"] if (is_final_attempt and not passed) else None
    }

    if passed or is_final_attempt:
        scores = session.get("interview_scores", [])
        scores.append(evaluation["score"])
        session["interview_scores"] = scores

        if passed:
            session["interview_correct"] = session.get("interview_correct", 0) + 1
        else:
            session["interview_wrong"] = session.get("interview_wrong", 0) + 1

        session["interview_index"] = index + 1
        response["advance"] = True
    else:
        response["advance"] = False

    return jsonify(response)


@app.route("/finish_interview")
@login_required
def finish_interview():
    scores = session.get("interview_scores", [])
    topic = session.get("interview_topic", "general")
    correct = session.get("interview_correct", 0)
    wrong = session.get("interview_wrong", 0)
    total = len(scores)

    average_score = round(sum(scores) / total, 1) if total else 0
    strong = topic if average_score >= 60 else ""
    weak = topic if average_score < 60 else ""

    result_id = models.save_interview_result(
        session["user_id"], topic, total, correct, wrong,
        average_score, strong, weak
    )

    session.pop("interview_topic", None)
    session.pop("interview_questions", None)
    session.pop("interview_index", None)
    session.pop("interview_scores", None)
    session.pop("interview_correct", None)
    session.pop("interview_wrong", None)

    return redirect(url_for("result", result_id=result_id))


@app.route("/result/<int:result_id>")
@login_required
def result(result_id):
    res = models.get_result_by_id(result_id)
    if not res or res["user_id"] != session["user_id"]:
        flash("Result not found.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("result.html", result=res, topic_name=TOPICS.get(res["topic"], {}).get("name", res["topic"]))


# ---------------------------------------------------------------- #
# App Init
# ---------------------------------------------------------------- #

if __name__ == "__main__":
    models.init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
