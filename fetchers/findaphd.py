"""findaphd.com scraper - PhD positions."""
import re
from ._shared import strip_html

# Try the main page instead of search
SEARCH_URL = "https://www.findaphd.com/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        import urllib.request
        req = urllib.request.Request(
            SEARCH_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", "replace")

        # Extract PhD listings from HTML
        # Look for links to PhD pages
        for m in re.finditer(r'<a[^>]+href="(https://www\.findaphd\.com/[^"]*phd[^"]*)"[^>]*>(.*?)</a>', html, re.S | re.I):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "UK",
                    "level": "PhD",
                })

        # Also try to find featured PhDs
        for m in re.finditer(r'<a[^>]+href="(https://www\.findaphd\.com/[^"]*\.aspx)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10 and ("phd" in title.lower() or "doctoral" in title.lower()):
                if not any(item["url"] == url for item in items):
                    items.append({
                        "title": title,
                        "url": url,
                        "description": title,
                        "posted_at": "",
                        "country": "UK",
                        "level": "PhD",
                    })
    except Exception as e:
        print(f"  [findaphd] scrape error: {e}")
    return items
