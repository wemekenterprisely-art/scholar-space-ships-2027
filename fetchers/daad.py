"""DAAD German Academic Exchange Service - German government scholarships."""
import re
from ._shared import get, strip_html

URL = "https://www.daad.de/en/studying-in-germany/scholarships/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.daad\.de/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": f"DAAD: {title}",
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "Germany",
                    "level": "Master",
                    "funding": "Fully Funded",
                })

        # Also try the scholarship database
        db_url = "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database"
        try:
            db_html = get(db_url, timeout)
            for m in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</a>', db_html, re.S):
                url = m.group(1)
                title = strip_html(m.group(2))[:200]
                if title and len(title) > 10:
                    if not url.startswith("http"):
                        url = f"https://www2.daad.de{url}"
                    if not any(item["title"] == f"DAAD: {title}" for item in items):
                        items.append({
                            "title": f"DAAD: {title}",
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "Germany",
                            "level": "Master",
                            "funding": "Fully Funded",
                        })
        except Exception:
            pass

    except Exception as e:
        print(f"  [daad] scrape error: {e}")
    return items
