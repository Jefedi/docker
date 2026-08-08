#!/usr/bin/env python3
"""Flask + SQLite + Docker boilerplate — copy and adapt for new apps."""
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, g

app = Flask(__name__)
app.jinja_env.auto_reload = True
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "app.db"))
PORT = int(os.environ.get("PORT", 9847))


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            -- TODO: Add your columns here
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


# ─── Routes ───────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/save", methods=["POST"])
def save():
    db = get_db()
    # TODO: Extract form fields, INSERT or UPDATE
    # db.execute("INSERT INTO entries ... VALUES (...)", (...))
    # db.commit()
    return redirect(url_for("index"))


@app.route("/history")
def history():
    db = get_db()
    entries = db.execute("SELECT * FROM entries ORDER BY date DESC LIMIT 60").fetchall()
    return render_template("history.html", entries=entries)


@app.route("/api/stats")
def api_stats():
    db = get_db()
    # TODO: Aggregate query
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)