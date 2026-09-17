from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .geo import geolocate_hops
from .nlp import analyze_text, domain_of
from .parse import (
    attachments,
    body_text,
    extract_emails_from_header,
    extract_urls,
    flatten_headers,
    origin_ip,
    parse_auth_results,
    parse_raw,
    received_hops,
)
from .score import score_case


def analyze_raw(raw: str, source_name: str = "paste") -> dict[str, Any]:
    msg = parse_raw(raw)
    headers = flatten_headers(msg)
    hops = received_hops(msg)
    origin = origin_ip(hops)
    xip = (headers.get("X-Originating-IP") or "").strip("[] ")
    if not origin and xip:
        origin = xip.split()[0]
    geo_hops = geolocate_hops(hops, origin)
    body = body_text(msg)
    urls = extract_urls(body) + extract_urls(headers.get("Subject", ""))
    files = attachments(msg)
    from_addr = extract_emails_from_header(headers.get("From"))
    reply = extract_emails_from_header(headers.get("Reply-To"))
    nlp = analyze_text(headers.get("Subject", ""), body, urls, from_addr, reply, files)
    auth = parse_auth_results(headers.get("Authentication-Results"))
    spf_hdr = headers.get("Received-SPF", "").lower()
    if "pass" in spf_hdr:
        auth["spf"] = auth.get("spf") if auth.get("spf") != "none" else "pass"
    if "fail" in spf_hdr:
        auth["spf"] = "fail"
    scored = score_case(auth, nlp, geo_hops, origin)
    return {
        "source_name": source_name,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "headers": headers,
        "from_addr": from_addr,
        "from_domain": domain_of(from_addr),
        "reply_to": reply,
        "subject": headers.get("Subject", ""),
        "body_preview": body[:2500],
        "urls": urls[:15],
        "attachments": files,
        "auth": auth,
        "hops": hops,
        "geo_hops": geo_hops,
        "nlp": nlp,
        **scored,
    }
