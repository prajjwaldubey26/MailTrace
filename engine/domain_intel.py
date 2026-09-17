"""Public DNS snapshot for the From domain (MX / A). No paid WHOIS key required."""

from __future__ import annotations

from typing import Any

import httpx


def _dns_google(name: str, rtype: str, timeout: float = 2.0) -> list[str]:
    try:
        r = httpx.get(
            "https://dns.google/resolve",
            params={"name": name, "type": rtype},
            timeout=timeout,
        )
        data = r.json()
        answers = data.get("Answer") or []
        out = []
        for a in answers:
            d = str(a.get("data") or "").strip().rstrip(".")
            if d:
                out.append(d)
        return out[:8]
    except Exception:
        return []


def lookup_domain(domain: str) -> dict[str, Any]:
    domain = (domain or "").lower().strip().rstrip(".")
    if not domain or "." not in domain:
        return {
            "domain": domain or "(none)",
            "ok": False,
            "a_records": [],
            "mx_records": [],
            "notes": ["No registrable From domain to query."],
            "nxdomain": False,
        }
    a = _dns_google(domain, "A")
    mx = _dns_google(domain, "MX")
    notes = []
    nx = False
    if not a and not mx:
        notes.append("No A/MX from public DNS (offline, blocked, or domain may not exist).")
        nx = True
    elif not mx:
        notes.append("No MX records — unusual for a mailbox domain.")
    else:
        notes.append("MX present — domain can receive mail (not proof the From is honest).")
    return {
        "domain": domain,
        "ok": bool(a or mx),
        "a_records": a,
        "mx_records": mx,
        "notes": notes,
        "nxdomain": nx and not a and not mx,
        "source": "dns.google",
    }
