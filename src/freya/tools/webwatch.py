# src/freya/tools/webwatch.py
"""
Cyber Watch Module for Freya

Security intelligence feeds:
- CISA KEV (Known Exploited Vulnerabilities)
- CERT-FR alerts (ANSSI)
- NVD (National Vulnerability Database)
- Exploit-DB
- GitHub Security Advisories
- VulnDB
- Packet Storm
- Threatpost RSS
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class WatchItem:
    """Security watch item."""
    source: str
    title: str
    url: str
    published: str
    cve: str | None = None
    severity: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class WatchStats:
    """Watch feed statistics."""
    source: str
    last_fetch: datetime | None
    item_count: int
    cache_age_minutes: float
    is_stale: bool


def _fetch_json(url: str, timeout: int = 20, headers: dict | None = None) -> Any:
    """Fetch JSON from URL."""
    hdrs = {"User-Agent": "Freya/2.0 CyberWatch"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def _fetch_text(url: str, timeout: int = 20, headers: dict | None = None) -> str:
    """Fetch text from URL."""
    hdrs = {"User-Agent": "Freya/2.0 CyberWatch"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def _cache_path(cache_dir: Path, name: str) -> Path:
    """Get cache file path."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{name}.json"


def _cache_get_json(cache_file: Path, ttl_sec: int) -> Any | None:
    """Get cached JSON if valid."""
    try:
        if not cache_file.exists():
            return None
        age = time.time() - cache_file.stat().st_mtime
        if age > ttl_sec:
            return None
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set_json(cache_file: Path, data: Any) -> None:
    """Set JSON cache."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _cache_get_text(cache_file: Path, ttl_sec: int) -> str | None:
    """Get cached text if valid."""
    try:
        if not cache_file.exists():
            return None
        age = time.time() - cache_file.stat().st_mtime
        if age > ttl_sec:
            return None
        return cache_file.read_text(encoding="utf-8")
    except Exception:
        return None


def _cache_set_text(cache_file: Path, text: str) -> None:
    """Set text cache."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text, encoding="utf-8")


def _extract_cve(text: str) -> str | None:
    """Extract CVE ID from text."""
    match = re.search(r"CVE-\d{4}-\d{4,}", text, re.IGNORECASE)
    return match.group(0).upper() if match else None


# =============================================================================
# CISA KEV (Known Exploited Vulnerabilities)
# =============================================================================
def fetch_cisa_kev(cache_dir: Path, ttl_sec: int = 1800) -> list[WatchItem]:
    """
    Fetch CISA Known Exploited Vulnerabilities.
    
    Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    """
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    cache_file = _cache_path(cache_dir, "cisa_kev")
    
    data = _cache_get_json(cache_file, ttl_sec)
    if data is None:
        data = _fetch_json(url)
        _cache_set_json(cache_file, data)
    
    items: list[WatchItem] = []
    for v in (data.get("vulnerabilities") or [])[:100]:
        cve = v.get("cveID", "")
        vendor = v.get("vendorProject", "")
        product = v.get("product", "")
        title = f"{cve} — {vendor} {product}".strip()
        
        items.append(WatchItem(
            source="CISA-KEV",
            title=title,
            url=f"https://nvd.nist.gov/vuln/detail/{cve}" if cve else "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            published=str(v.get("dateAdded", "")),
            cve=cve,
            severity="CRITICAL",  # All KEV items are actively exploited
            description=v.get("shortDescription", ""),
            tags=["actively-exploited", "kev"]
        ))
    
    return items


