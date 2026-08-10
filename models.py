"""
database/models.py
Handles SQLite connection, table creation, and all DB helper functions
for the PrepPilot AI application.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all required tables if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_image TEXT DEFAULT 'logo.png',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            total_questions INTEGER,
            correct_answers INTEGER,
            wrong_answers INTEGER,
            average_score REAL,
            strong_topics TEXT,
            weak_topics TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS answer_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            user_answer TEXT,
            score INTEGER,
            correctness TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- USER FUNCTIONS ---------------- #

def create_user(fullname, email, hashed_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (fullname, email, password, created_at) VALUES (?, ?, ?, ?)",
        (fullname, email, hashed_password, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user


def update_user_profile(user_id, fullname, profile_image=None):
    conn = get_connection()
    cur = conn.cursor()
    if profile_image:
        cur.execute("UPDATE users SET fullname = ?, profile_image = ? WHERE id = ?",
                    (fullname, profile_image, user_id))
    else:
        cur.execute("UPDATE users SET fullname = ? WHERE id = ?", (fullname, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, hashed_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    conn.commit()
    conn.close()


# ---------------- RESULTS FUNCTIONS ---------------- #

def save_interview_result(user_id, topic, total_questions, correct_answers,
                           wrong_answers, average_score, strong_topics, weak_topics):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO interview_results
        (user_id, topic, total_questions, correct_answers, wrong_answers,
         average_score, strong_topics, weak_topics, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, topic, total_questions, correct_answers, wrong_answers,
          average_score, strong_topics, weak_topics, datetime.now().isoformat()))
    conn.commit()
    result_id = cur.lastrowid
    conn.close()
    return result_id


def get_result_by_id(result_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_results WHERE id = ?", (result_id,))
    result = cur.fetchone()
    conn.close()
    return result


def get_results_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_results WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    results = cur.fetchall()
    conn.close()
    return results


def save_answer_attempt(user_id, topic, question, user_answer, score, correctness):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO answer_attempts (user_id, topic, question, user_answer, score, correctness, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, topic, question, user_answer, score, correctness, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_dashboard_stats(user_id):
    """Aggregate stats for the dashboard: completed interviews, avg score, strong/weak topics."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM interview_results WHERE user_id = ?", (user_id,))
    completed = cur.fetchone()["cnt"]

    cur.execute("SELECT AVG(average_score) as avg_score FROM interview_results WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    avg_score = round(row["avg_score"], 1) if row["avg_score"] else 0

    cur.execute("""
        SELECT topic, AVG(average_score) as topic_avg
        FROM interview_results WHERE user_id = ?
        GROUP BY topic ORDER BY topic_avg DESC
    """, (user_id,))
    topic_rows = cur.fetchall()

    strong_topics = [r["topic"] for r in topic_rows if r["topic_avg"] >= 60][:3]
    weak_topics = [r["topic"] for r in topic_rows if r["topic_avg"] < 60][:3]

    cur.execute("""
        SELECT topic, average_score, created_at FROM interview_results
        WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
    """, (user_id,))
    recent_activity = cur.fetchall()

    conn.close()
    return {
        "completed": completed,
        "avg_score": avg_score,
        "strong_topics": strong_topics or ["Not enough data"],
        "weak_topics": weak_topics or ["Not enough data"],
        "recent_activity": recent_activity
    }
