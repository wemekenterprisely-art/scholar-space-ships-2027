"""scholarship-positions.com - use Google News RSS as fallback (main site has Cloudflare)."""
import re
from ._shared import get, strip_html

QUERIES = [
    "site:scholarship-positions.com scholarship 2026",
    "site:scholarship-positions.com fully funded international",
]

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    seen = set()
    for q in QUERIES:
        url = f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"
        try:
            raw = get(url, timeout)
            for chunk in re.split(r"</item>|</entry>", raw):
                if "<item" not in chunk and "<entry" not in chunk:
                    continue
                t_m = re.search(r"<title[^>]*>(.*?)</title>", chunk, re.S)
                l_m = re.search(r"<link[^>]*>(.*?)</link>", chunk, re.S) or re.search(r'<link[^>]*href="([^"]*)"', chunk)
                if not t_m or not l_m:
                    continue
                title = re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", t_m.group(1)).strip()
                link = l_m.group(1).strip()
                if not title or not link or link in seen:
                    continue
                seen.add(link)
                items.append({"title": title, "url": link, "description": strip_html(title), "posted_at": ""})
        except Exception:
            continue
    return items
