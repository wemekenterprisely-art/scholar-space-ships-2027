"""reddit_scholarships.py - Fetch scholarships from Reddit."""
import re
from ._shared import get, strip_html

SUBREDDITS = [
    "scholarships",
    "gradadmissions",
    "AskAcademia",
    "InternationalStudents",
    "ApplyingToCollege",
    "GradSchool",
    "Funding",
    "FindMeFunding",
]

QUERIES = [
    "scholarship no IELTS",
    "fully funded scholarship",
    "PhD funding international",
    "MA scholarship no TOEFL",
    "academic fellowship",
    "research funding",
]


def fetch() -> list[dict]:
    items = []
    seen = set()
    
    for sub in SUBREDDITS:
        for query in QUERIES[:2]:  # Limit queries per subreddit
            url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&sort=new&t=month&limit=25"
            try:
                data = get(url, timeout=15)
                import json
                posts = json.loads(data).get("data", {}).get("children", [])
                for post in posts:
                    d = post.get("data", {})
                    title = d.get("title", "").strip()
                    link = f"https://reddit.com{d.get('permalink', '')}"
                    desc = strip_html(d.get("selftext", "")[:500])
                    if not title or not link or link in seen:
                        continue
                    seen.add(link)
                    items.append({
                        "title": title,
                        "url": link,
                        "description": desc or f"Reddit post from r/{sub}",
                        "posted_at": d.get("created_utc", ""),
                        "source": "reddit"
                    })
            except Exception:
                continue
    
    return items
