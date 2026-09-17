from __future__ import annotations

import email
import ipaddress
import re
from email import policy
from email.message import EmailMessage
from typing import Any

RECEIVED_IP = re.compile(
    r"\[?(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\]?"
)
# Skip RFC1918 / loopback when attributing "origin"
PRIVATE = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
)


def _is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.version != 4:
        return False
    return not any(addr in net for net in PRIVATE)


def parse_raw(raw: str) -> EmailMessage:
    return email.message_from_string(raw, policy=policy.default)


def body_text(msg: EmailMessage) -> str:
    if msg.is_multipart():
        parts: list[str] = []
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    parts.append(payload.decode("utf-8", errors="replace"))
            elif ctype == "text/html" and not parts:
                try:
                    html = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    html = payload.decode("utf-8", errors="replace")
                parts.append(re.sub(r"<[^>]+>", " ", html))
        return "\n".join(parts)
    try:
        return str(msg.get_content())
    except Exception:
        payload = msg.get_payload(decode=True) or b""
        return payload.decode("utf-8", errors="replace")


def parse_auth_results(value: str | None) -> dict[str, str]:
    out = {"spf": "none", "dkim": "none", "dmarc": "none", "dkim_domain": "", "spf_domain": "", "header_from": ""}
    if not value:
        return out
    low = value.lower()
    for proto in ("spf", "dkim", "dmarc"):
        m = re.search(rf"{proto}\s*=\s*(pass|fail|neutral|softfail|none|permerror|temperror)", low)
        if m:
            out[proto] = m.group(1)
    m = re.search(r"header\.d\s*=\s*([^\s;]+)", low)
    if m:
        out["dkim_domain"] = m.group(1).rstrip(";")
    m = re.search(r"smtp\.mailfrom\s*=\s*([^\s;]+)", low)
    if m:
        out["spf_domain"] = m.group(1).rstrip(";")
    m = re.search(r"header\.from\s*=\s*([^\s;]+)", low)
    if m:
        out["header_from"] = m.group(1).rstrip(";")
    return out


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>\"']+", text, flags=re.I)


def extract_emails_from_header(value: str | None) -> str:
    if not value:
        return ""
    m = re.search(r"<([^>]+)>", value)
    return (m.group(1) if m else value).strip()


def received_hops(msg: EmailMessage) -> list[dict[str, Any]]:
    """Received headers are prepended: first in list is last hop (closest to us)."""
    raw_list = msg.get_all("Received") or []
    hops = []
    for i, hdr in enumerate(raw_list):
        ips = [m.group("ip") for m in RECEIVED_IP.finditer(hdr)]
        public = [ip for ip in ips if _is_public(ip)]
        hops.append(
            {
                "index": i,
                "header": " ".join(hdr.split()),
                "ips": ips,
                "public_ips": public,
            }
        )
    return hops


def origin_ip(hops: list[dict[str, Any]]) -> str | None:
    """Earliest public IP in the Received chain (last header, last public IP)."""
    if not hops:
        return None
    last = hops[-1]
    pubs = last.get("public_ips") or []
    if pubs:
        return pubs[-1]
    for hop in reversed(hops):
        if hop["public_ips"]:
            return hop["public_ips"][-1]
    return None


def flatten_headers(msg: EmailMessage) -> dict[str, str]:
    keys = [
        "From",
        "To",
        "Cc",
        "Subject",
        "Date",
        "Reply-To",
        "Return-Path",
        "Message-ID",
        "Sender",
        "X-Originating-IP",
        "Authentication-Results",
        "Received-SPF",
    ]
    return {k: str(msg.get(k) or "") for k in keys}


def attachments(msg: EmailMessage) -> list[str]:
    names = []
    for part in msg.walk():
        fn = part.get_filename()
        if fn:
            names.append(fn)
    return names
