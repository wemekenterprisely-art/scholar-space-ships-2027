"""facebook_scholarships.py - Fetch scholarship info from Facebook pages via DuckDuckGo."""
import re
from ._shared import get, strip_html

# Facebook scholarship groups and pages (public)
FB_SOURCES = [
    "site:facebook.com scholarship no IELTS 2027",
    "site:facebook.com fully funded scholarship 2027",
    "site:facebook.com PhD scholarship international 2027",
    "site:facebook.com MA scholarship no TOEFL 2027",
    "site:facebook.com academic fellowship 2027",
    "site:facebook.com scholarship Libya 2027",
    "site:facebook.com African scholarship 2027",
    "site:facebook.com Erasmus scholarship 2027",
    "site:facebook.com Chevening scholarship 2027",
    "site:facebook.com Fulbright scholarship 2027",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for query in FB_SOURCES:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            raw = get(url, timeout=20)
            for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
                link = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if not title or not link or link in seen:
                    continue
                if "facebook.com" not in link:
                    continue
                seen.add(link)
                items.append({
                    "title": title,
                    "url": link,
                    "description": f"Facebook scholarship post",
                    "posted_at": "",
                    "source": "facebook"
                })
        except Exception:
            continue
    
    return items
