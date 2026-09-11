"""quora_scholarships.py - Fetch scholarship info from Quora via DuckDuckGo."""
import re
from ._shared import get, strip_html

# Quora scholarship questions and answers
QUORA_SOURCES = [
    "site:quora.com scholarship no IELTS 2027",
    "site:quora.com fully funded scholarship 2027",
    "site:quora.com PhD funding international 2027",
    "site:quora.com MA scholarship no TOEFL 2027",
    "site:quora.com how to get scholarship 2027",
    "site:quora.com best scholarships 2027",
    "site:quora.com scholarship for Libyan students",
    "site:quora.com African students scholarship",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for query in QUORA_SOURCES:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        try:
            raw = get(url, timeout=20)
            for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
                link = match.group(1)
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if not title or not link or link in seen:
                    continue
                if "quora.com" not in link:
                    continue
                seen.add(link)
                items.append({
                    "title": title,
                    "url": link,
                    "description": f"Quora scholarship answer",
                    "posted_at": "",
                    "source": "quora"
                })
        except Exception:
            continue
    
    return items
