# src/freya/tools/websearch.py
"""
Web Search Module for Freya

Provides free web search capabilities using multiple providers:
- DuckDuckGo (primary - no API key required, no rate limits)
- SearXNG (self-hosted meta-search)
- Wikipedia (fallback)
- Brave (optional - requires API key)
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any
from html import unescape


@dataclass
class WebResult:
    """Search result."""
    title: str
    url: str
    snippet: str
    source: str


class WebSearch:
    """
    Web search client supporting multiple free providers.
    
    Providers:
    - "duckduckgo": DuckDuckGo HTML scraping (no API, unlimited)
    - "searxng": SearXNG instance (self-hosted)
    - "wikipedia": Wikipedia API (limited to Wikipedia content)
    - "brave": Brave Search API (requires key)
    """
    
    def __init__(
        self,
        provider: str = "duckduckgo",
        brave_api_key: str = "",
        searxng_url: str = "",
        user_agent: str = "Freya/2.0"
    ):
        self.provider = (provider or "duckduckgo").lower()
        self.brave_api_key = brave_api_key or ""
        self.searxng_url = searxng_url or ""
        self.user_agent = user_agent or "Freya/2.0"
    
    def search(self, query: str, *, count: int = 5) -> list[WebResult]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            count: Number of results (max varies by provider)
        
        Returns:
            List of search results
        """
        q = (query or "").strip()
        if not q:
            return []
        
        # Try providers in order of preference
        if self.provider == "duckduckgo":
            return self._search_duckduckgo(q, count=count)
        elif self.provider == "searxng" and self.searxng_url:
            return self._search_searxng(q, count=count)
        elif self.provider == "brave" and self.brave_api_key:
            return self._search_brave(q, count=count)
        elif self.provider == "wikipedia":
            return self._search_wikipedia(q, count=count)
        else:
            # Default to DuckDuckGo
            return self._search_duckduckgo(q, count=count)
    
    def _search_duckduckgo(self, query: str, *, count: int) -> list[WebResult]:
        """
        DuckDuckGo search using HTML API (no API key required).
        
        Uses the DuckDuckGo HTML endpoint which doesn't require authentication.
        """
        # DuckDuckGo HTML lite version for scraping
        params = urllib.parse.urlencode({
            "q": query,
            "kl": "wt-wt",  # Region: worldwide
            "kp": "-1",      # Safe search off
        })
        url = f"https://html.duckduckgo.com/html/?{params}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode("utf-8", errors="ignore")
        except Exception:
            # Fallback to Wikipedia if DuckDuckGo fails
            return self._search_wikipedia(query, count=count)
        
        results: list[WebResult] = []
        
        # Parse DuckDuckGo HTML results
        # Results are in <div class="result"> blocks
        result_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>([^<]*(?:<[^>]+>[^<]*)*)</a>',
            re.DOTALL
        )
        
        for match in result_pattern.finditer(html):
            if len(results) >= count:
                break
            
            raw_url = match.group(1)
            title = unescape(match.group(2)).strip()
            snippet = unescape(re.sub(r'<[^>]+>', '', match.group(3))).strip()
            
            # DuckDuckGo wraps URLs, extract actual URL
            if "uddg=" in raw_url:
                url_match = re.search(r'uddg=([^&]+)', raw_url)
                if url_match:
                    actual_url = urllib.parse.unquote(url_match.group(1))
                else:
                    actual_url = raw_url
            else:
                actual_url = raw_url
            
            if title and actual_url:
                results.append(WebResult(
                    title=title,
                    url=actual_url,
                    snippet=snippet or "",
                    source="DuckDuckGo"
                ))
        
        # If no results from HTML parsing, try DuckDuckGo Instant Answer API
        if not results:
            return self._search_duckduckgo_instant(query, count=count)
        
        return results
    
    def _search_duckduckgo_instant(self, query: str, *, count: int) -> list[WebResult]:
        """
        DuckDuckGo Instant Answer API (free, limited to instant answers).
        """
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        })
        url = f"https://api.duckduckgo.com/?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            return self._search_wikipedia(query, count=count)
        
        results: list[WebResult] = []
        
        # Abstract (main result)
        if data.get("Abstract"):
            results.append(WebResult(
                title=data.get("Heading", query),
                url=data.get("AbstractURL", ""),
                snippet=data.get("Abstract", ""),
                source="DuckDuckGo"
            ))
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:count-1]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(WebResult(
                    title=topic.get("Text", "")[:100],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                    source="DuckDuckGo"
                ))
        
        return results[:count]
    
    def _search_searxng(self, query: str, *, count: int) -> list[WebResult]:
        """
        SearXNG meta-search (self-hosted or public instance).
        """
        if not self.searxng_url:
            return self._search_duckduckgo(query, count=count)
        
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "engines": "google,duckduckgo,bing",
        })
        url = f"{self.searxng_url.rstrip('/')}/search?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            return self._search_duckduckgo(query, count=count)
        
        results: list[WebResult] = []
        for item in data.get("results", [])[:count]:
            results.append(WebResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source=f"SearXNG ({item.get('engine', 'unknown')})"
            ))
        
        return results
    
    def _search_brave(self, query: str, *, count: int) -> list[WebResult]:
        """
        Brave Search API (requires API key).
        """
        if not self.brave_api_key:
            return self._search_duckduckgo(query, count=count)
        
        params = urllib.parse.urlencode({
            "q": query,
            "count": str(max(1, min(count, 10)))
        })
        url = f"https://api.search.brave.com/res/v1/web/search?{params}"
        
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key,
                "User-Agent": self.user_agent,
            },
        )
        
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            return self._search_duckduckgo(query, count=count)
        
        results: list[WebResult] = []
        for item in (data.get("web") or {}).get("results", [])[:count]:
            results.append(WebResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                source="Brave"
            ))
        
        return results
    
    def _search_wikipedia(self, query: str, *, count: int) -> list[WebResult]:
        """
        Wikipedia opensearch API (always free, limited to Wikipedia).
        """
        params = urllib.parse.urlencode({
            "action": "opensearch",
            "search": query,
            "limit": str(max(1, min(count, 10))),
            "namespace": "0",
            "format": "json"
        })
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
        except Exception:
            return []
        
        # data = [query, titles[], descriptions[], links[]]
        titles = data[1] if len(data) > 1 else []
        descs = data[2] if len(data) > 2 else []
        links = data[3] if len(data) > 3 else []
        
        results: list[WebResult] = []
        for i in range(min(len(titles), count)):
            results.append(WebResult(
                title=str(titles[i]),
                url=str(links[i]) if i < len(links) else "",
                snippet=str(descs[i]) if i < len(descs) else "",
                source="Wikipedia"
            ))
        
        return results


# Convenience function
def web_search(
    query: str,
    *,
    count: int = 5,
    provider: str = "duckduckgo"
) -> list[WebResult]:
    """
    Quick web search function.
    
    Args:
        query: Search query
        count: Number of results
        provider: Search provider (duckduckgo, wikipedia, etc.)
    
    Returns:
        List of search results
    """
    searcher = WebSearch(provider=provider)
    return searcher.search(query, count=count)
