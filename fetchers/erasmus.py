"""Erasmus+ EU scholarship listings - major international program."""
import re
from ._shared import get, strip_html

URL = "https://erasmus-plus.ec.europa.eu/opportunities"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship cards
        for m in re.finditer(r'<a[^>]+href="(https://erasmus-plus\.ec\.europa\.eu/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "EU",
                    "level": "Master",
                    "funding": "Fully Funded",
                })

        # Also look for opportunity cards
        for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html, re.S):
            title = strip_html(m.group(1))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["scholarship", "grant", "fellowship", "master", "phd"]):
                # Find the nearest link
                link_m = re.search(r'<a[^>]+href="([^"]*)"[^>]*>', html[m.end():m.end()+500])
                url = f"https://erasmus-plus.ec.europa.eu{link_m.group(1)}" if link_m and link_m.group(1).startswith("/") else (link_m.group(1) if link_m else "")
                if url and not any(item["url"] == url for item in items):
                    items.append({
                        "title": title,
                        "url": url,
                        "description": title,
                        "posted_at": "",
                        "country": "EU",
                        "level": "Master",
                        "funding": "Fully Funded",
                    })
    except Exception as e:
        print(f"  [erasmus] scrape error: {e}")
    return items
