from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "dev-key-change-later"  # change later

DB_PATH = Path("app.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            programme_code TEXT NOT NULL,
            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            judge_name TEXT NOT NULL,
            score REAL NOT NULL,
            remarks TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

@app.route("/")
def home():
    return render_template("home.html", title="Madrasa Fest")

@app.route("/judges", methods=["GET", "POST"])
def judges():
    if request.method == "POST":
        try:
            data = (
                request.form.get("programme_code","").strip(),
                request.form.get("student_id","").strip(),
                request.form.get("student_name","").strip(),
                request.form.get("judge_name","").strip(),
                float(request.form.get("score","0") or 0),
                request.form.get("remarks","").strip()
            )
        except ValueError:
            flash("Score must be a number.", "err")
            return redirect(url_for("judges"))

        if not all([data[0], data[1], data[2], data[3]]):
            flash("All fields except remarks are required.", "err")
            return redirect(url_for("judges"))

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""INSERT INTO scores
                (programme_code, student_id, student_name, judge_name, score, remarks)
                VALUES (?,?,?,?,?,?)""", data)
            conn.commit()
        flash("Score saved ✅", "ok")
        return redirect(url_for("judges"))
    return render_template("judges.html", title="Judges Portal")

@app.route("/results")
def results():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # latest 30 entries
        c.execute("""
            SELECT programme_code, student_id, student_name, judge_name, score, remarks, created_at
            FROM scores ORDER BY created_at DESC LIMIT 30
        """)
        recent = c.fetchall()
        # totals per student
        c.execute("""
            SELECT student_id, student_name, SUM(score) AS total
            FROM scores
            GROUP BY student_id, student_name
            ORDER BY total DESC
        """)
        totals = c.fetchall()
    return render_template("results.html", title="Results", recent=recent, totals=totals)
   
@app.before_request
def _init_db_once():
    init_db()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    init_db()  # create tables locally and on Render
    app.run(host="0.0.0.0", port=port)
else:
    # When Gunicorn runs it (Render)
    init_db()