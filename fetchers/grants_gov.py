"""Simpler Grants API - US federal grants and scholarships."""
import json, urllib.request
from ._shared import UA

# Simpler Grants API - modern endpoint
SEARCH_URL = "https://api.simpler.grants.gov/v1/opportunities/search"

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        payload = json.dumps({
            "query": "scholarship",
            "status": "open",
            "limit": 50,
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

        opportunities = data.get("opportunities", data.get("data", []))
        for opp in opportunities:
            title = opp.get("title", opp.get("opportunityTitle", ""))
            if not title:
                continue
            opp_id = opp.get("id", opp.get("opportunityId", ""))
            url = f"https://www.grants.gov/search-results-detail/{opp_id}" if opp_id else ""
            desc = opp.get("description", opp.get("summary", ""))[:2000]
            deadline = opp.get("closeDate", opp.get("applicationDeadline", ""))
            items.append({
                "title": title,
                "url": url,
                "description": desc,
                "posted_at": opp.get("openDate", opp.get("postedDate", "")),
                "deadline": deadline,
                "country": "USA",
                "funding": opp.get("awardAmount", "Unknown"),
                "field": "General",
            })
    except Exception as e:
        print(f"  [grants-gov] API error: {e}")
    return items
