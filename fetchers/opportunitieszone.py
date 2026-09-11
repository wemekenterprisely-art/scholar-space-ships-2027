"""opportunitieszone.com - free scholarship listing site."""
import re
from ._shared import get, strip_html

URL = "https://opportunitieszone.com/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)
        for m in re.finditer(r'<a[^>]+href="(https://opportunitieszone\.com/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if not title or len(title) < 10:
                continue
            if any(x in url for x in ['/tag/', '/category/', '/page/', '/feed/', '/about/', '/contact/', '/privacy']):
                continue
            items.append({"title": title, "url": url, "description": strip_html(title), "posted_at": ""})
    except Exception as e:
        print(f"  [opportunitieszone] scrape error: {e}")
    return items
