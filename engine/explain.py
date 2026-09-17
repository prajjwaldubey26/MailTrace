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
    pillars = [{"id": k, "label": k, "points": v, "share": round(100 * v / cap, 1)} for k, v in buckets.items()]

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
        "note": "Not SHAP / not a neural net. Each bar is that rule’s share of the risk score.",
        "contributions": contrib[:12],
        "intents": intents,
        "hitl_review": hitl,
        "hitl_reason": "Score sits in the 40–65 uncertainty band — a human should confirm." if hitl else "",
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
        "Confirm the request on a known channel (phone / in person), not Reply.",
        "Preserve the original (.eml / Show original) — do not forward as a new mail.",
    ]
    extra = {
        "fraud": [
            "Block payment / wire / gift-card requests until finance verifies the vendor on file.",
            "Notify accounts payable of a possible diversion attempt.",
        ],
        "phishing": [
            "Warn users not to enter passwords or OTP on the linked page.",
            "Defang IOCs before sharing in tickets.",
        ],
        "impersonated": [
            "Treat as BEC: executive or staff name may be fake even if the tone is calm.",
            "Check whether the real mailbox was compromised, or this is a lookalike From.",
        ],
        "suspicious": ["Park the message; a human should review the 40–65 band."],
        "legitimate": ["No strong playbook step — still avoid clicking unexpected links."],
    }
    return common + extra.get(tclass, [])


def analyst_guidance(tclass: str, score: int, auth: dict, identity: dict, hitl: bool) -> str:
    fails = [k.upper() for k in ("spf", "dkim", "dmarc") if auth.get(k) == "fail"]
    mm = (identity or {}).get("mismatch_count") or 0
    if tclass == "legitimate" and not fails:
        return (
            "Treat as low-priority. Authentication stamps did not fail and no strong fraud/phish/BEC class fired. "
            "Still avoid unexpected links. This is a weighted-rule verdict, not a neural-net guarantee."
        )
    bits = []
    if fails:
        bits.append("Authentication failed: " + ", ".join(fails) + ".")
    if mm:
        bits.append(f"{mm} identity-domain mismatch(es) versus From.")
    if tclass == "fraud":
        bits.append("Do not pay or change bank details until finance confirms on a known channel.")
    elif tclass == "phishing":
        bits.append("Do not click links or enter passwords. Preserve the .eml.")
    elif tclass == "impersonated":
        bits.append("Trusted display name is not proof of mailbox ownership — treat as BEC.")
    elif tclass == "suspicious":
        bits.append("Mixed indicators — park and verify.")
    if hitl:
        bits.append("Score is in the 40–65 uncertainty band: a human analyst should confirm.")
    bits.append(f"Recorded risk {score}/100 under explainable heuristics.")
    return " ".join(bits)


def findings_board(reasons: list[dict], anomalies: list[dict], auth: dict) -> dict[str, Any]:
    items: list[dict] = []
    for proto in ("spf", "dkim", "dmarc"):
        val = auth.get(proto) or "none"
        if val == "fail":
            items.append({"severity": "high", "title": f"{proto.upper()} FAIL", "detail": f"{proto.upper()} authentication failed."})
        elif val == "pass":
            items.append({"severity": "info", "title": f"{proto.upper()} PASS", "detail": f"{proto.upper()} aligned with Authentication-Results."})
        else:
            items.append({"severity": "warning", "title": f"{proto.upper()} {val.upper()}", "detail": f"No clear {proto.upper()} pass in Authentication-Results."})
    for r in reasons or []:
        pts = int(r.get("points") or 0)
        if pts <= 0:
            continue
        code = (r.get("code") or "")
        if code.startswith(("spf_", "dkim_", "dmarc_")):
            continue
        sev = "high" if pts >= 12 else "warning"
        items.append({"severity": sev, "title": r.get("code") or "signal", "detail": r.get("detail") or "", "points": pts})
    for a in anomalies or []:
        pts = int(a.get("points") or 0)
        sev = "high" if pts >= 10 else "warning" if pts else "info"
        items.append({"severity": sev, "title": a.get("code") or "header", "detail": a.get("detail") or "", "points": pts})
    counts = {"high": 0, "warning": 0, "info": 0}
    for i in items:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1
    return {"counts": counts, "items": items[:18]}
