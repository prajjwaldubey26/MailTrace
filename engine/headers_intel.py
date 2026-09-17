"""Header forensics: Return-Path, Message-ID, Sender, Received-chain anomalies."""

from __future__ import annotations

from typing import Any

from .nlp import domain_of


def _msgid_domain(msgid: str) -> str:
    msgid = (msgid or "").strip().strip("<>")
    if "@" in msgid:
        return msgid.rsplit("@", 1)[-1].lower().rstrip(">")
    return ""


def analyze_headers(headers: dict[str, str], hops: list[dict], from_addr: str, reply_to: str) -> dict[str, Any]:
    from_d = domain_of(from_addr)
    rp = headers.get("Return-Path") or ""
    rp_addr = rp.strip().strip("<>")
    rp_d = domain_of(rp_addr) if rp_addr else ""
    sender = headers.get("Sender") or ""
    sender_d = domain_of(sender) if sender else ""
    mid_d = _msgid_domain(headers.get("Message-ID") or "")

    anomalies: list[dict[str, Any]] = []

    if rp_d and from_d and rp_d != from_d:
        anomalies.append(
            {
                "code": "return_path_mismatch",
                "detail": f"Return-Path domain ({rp_d}) differs from From ({from_d}) — possible spoof / bounce mismatch",
                "points": 10,
            }
        )
    if mid_d and from_d and mid_d != from_d and "google.com" not in mid_d:
        # Gmail Message-IDs are often mail.gmail.com vs From gmail.com — skip close cousins
        from_root = ".".join(from_d.split(".")[-2:])
        mid_root = ".".join(mid_d.split(".")[-2:])
        if from_root != mid_root:
            anomalies.append(
                {
                    "code": "msgid_mismatch",
                    "detail": f"Message-ID host ({mid_d}) does not match From domain ({from_d})",
                    "points": 6,
                }
            )
    if sender_d and from_d and sender_d != from_d:
        anomalies.append(
            {
                "code": "sender_mismatch",
                "detail": f"Sender header ({sender_d}) differs from From ({from_d})",
                "points": 8,
            }
        )
    if hops and not any(h.get("public_ips") for h in hops):
        anomalies.append(
            {
                "code": "no_public_received_ip",
                "detail": "No public IPv4 in Received chain (common for Gmail). Origin geo not available.",
                "points": 0,
            }
        )
    if len(hops) >= 8:
        anomalies.append(
            {
                "code": "long_relay_chain",
                "detail": f"Unusually long Received chain ({len(hops)} hops) — possible relay manipulation",
                "points": 4,
            }
        )

    authorized = False
    auth_line = (headers.get("Authentication-Results") or "").lower()
    if "spf=pass" in auth_line and "dmarc=pass" in auth_line:
        authorized = True

    return {
        "from_domain": from_d,
        "return_path_domain": rp_d,
        "message_id_domain": mid_d,
        "sender_domain": sender_d,
        "reply_to_domain": domain_of(reply_to) if reply_to else "",
        "received_count": len(hops),
        "anomalies": anomalies,
        "authorized_infra_hint": authorized,
    }
