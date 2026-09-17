from __future__ import annotations

from typing import Any

THREAT_CLASSES = ("legitimate", "suspicious", "impersonated", "phishing", "fraud")


def threat_class(score: int, nlp: dict[str, Any], tags: set, header_anoms: list) -> str:
    """PS five-way label. Score still 0–100; class is the investigative category."""
    payment = bool(nlp.get("fraud_cues"))
    phishy = bool(
        nlp.get("lookalike_tokens")
        or nlp.get("harvest_cues")
        or nlp.get("obfuscated_urls")
        or nlp.get("typosquat")
        or nlp.get("quishing")
    )
    raw_ip = any("raw IP" in x for x in (nlp.get("url_issues") or []))
    imperson = bool(nlp.get("impersonation_cues") or nlp.get("display_name_spoof") or nlp.get("from_reply_mismatch"))
    anon = "anonymizer" in tags or "vps" in tags or "bulletproof_host" in tags

    if payment and (score >= 50 or phishy or nlp.get("risky_attachments")):
        return "fraud"
    if phishy or raw_ip or (score >= 70 and (nlp.get("url_issues") or anon)):
        return "phishing"
    if imperson and score >= 40:
        return "impersonated"
    if score >= 40 or header_anoms:
        return "suspicious"
    return "legitimate"


def score_case(
    auth: dict[str, str],
    nlp: dict[str, Any],
    hops_geo: list[dict],
    origin: str | None,
    header_intel: dict | None = None,
    domain_intel: dict | None = None,
) -> dict[str, Any]:
    reasons: list[dict[str, Any]] = []
    score = 0
    header_intel = header_intel or {}
    domain_intel = domain_intel or {}

    def add(pts: int, code: str, detail: str) -> None:
        nonlocal score
        if pts:
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
    if nlp.get("fraud_cues"):
        add(10, "fraud_language", "Payment / invoice / gift-card language: " + ", ".join(nlp["fraud_cues"][:4]))
    if nlp.get("harvest_cues"):
        add(12, "credential_harvest", "Credential-harvest language: " + ", ".join(nlp["harvest_cues"][:3]))
    if nlp.get("obfuscated_urls"):
        add(8, "obfuscated_url", "Shortener or encoded URL (possible hidden redirect)")
    if nlp.get("typosquat"):
        add(16, "typosquat", "Lookalike domain (edit distance ≤ 2): " + ", ".join(nlp["typosquat"][:3]))
    if nlp.get("quishing"):
        add(14, "quishing", "QR / scan-code lure in body or URL (quishing-style)")
    if nlp.get("calm_bec"):
        add(6, "calm_bec", "Impersonation language without urgency words (professional-tone BEC pattern)")

    for a in header_intel.get("anomalies") or []:
        add(int(a.get("points") or 0), a.get("code", "header"), a.get("detail", ""))

    if domain_intel.get("nxdomain"):
        add(12, "domain_dns", f"No public A/MX for From domain {domain_intel.get('domain')} (may be fake or newly parked)")

    tags = {p.get("threat_tag") for p in hops_geo}
    if "anonymizer" in tags:
        add(18, "tor_or_anon", "Origin/relay tagged as anonymizer (Tor/VPN-style)")
    if "bulletproof_host" in tags or "vps" in tags:
        add(10, "vps_origin", "Earliest hop on cheap VPS / bulletproof-style host")

    score = max(0, min(100, score))
    origin_geo = next((p for p in hops_geo if p.get("role") == "origin"), hops_geo[0] if hops_geo else None)

    tclass = threat_class(score, nlp, tags, [a for a in (header_intel.get("anomalies") or []) if a.get("points")])

    likely = "unknown"
    confidence = "low"
    if tclass == "fraud":
        likely = "direct malicious / payment-diversion campaign"
        confidence = "medium"
    elif tclass == "phishing" and nlp.get("from_reply_mismatch"):
        likely = "spoofed domain + separate mailbox (classic phishing)"
        confidence = "medium"
    elif "anonymizer" in tags:
        likely = "anonymized infrastructure (Tor/VPN-style)"
        confidence = "medium"
    elif tclass == "impersonated":
        likely = "display-name or role impersonation (possible BEC or compromised-looking From)"
        confidence = "medium"
    elif tclass == "legitimate" or score < 25:
        likely = "authorized mailbox provider path"
        confidence = "medium"
    elif tclass == "suspicious":
        likely = "mixed indicators — treat as unverified infrastructure"
        confidence = "low"

    attribution = {
        "confidence": confidence,
        "summary": (
            "Infrastructure attribution only — not a named person. "
            "Earliest reliable public IP in Received is the sending node we report."
        ),
        "origin_ip": origin,
        "origin_geo": origin_geo,
        "likely_pattern": likely,
        "origin_kind": (
            "anonymized"
            if "anonymizer" in tags
            else "spoofed_domain"
            if nlp.get("from_reply_mismatch") or nlp.get("lookalike_tokens")
            else "authorized_path"
            if score < 25
            else "unverified"
        ),
    }

    return {
        "score": score,
        "label": tclass,
        "threat_class": tclass,
        "reasons": reasons,
        "attribution": attribution,
    }
