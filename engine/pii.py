"""DPDP-style redaction for report preview (prototype, not a legal DPDP product)."""

from __future__ import annotations

import re

AADHAAR = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.I)
PHONE = re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def mask_text(text: str) -> str:
    out = AADHAAR.sub("[AADHAAR-REDACTED]", text or "")
    out = PAN.sub("[PAN-REDACTED]", out)
    out = PHONE.sub("[PHONE-REDACTED]", out)
    out = EMAIL.sub("[EMAIL-REDACTED]", out)
    return out
