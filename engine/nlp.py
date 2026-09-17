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
CDN_HOSTS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "www.gstatic.com",
    "ajax.googleapis.com",
    "cdnjs.cloudflare.com",
)
SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd")
FRAUD = [
    "gift cards",
    "wire transfer",
    "invoice",
    "overdue",
    "payment diversion",
    "change of account",
    "beneficiary",
]
HARVEST = ["verify kyc", "enter otp", "password", "login to continue", "confirm your password"]
QUISH = ["qr code", "scan the qr", "scan this qr", "quishing"]
BRAND_LABELS = ("paypal", "microsoft", "google", "hdfcbank", "sbi", "gmail", "outlook", "amazon", "apple")


def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


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
        if any(host == c or host.endswith("." + c) for c in CDN_HOSTS):
            continue
        if any(s in host for s in SHORTENERS):
            url_issues.append(f"URL shortener / possible hidden redirect: {host}")
        fd = domain_of(from_addr)
        if fd and host and fd not in host and "http" in u:
            url_issues.append(f"Link host {host} does not match From domain {fd}")
    bad_files = [f for f in files if any(f.lower().endswith(ext) for ext in RISKY_EXTS)]
    mismatch = bool(reply_to and domain_of(reply_to) and domain_of(from_addr) and domain_of(reply_to) != domain_of(from_addr))
    display = from_addr.lower()
    spoof_name = any(k in display for k in ("sbi", "hdfc", "microsoft", "google", "income tax", "gst")) and not any(
        x in domain_of(from_addr) for x in ("sbi", "hdfc", "microsoft", "google", "gov.in", "nic.in")
    )
    fraud_cues = [w for w in FRAUD if w in blob]
    harvest_cues = [w for w in HARVEST if w in blob]
    obfuscated = [u for u in urls if "%" in u or any(s in u.lower() for s in SHORTENERS)]
    quishing = any(q in blob for q in QUISH) or any("qr" in u.lower() and "http" in u.lower() for u in urls)
    typosquat = []
    host_bits: list[str] = []
    if domain_of(from_addr):
        host_bits.extend(re.split(r"[.\-]", domain_of(from_addr)))
    for u in urls:
        h = (urlparse(u).hostname or "").lower()
        if h:
            host_bits.extend(re.split(r"[.\-]", h))
    for token in {t.lower() for t in host_bits if len(t) >= 4}:
        for brand in BRAND_LABELS:
            d = _lev(token, brand)
            if 0 < d <= 2 and token != brand:
                typosquat.append(f"{token}~{brand} (edit distance {d})")
    return {
        "urgency_cues": hits_u,
        "impersonation_cues": hits_i,
        "lookalike_tokens": look,
        "url_issues": list(dict.fromkeys(url_issues))[:8],
        "risky_attachments": bad_files,
        "from_reply_mismatch": mismatch,
        "display_name_spoof": spoof_name,
        "url_count": len(urls),
        "fraud_cues": fraud_cues,
        "harvest_cues": harvest_cues,
        "obfuscated_urls": obfuscated[:8],
        "quishing": quishing,
        "typosquat": list(dict.fromkeys(typosquat))[:6],
        "calm_bec": bool(hits_i and not hits_u),
    }
