"""opportunitiescorners.com - scrape individual scholarship pages for details."""
import re, time
from ._shared import get, strip_html, parse_date

BASE = "https://opportunitiescorners.com/"

def _extract_detail(html: str) -> dict:
    """Extract country, funding, level, deadline from individual page."""
    info = {"country": "", "funding": "", "level": "", "deadline": ""}
    text = strip_html(html, 5000).lower()

    # Country detection
    countries = ["usa", "united states", "uk", "united kingdom", "canada", "australia",
                 "germany", "france", "netherlands", "japan", "china", "korea",
                 "turkey", "malaysia", "singapore", "india", "italy", "spain",
                 "sweden", "norway", "denmark", "finland", "new zealand",
                 "south africa", "nigeria", "kenya", "ghana", "egypt",
                 "uae", "saudi arabia", "qatar", "kuwait", "bahrain",
                 "open", "worldwide", "global", "international", "any country"]
    for c in countries:
        if c in text:
            info["country"] = c.title()
            break

    # Funding detection
    if any(x in text for x in ["fully funded", "full funding", "100% funded", "tuition + stipend"]):
        info["funding"] = "Fully Funded"
    elif any(x in text for x in ["partial", "partial funding", "50% funded"]):
        info["funding"] = "Partially Funded"
    elif any(x in text for x in ["tuition waiver", "tuition only"]):
        info["funding"] = "Tuition Waiver"
    elif any(x in text for x in ["stipend", "monthly allowance"]):
        info["funding"] = "With Stipend"

    # Level detection
    if any(x in text for x in ["phd", "doctoral", "doctorate"]):
        info["level"] = "PhD"
    elif any(x in text for x in ["master", "ma", "msc", "mba", "graduate"]):
        info["level"] = "Master"
    elif any(x in text for x in ["bachelor", "undergraduate", "degree"]):
        info["level"] = "Bachelor"
    elif any(x in text for x in ["postdoc", "post-doctoral"]):
        info["level"] = "Postdoc"

    # Deadline detection
    dl_match = re.search(r"deadline[:\s]*([\w\s,./-]+?)(?:\.|$|\n)", text)
    if dl_match:
        info["deadline"] = dl_match.group(1).strip()[:50]
    else:
        date_match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text)
        if date_match:
            info["deadline"] = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"

    return info

def _extract_university(title: str, desc: str) -> str:
    """Try to extract university name from title or description."""
    combined = f"{title} {desc}"
    # Common patterns
    patterns = [
        r"at\s+([\w\s]+(?:University|Institute|College|School))",
        r"([\w\s]+(?:University|Institute|College|School))\s+(?:offers?|announces?|scholarship)",
        r"(?:University|Institute|College)\s+of\s+([\w\s]+)",
    ]
    for p in patterns:
        m = re.search(p, combined, re.I)
        if m:
            return m.group(1).strip()[:100]
    return ""

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(BASE, timeout)
        links = []
        for m in re.finditer(r'<a[^>]+href="(https://opportunitiescorners\.com/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if not title or len(title) < 10:
                continue
            if any(x in url for x in ['/tag/', '/category/', '/page/', '/feed/', '/about/', '/contact/', '/privacy']):
                continue
            links.append((url, title))

        # Scrape top 30 pages for details
        for url, title in links[:30]:
            try:
                detail_html = get(url, timeout=10)
                detail = _extract_detail(detail_html)
                university = _extract_university(title, strip_html(detail_html, 1000))
                desc = strip_html(detail_html, 500)

                items.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "university": university,
                    "country": detail["country"],
                    "funding": detail["funding"] or "Unknown",
                    "level": detail["level"] or "Unknown",
                    "deadline": detail["deadline"],
                    "posted_at": "",
                })
                time.sleep(0.3)  # Be polite
            except Exception:
                items.append({
                    "title": title,
                    "url": url,
                    "description": strip_html(title),
                    "posted_at": "",
                })
    except Exception as e:
        print(f"  [opportunitiescorners] scrape error: {e}")
    return items
