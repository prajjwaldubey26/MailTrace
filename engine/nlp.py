from __future__ import annotations

import re
from urllib.parse import urlparse

URGENCY = [
    "urgent",
    "immediately",
    "within 24 hours",
    "account will be closed",
    "suspended",
    "verify now",
    "click here",
    "act now",
    "last warning",
    "failed payment",
    "wire transfer",
    "gift cards",
    "do not tell",
    "keep this confidential",
    "otp",
    "one-time password",
    "kyc pending",
    "gst notice",
    "pan aadhaar",
]

IMPERSONATION = [
    "dean",
    "registrar",
    "vice chancellor",
    "principal",
    "accounts payable",
    "ceo",
    "cfo",
    "managing director",
    "it helpdesk",
    "microsoft security",
    "google workspace",
    "income tax",
    "gstn",
    "sbi",
    "hdfc",
    "reserve bank",
    "uidai",
]

LOOKALIKE = [
    "paypa1",
    "rnicrosoft",
    "g00gle",
    "app1e",
    "secure-login",
    "account-verify",
    "college-edu",
    "gov-in-secure",
    "offlce365",
    "micr0soft",
]

RISKY_TLDS = {".xyz", ".top", ".icu", ".click", ".country", ".gq", ".tk", ".ml", ".cf", ".zip", ".mov"}
RISKY_EXTS = {".exe", ".js", ".vbs", ".scr", ".iso", ".html", ".htm", ".docm", ".xlsm"}


def domain_of(addr: str) -> str:
    addr = addr.lower().strip()
    if "@" in addr:
        return addr.rsplit("@", 1)[-1]
    return addr


def analyze_text(subject: str, body: str, urls: list[str], from_addr: str, reply_to: str, files: list[str]) -> dict:
    blob = f"{subject}\n{body}\n{from_addr}".lower()
    hits_u = [w for w in URGENCY if w in blob]
    hits_i = [w for w in IMPERSONATION if w in blob or w in from_addr.lower()]
    look = [w for w in LOOKALIKE if w in blob or any(w in u.lower() for u in urls)]
    url_issues = []
    for u in urls:
        host = (urlparse(u).hostname or "").lower()
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            url_issues.append(f"URL uses raw IP: {host}")
        if any(host.endswith(t) for t in RISKY_TLDS):
            url_issues.append(f"Risky TLD: {host}")
        fd = domain_of(from_addr)
        if fd and host and fd not in host and "http" in u:
            url_issues.append(f"Link host {host} does not match From domain {fd}")
    bad_files = [f for f in files if any(f.lower().endswith(ext) for ext in RISKY_EXTS)]
    mismatch = bool(reply_to and domain_of(reply_to) and domain_of(from_addr) and domain_of(reply_to) != domain_of(from_addr))
    display = from_addr.lower()
    spoof_name = any(k in display for k in ("sbi", "hdfc", "microsoft", "google", "income tax", "gst")) and not any(
        x in domain_of(from_addr) for x in ("sbi", "hdfc", "microsoft", "google", "gov.in", "nic.in")
    )
    return {
        "urgency_cues": hits_u,
        "impersonation_cues": hits_i,
        "lookalike_tokens": look,
        "url_issues": list(dict.fromkeys(url_issues))[:8],
        "risky_attachments": bad_files,
        "from_reply_mismatch": mismatch,
        "display_name_spoof": spoof_name,
        "url_count": len(urls),
    }
