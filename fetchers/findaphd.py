"""findaphd.com scraper - PhD positions with JSON-LD structured data."""
import re, json
from ._shared import get, strip_html

SEARCH_URL = "https://www.findaphd.com/search/Phds.aspx"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(SEARCH_URL, timeout)

        # Extract JSON-LD structured data
        for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
            try:
                data = json.loads(m.group(1))
                if isinstance(data, list):
                    for item in data:
                        _process_jsonld(item, items)
                elif isinstance(data, dict):
                    _process_jsonld(data, items)
            except json.JSONDecodeError:
                continue

        # Fallback: extract from HTML cards
        if not items:
            for m in re.finditer(r'<a[^>]+href="(https://www\.findaphd\.com/[^"]*\.aspx)"[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</a>', html, re.S):
                url = m.group(1)
                title = strip_html(m.group(2))[:200]
                if title and len(title) > 10:
                    items.append({
                        "title": title,
                        "url": url,
                        "description": title,
                        "posted_at": "",
                        "country": "UK",
                        "level": "PhD",
                    })
    except Exception as e:
        print(f"  [findaphd] scrape error: {e}")
    return items


def _process_jsonld(data: dict, items: list):
    """Extract scholarship from JSON-LD EducationalOccupationalProgram."""
    if data.get("@type") not in ("EducationalOccupationalProgram", "College"):
        if "@graph" in data:
            for item in data["@graph"]:
                _process_jsonld(item, items)
        return

    title = data.get("name", "")
    if not title:
        return

    url = data.get("url", "")
    desc = data.get("description", "")[:2000]
    deadline = data.get("applicationDeadline", "")
    provider = data.get("provider", {})
    if isinstance(provider, dict):
        provider = provider.get("name", "")

    items.append({
        "title": f"{title} - {provider}" if provider else title,
        "url": url,
        "description": desc,
        "posted_at": "",
        "deadline": deadline,
        "country": "UK",
        "level": "PhD",
        "funding": "Unknown",
    })
