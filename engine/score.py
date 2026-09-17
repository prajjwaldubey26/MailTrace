from __future__ import annotations

from typing import Any

LABELS = [
    (85, "phishing / fraud-likely"),
    (65, "impersonation / BEC-likely"),
    (40, "suspicious"),
    (0, "likely legitimate"),
]


def classify(score: int) -> str:
    for thresh, label in LABELS:
        if score >= thresh:
            return label
    return "likely legitimate"


def score_case(auth: dict[str, str], nlp: dict[str, Any], hops_geo: list[dict], origin: str | None) -> dict[str, Any]:
    reasons: list[dict[str, Any]] = []
    score = 0

    def add(pts: int, code: str, detail: str) -> None:
        nonlocal score
        score += pts
        reasons.append({"points": pts, "code": code, "detail": detail})

    for proto, pts in (("spf", 22), ("dkim", 16), ("dmarc", 18)):
        val = auth.get(proto, "none")
        if val == "fail":
            add(pts, f"{proto}_fail", f"{proto.upper()} authentication failed")
        elif val in ("softfail", "permerror"):
            add(pts // 2, f"{proto}_{val}", f"{proto.upper()} is {val}")

    if nlp.get("from_reply_mismatch"):
        add(14, "reply_to_mismatch", "Reply-To domain differs from From domain")
    if nlp.get("display_name_spoof"):
        add(16, "display_spoof", "Trusted brand/role in display name, unmatched From domain")
    if nlp.get("urgency_cues"):
        add(min(18, 4 * len(nlp["urgency_cues"])), "urgency", "Urgency / social-engineering language: " + ", ".join(nlp["urgency_cues"][:5]))
    if nlp.get("impersonation_cues"):
        add(12, "impersonation", "Possible role/org impersonation: " + ", ".join(nlp["impersonation_cues"][:4]))
    if nlp.get("lookalike_tokens"):
        add(20, "lookalike", "Lookalike / typosquat tokens: " + ", ".join(nlp["lookalike_tokens"]))
    if nlp.get("url_issues"):
        add(min(20, 6 * len(nlp["url_issues"])), "url", nlp["url_issues"][0])
    if nlp.get("risky_attachments"):
        add(22, "attachment", "Risky attachment: " + ", ".join(nlp["risky_attachments"]))

    tags = {p.get("threat_tag") for p in hops_geo}
    if "anonymizer" in tags:
        add(18, "tor_or_anon", "Origin/relay tagged as anonymizer (Tor/VPN-style) in demo intel")
    if "bulletproof_host" in tags or "vps" in tags:
        add(10, "vps_origin", "Earliest hop on cheap VPS / bulletproof-style host")

    score = max(0, min(100, score))
    origin_geo = next((p for p in hops_geo if p.get("role") == "origin"), hops_geo[0] if hops_geo else None)
    attribution = {
        "confidence": "low",
        "summary": (
            "This is infrastructure attribution, not a named person. "
            "The earliest reliable public IP in the Received chain is treated as the sending node."
        ),
        "origin_ip": origin,
        "origin_geo": origin_geo,
        "likely_pattern": "unknown",
    }
    if score >= 70 and nlp.get("from_reply_mismatch"):
        attribution["likely_pattern"] = "spoofed domain + separate mailbox (classic phishing)"
        attribution["confidence"] = "medium"
    elif "anonymizer" in tags:
        attribution["likely_pattern"] = "anonymized infrastructure"
        attribution["confidence"] = "medium"
    elif score < 25:
        attribution["likely_pattern"] = "authorized mailbox provider path"
        attribution["confidence"] = "medium"

    return {
        "score": score,
        "label": classify(score),
        "reasons": reasons,
        "attribution": attribution,
    }
