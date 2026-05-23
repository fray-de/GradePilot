from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from gradepilot.session.store import (
    PaperRecord,
    close_session,
    export_csv,
    init_db,
    open_session,
    record_paper,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def test_init_db_is_idempotent(tmp_path: Path):
    db = tmp_path / "gradepilot.db"
    init_db(db)
    init_db(db)
    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        indexes = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    assert {"sessions", "papers"} <= tables
    assert "idx_papers_session" in indexes


def test_schema_columns(tmp_path: Path):
    db = tmp_path / "gradepilot.db"
    init_db(db)
    with sqlite3.connect(db) as conn:
        papers_cols = {r[1] for r in conn.execute("PRAGMA table_info(papers)")}
    expected = {
        "id", "session_id", "ts", "ocr_engine", "ocr_raw", "llm_response_json",
        "proposed_score", "max_score", "final_score", "overridden",
        "confidence", "screenshot_path", "submitted", "notes",
    }
    assert expected <= papers_cols


def test_record_and_export(tmp_path: Path):
    db = tmp_path / "gradepilot.db"
    init_db(db)
    sid = open_session(db, profile_name="q1", mode="trial", dry_run=True)
    record_paper(
        db,
        sid,
        PaperRecord(
            ts=_now(),
            ocr_engine="vlm",
            ocr_raw="学生答案示例",
            llm_response_json='{"score": 1.5, "max_score": 2, "breakdown": [], "confidence": 0.8, "notes": ""}',
            proposed_score=1.5,
            max_score=2.0,
            final_score=1.5,
            overridden=False,
            confidence=0.8,
            screenshot_path="data/crops/1.png",
            submitted=False,
        ),
    )
    close_session(db, sid, notes="done")

    out = tmp_path / "out.csv"
    n = export_csv(db, out, session_id=sid)
    assert n == 1
    content = out.read_text(encoding="utf-8-sig")
    assert "学生答案示例" in content
    assert "proposed_score" in content
