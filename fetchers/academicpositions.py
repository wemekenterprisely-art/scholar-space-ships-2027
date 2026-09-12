"""AcademicPositions - academic job and PhD listings."""
import re
from ._shared import get, strip_html

URL = "https://www.academicpositions.com/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract job/PhD listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.academicpositions\.com/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10 and any(w in title.lower() for w in ["phd", "postdoc", "fellowship", "research", "position"]):
                items.append({
                    "title": title,
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "",
                    "level": "PhD",
                    "funding": "Unknown",
                })

        # Look for featured positions
        for m in re.finditer(r'<div[^>]*class="[^"]*position[^"]*"[^>]*>(.*?)</div>', html, re.S):
            card = m.group(1)
            title_m = re.search(r'<h[23][^>]*>(.*?)</h[23]>', card, re.S)
            link_m = re.search(r'<a[^>]+href="([^"]*)"', card, re.S)
            if title_m and link_m:
                title = strip_html(title_m.group(1))[:200]
                url = link_m.group(1)
                if title and len(title) > 10:
                    if not url.startswith("http"):
                        url = f"https://www.academicpositions.com{url}"
                    if not any(item["url"] == url for item in items):
                        items.append({
                            "title": title,
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "",
                            "level": "PhD",
                            "funding": "Unknown",
                        })
    except Exception as e:
        print(f"  [academicpositions] scrape error: {e}")
    return items
