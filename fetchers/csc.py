"""CSC China Scholarship Council - Chinese government scholarships."""
import re
from ._shared import get, strip_html

URL = "https://www.campuschina.org/en/"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(URL, timeout)

        # Extract scholarship listings
        for m in re.finditer(r'<a[^>]+href="(https?://www\.campuschina\.org/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url = m.group(1)
            title = strip_html(m.group(2))[:200]
            if title and len(title) > 10:
                items.append({
                    "title": f"CSC China: {title}",
                    "url": url,
                    "description": title,
                    "posted_at": "",
                    "country": "China",
                    "level": "Master",
                    "funding": "Fully Funded",
                })

        # Also check the main CSC page
        csc_url = "https://www.csc.edu.cn/studyinchina"
        try:
            csc_html = get(csc_url, timeout)
            for m in re.finditer(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', csc_html, re.S):
                url = m.group(1)
                title = strip_html(m.group(2))[:200]
                if title and len(title) > 10 and any(w in title.lower() for w in ["scholarship", "fellowship", "program"]):
                    if not url.startswith("http"):
                        url = f"https://www.csc.edu.cn{url}"
                    if not any(item["url"] == url for item in items):
                        items.append({
                            "title": f"CSC China: {title}",
                            "url": url,
                            "description": title,
                            "posted_at": "",
                            "country": "China",
                            "level": "Master",
                            "funding": "Fully Funded",
                        })
        except Exception:
            pass

    except Exception as e:
        print(f"  [csc] scrape error: {e}")
    return items
