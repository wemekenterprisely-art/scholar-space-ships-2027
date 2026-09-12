"""MEXT Japan - Japanese government scholarships."""
import re
from ._shared import get, strip_html

URL = "https://www.studyinjapan.go.jp/en/smap-stopj-applications-scholarship.html"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.studyinjapan\.go\.jp/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": f"MEXT Japan: {title}",
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "Japan",
                    "level": "Master",
                    "funding": "Fully Funded",
                })

        # Also check the main MEXT page
        mext_url = "https://www.mext.go.jp/en/policy/education/highered/title02/detail02/1373897.htm"
        try:
            mext_html = get(mext_url, timeout)
            for m in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', mext_html, re.S):
                url = m.group(1)
                title = strip_html(m.group(2))[:200]
                if title and len(title) > 10 and any(w in title.lower() for w in ["scholarship", "fellowship", "program"]):
                    if not url.startswith("http"):
                        url = f"https://www.mext.go.jp{url}"
                    if not any(item["url"] == url for item in items):
                        items.append({
                            "title": f"MEXT Japan: {title}",
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "Japan",
                            "level": "Master",
                            "funding": "Fully Funded",
                        })
        except Exception:
            pass

    except Exception as e:
        print(f"  [mext] scrape error: {e}")
    return items
