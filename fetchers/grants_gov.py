"""Grants.gov API - US federal grants and scholarships."""
import json, urllib.request
from ._shared import UA

SEARCH_URL = "https://grants.gov/api/common/search2"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        payload = json.dumps({
            "keyword": "scholarship",
            "oppStatus": "open",
            "rows": 50,
            "sortBy": "openDate",
            "sortOrder": "desc",
        }).encode()
        req = urllib.request.Request(
            SEARCH_URL,
            data=payload,
            headers={
                "User-Agent": UA,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())

        opportunities = data.get("oppHits", [])
        for opp in opportunities:
            title = opp.get("title", "")
            if not title:
                continue
            opp_id = opp.get("id", "")
            url = f"https://www.grants.gov/search-results-detail/{opp_id}" if opp_id else ""
            desc = opp.get("description", "")[:2000]
            deadline = opp.get("closeDate", "")
            items.append({
                "title": title,
                "url": url,
                "description": desc,
                "posted_at": opp.get("openDate", ""),
                "deadline": deadline,
                "country": "USA",
                "funding": opp.get("awardAmount", "Unknown"),
                "field": "General",
            })
    except Exception as e:
        print(f"  [grants-gov] API error: {e}")
    return items
