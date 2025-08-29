from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-later")

DB_PATH = Path("app.db")


# ---------- DB Utilities ----------
def connect_db():
    return sqlite3.connect(DB_PATH)

def table_has_column(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def init_db():
    """
    Create the scores table if missing.
    If an old table exists with a 'judge_name' column, migrate it to the new schema
    (no judge_name).
    """
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                programme_code TEXT NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                score REAL NOT NULL,
                remarks TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # If table exists with old schema (judge_name), migrate
        # (Only does anything if it finds the old column)
        try:
            if table_has_column(conn, "scores", "judge_name"):
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS scores_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        programme_code TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        student_name TEXT NOT NULL,
                        score REAL NOT NULL,
                        remarks TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    INSERT INTO scores_new (programme_code, student_id, student_name, score, remarks, created_at)
                    SELECT programme_code, student_id, student_name, score, remarks, created_at
                    FROM scores
                """)
                cur.execute("DROP TABLE scores")
                cur.execute("ALTER TABLE scores_new RENAME TO scores")
                conn.commit()
        except sqlite3.Error:
            # If anything odd happens during migration, ignore silently for now.
            pass


# Initialize DB on import (needed for Gunicorn on Render)
init_db()


# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("home.html", title="Madrasa Fest")

@app.route("/judges", methods=["GET", "POST"])
def judges():
    if request.method == "POST":
        # Get form data
        programme_code = (request.form.get("programme_code") or "").strip()
        student_id = (request.form.get("student_id") or "").strip()
        student_name = (request.form.get("student_name") or "").strip()
        remarks = (request.form.get("remarks") or "").strip()

        # Score numeric
        try:
            score = float(request.form.get("score") or "0")
        except ValueError:
            flash("Score must be a number.", "err")
            return redirect(url_for("judges"))

        # Required checks
        if not programme_code or not student_id or not student_name:
            flash("Programme, Student ID and Student Name are required.", "err")
            return redirect(url_for("judges"))

        with connect_db() as conn:
            conn.execute(
                """
                INSERT INTO scores (programme_code, student_id, student_name, score, remarks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (programme_code, student_id, student_name, score, remarks),
            )
            conn.commit()

        flash("Score saved ✅", "ok")
        return redirect(url_for("judges"))

    return render_template("judges.html", title="Judges Portal")

@app.route("/results")
def results():
    with connect_db() as conn:
        cur = conn.cursor()

        # Recent (include the id FIRST so we can delete safely)
        cur.execute("""
            SELECT id, programme_code, student_id, student_name, score, remarks, created_at
            FROM scores
            ORDER BY created_at DESC, id DESC
            LIMIT 50
        """)
        recent = cur.fetchall()

        # Totals per student
        cur.execute("""
            SELECT student_id, student_name, SUM(score) as total
            FROM scores
            GROUP BY student_id, student_name
            ORDER BY total DESC
        """)
        totals = cur.fetchall()

    return render_template("results.html", title="Results", recent=recent, totals=totals)

@app.post("/delete/<int:score_id>")
def delete_score(score_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM scores WHERE id = ?", (score_id,))
        conn.commit()
    flash(f"Deleted entry #{score_id}", "ok")
    return redirect(url_for("results"))

# Optional: clear all (keep commented for safety)
# @app.post("/clear_all")
# def clear_all():
#     with connect_db() as conn:
#         conn.execute("DELETE FROM scores")
#         conn.commit()
#     flash("All scores cleared", "ok")
#     return redirect(url_for("results"))


# ---------- Local run ----------
if __name__ == "__main__":
    # Render passes PORT; local defaults to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)