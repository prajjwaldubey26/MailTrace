from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from .custody import custody_record
from .domain_intel import lookup_domain
from .explain import analyst_guidance, explain_case, findings_board, iocs, playbook
from .graph import build_graph
from .geo import geolocate_hops
from .headers_intel import analyze_headers
from .identity import identity_alignment
from .nlp import analyze_text, domain_of
from .pii import mask_text
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


def _phase(name: str, status: str, detail: str, started: float) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }


def analyze_raw(raw: str, source_name: str = "paste") -> dict[str, Any]:
    t_all = time.perf_counter()
    phases: list[dict[str, Any]] = []

    t0 = time.perf_counter()
    custody = custody_record(raw)
    msg = parse_raw(raw)
    headers = flatten_headers(msg)
    phases.append(
        _phase(
            "1 · Ingestion & SHA-256",
            "CLEAN",
            f"{custody.get('algorithm')} {str(custody.get('sha256') or '')[:16]}… · {custody.get('byte_length')} bytes",
            t0,
        )
    )

    t0 = time.perf_counter()
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
    auth = parse_auth_results(headers.get("Authentication-Results"))
    spf_hdr = headers.get("Received-SPF", "").lower()
    if "pass" in spf_hdr:
        auth["spf"] = auth.get("spf") if auth.get("spf") != "none" else "pass"
    if "fail" in spf_hdr:
        auth["spf"] = "fail"
    auth_fail = any(auth.get(k) == "fail" for k in ("spf", "dkim", "dmarc"))
    phases.append(
        _phase(
            "2 · Authentication (SPF / DKIM / DMARC)",
            "FLAGGED" if auth_fail else "CLEAN",
            f"SPF {auth.get('spf')} · DKIM {auth.get('dkim')} · DMARC {auth.get('dmarc')}",
            t0,
        )
    )

    t0 = time.perf_counter()
    identity = identity_alignment(headers, from_addr, reply, auth)
    header_intel = analyze_headers(headers, hops, from_addr, reply)
    id_status = "FLAGGED" if identity.get("mismatch_count") else "CLEAN"
    phases.append(
        _phase(
            "3 · Sender identity",
            id_status,
            f"{identity.get('mismatch_count', 0)} org-domain mismatch(es) vs From {identity.get('from_domain') or 'n/a'}",
            t0,
        )
    )

    t0 = time.perf_counter()
    nlp = analyze_text(headers.get("Subject", ""), body, urls, from_addr, reply, files)
    lang_hits = bool(
        nlp.get("urgency_cues")
        or nlp.get("fraud_cues")
        or nlp.get("harvest_cues")
        or nlp.get("impersonation_cues")
    )
    phases.append(
        _phase(
            "4 · Language / behavioural scan",
            "FLAGGED" if lang_hits else "CLEAN",
            "Weighted keyword + lookalike heuristics (not a transformer).",
            t0,
        )
    )

    t0 = time.perf_counter()
    anoms = header_intel.get("anomalies") or []
    phases.append(
        _phase(
            "5 · Header & relay chain",
            "FLAGGED" if any(int(a.get("points") or 0) > 0 for a in anoms) else "CLEAN",
            f"{len(hops)} Received hop(s) · {len(anoms)} header note(s)",
            t0,
        )
    )

    t0 = time.perf_counter()
    domain_intel = lookup_domain(domain_of(from_addr))
    dns_flag = bool(domain_intel.get("nxdomain") or not domain_intel.get("ok"))
    phases.append(
        _phase(
            "6 · Domain DNS / MX",
            "FLAGGED" if dns_flag else "CLEAN",
            " ".join(domain_intel.get("notes") or []) or (domain_intel.get("domain") or "no domain"),
            t0,
        )
    )

    t0 = time.perf_counter()
    scored = score_case(auth, nlp, geo_hops, origin, header_intel, domain_intel)
    result = {
        "source_name": source_name,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "headers": headers,
        "from_addr": from_addr,
        "from_domain": domain_of(from_addr),
        "reply_to": reply,
        "subject": headers.get("Subject", ""),
        "body_preview": mask_text(body[:2500]),
        "urls": urls[:15],
        "attachments": files,
        "auth": auth,
        "hops": hops,
        "geo_hops": geo_hops,
        "nlp": nlp,
        "header_intel": header_intel,
        "domain_intel": domain_intel,
        "identity": identity,
        "custody": custody,
        **scored,
    }
    result["explain"] = explain_case(result["score"], result["reasons"], nlp, auth)
    result["iocs"] = iocs(result)
    result["graph"] = build_graph(result)
    tclass = result.get("threat_class") or result.get("label") or ""
    result["playbook"] = playbook(tclass)
    result["severity"] = result["explain"].get("severity")
    result["findings"] = findings_board(result.get("reasons") or [], anoms, auth)
    result["guidance"] = analyst_guidance(
        tclass,
        int(result.get("score") or 0),
        auth,
        identity,
        bool(result["explain"].get("hitl_review")),
    )
    result["evidence"] = {
        "sealed": True,
        "algorithm": custody.get("algorithm"),
        "sha256": custody.get("sha256"),
        "byte_length": custody.get("byte_length"),
        "hashed_at": custody.get("hashed_at"),
        "note": custody.get("note"),
        "vault": "local SQLite case store — prototype chain of custody, not a courtroom exhibit",
    }
    cls_flag = "FLAGGED" if tclass not in ("legitimate", "") else "CLEAN"
    phases.append(
        _phase(
            "7 · Score, class & attribution",
            cls_flag,
            f"{tclass} · {result.get('score')}/100 · first public hop is infrastructure, not a person",
            t0,
        )
    )
    result["phases"] = phases
    result["pipeline_s"] = round(time.perf_counter() - t_all, 3)
    return result
