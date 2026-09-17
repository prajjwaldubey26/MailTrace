"""Graph-based correlation: mailbox, domain, origin IP, URLs (PS identity correlation)."""

from __future__ import annotations

from typing import Any


def build_graph(result: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict] = []
    edges: list[dict] = []

    def add(nid: str, kind: str, label: str, detail: str = "") -> None:
        if any(n["id"] == nid for n in nodes):
            return
        nodes.append({"id": nid, "kind": kind, "label": label, "detail": detail})

    from_addr = result.get("from_addr") or ""
    domain = result.get("from_domain") or ""
    reply = result.get("reply_to") or ""
    origin = (result.get("attribution") or {}).get("origin_ip") or ""
    tclass = result.get("threat_class") or result.get("label") or ""

    if from_addr:
        add("from", "mailbox", from_addr, "From header")
    if domain:
        add("domain", "domain", domain, "From domain")
        if from_addr:
            edges.append({"source": "from", "target": "domain", "rel": "uses domain"})
    if reply:
        add("reply", "mailbox", reply, "Reply-To")
        if from_addr:
            edges.append({"source": "from", "target": "reply", "rel": "reply-to hijack" if result.get("nlp", {}).get("from_reply_mismatch") else "reply-to"})
    if origin:
        geo = (result.get("attribution") or {}).get("origin_geo") or {}
        place = ", ".join(x for x in [geo.get("city"), geo.get("country")] if x) or "unknown geo"
        add("origin", "ip", origin, f"First public hop · {place} · {geo.get('isp') or ''}")
        if domain:
            edges.append({"source": "domain", "target": "origin", "rel": "sent via"})
    for i, url in enumerate((result.get("urls") or [])[:5]):
        nid = f"url{i}"
        add(nid, "url", url[:80], "Extracted URL")
        if domain:
            edges.append({"source": "domain", "target": nid, "rel": "linked"})
    for i, fn in enumerate((result.get("attachments") or [])[:3]):
        nid = f"file{i}"
        add(nid, "file", fn, "Attachment")
        if from_addr:
            edges.append({"source": "from", "target": nid, "rel": "attached"})

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": f"{len(nodes)} artefacts · {len(edges)} links · class {tclass}",
        "note": "Infrastructure graph only — nodes are mailboxes, domains, IPs, and URLs, not a named person.",
    }
