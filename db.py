"""Minimal SQLite persistence for eval runs and results."""
import json
import sqlite3
import time
from pathlib import Path

from .schema import EvalResult

DB_PATH = Path(__file__).resolve().parent.parent / "grader.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    created_at REAL NOT NULL,
    label TEXT
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    test_case_id TEXT NOT NULL,
    response_code TEXT NOT NULL,
    passed INTEGER NOT NULL,
    total INTEGER NOT NULL,
    check_errors TEXT NOT NULL,
    correctness INTEGER,
    code_quality INTEGER,
    safety INTEGER,
    flags TEXT,
    reasoning TEXT,
    final_score REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs (id)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_run(model_name: str, label: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO runs (model_name, created_at, label) VALUES (?, ?, ?)",
        (model_name, time.time(), label),
    )
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def save_result(run_id: int, result: EvalResult) -> None:
    conn = get_conn()
    judge = result.judge
    conn.execute(
        """INSERT INTO results
           (run_id, test_case_id, response_code, passed, total, check_errors,
            correctness, code_quality, safety, flags, reasoning, final_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            result.test_case_id,
            result.response_code,
            result.check.passed,
            result.check.total,
            json.dumps(result.check.errors),
            judge.correctness if judge else None,
            judge.code_quality if judge else None,
            judge.safety if judge else None,
            json.dumps(judge.flags) if judge else "[]",
            judge.reasoning if judge else "",
            result.final_score,
        ),
    )
    conn.commit()
    conn.close()


def list_runs() -> list[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT r.id, r.model_name, r.created_at, r.label,
                  AVG(res.final_score) AS avg_score, COUNT(res.id) AS n
           FROM runs r LEFT JOIN results res ON res.run_id = r.id
           GROUP BY r.id ORDER BY r.created_at ASC"""
    ).fetchall()
    conn.close()
    return rows


def get_run(run_id: int) -> sqlite3.Row:
    conn = get_conn()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    return row


def get_results_for_run(run_id: int) -> list[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM results WHERE run_id = ? ORDER BY id ASC", (run_id,)
    ).fetchall()
    conn.close()
    return rows
