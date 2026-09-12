"""Grants.gov API - US federal grants and scholarships."""
import json, urllib.request
from ._shared import UA

# Grants.gov uses a different search endpoint
SEARCH_URL = "https://www.grants.gov/api/v1/opportunities/search"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        # Try the newer API endpoint
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

        # Handle different response formats
        opportunities = data.get("oppHits", data.get("opportunities", []))
        if not opportunities and isinstance(data, list):
            opportunities = data

        for opp in opportunities:
            title = opp.get("title", opp.get("oppTitle", ""))
            if not title:
                continue
            opp_id = opp.get("id", opp.get("oppId", ""))
            url = f"https://www.grants.gov/search-results-detail/{opp_id}" if opp_id else ""
            desc = opp.get("description", opp.get("synopsis", ""))[:2000]
            deadline = opp.get("closeDate", opp.get("closeDt", ""))
            items.append({
                "title": title,
                "url": url,
                "description": desc,
                "posted_at": opp.get("openDate", opp.get("openDt", "")),
                "deadline": deadline,
                "country": "USA",
                "funding": opp.get("awardAmount", "Unknown"),
                "field": "General",
            })
    except Exception as e:
        print(f"  [grants-gov] API error: {e}")
    return items
