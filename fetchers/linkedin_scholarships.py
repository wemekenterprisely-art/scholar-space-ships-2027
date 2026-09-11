"""linkedin_scholarships.py - Fetch scholarship info from LinkedIn via DuckDuckGo."""
import re
from ._shared import get, strip_html

# LinkedIn scholarship posts and articles
LINKEDIN_SOURCES = [
    "site:linkedin.com scholarship no IELTS 2027",
    "site:linkedin.com fully funded scholarship 2027",
    "site:linkedin.com PhD funding international 2027",
    "site:linkedin.com MA scholarship no TOEFL 2027",
    "site:linkedin.com academic fellowship 2027",
    "site:linkedin.com scholarship announcement 2027",
    "site:linkedin.com research funding 2027",
    "site:linkedin.com graduate scholarship 2027",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for query in LINKEDIN_SOURCES:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            raw = get(url, timeout=20)
            for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
                link = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if not title or not link or link in seen:
                    continue
                if "linkedin.com" not in link:
                    continue
                seen.add(link)
                items.append({
                    "title": title,
                    "url": link,
                    "description": f"LinkedIn scholarship post",
                    "posted_at": "",
                    "source": "linkedin"
                })
        except Exception:
            continue
    
    return items
