# src/freya/api/routes/watch.py
"""
Cyber Watch API Routes

Endpoints for security monitoring:
- CISA KEV (Known Exploited Vulnerabilities)
- CERT-FR alerts
- CVE search
- Custom RSS feeds
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------
class WatchItem(BaseModel):
    """Security watch item."""
    source: str
    title: str
    url: str
    published: str
    cve: str | None = None
    severity: str | None = None
    description: str | None = None


class WatchFeed(BaseModel):
    """Watch feed response."""
    source: str
    items: list[WatchItem]
    fetched_at: str
    cached: bool


class CVEInfo(BaseModel):
    """CVE information."""
    cve_id: str
    description: str
    severity: str | None = None
    cvss_score: float | None = None
    references: list[str] = []
    affected_products: list[str] = []


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/", response_model=list[WatchItem])
async def get_watch_feed(request: Request, limit: int = 25) -> list[WatchItem]:
    """
    Get combined cyber watch feed.
    
    Combines CISA KEV and CERT-FR alerts, prioritized by criticality.
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import cyber_watch
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = cyber_watch(cache_dir)
        return [
            WatchItem(
                source=item.source,
                title=item.title,
                url=item.url,
                published=item.published,
                cve=item.cve
            )
            for item in items[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch watch feed: {e}")


@router.get("/cisa-kev", response_model=WatchFeed)
async def get_cisa_kev(request: Request, limit: int = 50) -> WatchFeed:
    """
    Get CISA Known Exploited Vulnerabilities catalog.
    
    Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_cisa_kev
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = fetch_cisa_kev(cache_dir, ttl_sec=1800)
        return WatchFeed(
            source="CISA-KEV",
            items=[
                WatchItem(
                    source=item.source,
                    title=item.title,
                    url=item.url,
                    published=item.published,
                    cve=item.cve
                )
                for item in items[:limit]
            ],
            fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            cached=True  # Cache TTL is 30 min
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CISA KEV: {e}")


@router.get("/cert-fr", response_model=WatchFeed)
async def get_cert_fr(request: Request, limit: int = 30) -> WatchFeed:
    """
    Get CERT-FR security alerts (ANSSI).
    
    Source: https://www.cert.ssi.gouv.fr/alerte/feed/
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_certfr_rss
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = fetch_certfr_rss(cache_dir, ttl_sec=1800)
        return WatchFeed(
            source="CERT-FR",
            items=[
                WatchItem(
                    source=item.source,
                    title=item.title,
                    url=item.url,
                    published=item.published,
                    cve=item.cve
                )
                for item in items[:limit]
            ],
            fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            cached=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CERT-FR: {e}")


@router.get("/cve/{cve_id}")
async def lookup_cve(request: Request, cve_id: str) -> CVEInfo:
    """
    Lookup a specific CVE.
    
    Uses NVD (National Vulnerability Database) API.
    Note: Rate limited to 5 requests per 30 seconds without API key.
    """
    import urllib.request
    import urllib.parse
    
    # Validate CVE format
    if not cve_id.upper().startswith("CVE-"):
        raise HTTPException(status_code=400, detail="Invalid CVE format. Expected: CVE-YYYY-NNNNN")
    
    cve_id = cve_id.upper()
    
    # NVD API 2.0
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={urllib.parse.quote(cve_id)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Freya/2.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        
        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            raise HTTPException(status_code=404, detail=f"CVE not found: {cve_id}")
        
        cve_data = vulnerabilities[0].get("cve", {})
        
        # Extract description (prefer English)
        descriptions = cve_data.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        if not description and descriptions:
            description = descriptions[0].get("value", "")
        
        # Extract CVSS score
        metrics = cve_data.get("metrics", {})
        cvss_score = None
        severity = None
        
        # Try CVSS 3.1 first, then 3.0, then 2.0
        for cvss_key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if cvss_key in metrics and metrics[cvss_key]:
                metric = metrics[cvss_key][0]
                cvss_data = metric.get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                severity = cvss_data.get("baseSeverity")
                break
        
        # Extract references
        references = []
        for ref in cve_data.get("references", [])[:10]:
            url = ref.get("url")
            if url:
                references.append(url)
        
        # Extract affected products (CPE)
        affected = []
        configurations = cve_data.get("configurations", [])
        for config in configurations[:5]:
            for node in config.get("nodes", [])[:5]:
                for match in node.get("cpeMatch", [])[:5]:
                    criteria = match.get("criteria", "")
                    if criteria:
                        # Extract product name from CPE
                        parts = criteria.split(":")
                        if len(parts) >= 5:
                            vendor = parts[3]
                            product = parts[4]
                            affected.append(f"{vendor}/{product}")
        
        return CVEInfo(
            cve_id=cve_id,
            description=description,
            severity=severity,
            cvss_score=cvss_score,
            references=references,
            affected_products=list(set(affected))[:10]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CVE lookup failed: {e}")


@router.get("/stats")
async def get_watch_stats(request: Request) -> dict[str, Any]:
    """Get watch statistics and cache status."""
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cache_dir = state.config.cache_root / "watch"
    
    stats = {
        "cache_dir": str(cache_dir),
        "sources": {},
    }
    
    # Check each cache file
    cache_files = {
        "cisa_kev": cache_dir / "cisa_kev.json",
        "cert_fr": cache_dir / "certfr_alerte_rss.xml",
    }
    
    for name, path in cache_files.items():
        if path.exists():
            stat = path.stat()
            age_seconds = time.time() - stat.st_mtime
            stats["sources"][name] = {
                "cached": True,
                "age_minutes": round(age_seconds / 60, 1),
                "size_bytes": stat.st_size,
                "stale": age_seconds > 1800  # > 30 min
            }
        else:
            stats["sources"][name] = {
                "cached": False,
                "age_minutes": None,
                "size_bytes": 0,
                "stale": True
            }
    
    return stats
