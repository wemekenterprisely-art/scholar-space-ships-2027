"""Google News RSS - renewable scholarship listing source."""
from ._shared import get, parse_rss, strip_html

QUERIES = [
    "scholarship+no+ielts+fully+funded+international",
    "scholarship+no+toefl+libyan+students",
    "scholarship+fully+funded+applied+linguistics",
]

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    seen = set()
    for q in QUERIES:
        url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
        try:
            raw = get(url, timeout)
            for it in parse_rss(raw):
                t = it.get("title", "")
                u = it.get("url", "")
                if "search?q=" in u or t.startswith('"') or t.endswith("Google News"):
                    continue
                if t in seen:
                    continue
                seen.add(t)
                it["description"] = strip_html(it.get("description", ""))
                items.append(it)
        except Exception:
            continue
    return items