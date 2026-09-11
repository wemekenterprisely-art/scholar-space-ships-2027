"""scholarshiproar.com - scrape individual scholarship pages for details."""
import re, time
from ._shared import get, strip_html

BASE = "https://scholarshiproar.com/"

def _extract_detail(html: str) -> dict:
    info = {"country": "", "funding": "", "level": "", "deadline": ""}
    text = strip_html(html, 5000).lower()

    countries = ["usa", "united states", "uk", "united kingdom", "canada", "australia",
                 "germany", "france", "netherlands", "japan", "china", "korea",
                 "turkey", "malaysia", "singapore", "india", "italy", "spain",
                 "sweden", "norway", "denmark", "finland", "new zealand",
                 "open", "worldwide", "global", "international"]
    for c in countries:
        if c in text:
            info["country"] = c.title()
            break

    if any(x in text for x in ["fully funded", "full funding", "100% funded"]):
        info["funding"] = "Fully Funded"
    elif any(x in text for x in ["partial", "partial funding"]):
        info["funding"] = "Partially Funded"
    elif any(x in text for x in ["tuition waiver"]):
        info["funding"] = "Tuition Waiver"

    if any(x in text for x in ["phd", "doctoral"]):
        info["level"] = "PhD"
    elif any(x in text for x in ["master", "ma", "msc", "mba"]):
        info["level"] = "Master"
    elif any(x in text for x in ["bachelor", "undergraduate"]):
        info["level"] = "Bachelor"

    dl_match = re.search(r"deadline[:\s]*([\w\s,./-]+?)(?:\.|$|\n)", text)
    if dl_match:
        info["deadline"] = dl_match.group(1).strip()[:50]

    return info

def fetch(timeout: int = 20) -> list[dict]:
    items = []
    try:
        html = get(BASE, timeout)
        links = []
        for m in re.finditer(r'<a[^>]+href="(https://scholarshiproar\.com/[^"]*)"[^>]*>(.*?)</a>', html, re.S):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if not title or len(title) < 10:
                continue
            if any(x in url for x in ['/tag/', '/category/', '/page/', '/feed/', '/about/', '/contact/', '/privacy']):
                continue
            links.append((url, title))

        for url, title in links[:25]:
            try:
                detail_html = get(url, timeout=10)
                detail = _extract_detail(detail_html)
                desc = strip_html(detail_html, 500)
                items.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "country": detail["country"],
                    "funding": detail["funding"] or "Unknown",
                    "level": detail["level"] or "Unknown",
                    "deadline": detail["deadline"],
                    "posted_at": "",
                })
                time.sleep(0.3)
            except Exception:
                items.append({"title": title, "url": url, "description": strip_html(title), "posted_at": ""})
    except Exception as e:
        print(f"  [scholarshiproar] scrape error: {e}")
    return items
