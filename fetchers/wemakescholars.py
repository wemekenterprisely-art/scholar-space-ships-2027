"""WeMakeScholars - comprehensive scholarship database."""
import re
from ._shared import get, strip_html

URL = "https://www.wemakescholars.com/scholarship"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship cards
        for m in re.finditer(r'<a[^>]+href="(https?://www\.wemakescholars\.com/scholarship/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "",
                    "level": "",
                    "funding": "Unknown",
                })

        # Also look for scholarship listings
        for m in re.finditer(r'<div[^>]*class="[^"]*scholarship[^"]*"[^>]*>(.*?)</div>', html, re.S):
            card = m.group(1)
            title_m = re.search(r'<h[23][^>]*>(.*?)</h[23]>', card, re.S)
            link_m = re.search(r'<a[^>]+href="([^"]*)"', card, re.S)
            if title_m and link_m:
                title = strip_html(title_m.group(1))[:200]
                url = link_m.group(1)
                if title and len(title) > 10 and not url.startswith("#"):
                    if not url.startswith("http"):
                        url = f"https://www.wemakescholars.com{url}"
                    if not any(item["url"] == url for item in items):
                        items.append({
                            "title": title,
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "",
                            "level": "",
                            "funding": "Unknown",
                        })
    except Exception as e:
        print(f"  [wemakescholars] scrape error: {e}")
    return items
