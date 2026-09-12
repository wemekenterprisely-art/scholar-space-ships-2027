"""opportunitydesk.org RSS feed - high-quality international scholarships."""
from ._shared import get, parse_rss

URL = "https://opportunitydesk.org/feed/"

def fetch(timeout: int = 15) -> list[dict]:
    items = []
    try:
        xml = get(URL, timeout)
        for item in parse_rss(xml):
            title = item.get("title", "")
            if not title or len(title) < 10:
                continue
            items.append({
                "title": title,
                "url": item.get("url", ""),
                "description": item.get("description", "")[:2000],
                "posted_at": item.get("posted_at", ""),
            })
    except Exception as e:
        print(f"  [opportunitydesk] RSS error: {e}")
    return items
