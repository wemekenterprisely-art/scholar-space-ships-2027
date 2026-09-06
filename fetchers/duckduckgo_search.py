"""Free web search for scholarships - DuckDuckGo HTML (no key).
Queries are built from the profile: IELTS-free + Libya + MA + field terms."""
import re
from urllib.parse import quote
from ._shared import get, strip_html

QUERIES = [
    'scholarship "no IELTS" "fully funded" international students MA',
    'scholarship "without IELTS" "no TOEFL" Libya students master',
    'scholarship Libyan students "no English test" fully funded',
    'scholarship applied linguistics "no IELTS" PhD fully funded',
    'scholarship Arab League Libyan students fully funded no English requirement',
    'scholarship "medium of instruction" certificate no IELTS masters',
]

def fetch(timeout: int = 25) -> list[dict]:
    items = []
    seen = set()
    for q in QUERIES:
        url = "https://html.duckduckgo.com/html/?q=" + quote(q)
        try:
            html = get(url, timeout)
        except Exception:
            continue
        for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if "duckduckgo.com" in href and "uddg=" in href:
                import urllib.parse as up
                href = up.parse_qs(up.urlparse(href).query).get("uddg", [""])[0]
            if not href or href in seen:
                continue
            seen.add(href)
            items.append({"title": title, "url": href, "description": "Found via free web search", "posted_at": ""})
    return items
