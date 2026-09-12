"""UNESCO Fellowships - international fellowship programs."""
import re
from ._shared import get, strip_html

URL = "https://www.unesco.org/en/scholarships"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract fellowship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.unesco\.org/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["fellowship", "scholarship", "grant", "award", "program"]):
                items.append({
                    "title": f"UNESCO: {title}",
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "International",
                    "level": "Postgrad",
                    "funding": "Fully Funded",
                })

        # Look for specific programs
        for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html, re.S):
            title = strip_html(m.group(1))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["fellowship", "program", "award"]):
                link_m = re.search(r'<a[^>]+href="([^"]*)"[^>]*>', html[m.end():m.end()+1000])
                url = f"https://www.unesco.org{link_m.group(1)}" if link_m and link_m.group(1).startswith("/") else (link_m.group(1) if link_m else "")
                if url and not any(item["url"] == url for item in items):
                    items.append({
                        "title": f"UNESCO: {title}",
                        "url": url,
                        "description": title,
                        "posted_at": "",
                        "country": "International",
                        "level": "Postgrad",
                        "funding": "Fully Funded",
                    })
    except Exception as e:
        print(f"  [unesco] scrape error: {e}")
    return items
