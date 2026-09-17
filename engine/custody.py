"""SHA-256 of the raw RFC822 bytes for evidence preservation (prototype chain-of-custody)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def custody_record(raw: str) -> dict:
    blob = raw.encode("utf-8", errors="replace")
    return {
        "algorithm": "SHA-256",
        "sha256": hashlib.sha256(blob).hexdigest(),
        "byte_length": len(blob),
        "hashed_at": datetime.now(timezone.utc).isoformat(),
        "note": "Hash of the exact pasted/uploaded original. Prototype evidence log, not a legal chain-of-custody.",
    }
