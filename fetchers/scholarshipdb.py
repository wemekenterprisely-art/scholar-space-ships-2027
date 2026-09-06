"""scholarshipdb.net public JSON index - no API key required."""
from ._shared import get_json, strip_html

API = "https://scholarshipdb.net/api/scholarships.json"

def fetch(timeout: int = 30) -> list[dict]:
    data = get_json(API, timeout)
    if not isinstance(data, list):
        return []
    out = []
    for row in data:
        if not isinstance(row, dict):
            continue
        title = row.get("title") or row.get("name") or ""
        if not title:
            continue
        out.append({
            "title": title,
            "description": strip_html(row.get("description") or row.get("summary") or ""),
            "url": row.get("url") or row.get("link") or row.get("scholarship_url") or "",
            "country": row.get("country") or row.get("host_country") or "",
            "deadline": row.get("deadline") or row.get("application_deadline") or "",
            "funding": row.get("funding") or row.get("funding_type") or "Unknown",
            "level": row.get("level") or row.get("degree_level") or "",
        })
    return out
