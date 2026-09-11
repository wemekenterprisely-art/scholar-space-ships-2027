"""twitter_scholarships.py - Fetch scholarship info from Twitter/X via DuckDuckGo."""
import re
from ._shared import get, strip_html

# Twitter/X scholarship posts
TWITTER_SOURCES = [
    "site:twitter.com scholarship no IELTS 2027",
    "site:x.com scholarship no IELTS 2027",
    "site:twitter.com fully funded scholarship 2027",
    "site:x.com fully funded scholarship 2027",
    "site:twitter.com PhD scholarship international 2027",
    "site:x.com PhD scholarship international 2027",
    "site:twitter.com MA scholarship no TOEFL 2027",
    "site:x.com academic fellowship 2027",
    "site:twitter.com Erasmus scholarship 2027",
    "site:x.com Chevening scholarship 2027",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for query in TWITTER_SOURCES:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            raw = get(url, timeout=20)
            for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
                link = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if not title or not link or link in seen:
                    continue
                if "twitter.com" not in link and "x.com" not in link:
                    continue
                seen.add(link)
                items.append({
                    "title": title,
                    "url": link,
                    "description": f"Twitter/X scholarship post",
                    "posted_at": "",
                    "source": "twitter"
                })
        except Exception:
            continue
    
    return items
