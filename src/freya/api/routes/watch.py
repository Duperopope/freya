# src/freya/api/routes/watch.py
"""
Cyber Watch API Routes

Endpoints for security monitoring:
- CISA KEV (Known Exploited Vulnerabilities)
- CERT-FR alerts (ANSSI)
- NVD recent CVEs
- Exploit-DB
- GitHub Security Advisories
- CVE search
- Real-time statistics
"""

from __future__ import annotations

import json
import time
from datetime import datetime
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
    tags: list[str] = []


class WatchFeed(BaseModel):
    """Watch feed response."""
    source: str
    items: list[WatchItem]
    fetched_at: str
    cached: bool
    item_count: int


class CVEInfo(BaseModel):
    """CVE information."""
    cve_id: str
    description: str
    severity: str | None = None
    cvss_score: float | None = None
    references: list[str] = []
    affected_products: list[str] = []


class WatchStats(BaseModel):
    """Watch statistics."""
    source: str
    last_fetch: str | None
    item_count: int
    cache_age_minutes: float
    is_stale: bool


class WatchConfig(BaseModel):
    """Watch configuration."""
    auto_refresh: bool = True
    refresh_interval_minutes: int = 30
    enabled_sources: list[str] = ["cisa", "certfr", "nvd", "exploitdb", "github"]


# Global config (in-memory, could be persisted)
_watch_config = WatchConfig()


# -----------------------------------------------------------------------------
# Helper to convert internal WatchItem to API WatchItem
# -----------------------------------------------------------------------------
def _to_api_item(item) -> WatchItem:
    """Convert internal WatchItem to API WatchItem."""
    return WatchItem(
        source=item.source,
        title=item.title,
        url=item.url,
        published=item.published,
        cve=item.cve,
        severity=getattr(item, 'severity', None),
        description=getattr(item, 'description', None),
        tags=getattr(item, 'tags', [])
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/", response_model=list[WatchItem])
async def get_watch_feed(
    request: Request,
    limit: int = 50,
    sources: str | None = None
) -> list[WatchItem]:
    """
    Get combined cyber watch feed.
    
    Args:
        limit: Maximum items to return (default 50)
        sources: Comma-separated list of sources (default: all enabled)
                 Options: cisa, certfr, nvd, exploitdb, github, packetstorm, threatpost
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import cyber_watch
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse sources
    source_list = None
    if sources:
        source_list = [s.strip().lower() for s in sources.split(",")]
    else:
        source_list = _watch_config.enabled_sources
    
    try:
        items = cyber_watch(cache_dir, sources=source_list, limit=limit)
        return [_to_api_item(item) for item in items]
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
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
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
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CERT-FR: {e}")


@router.get("/cert-fr-avis", response_model=WatchFeed)
async def get_cert_fr_avis(request: Request, limit: int = 30) -> WatchFeed:
    """
    Get CERT-FR security advisories (less critical than alerts).
    
    Source: https://www.cert.ssi.gouv.fr/avis/feed/
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_certfr_avis
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = fetch_certfr_avis(cache_dir, ttl_sec=1800)
        return WatchFeed(
            source="CERT-FR-Avis",
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CERT-FR Avis: {e}")


@router.get("/nvd", response_model=WatchFeed)
async def get_nvd_recent(request: Request, limit: int = 50, days: int = 7) -> WatchFeed:
    """
    Get recent CVEs from NVD (National Vulnerability Database).
    
    Note: Rate limited without API key.
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_nvd_recent
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = fetch_nvd_recent(cache_dir, ttl_sec=3600, days=days)
        return WatchFeed(
            source="NVD",
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch NVD: {e}")


@router.get("/exploitdb", response_model=WatchFeed)
async def get_exploitdb(request: Request, limit: int = 30) -> WatchFeed:
    """
    Get recent exploits from Exploit-DB.
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_exploitdb
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        items = fetch_exploitdb(cache_dir, ttl_sec=3600)
        return WatchFeed(
            source="Exploit-DB",
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Exploit-DB: {e}")


@router.get("/github", response_model=WatchFeed)
async def get_github_advisories(request: Request, limit: int = 30) -> WatchFeed:
    """
    Get GitHub Security Advisories.
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import fetch_github_advisories
    
    cache_dir = state.config.cache_root / "watch"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # TODO: Get GitHub token from config if available
        items = fetch_github_advisories(cache_dir, ttl_sec=1800, token="")
        return WatchFeed(
            source="GitHub-GHSA",
            items=[_to_api_item(item) for item in items[:limit]],
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cached=True,
            item_count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub advisories: {e}")


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
            ref_url = ref.get("url")
            if ref_url:
                references.append(ref_url)
        
        # Extract affected products (CPE)
        affected = []
        configurations = cve_data.get("configurations", [])
        for config in configurations[:5]:
            for node in config.get("nodes", [])[:5]:
                for match in node.get("cpeMatch", [])[:5]:
                    criteria = match.get("criteria", "")
                    if criteria:
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
    """
    Get watch statistics and cache status.
    
    Returns timing information for each source.
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    from ...tools.webwatch import get_watch_stats as _get_stats
    
    cache_dir = state.config.cache_root / "watch"
    
    stats = _get_stats(cache_dir)
    
    result = {
        "cache_dir": str(cache_dir),
        "config": {
            "auto_refresh": _watch_config.auto_refresh,
            "refresh_interval_minutes": _watch_config.refresh_interval_minutes,
            "enabled_sources": _watch_config.enabled_sources
        },
        "sources": {}
    }
    
    for name, stat in stats.items():
        result["sources"][name] = {
            "last_fetch": stat.last_fetch.isoformat() if stat.last_fetch else None,
            "item_count": stat.item_count,
            "cache_age_minutes": stat.cache_age_minutes,
            "is_stale": stat.is_stale
        }
    
    return result


@router.get("/config", response_model=WatchConfig)
async def get_watch_config() -> WatchConfig:
    """Get current watch configuration."""
    return _watch_config


@router.post("/config", response_model=WatchConfig)
async def update_watch_config(config: WatchConfig) -> WatchConfig:
    """Update watch configuration."""
    global _watch_config
    _watch_config = config
    return _watch_config


@router.post("/refresh")
async def force_refresh(request: Request, sources: str | None = None) -> dict[str, Any]:
    """
    Force refresh of watch feeds (bypasses cache).
    
    Args:
        sources: Comma-separated list of sources to refresh (default: all)
    """
    state = request.app.state.freya
    
    if not state.ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cache_dir = state.config.cache_root / "watch"
    
    # Clear cache files for requested sources
    source_files = {
        "cisa": "cisa_kev.json",
        "certfr": "certfr_alerte.xml",
        "certfr-avis": "certfr_avis.xml",
        "nvd": "nvd_recent.json",
        "exploitdb": "exploitdb.xml",
        "github": "github_advisories.json",
        "packetstorm": "packetstorm.xml",
        "threatpost": "threatpost.xml",
    }
    
    source_list = None
    if sources:
        source_list = [s.strip().lower() for s in sources.split(",")]
    else:
        source_list = list(source_files.keys())
    
    cleared = []
    for source in source_list:
        if source in source_files:
            cache_file = cache_dir / source_files[source]
            if cache_file.exists():
                cache_file.unlink()
                cleared.append(source)
    
    # Re-fetch the feeds
    from ...tools.webwatch import cyber_watch
    try:
        items = cyber_watch(cache_dir, sources=source_list, limit=50)
        return {
            "status": "refreshed",
            "cleared_caches": cleared,
            "new_item_count": len(items),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "partial",
            "cleared_caches": cleared,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
