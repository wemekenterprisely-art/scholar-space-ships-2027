"""ProFellow - curated fellowship database."""
import re
from ._shared import get, strip_html

URL = "https://www.profellow.com/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract fellowship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.profellow\.com/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["fellowship", "scholarship", "grant", "award", "program"]):
                items.append({
                    "title": title,
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "",
                    "level": "Postgrad",
                    "funding": "Unknown",
                })

        # Look for featured fellowships
        for m in re.finditer(r'<article[^>]*>(.*?)</article>', html, re.S):
            article = m.group(1)
            title_m = re.search(r'<h[23][^>]*>(.*?)</h[23]>', article, re.S)
            link_m = re.search(r'<a[^>]+href="([^"]*)"', article, re.S)
            if title_m and link_m:
                title = strip_html(title_m.group(1))[:200]
                url = link_m.group(1)
                if title and len(title) > 10:
                    if not url.startswith("http"):
                        url = f"https://www.profellow.com{url}"
                    if not any(item["url"] == url for item in items):
                        items.append({
                            "title": title,
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "",
                            "level": "Postgrad",
                            "funding": "Unknown",
                        })
    except Exception as e:
        print(f"  [profellow] scrape error: {e}")
    return items
