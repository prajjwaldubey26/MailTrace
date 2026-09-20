"""Explainable feature contributions (SHAP-style bars without a neural net)."""

from __future__ import annotations

from typing import Any


def _defang(url: str) -> str:
    return url.replace("http://", "hxxp://").replace("https://", "hxxps://").replace(".", "[.]")


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
    buckets = {"auth": 0, "sender": 0, "url": 0, "content": 0, "infra": 0}
    for r in pos:
        code = r.get("code") or ""
        pts = int(r.get("points") or 0)
        if code.startswith(("spf", "dkim", "dmarc")):
            buckets["auth"] += pts
        elif code in (
            "reply_to_mismatch",
            "display_spoof",
            "typosquat",
            "lookalike",
            "return_path_mismatch",
            "msgid_mismatch",
            "sender_mismatch",
        ):
            buckets["sender"] += pts
        elif code in ("url", "obfuscated_url", "quishing"):
            buckets["url"] += pts
        elif code in ("tor_or_anon", "vps_origin", "domain_dns"):
            buckets["infra"] += pts
        else:
            buckets["content"] += pts
    cap = max(buckets.values()) or 1
    pillar_labels = {
        "auth": "Sender stamps",
        "sender": "Who it claims to be",
        "url": "Links",
        "content": "Words in the email",
        "infra": "Mail computers",
    }
    pillars = [
        {"id": k, "label": pillar_labels[k], "points": v, "share": round(100 * v / cap, 1)}
        for k, v in buckets.items()
    ]

    if score >= 85:
        severity = "critical"
    elif score >= 65:
        severity = "high"
    elif score >= 40:
        severity = "medium"
    else:
        severity = "low"

    return {
        "method": "weighted_feature_contributions",
        "note": "Each bar is how much that warning added to the score. These are simple rules, not a chatbot.",
        "contributions": contrib[:12],
        "intents": intents,
        "hitl_review": hitl,
        "hitl_reason": "The score is between 40 and 65 — a person should confirm before you act." if hitl else "",
        "workflow": ["detect", "explain", "trace", "investigate"],
        "auth_matrix": {"spf": auth.get("spf"), "dkim": auth.get("dkim"), "dmarc": auth.get("dmarc")},
        "pillars": pillars,
        "severity": severity,
    }


def iocs(result: dict) -> dict[str, Any]:
    hops = result.get("geo_hops") or []
    nlp = result.get("nlp") or {}
    di = result.get("domain_intel") or {}
    items: list[dict] = []
    origin = (result.get("attribution") or {}).get("origin_ip")
    for h in hops:
        ip = h.get("ip")
        if not ip:
            continue
        tag = h.get("threat_tag") or "unknown"
        conf = "high" if tag in ("anonymizer", "vps", "bulletproof_host") else "medium"
        items.append(
            {
                "type": "ip",
                "value": ip,
                "defanged": ip,
                "confidence": conf,
                "reputation": tag,
                "role": h.get("role"),
                "place": " ".join(x for x in [h.get("city"), h.get("country")] if x),
            }
        )
    if result.get("from_addr"):
        items.append(
            {
                "type": "email",
                "value": result["from_addr"],
                "defanged": result["from_addr"].replace("@", "[at]"),
                "confidence": "high",
                "reputation": "from",
            }
        )
    if result.get("reply_to"):
        items.append(
            {
                "type": "email",
                "value": result["reply_to"],
                "defanged": result["reply_to"].replace("@", "[at]"),
                "confidence": "medium",
                "reputation": "reply-to",
            }
        )
    if result.get("from_domain"):
        items.append(
            {
                "type": "domain",
                "value": result["from_domain"],
                "defanged": result["from_domain"].replace(".", "[.]"),
                "confidence": "high" if di.get("nxdomain") or nlp.get("typosquat") else "medium",
                "reputation": "no-mx" if di.get("nxdomain") else "has-mx" if di.get("ok") else "unknown",
            }
        )
    for u in result.get("urls") or []:
        items.append(
            {
                "type": "url",
                "value": u,
                "defanged": _defang(u),
                "confidence": "high" if nlp.get("url_issues") else "low",
                "reputation": "suspicious" if nlp.get("url_issues") else "unscored",
            }
        )
    for f in result.get("attachments") or []:
        items.append({"type": "file", "value": f, "defanged": f, "confidence": "medium", "reputation": "attachment"})
    return {
        "emails": [e for e in [result.get("from_addr"), result.get("reply_to")] if e],
        "domains": [d for d in [result.get("from_domain")] if d],
        "urls": result.get("urls") or [],
        "ips": [h.get("ip") for h in hops if h.get("ip")],
        "files": result.get("attachments") or [],
        "explorer": items[:24],
        "origin_ip": origin,
    }


