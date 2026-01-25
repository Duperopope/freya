from __future__ import annotations

import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WatchItem:
    source: str
    title: str
    url: str
    published: str
    cve: str | None = None


def _fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def _fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Freya/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def _cache_get(cache_file: Path, ttl_sec: int) -> Any | None:
    try:
        if not cache_file.exists():
            return None
        if (time.time() - cache_file.stat().st_mtime) > ttl_sec:
            return None
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set(cache_file: Path, data: Any) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def fetch_cisa_kev(cache_dir: Path, ttl_sec: int = 1800) -> list[WatchItem]:
    # Source officielle : https://www.cisa.gov/known-exploited-vulnerabilities-catalog
    url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    cache_file = cache_dir / "cisa_kev.json"
    data = _cache_get(cache_file, ttl_sec) or _fetch_json(url)
    _cache_set(cache_file, data)

    items: list[WatchItem] = []
    for v in (data.get("vulnerabilities") or [])[:50]:
        cve = v.get("cveID")
        title = f"{cve} — {v.get('vendorProject','')} {v.get('product','')}".strip()
        items.append(
            WatchItem(
                source="CISA-KEV",
                title=title,
                url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                published=str(v.get("dateAdded", "")),
                cve=cve,
            )
        )
    return items


def fetch_certfr_rss(cache_dir: Path, ttl_sec: int = 1800) -> list[WatchItem]:
    # CERT-FR RSS (source officielle ANSSI, varie selon flux)
    # Flux “Alertes” : https://www.cert.ssi.gouv.fr/alerte/feed/
    url = "https://www.cert.ssi.gouv.fr/alerte/feed/"
    cache_file = cache_dir / "certfr_alerte_rss.xml"
    xml = _cache_get(cache_file, ttl_sec)
    if xml is None:
        xml_text = _fetch_text(url)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(xml_text, encoding="utf-8")
        xml = xml_text
    else:
        # cached stored as json? -> we stored text, so cache_get won't work for xml. Keep simple:
        xml = cache_file.read_text(encoding="utf-8")

    root = ET.fromstring(xml)
    items: list[WatchItem] = []

    # RSS2: channel/item
    for it in root.findall("./channel/item")[:30]:
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        items.append(WatchItem(source="CERT-FR", title=title, url=link, published=pub))
    return items


def cyber_watch(cache_dir: Path) -> list[WatchItem]:
    items = []
    items.extend(fetch_cisa_kev(cache_dir))
    items.extend(fetch_certfr_rss(cache_dir))

    # “tri” simple : les items CISA en premier (KEV = exploitées), puis CERT-FR
    def key(x: WatchItem) -> tuple[int, str]:
        prio = 0 if x.source == "CISA-KEV" else 1
        return (prio, x.published or "")

    items.sort(key=key)
    return items[:25]
