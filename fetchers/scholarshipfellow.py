"""scholarshipfellow.com RSS."""
from ._shared import get, parse_rss, strip_html

FEED = "https://scholarshipfellow.com/feed/"

def fetch(timeout: int = 20) -> list[dict]:
    xml = get(FEED, timeout)
    items = parse_rss(xml)
    for it in items:
        it["description"] = strip_html(it.get("description", ""))
    return items
