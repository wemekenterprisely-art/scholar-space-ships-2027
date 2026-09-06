"""Fetcher registry - tier-aware scholarship sources with circuit breaker."""
import hashlib, time
from . import scholars4dev, scholarship_positions, google_news, duckduckgo_search

REGISTRY = {
    "scholars4dev":       {"tier": 1, "fn": scholars4dev.fetch},
    "scholarship-positions": {"tier": 1, "fn": scholarship_positions.fetch},
    "google-news":        {"tier": 1, "fn": google_news.fetch},
    "web-search":         {"tier": 2, "fn": duckduckgo_search.fetch},
}

_COOLDOWN = {}

def _circuit_open(name: str) -> bool:
    opened, fails = _COOLDOWN.get(name, (0.0, 0))
    return fails >= 3 and (time.time() - opened) < 600

def _mark(name: str, ok: bool):
    _, fails = _COOLDOWN.get(name, (0.0, 0))
    _COOLDOWN[name] = (0.0, 0) if ok else (time.time(), fails + 1)

def fetch_source(name: str, tier_cap: int = 0) -> list[dict]:
    """Fetch one source; returns list of raw scholarship dicts."""
    if name not in REGISTRY:
        return []
    info = REGISTRY[name]
    if tier_cap and info["tier"] > tier_cap:
        return []
    if _circuit_open(name):
        print(f"  [{name}] circuit open - skipping")
        return []
    try:
        items = info["fn"]()
        _mark(name, True)
        return items
    except Exception as e:
        _mark(name, False)
        print(f"  [{name}] ERROR: {e}")
        return []

def fetch_all(tier_cap: int = 0, names: list[str] | None = None) -> dict[str, list[dict]]:
    out = {}
    for name in (names or list(REGISTRY)):
        out[name] = fetch_source(name, tier_cap)
    return out

def normalize(raw: dict, source: str) -> dict:
    """Normalize a raw record into the canonical scholarship dict."""
    title = str(raw.get("title") or "").strip()
    desc = str(raw.get("description") or "").strip()
    url = str(raw.get("url") or raw.get("link") or "").strip()
    country = str(raw.get("country") or raw.get("host") or "")
    deadline = str(raw.get("deadline") or "").strip()
    funding = (raw.get("funding") or "").strip() or "Unknown"
    level = (raw.get("level") or "").strip() or "Unknown"
    key = hashlib.sha1(f"{source}|{url or title}".encode()).hexdigest()[:12]
    return {
        "id": key, "title": title, "source": source, "url": url, "description": desc[:2000],
        "country": country, "deadline": deadline, "funding": funding, "level": level,
        "field": raw.get("field", ""), "posted_at": raw.get("posted_at", ""),
        "keywords": raw.get("keywords", []), "all_tags": raw.get("tags", []),
    }