"""Sender identity alignment: Return-Path, Reply-To, DKIM/SPF domains vs From org."""

from __future__ import annotations

from typing import Any

from .nlp import domain_of


def org_root(domain: str) -> str:
    d = (domain or "").lower().strip().strip(".")
    if not d:
        return ""
    parts = [p for p in d.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return d


def _cmp(from_d: str, other_d: str, label: str, missing: str) -> dict[str, str]:
    if not other_d:
        return {"field": label, "value": "—", "status": "n/a", "note": missing}
    root_f, root_o = org_root(from_d), org_root(other_d)
    if root_f and root_o and root_f == root_o:
        return {
            "field": label,
            "value": other_d,
            "status": "same_org",
            "note": f"Shares organisational root {root_f} with From domain {from_d}.",
        }
    return {
        "field": label,
        "value": other_d,
        "status": "mismatch",
        "note": f"{label} domain {other_d} does not match From domain {from_d}.",
    }


def identity_alignment(
    headers: dict[str, str],
    from_addr: str,
    reply_to: str,
    auth: dict[str, str],
) -> dict[str, Any]:
    from_d = domain_of(from_addr)
    rp = (headers.get("Return-Path") or "").strip().strip("<>")
    rp_d = domain_of(rp) if rp else ""
    reply_d = domain_of(reply_to) if reply_to else ""
    dkim_d = (auth.get("dkim_domain") or "").lower()
    spf_d = (auth.get("spf_domain") or "").lower()
    if "@" in spf_d:
        spf_d = domain_of(spf_d)

    rows = [
        _cmp(from_d, rp_d, "Return-Path", "No Return-Path (or empty). Bounce routing not independently declared."),
        _cmp(from_d, reply_d, "Reply-To", "No separate Reply-To (defaults to From)."),
        _cmp(from_d, dkim_d, "DKIM signing domain", "No header.d= in Authentication-Results."),
        _cmp(from_d, spf_d, "SPF evaluated domain", "No smtp.mailfrom= in Authentication-Results."),
    ]
    mismatches = sum(1 for r in rows if r["status"] == "mismatch")
    return {
        "from_domain": from_d,
        "rows": rows,
        "mismatch_count": mismatches,
        "clean": mismatches == 0,
        "note": "Same organisational root is not a person. It only means bounce/signing domains belong to the same DNS tree.",
    }