# =============================================================================
# CERT-FR (ANSSI)
# =============================================================================
def fetch_certfr_rss(cache_dir: Path, ttl_sec: int = 1800) -> list[WatchItem]:
    """
    Fetch CERT-FR security alerts from ANSSI.
    
    Source: https://www.cert.ssi.gouv.fr/alerte/feed/
    """
    url = "https://www.cert.ssi.gouv.fr/alerte/feed/"
    cache_file = cache_dir / "certfr_alerte.xml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Try cache first
    xml_text = _cache_get_text(cache_file, ttl_sec)
    if xml_text is None:
        try:
            xml_text = _fetch_text(url)
            _cache_set_text(cache_file, xml_text)
        except Exception as e:
            # If fetch fails and we have old cache, use it
            if cache_file.exists():
                xml_text = cache_file.read_text(encoding="utf-8")
            else:
                raise RuntimeError(f"CERT-FR fetch failed: {e}")
    
    items: list[WatchItem] = []
    
    try:
        root = ET.fromstring(xml_text)
        
        # RSS 2.0 format: channel/item
        for item_elem in root.findall("./channel/item")[:50]:
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip()
            description = (item_elem.findtext("description") or "").strip()
            
            # Extract CVE from title or description
            cve = _extract_cve(title) or _extract_cve(description)
            
            if title and link:
                items.append(WatchItem(
                    source="CERT-FR",
                    title=title,
                    url=link,
                    published=pub_date,
                    cve=cve,
                    description=description[:500] if description else None,
                    tags=["anssi", "france"]
                ))
    except ET.ParseError as e:
        raise RuntimeError(f"CERT-FR XML parse error: {e}")
    
    return items


# =============================================================================
# CERT-FR Avis (Advisory, less critical than Alerte)
# =============================================================================
def fetch_certfr_avis(cache_dir: Path, ttl_sec: int = 1800) -> list[WatchItem]:
    """
    Fetch CERT-FR security advisories.
    
    Source: https://www.cert.ssi.gouv.fr/avis/feed/
    """
    url = "https://www.cert.ssi.gouv.fr/avis/feed/"
    cache_file = cache_dir / "certfr_avis.xml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    xml_text = _cache_get_text(cache_file, ttl_sec)
    if xml_text is None:
        try:
            xml_text = _fetch_text(url)
            _cache_set_text(cache_file, xml_text)
        except Exception:
            if cache_file.exists():
                xml_text = cache_file.read_text(encoding="utf-8")
            else:
                return []
    
    items: list[WatchItem] = []
    
    try:
        root = ET.fromstring(xml_text)
        for item_elem in root.findall("./channel/item")[:30]:
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip()
            description = (item_elem.findtext("description") or "").strip()
            cve = _extract_cve(title) or _extract_cve(description)
            
            if title and link:
                items.append(WatchItem(
                    source="CERT-FR-Avis",
                    title=title,
                    url=link,
                    published=pub_date,
                    cve=cve,
                    description=description[:500] if description else None,
                    tags=["anssi", "france", "advisory"]
                ))
    except ET.ParseError:
        pass
    
    return items