def playbook(tclass: str) -> list[str]:
    common = [
        "Do not click links or open attachments from this message.",
        "Confirm the request by calling or meeting the real person — do not just hit Reply.",
        "Keep the original email file. Do not forward it as a new mail.",
    ]
    extra = {
        "fraud": [
            "Do not pay or change bank details until finance checks the real vendor.",
            "Tell accounts payable this may be a fake payment request.",
        ],
        "phishing": [
            "Do not type passwords or OTP on the linked page.",
            "Share clues as copied text, not as a live clickable link.",
        ],
        "impersonated": [
            "A familiar name is not proof. Treat this as someone pretending to be staff.",
            "Check whether the real mailbox was stolen, or this is a lookalike From address.",
        ],
        "suspicious": ["Hold the message. A person should look again because the score is in the middle."],
        "legitimate": ["No urgent action. Still skip unexpected links."],
    }
    return common + extra.get(tclass, [])


def analyst_guidance(tclass: str, score: int, auth: dict, identity: dict, hitl: bool) -> str:
    names = {"spf": "sender check", "dkim": "signature", "dmarc": "policy"}
    fails = [names[k] for k in ("spf", "dkim", "dmarc") if auth.get(k) == "fail"]
    mm = (identity or {}).get("mismatch_count") or 0
    if tclass == "legitimate" and not fails:
        return (
            "Looks low risk. Sender stamps did not fail, and we did not see strong scam signs. "
            "Still skip unexpected links. This is a rule-based result, not a chatbot guarantee."
        )
    bits = []
    if fails:
        bits.append("Sender stamps failed: " + ", ".join(fails) + ".")
    if mm:
        bits.append(f"{mm} From / reply mismatch.")
    if tclass == "fraud":
        bits.append("Do not pay or change bank details until finance confirms by phone.")
    elif tclass == "phishing":
        bits.append("Do not click links or type passwords. Keep the original file.")
    elif tclass == "impersonated":
        bits.append("A trusted display name is not proof — treat this as someone pretending.")
    elif tclass == "suspicious":
        bits.append("Mixed signs — hold and verify.")
    if hitl:
        bits.append("Score is between 40 and 65: a person should confirm.")
    bits.append(f"Recorded risk {score}/100 from simple rules.")
    return " ".join(bits)


def findings_board(reasons: list[dict], anomalies: list[dict], auth: dict) -> dict[str, Any]:
    stamp = {"spf": "Sender check", "dkim": "Signature", "dmarc": "Policy"}
    items: list[dict] = []
    for proto in ("spf", "dkim", "dmarc"):
        val = auth.get(proto) or "none"
        if val == "fail":
            items.append({"severity": "high", "title": f"{stamp[proto]} failed", "detail": f"{stamp[proto]} failed."})
        elif val == "pass":
            items.append({"severity": "info", "title": f"{stamp[proto]} passed", "detail": f"{stamp[proto]} passed."})
        else:
            items.append({"severity": "warning", "title": f"{stamp[proto]} not found", "detail": f"No clear {stamp[proto]} result."})
    for r in reasons or []:
        pts = int(r.get("points") or 0)
        if pts <= 0:
            continue
        code = (r.get("code") or "")
        if code.startswith(("spf_", "dkim_", "dmarc_")):
            continue
        sev = "high" if pts >= 12 else "warning"
        items.append({"severity": sev, "title": r.get("detail") or "Warning", "detail": "", "points": pts})
    for a in anomalies or []:
        pts = int(a.get("points") or 0)
        sev = "high" if pts >= 10 else "warning" if pts else "info"
        items.append({"severity": sev, "title": a.get("detail") or "Header note", "detail": "", "points": pts})
    counts = {"high": 0, "warning": 0, "info": 0}
    for i in items:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1
    return {"counts": counts, "items": items[:18]}
