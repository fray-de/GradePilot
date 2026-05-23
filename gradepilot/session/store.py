"""SQLite persistence: sessions + papers tables, plus CSV export (M7)."""
from __future__ import annotations

import csv
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      TEXT    NOT NULL,
    ended_at        TEXT,
    profile_name    TEXT,
    mode            TEXT    NOT NULL CHECK (mode IN ('trial', 'batch')),
    dry_run         INTEGER NOT NULL CHECK (dry_run IN (0, 1)),
    rubric_snapshot TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    ts                TEXT    NOT NULL,
    ocr_engine        TEXT,
    ocr_raw           TEXT,
    llm_response_json TEXT,
    proposed_score    REAL,
    max_score         REAL,
    final_score       REAL,
    overridden        INTEGER NOT NULL CHECK (overridden IN (0, 1)),
    confidence        REAL,
    screenshot_path   TEXT,
    submitted         INTEGER NOT NULL CHECK (submitted IN (0, 1)),
    notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_papers_session ON papers(session_id);
CREATE INDEX IF NOT EXISTS idx_papers_ts ON papers(ts);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


@dataclass
class PaperRecord:
    ts: str
    ocr_engine: str | None
    ocr_raw: str | None
    llm_response_json: str | None
    proposed_score: float | None
    max_score: float | None
    final_score: float | None
    overridden: bool
    confidence: float | None
    screenshot_path: str | None
    submitted: bool
    notes: str | None = None


def open_session(
    db_path: Path,
    *,
    profile_name: str | None,
    mode: str,
    dry_run: bool,
    rubric_snapshot: str | None = None,
    notes: str | None = None,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO sessions (started_at, profile_name, mode, dry_run, rubric_snapshot, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_now_iso(), profile_name, mode, int(dry_run), rubric_snapshot, notes),
        )
        return int(cur.lastrowid)


def close_session(db_path: Path, session_id: int, notes: str | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, notes = COALESCE(?, notes) WHERE id = ?",
            (_now_iso(), notes, session_id),
        )


def record_paper(db_path: Path, session_id: int, rec: PaperRecord) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO papers (
                 session_id, ts, ocr_engine, ocr_raw, llm_response_json,
                 proposed_score, max_score, final_score, overridden,
                 confidence, screenshot_path, submitted, notes
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                rec.ts,
                rec.ocr_engine,
                rec.ocr_raw,
                rec.llm_response_json,
                rec.proposed_score,
                rec.max_score,
                rec.final_score,
                int(rec.overridden),
                rec.confidence,
                rec.screenshot_path,
                int(rec.submitted),
                rec.notes,
            ),
        )
        return int(cur.lastrowid)


def export_csv(db_path: Path, out_path: Path, session_id: int | None = None) -> int:
    """Dump papers to CSV. Returns row count. (Surface in M7 UI.)"""
    query = "SELECT * FROM papers"
    params: tuple = ()
    if session_id is not None:
        query += " WHERE session_id = ?"
        params = (session_id,)
    query += " ORDER BY id"

    with connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = list(conn.execute(query, params))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        if not rows:
            return 0
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for r in rows:
            d = dict(r)
            if d.get("llm_response_json"):
                try:
                    json.loads(d["llm_response_json"])
                except (TypeError, ValueError):
                    pass
            writer.writerow(d)
    return len(rows)
