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


def list_campaigns() -> list[dict]:
    """Group saved cases by From domain (PS campaign-pattern view)."""
    con = connect()
    rows = con.execute(
        "SELECT id, created_at, subject, from_addr, score, label, payload FROM cases ORDER BY id DESC"
    ).fetchall()
    con.close()
    buckets: dict[str, dict] = {}
    for r in rows:
        payload = json.loads(r["payload"] or "{}")
        domain = (payload.get("from_domain") or "").lower()
        if not domain and r["from_addr"] and "@" in r["from_addr"]:
            domain = r["from_addr"].rsplit("@", 1)[-1].lower()
        domain = domain or "(unknown)"
        b = buckets.setdefault(
            domain,
            {"domain": domain, "count": 0, "max_score": 0, "classes": {}, "case_ids": []},
        )
        b["count"] += 1
        b["max_score"] = max(b["max_score"], int(r["score"] or 0))
        cls = payload.get("threat_class") or r["label"] or "unknown"
        b["classes"][cls] = b["classes"].get(cls, 0) + 1
        if len(b["case_ids"]) < 8:
            b["case_ids"].append(r["id"])
    return sorted(buckets.values(), key=lambda x: (-x["count"], -x["max_score"]))
