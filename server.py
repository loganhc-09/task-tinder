#!/usr/bin/env python3
"""
Task Tinder — lightweight backend.

A metacognition-forcing task triage system. Swipe through your tasks,
sprint through the ones you accept, and capture HOW you completed them
so the system learns your patterns over time.

Usage:
    pip install flask
    python server.py
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).parent.resolve()
DB_PATH = BASE / "task_tinder.db"
DELEGATIONS = BASE / "delegations.jsonl"
SAMPLE_FILE = BASE / "sample_tasks.json"

app = Flask(__name__, static_folder=str(BASE), static_url_path="")


# ── Database ──

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            source TEXT DEFAULT 'task',
            effort TEXT DEFAULT '10min',
            context TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            method_notes TEXT,
            delegation_notes TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget TEXT NOT NULL,
            started_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            tasks_completed INTEGER DEFAULT 0,
            tasks_delegated INTEGER DEFAULT 0,
            tasks_skipped INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            task_title TEXT,
            method_notes TEXT,
            time_taken_sec INTEGER,
            completed_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );
    """)
    # Seed with sample data if empty
    count = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0 and SAMPLE_FILE.exists():
        with open(SAMPLE_FILE) as f:
            samples = json.load(f)
        for t in samples:
            db.execute(
                "INSERT INTO tasks (title, source, effort, context) VALUES (?, ?, ?, ?)",
                (t["title"], t.get("source", "task"), t.get("effort", "10min"), t.get("context", ""))
            )
    db.commit()
    db.close()


# ── Routes ──

@app.route("/")
def index():
    return send_from_directory(str(BASE), "index.html")


@app.route("/api/tasks")
def api_tasks():
    """Return pending tasks, optionally filtered by effort budget."""
    budget = request.args.get("budget")  # 10min, 30min, 60min
    db = get_db()
    if budget:
        rows = db.execute(
            "SELECT * FROM tasks WHERE status = 'pending' AND effort = ? ORDER BY id",
            (budget,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM tasks WHERE status = 'pending' ORDER BY id"
        ).fetchall()
    db.close()
    return jsonify({"tasks": [dict(r) for r in rows]})


@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    """Add a new task."""
    data = request.json or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO tasks (title, source, effort, context) VALUES (?, ?, ?, ?)",
        (title, data.get("source", "task"), data.get("effort", "10min"), data.get("context", ""))
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/api/complete", methods=["POST"])
def api_complete():
    """Mark a task as completed with metacognition notes."""
    data = request.json or {}
    task_id = data.get("task_id")
    method_notes = data.get("method_notes", "")
    time_taken = data.get("time_taken_sec", 0)
    if not task_id:
        return jsonify({"error": "task_id required"}), 400
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "UPDATE tasks SET status = 'completed', completed_at = ?, method_notes = ? WHERE id = ?",
        (now, method_notes, task_id)
    )
    # Get task title for completions log
    row = db.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
    title = row["title"] if row else ""
    db.execute(
        "INSERT INTO completions (task_id, task_title, method_notes, time_taken_sec) VALUES (?, ?, ?, ?)",
        (task_id, title, method_notes, time_taken)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/api/dismiss", methods=["POST"])
def api_dismiss():
    """Skip or delegate a task."""
    data = request.json or {}
    task_id = data.get("task_id")
    reason = data.get("reason", "skip")  # skip, delegate
    note = data.get("note", "")
    if not task_id:
        return jsonify({"error": "task_id required"}), 400
    db = get_db()
    now = datetime.now().isoformat()
    status = "delegated" if reason == "delegate" else "skipped"
    db.execute(
        "UPDATE tasks SET status = ?, completed_at = ?, delegation_notes = ? WHERE id = ?",
        (status, now, note, task_id)
    )
    # Write delegation to JSONL for Claude Code to pick up
    if reason == "delegate":
        row = db.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        title = row["title"] if row else ""
        entry = {"task": title, "note": note, "delegated_at": now, "status": "pending"}
        with open(DELEGATIONS, "a") as f:
            f.write(json.dumps(entry) + "\n")
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/api/session", methods=["POST"])
def api_session():
    """Start or end a sprint session."""
    data = request.json or {}
    action = data.get("action", "start")
    if action == "start":
        budget = data.get("budget", "30min")
        db = get_db()
        cur = db.execute("INSERT INTO sessions (budget) VALUES (?)", (budget,))
        session_id = cur.lastrowid
        db.commit()
        db.close()
        return jsonify({"session_id": session_id})
    elif action == "end":
        session_id = data.get("session_id")
        stats = data.get("stats", {})
        db = get_db()
        db.execute(
            "UPDATE sessions SET completed_at = ?, tasks_completed = ?, tasks_delegated = ?, tasks_skipped = ? WHERE id = ?",
            (datetime.now().isoformat(), stats.get("completed", 0), stats.get("delegated", 0), stats.get("skipped", 0), session_id)
        )
        db.commit()
        db.close()
        return jsonify({"ok": True})
    return jsonify({"error": "unknown action"}), 400


@app.route("/api/stats")
def api_stats():
    """Return lifetime stats."""
    db = get_db()
    completed = db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'").fetchone()[0]
    delegated = db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'delegated'").fetchone()[0]
    skipped = db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'skipped'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'").fetchone()[0]
    sessions = db.execute("SELECT COUNT(*) FROM sessions WHERE completed_at IS NOT NULL").fetchone()[0]
    # Recent completions with method notes (the learning data)
    recent = db.execute(
        "SELECT task_title, method_notes, time_taken_sec, completed_at FROM completions ORDER BY id DESC LIMIT 10"
    ).fetchall()
    db.close()
    return jsonify({
        "completed": completed,
        "delegated": delegated,
        "skipped": skipped,
        "pending": pending,
        "sessions": sessions,
        "recent_completions": [dict(r) for r in recent]
    })


@app.route("/api/patterns")
def api_patterns():
    """Return metacognition patterns — how you tend to complete different types of tasks."""
    db = get_db()
    rows = db.execute("""
        SELECT c.task_title, c.method_notes, c.time_taken_sec, t.source, t.effort
        FROM completions c
        LEFT JOIN tasks t ON c.task_id = t.id
        WHERE c.method_notes IS NOT NULL AND c.method_notes != ''
        ORDER BY c.id DESC LIMIT 50
    """).fetchall()
    db.close()
    return jsonify({"patterns": [dict(r) for r in rows]})


if __name__ == "__main__":
    init_db()
    print("\n  Task Tinder running at http://localhost:5050\n")
    app.run(host="0.0.0.0", port=5050, debug=True)
