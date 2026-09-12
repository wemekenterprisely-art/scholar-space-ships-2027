"""LinkedIn guest endpoint - scholarship/fellowship listings without login."""
import re, time, random
from ._shared import strip_html

# LinkedIn guest API for job search
LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

# Use a realistic browser User-Agent
LINKEDIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

QUERIES = [
    "scholarship international students",
    "graduate fellowship funded",
    "masters scholarship 2027",
    "PhD funding international",
]

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    seen_urls = set()

    for query in QUERIES:
        try:
            import urllib.request
            url = f"{LINKEDIN_SEARCH_URL}?keywords={query.replace(' ', '+')}&start=0&sortBy=DD"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": LINKEDIN_UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "identity",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8", "replace")

            # Extract job cards from HTML
            for m in re.finditer(r'<li[^>]*>(.*?)</li>', html, re.S):
                card = m.group(1)

                # Extract title
                title_m = re.search(r'<h3[^>]*>(.*?)</h3>', card, re.S)
                title = strip_html(title_m.group(1)) if title_m else ""
                if not title:
                    continue

                # Extract URL
                link_m = re.search(r'<a[^>]+href="([^"]*)"', card, re.S)
                item_url = link_m.group(1).split("?")[0] if link_m else ""
                if not item_url or item_url in seen_urls:
                    continue
                seen_urls.add(item_url)

                # Extract company/organization
                company_m = re.search(r'<h4[^>]*>(.*?)</h4>', card, re.S)
                company = strip_html(company_m.group(1)) if company_m else ""

                # Extract location
                loc_m = re.search(r'<span[^>]*>(.*?)</span>', card, re.S)
                location = strip_html(loc_m.group(1)) if loc_m else ""

                full_title = f"{title} - {company}" if company else title
                items.append({
                    "title": full_title,
                    "url": item_url,
                    "description": f"{title} at {company} in {location}".strip(" -"),
                    "posted_at": "",
                    "country": _extract_country(location),
                    "level": _extract_level(title),
                    "funding": "Unknown",
                })

            # Rate limit between queries
            time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            print(f"  [linkedin] query error ({query}): {e}")

    return items


def _extract_country(location: str) -> str:
    """Extract country from LinkedIn location string."""
    loc = location.lower()
    mapping = {
        "united states": "USA", "usa": "USA", "california": "USA", "new york": "USA",
        "united kingdom": "UK", "london": "UK", "england": "UK",
        "canada": "Canada", "toronto": "Canada",
        "australia": "Australia", "sydney": "Australia",
        "germany": "Germany", "berlin": "Germany",
        "france": "France", "paris": "France",
        "netherlands": "Netherlands", "amsterdam": "Netherlands",
        "japan": "Japan", "tokyo": "Japan",
        "singapore": "Singapore",
        "uae": "UAE", "dubai": "UAE",
    }
    for keyword, country in mapping.items():
        if keyword in loc:
            return country
    return ""


def _extract_level(title: str) -> str:
    """Extract level from title."""
    t = title.lower()
    if any(w in t for w in ["phd", "doctoral", "doctorate"]):
        return "PhD"
    if any(w in t for w in ["master", "msc", "ma", "mba"]):
        return "Master"
    if any(w in t for w in ["bachelor", "undergraduate", "bsc", "ba"]):
        return "Bachelor"
    return ""