# =============================================================================
# NVD Recent CVEs
# =============================================================================
def fetch_nvd_recent(cache_dir: Path, ttl_sec: int = 3600, days: int = 7) -> list[WatchItem]:
    """
    Fetch recent CVEs from NVD.
    
    Note: Rate limited without API key (5 requests per 30 seconds).
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    params = {
        "pubStartDate": start_date.strftime("%Y-%m-%dT00:00:00.000"),
        "pubEndDate": end_date.strftime("%Y-%m-%dT23:59:59.999"),
        "resultsPerPage": "50"
    }
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    cache_file = _cache_path(cache_dir, "nvd_recent")
    
    data = _cache_get_json(cache_file, ttl_sec)
    if data is None:
        try:
            data = _fetch_json(url, timeout=30)
            _cache_set_json(cache_file, data)
        except Exception:
            return []
    
    items: list[WatchItem] = []
    for vuln in data.get("vulnerabilities", [])[:50]:
        cve_data = vuln.get("cve", {})
        cve_id = cve_data.get("id", "")
        
        # Get description
        descriptions = cve_data.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        
        # Get CVSS
        severity = None
        metrics = cve_data.get("metrics", {})
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if key in metrics and metrics[key]:
                cvss = metrics[key][0].get("cvssData", {})
                severity = cvss.get("baseSeverity")
                break
        
        published = cve_data.get("published", "")[:10]
        
        items.append(WatchItem(
            source="NVD",
            title=f"{cve_id}: {description[:100]}..." if len(description) > 100 else f"{cve_id}: {description}",
            url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            published=published,
            cve=cve_id,
            severity=severity,
            description=description[:500] if description else None,
            tags=["nvd", "cve"]
        ))
    
    return items


# =============================================================================
# Exploit-DB
# =============================================================================
def fetch_exploitdb(cache_dir: Path, ttl_sec: int = 3600) -> list[WatchItem]:
    """
    Fetch recent exploits from Exploit-DB RSS.
    """
    url = "https://www.exploit-db.com/rss.xml"
    cache_file = cache_dir / "exploitdb.xml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    xml_text = _cache_get_text(cache_file, ttl_sec)
    if xml_text is None:
        try:
            xml_text = _fetch_text(url)
            _cache_set_text(cache_file, xml_text)
        except Exception:
            return []
    
    items: list[WatchItem] = []
    
    try:
        root = ET.fromstring(xml_text)
        for item_elem in root.findall("./channel/item")[:30]:
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip()
            description = (item_elem.findtext("description") or "").strip()
            cve = _extract_cve(title) or _extract_cve(description)
            
            if title and link:
                items.append(WatchItem(
                    source="Exploit-DB",
                    title=title,
                    url=link,
                    published=pub_date,
                    cve=cve,
                    severity="HIGH",  # Exploits are inherently high risk
                    description=description[:500] if description else None,
                    tags=["exploit", "poc"]
                ))
    except ET.ParseError:
        pass
    
    return items


# =============================================================================
# GitHub Security Advisories
# =============================================================================
def fetch_github_advisories(cache_dir: Path, ttl_sec: int = 1800, token: str = "") -> list[WatchItem]:
    """
    Fetch GitHub Security Advisories.
    
    Uses GitHub API (optional token for higher rate limits).
    """
    url = "https://api.github.com/advisories?per_page=30"
    cache_file = _cache_path(cache_dir, "github_advisories")
    
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    data = _cache_get_json(cache_file, ttl_sec)
    if data is None:
        try:
            data = _fetch_json(url, headers=headers)
            _cache_set_json(cache_file, data)
        except Exception:
            return []
    
    items: list[WatchItem] = []
    for adv in data[:30]:
        ghsa_id = adv.get("ghsa_id", "")
        cve_id = adv.get("cve_id")
        summary = adv.get("summary", "")
        severity = adv.get("severity", "").upper()
        published = adv.get("published_at", "")[:10]
        html_url = adv.get("html_url", "")
        
        items.append(WatchItem(
            source="GitHub-GHSA",
            title=f"{ghsa_id}: {summary[:100]}" if len(summary) > 100 else f"{ghsa_id}: {summary}",
            url=html_url,
            published=published,
            cve=cve_id,
            severity=severity,
            description=adv.get("description", "")[:500],
            tags=["github", "advisory"]
        ))
    
    return items


# =============================================================================
# Packet Storm Security
# =============================================================================
def fetch_packetstorm(cache_dir: Path, ttl_sec: int = 3600) -> list[WatchItem]:
    """
    Fetch from Packet Storm Security RSS.
    """
    url = "https://packetstormsecurity.com/rss/"
    cache_file = cache_dir / "packetstorm.xml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    xml_text = _cache_get_text(cache_file, ttl_sec)
    if xml_text is None:
        try:
            xml_text = _fetch_text(url)
            _cache_set_text(cache_file, xml_text)
        except Exception:
            return []
    
    items: list[WatchItem] = []
    
    try:
        root = ET.fromstring(xml_text)
        for item_elem in root.findall("./channel/item")[:20]:
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip()
            description = (item_elem.findtext("description") or "").strip()
            cve = _extract_cve(title) or _extract_cve(description)
            
            if title and link:
                items.append(WatchItem(
                    source="PacketStorm",
                    title=title,
                    url=link,
                    published=pub_date,
                    cve=cve,
                    description=description[:500] if description else None,
                    tags=["security", "exploit", "research"]
                ))
    except ET.ParseError:
        pass
    
    return items


# =============================================================================
# Threatpost / Security News
# =============================================================================
def fetch_threatpost(cache_dir: Path, ttl_sec: int = 3600) -> list[WatchItem]:
    """
    Fetch security news from Threatpost RSS.
    """
    url = "https://threatpost.com/feed/"
    cache_file = cache_dir / "threatpost.xml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    xml_text = _cache_get_text(cache_file, ttl_sec)
    if xml_text is None:
        try:
            xml_text = _fetch_text(url)
            _cache_set_text(cache_file, xml_text)
        except Exception:
            return []
    
    items: list[WatchItem] = []
    
    try:
        root = ET.fromstring(xml_text)
        for item_elem in root.findall("./channel/item")[:15]:
            title = (item_elem.findtext("title") or "").strip()
            link = (item_elem.findtext("link") or "").strip()
            pub_date = (item_elem.findtext("pubDate") or "").strip()
            description = (item_elem.findtext("description") or "").strip()
            cve = _extract_cve(title) or _extract_cve(description)
            
            if title and link:
                items.append(WatchItem(
                    source="Threatpost",
                    title=title,
                    url=link,
                    published=pub_date,
                    cve=cve,
                    description=description[:500] if description else None,
                    tags=["news", "threat-intel"]
                ))
    except ET.ParseError:
        pass
    
    return items


# =============================================================================
# Combined Cyber Watch
# =============================================================================
def cyber_watch(
    cache_dir: Path,
    sources: list[str] | None = None,
    limit: int = 50
) -> list[WatchItem]:
    """
    Get combined cyber watch feed from all sources.
    
    Args:
        cache_dir: Directory for caching
        sources: List of sources to include (None = all)
        limit: Maximum items to return
    
    Sources: cisa, certfr, nvd, exploitdb, github, packetstorm, threatpost
    """
    all_sources = sources or ["cisa", "certfr", "nvd", "exploitdb", "github"]
    
    items: list[WatchItem] = []
    
    # Priority order
    fetch_funcs = {
        "cisa": lambda: fetch_cisa_kev(cache_dir),
        "certfr": lambda: fetch_certfr_rss(cache_dir),
        "certfr-avis": lambda: fetch_certfr_avis(cache_dir),
        "nvd": lambda: fetch_nvd_recent(cache_dir),
        "exploitdb": lambda: fetch_exploitdb(cache_dir),
        "github": lambda: fetch_github_advisories(cache_dir),
        "packetstorm": lambda: fetch_packetstorm(cache_dir),
        "threatpost": lambda: fetch_threatpost(cache_dir),
    }
    
    for source in all_sources:
        source_key = source.lower()
        if source_key in fetch_funcs:
            try:
                items.extend(fetch_funcs[source_key]())
            except Exception:
                pass  # Skip failed sources
    
    # Sort by severity and date
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, None: 4}
    
    def sort_key(item: WatchItem) -> tuple:
        sev = severity_order.get(item.severity, 4)
        # Parse date for sorting
        try:
            if item.published:
                date_str = item.published[:10]
                return (sev, -time.mktime(time.strptime(date_str, "%Y-%m-%d")))
        except Exception:
            pass
        return (sev, 0)
    
    items.sort(key=sort_key)
    
    return items[:limit]


def get_watch_stats(cache_dir: Path) -> dict[str, WatchStats]:
    """Get statistics for all watch sources."""
    sources = {
        "cisa_kev": "cisa_kev.json",
        "cert_fr_alerte": "certfr_alerte.xml",
        "cert_fr_avis": "certfr_avis.xml",
        "nvd_recent": "nvd_recent.json",
        "exploitdb": "exploitdb.xml",
        "github_advisories": "github_advisories.json",
        "packetstorm": "packetstorm.xml",
        "threatpost": "threatpost.xml",
    }
    
    stats = {}
    
    for name, filename in sources.items():
        cache_file = cache_dir / filename
        if cache_file.exists():
            stat = cache_file.stat()
            age_seconds = time.time() - stat.st_mtime
            age_minutes = age_seconds / 60
            
            # Count items (rough estimate)
            item_count = 0
            try:
                content = cache_file.read_text(encoding="utf-8")
                if filename.endswith(".json"):
                    data = json.loads(content)
                    if isinstance(data, list):
                        item_count = len(data)
                    elif isinstance(data, dict):
                        item_count = len(data.get("vulnerabilities", data.get("items", [])))
                else:
                    item_count = content.count("<item>")
            except Exception:
                pass
            
            stats[name] = WatchStats(
                source=name,
                last_fetch=datetime.fromtimestamp(stat.st_mtime),
                item_count=item_count,
                cache_age_minutes=round(age_minutes, 1),
                is_stale=age_seconds > 1800  # > 30 min
            )
        else:
            stats[name] = WatchStats(
                source=name,
                last_fetch=None,
                item_count=0,
                cache_age_minutes=-1,
                is_stale=True
            )
    
    return stats
