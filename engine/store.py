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


def correlate(from_addr: str, from_domain: str, origin_ip: str | None, exclude_id: int | None = None) -> dict[str, Any]:
    """Local sighting stats from this prototype's case store — not a global intel feed."""
    con = connect()
    rows = con.execute(
        "SELECT id, created_at, subject, from_addr, score, label, payload FROM cases ORDER BY id DESC"
    ).fetchall()
    con.close()
    from_addr = (from_addr or "").lower()
    from_domain = (from_domain or "").lower()
    origin_ip = (origin_ip or "").strip()
    sender_hits: list[dict] = []
    domain_hits: list[dict] = []
    ip_hits: list[dict] = []
    log: list[dict] = []
    for r in rows:
        cid = int(r["id"])
        if exclude_id is not None and cid == exclude_id:
            continue
        payload = json.loads(r["payload"] or "{}")
        addr = (r["from_addr"] or payload.get("from_addr") or "").lower()
        domain = (payload.get("from_domain") or "").lower()
        if not domain and "@" in addr:
            domain = addr.rsplit("@", 1)[-1]
        ip = ((payload.get("attribution") or {}).get("origin_ip") or "").strip()
        item = {
            "id": cid,
            "created_at": r["created_at"],
            "subject": r["subject"] or "(no subject)",
            "from_addr": r["from_addr"],
            "score": int(r["score"] or 0),
            "label": payload.get("threat_class") or r["label"],
            "origin_ip": ip or "n/a",
        }
        match = False
        if from_addr and addr == from_addr:
            sender_hits.append(item)
            match = True
        if from_domain and domain == from_domain:
            domain_hits.append(item)
            match = True
        if origin_ip and ip and ip == origin_ip:
            ip_hits.append(item)
            match = True
        if match and len(log) < 12:
            log.append(item)

    prior = max(len(sender_hits), len(domain_hits), len(ip_hits))
    return {
        "source": "local_sqlite_case_store",
        "note": "Seen Before means this mailbox/domain/IP appeared in prior analyses on this MailTrace instance, not a commercial threat-intel feed.",
        "sender": {"seen_before": bool(sender_hits), "count": len(sender_hits)},
        "domain": {"seen_before": bool(domain_hits), "count": len(domain_hits)},
        "origin_ip": {"seen_before": bool(ip_hits), "count": len(ip_hits), "value": origin_ip or ""},
        "prior_sightings": prior,
        "correlated_campaign": from_domain or "(unknown)",
        "incident_log": log,
    }


def dashboard() -> dict:
    cases = list_cases()
    n = len(cases)
    scores = [int(c.get("score") or 0) for c in cases]
    labels: dict[str, int] = {}
    for c in cases:
        lab = c.get("label") or "unknown"
        labels[lab] = labels.get(lab, 0) + 1
    high = sum(1 for s in scores if s >= 65)
    return {
        "investigations": n,
        "avg_score": round(sum(scores) / n, 1) if n else 0,
        "high_risk": high,
        "critical": sum(1 for s in scores if s >= 85),
        "classes": labels,
        "evidence_sealed": n,
        "campaigns": len(list_campaigns()),
    }
