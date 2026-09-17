from __future__ import annotations

import ipaddress
from typing import Any

import httpx

from .geo_db import GEO_BY_IP, PREFIX_FALLBACK


def _local(ip: str) -> dict | None:
    if ip in GEO_BY_IP:
        return {"ip": ip, "source": "local_demo_db", **GEO_BY_IP[ip]}
    for prefix, row in PREFIX_FALLBACK:
        if ip.startswith(prefix):
            return {"ip": ip, "source": "local_prefix", **row}
    return None


def lookup_ip(ip: str, timeout: float = 2.5) -> dict[str, Any]:
    local = _local(ip)
    if local:
        return local
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback:
            return {
                "ip": ip,
                "source": "private",
                "city": "",
                "region": "",
                "country": "Private / internal",
                "lat": None,
                "lon": None,
                "isp": "internal",
                "org": "RFC1918",
                "threat_tag": "internal",
            }
    except ValueError:
        return {"ip": ip, "source": "invalid", "country": "invalid", "lat": None, "lon": None, "threat_tag": "invalid"}

    try:
        r = httpx.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,query", timeout=timeout)
        data = r.json()
        if data.get("status") == "success":
            return {
                "ip": ip,
                "source": "ip-api",
                "city": data.get("city") or "",
                "region": data.get("regionName") or "",
                "country": data.get("country") or "",
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "isp": data.get("isp") or "",
                "org": data.get("org") or "",
                "threat_tag": "lookup",
            }
    except Exception:
        pass
    return {
        "ip": ip,
        "source": "unknown",
        "city": "",
        "region": "",
        "country": "Unknown (offline)",
        "lat": None,
        "lon": None,
        "isp": "",
        "org": "",
        "threat_tag": "unknown",
    }


def geolocate_hops(hops: list[dict], origin: str | None) -> list[dict]:
    seen: set[str] = set()
    points = []
    for hop in reversed(hops):  # chronological: first sender → last MX
        for ip in hop.get("public_ips") or []:
            if ip in seen:
                continue
            seen.add(ip)
            geo = lookup_ip(ip)
            geo["role"] = "origin" if origin and ip == origin else "relay"
            points.append(geo)
    if origin and origin not in seen:
        geo = lookup_ip(origin)
        geo["role"] = "origin"
        points.insert(0, geo)
    return points
