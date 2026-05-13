"""
web_search_utils.py
===================
Wikipedia lookup + real-time web search using free APIs:
  - Wikipedia: wikipedia-api (free, no key)
  - DuckDuckGo: duckduckgo-search (free, no key)
  - SerpAPI: optional API key for Google results
  - NewsAPI: optional key for news
  - Nominatim for geolocation (free)

Limit tracking included.
"""
from __future__ import annotations
import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import json

# ─── Usage state ─────────────────────────────────────────────────────────────
def init_search_state():
    if "search_usage" not in st.session_state:
        st.session_state.search_usage = {
            "wikipedia": {"calls": 0, "errors": 0},
            "ddg": {"calls": 0, "errors": 0},
            "news": {"calls": 0, "errors": 0},
            "geo": {"calls": 0, "errors": 0},
        }
    if "search_cache" not in st.session_state:
        st.session_state.search_cache = {}


# ═══════════════════════════════════════════════════════════════════════
# WIKIPEDIA
# ═══════════════════════════════════════════════════════════════════════
def wikipedia_search(query: str, sentences: int = 5, language: str = "en") -> dict:
    """
    Search Wikipedia. Returns:
    { "title": str, "summary": str, "url": str, "image": str, "sections": [], "error": None }
    """
    init_search_state()
    cache_key = f"wiki_{query}_{language}"
    if cache_key in st.session_state.search_cache:
        return st.session_state.search_cache[cache_key]

    try:
        # Search for pages
        search_url = f"https://{language}.wikipedia.org/w/api.php"
        params = {
            "action": "query", "list": "search", "srsearch": query,
            "format": "json", "srlimit": 5,
        }
        resp = requests.get(search_url, params=params, timeout=10)
        resp.raise_for_status()
        search_data = resp.json()
        results = search_data.get("query", {}).get("search", [])

        if not results:
            return {"title": "", "summary": "No results found.", "url": "", "image": "", "sections": [], "error": None}

        top_title = results[0]["title"]

        # Get summary via REST API
        summary_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(top_title)}"
        sresp = requests.get(summary_url, timeout=10)
        sresp.raise_for_status()
        sdata = sresp.json()

        result = {
            "title": sdata.get("title", top_title),
            "summary": sdata.get("extract", ""),
            "url": sdata.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "image": sdata.get("thumbnail", {}).get("source", ""),
            "description": sdata.get("description", ""),
            "all_results": [{"title": r["title"], "snippet": r.get("snippet", "")} for r in results],
            "error": None,
        }
        st.session_state.search_cache[cache_key] = result
        st.session_state.search_usage["wikipedia"]["calls"] += 1
        return result

    except Exception as e:
        st.session_state.search_usage["wikipedia"]["errors"] += 1
        return {"title": "", "summary": "", "url": "", "image": "", "sections": [], "error": str(e)}


def wikipedia_get_full_article(title: str, language: str = "en") -> dict:
    """Get full article sections."""
    try:
        url = f"https://{language}.wikipedia.org/w/api.php"
        params = {
            "action": "query", "prop": "extracts|info",
            "titles": title, "explaintext": True, "format": "json",
            "inprop": "url",
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = list(pages.values())[0] if pages else {}
        return {
            "title": page.get("title", title),
            "content": page.get("extract", ""),
            "url": page.get("fullurl", ""),
            "error": None,
        }
    except Exception as e:
        return {"title": title, "content": "", "url": "", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# DUCKDUCKGO WEB SEARCH (free, no API key)
# ═══════════════════════════════════════════════════════════════════════
def ddg_search(query: str, max_results: int = 8, region: str = "wt-wt") -> dict:
    """
    DuckDuckGo web search. Returns:
    { "results": [{"title", "url", "snippet"}], "error": None }
    """
    init_search_state()
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=region, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        st.session_state.search_usage["ddg"]["calls"] += 1
        return {"results": results, "error": None}
    except ImportError:
        return {"results": [], "error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}
    except Exception as e:
        st.session_state.search_usage["ddg"]["errors"] += 1
        return {"results": [], "error": str(e)}


def ddg_news(query: str, max_results: int = 8) -> dict:
    """DuckDuckGo news search."""
    init_search_state()
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "image": r.get("image", ""),
                })
        st.session_state.search_usage["news"]["calls"] += 1
        return {"results": results, "error": None}
    except ImportError:
        return {"results": [], "error": "duckduckgo-search not installed."}
    except Exception as e:
        st.session_state.search_usage["news"]["errors"] += 1
        return {"results": [], "error": str(e)}


def ddg_images(query: str, max_results: int = 6) -> dict:
    """DuckDuckGo image search."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.images(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "image_url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", ""),
                    "source_url": r.get("url", ""),
                    "width": r.get("width", 0),
                    "height": r.get("height", 0),
                })
        return {"results": results, "error": None}
    except Exception as e:
        return {"results": [], "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# NEWS API (optional key — falls back to DDG)
# ═══════════════════════════════════════════════════════════════════════
def fetch_news(query: str, api_key: Optional[str] = None, max_results: int = 10) -> dict:
    """Fetch news. Uses NewsAPI if key provided, else DuckDuckGo."""
    if api_key:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {"q": query, "pageSize": max_results, "sortBy": "publishedAt", "apiKey": api_key}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            articles = data.get("articles", [])
            return {
                "results": [{"title": a["title"], "url": a["url"], "snippet": a.get("description", ""),
                             "source": a.get("source", {}).get("name", ""), "date": a.get("publishedAt", ""),
                             "image": a.get("urlToImage", "")} for a in articles],
                "total": data.get("totalResults", 0),
                "error": None,
            }
        except Exception as e:
            pass  # Fall through to DDG
    return ddg_news(query, max_results)


# ═══════════════════════════════════════════════════════════════════════
# REALTIME DATA — exchange rates, crypto, weather
# ═══════════════════════════════════════════════════════════════════════
def get_exchange_rates(base: str = "USD") -> dict:
    """Free exchange rates via exchangerate-api.com (no key needed for basic)."""
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "base": base,
            "rates": data.get("rates", {}),
            "time_last_update": data.get("time_last_update_utc", ""),
            "error": None,
        }
    except Exception as e:
        return {"base": base, "rates": {}, "error": str(e)}


def get_crypto_prices(coins: list = None) -> dict:
    """Free crypto prices via CoinGecko (no key, 10-50 req/min)."""
    if coins is None:
        coins = ["bitcoin", "ethereum", "dogecoin", "solana", "cardano"]
    try:
        ids = ",".join(coins)
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ids, "vs_currencies": "usd,eur", "include_24hr_change": "true"},
            timeout=10,
        )
        r.raise_for_status()
        return {"prices": r.json(), "error": None}
    except Exception as e:
        return {"prices": {}, "error": str(e)}


def get_ip_info(ip: str = "") -> dict:
    """Free IP geolocation via ipapi.co (no key, ~1000 req/day)."""
    try:
        url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        return {**r.json(), "error": None}
    except Exception as e:
        return {"error": str(e)}


def get_search_usage() -> dict:
    init_search_state()
    return st.session_state.search_usage.copy()