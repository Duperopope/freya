from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str
    source: str


class WebSearch:
    def __init__(self, provider: str, brave_api_key: str, user_agent: str = "Freya/1.0"):
        self.provider = (provider or "wikipedia").lower()
        self.brave_api_key = brave_api_key or ""
        self.user_agent = user_agent or "Freya/1.0"

    def search(self, query: str, *, count: int = 5) -> list[WebResult]:
        q = (query or "").strip()
        if not q:
            return []
        if self.provider == "brave":
            return self._search_brave(q, count=count)
        return self._search_wikipedia(q, count=count)

    def _search_brave(self, query: str, *, count: int) -> list[WebResult]:
        # Brave Search API (requires key)
        # Docs: https://api.search.brave.com/app/documentation/web-search/get-started
        if not self.brave_api_key:
            raise RuntimeError("BRAVE_API_KEY manquant. Mets-le en variable d'environnement.")
        params = urllib.parse.urlencode({"q": query, "count": str(max(1, min(count, 10)))})
        url = f"https://api.search.brave.com/res/v1/web/search?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key,
                "User-Agent": self.user_agent,
            },
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))

        results: list[WebResult] = []
        web = (data.get("web") or {}).get("results") or []
        for it in web[:count]:
            results.append(
                WebResult(
                    title=str(it.get("title") or ""),
                    url=str(it.get("url") or ""),
                    snippet=str(it.get("description") or ""),
                    source="Brave",
                )
            )
        return results

    def _search_wikipedia(self, query: str, *, count: int) -> list[WebResult]:
        # Wikipedia opensearch (free)
        # Docs: https://www.mediawiki.org/wiki/API:Main_page
        params = urllib.parse.urlencode(
            {"action": "opensearch", "search": query, "limit": str(max(1, min(count, 10))), "namespace": "0", "format": "json"}
        )
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        # data = [query, titles[], descs[], links[]]
        titles = data[1] if len(data) > 1 else []
        descs = data[2] if len(data) > 2 else []
        links = data[3] if len(data) > 3 else []
        results: list[WebResult] = []
        for i in range(min(len(titles), count)):
            results.append(
                WebResult(
                    title=str(titles[i]),
                    url=str(links[i]) if i < len(links) else "",
                    snippet=str(descs[i]) if i < len(descs) else "",
                    source="Wikipedia",
                )
            )
        return results
