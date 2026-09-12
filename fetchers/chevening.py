"""Chevening UK government scholarships - fully funded master's."""
import re
from ._shared import get, strip_html

URL = "https://www.chevening.org/scholarships/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.chevening\.org/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": f"Chevening: {title}",
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "UK",
                    "level": "Master",
                    "funding": "Fully Funded",
                })

        # Look for country-specific scholarships
        for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html, re.S):
            title = strip_html(m.group(1))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["scholarship", "award", "fellowship"]):
                link_m = re.search(r'<a[^>]+href="([^"]*)"[^>]*>', html[m.end():m.end()+1000])
                url = f"https://www.chevening.org{link_m.group(1)}" if link_m and link_m.group(1).startswith("/") else (link_m.group(1) if link_m else "")
                if url and not any(item["url"] == url for item in items):
                    items.append({
                        "title": f"Chevening: {title}",
                        "url": url,
                        "description": title,
                        "posted_at": "",
                        "country": "UK",
                        "level": "Master",
                        "funding": "Fully Funded",
                    })
    except Exception as e:
        print(f"  [chevening] scrape error: {e}")
    return items
