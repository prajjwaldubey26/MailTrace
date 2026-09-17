"""Explainable feature contributions (SHAP-style bars without a neural net)."""

from __future__ import annotations

from typing import Any


def explain_case(score: int, reasons: list[dict], nlp: dict, auth: dict) -> dict[str, Any]:
    pos = [r for r in reasons if (r.get("points") or 0) > 0]
    total = sum(int(r["points"]) for r in pos) or 1
    contrib = [
        {
            "code": r.get("code"),
            "detail": r.get("detail"),
            "points": int(r.get("points") or 0),
            "share": round(100 * int(r.get("points") or 0) / total, 1),
        }
        for r in sorted(pos, key=lambda x: -int(x.get("points") or 0))
    ]
    intents = []
    if nlp.get("urgency_cues"):
        intents.append("urgency")
    if nlp.get("harvest_cues"):
        intents.append("credential")
    if nlp.get("lookalike_tokens") or nlp.get("typosquat") or nlp.get("from_reply_mismatch"):
        intents.append("deception")
    if nlp.get("fraud_cues"):
        intents.append("payment")
    if nlp.get("quishing"):
        intents.append("quishing")
    if not intents and score < 25:
        intents.append("none_detected")

    hitl = 40 <= score <= 65
    return {
        "method": "weighted_feature_contributions",
        "note": "Not SHAP / not a neural net. Each bar is that rule’s share of the risk score.",
        "contributions": contrib[:12],
        "intents": intents,
        "hitl_review": hitl,
        "hitl_reason": "Score sits in the 40–65 uncertainty band — a human should confirm." if hitl else "",
        "workflow": ["detect", "explain", "trace", "investigate"],
        "auth_matrix": {"spf": auth.get("spf"), "dkim": auth.get("dkim"), "dmarc": auth.get("dmarc")},
    }


def iocs(result: dict) -> dict[str, list]:
    hops = result.get("geo_hops") or []
    ips = [h.get("ip") for h in hops if h.get("ip")]
    return {
        "emails": [e for e in [result.get("from_addr"), result.get("reply_to")] if e],
        "domains": [d for d in [result.get("from_domain")] if d],
        "urls": result.get("urls") or [],
        "ips": ips,
        "files": result.get("attachments") or [],
    }
