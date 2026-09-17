from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB = Path(__file__).resolve().parents[1] / "data" / "cases.db"


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            source_name TEXT,
            subject TEXT,
            from_addr TEXT,
            score INTEGER,
            label TEXT,
            payload TEXT
        )
        """
    )
    con.commit()
    return con


def save_case(result: dict[str, Any]) -> int:
    con = connect()
    cur = con.execute(
        "INSERT INTO cases (created_at, source_name, subject, from_addr, score, label, payload) VALUES (?,?,?,?,?,?,?)",
        (
            result.get("analyzed_at"),
            result.get("source_name"),
            result.get("subject"),
            result.get("from_addr"),
            result.get("score"),
            result.get("label"),
            json.dumps(result),
        ),
    )
    con.commit()
    cid = int(cur.lastrowid)
    con.close()
    return cid


def list_cases() -> list[dict]:
    con = connect()
    rows = con.execute("SELECT id, created_at, source_name, subject, from_addr, score, label FROM cases ORDER BY id DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_case(cid: int) -> dict | None:
    con = connect()
    row = con.execute("SELECT payload FROM cases WHERE id=?", (cid,)).fetchone()
    con.close()
    if not row:
        return None
    data = json.loads(row["payload"])
    data["id"] = cid
    return data
