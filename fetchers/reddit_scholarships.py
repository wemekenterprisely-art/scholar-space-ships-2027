"""reddit_scholarships.py - Fetch scholarships from Reddit via DuckDuckGo."""
import re
from ._shared import get, strip_html

# Reddit scholarship posts via DuckDuckGo (avoids Reddit API blocking)
REDDIT_QUERIES = [
    "site:reddit.com scholarship no IELTS fully funded 2027",
    "site:reddit.com PhD funding international 2027",
    "site:reddit.com MA scholarship no TOEFL 2027",
    "site:reddit.com scholarship for African students",
    "site:reddit.com scholarship for Libyan students",
    "site:reddit.com fully funded masters scholarship",
    "site:reddit.com grad school funding no IELTS",
    "site:reddit.com Erasmus scholarship reddit",
    "site:reddit.com Chevening scholarship reddit",
    "site:reddit.com Fulbright scholarship reddit",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for query in REDDIT_QUERIES:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            raw = get(url, timeout=20)
            for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
                link = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if not title or not link or link in seen:
                    continue
                if "reddit.com" not in link:
                    continue
                seen.add(link)
                items.append({
                    "title": title,
                    "url": link,
                    "description": f"Reddit scholarship post",
                    "posted_at": "",
                    "source": "reddit"
                })
        except Exception:
            continue
    
    return items
