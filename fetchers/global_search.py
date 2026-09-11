"""global_search.py - Deep global scholarship search using broad field queries.

Instead of searching each university individually (rate-limited by Google News),
this performs broad field-specific searches that cover ALL regions globally.
"""
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from ._shared import get, strip_html

DATA_DIR = Path(__file__).parent.parent / "data"
UNIVERSITIES_FILE = DATA_DIR / "global_universities.json"

# Broad field-level search queries (not university-specific)
# These are designed to find scholarships across ALL universities globally
SEARCH_QUERIES = [
    # Applied Linguistics
    "scholarship applied linguistics no IELTS fully funded 2027",
    "PhD fellowship linguistics no TOEFL international students 2027",
    "MA scholarship English language teaching no English test 2027",
    # ESL/EFL
    "scholarship ESL TESOL no IELTS fully funded 2027",
    "PhD fellowship language education no TOEFL 2027",
    # Translation
    "scholarship translation studies Arabic English no IELTS 2027",
    "MA translation no English test fully funded 2027",
    # Academic Writing
    "scholarship academic writing discourse analysis no IELTS 2027",
    "research grant academic communication no TOEFL 2027",
    # Education
    "scholarship education no IELTS fully funded international 2027",
    "PhD education no English test developing countries 2027",
    # General Linguistics
    "scholarship linguistics no IELTS fully funded 2027",
    "computational linguistics fellowship no TOEFL 2027",
    # Regional searches
    "scholarship Libya students no IELTS fully funded 2027",
    "African students scholarship no English test 2027",
    "Middle East scholarship fully funded no IELTS 2027",
    "European scholarship no TOEFL international 2027",
    "Asian scholarship no IELTS fully funded 2027",
    "Turkish scholarship no English test 2027",
    "Japanese scholarship MEXT no IELTS 2027",
    "Chinese scholarship CSC no TOEFL 2027",
    "German scholarship DAAD no IELTS 2027",
    "UK scholarship no TOEFL fully funded 2027",
    "Australian scholarship no IELTS international 2027",
    "Canadian scholarship no English test 2027",
]


def search_google_news(query: str) -> list[dict]:
    """Search Google News RSS for a specific query."""
    items = []
    seen = set()
    url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
    
    try:
        raw = get(url, timeout=20)
        for chunk in re.split(r"</item>|</entry>", raw):
            if "<item" not in chunk and "<entry" not in chunk:
                continue
            t_m = re.search(r"<title[^>]*>(.*?)</title>", chunk, re.S)
            l_m = re.search(r"<link[^>]*>(.*?)</link>", chunk, re.S) or re.search(r'<link[^>]*href="([^"]*)"', chunk)
            if not t_m or not l_m:
                continue
            title = re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", t_m.group(1)).strip()
            link = l_m.group(1).strip()
            if not title or not link or link in seen:
                continue
            seen.add(link)
            items.append({
                "title": title,
                "url": link,
                "description": f"Found via global field search: {query[:50]}",
                "posted_at": "",
                "source": "global-search"
            })
    except Exception:
        pass
    
    return items


def load_universities() -> dict:
    """Load the global university database."""
    try:
        return json.loads(UNIVERSITIES_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [global_search] Error loading universities: {e}")
        return {}


def search_university_scholarships(university: dict, country: str, field_queries: list[str]) -> list[dict]:
    """Search for scholarships at a specific university using Google News RSS."""
    items = []
    seen = set()
    uni_name = university.get("name", "")
    
    # Use only the most targeted query per university to avoid rate limiting
    best_query = field_queries[0] if field_queries else "scholarship no IELTS fully funded"
    search_query = f"{best_query} {uni_name}"
    url = f"https://news.google.com/rss/search?q={search_query}&hl=en&gl=US&ceid=US:en"
    
    try:
        raw = get(url, timeout=20)
        for chunk in re.split(r"</item>|</entry>", raw):
            if "<item" not in chunk and "<entry" not in chunk:
                continue
            t_m = re.search(r"<title[^>]*>(.*?)</title>", chunk, re.S)
            l_m = re.search(r"<link[^>]*>(.*?)</link>", chunk, re.S) or re.search(r'<link[^>]*href="([^"]*)"', chunk)
            if not t_m or not l_m:
                continue
            title = re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", t_m.group(1)).strip()
            link = l_m.group(1).strip()
            if not title or not link or link in seen:
                continue
            seen.add(link)
            items.append({
                "title": title,
                "url": link,
                "description": f"Found via global search at {uni_name}, {country}",
                "posted_at": "",
                "university": uni_name,
                "country": country,
                "source": "global-search"
            })
    except Exception:
        pass
    
    return items


def search_country_scholarships(country_data: dict, country_name: str, field_queries: list[str]) -> list[dict]:
    """Search for scholarships across all universities in a country."""
    items = []
    universities = country_data.get("universities", [])
    
    for uni in universities:  # Search ALL universities in the country
        uni_items = search_university_scholarships(uni, country_name, field_queries)
        items.extend(uni_items)
        time.sleep(0.3)  # Minimal rate limiting between universities
    
    return items


def search_continent_scholarships(continent_data: dict, continent_name: str, field_queries: list[str]) -> list[dict]:
    """Search for scholarships across all countries in a continent."""
    items = []
    countries = continent_data.get("countries", {})
    
    for country_name, country_data in countries.items():  # Search ALL countries in the continent
        country_items = search_country_scholarships(country_data, country_name, field_queries)
        items.extend(country_items)
        time.sleep(0.5)  # Minimal rate limiting between countries
    
    return items


def deep_global_search(max_continents: int = 7) -> list[dict]:
    """Perform a deep global search across ALL continents, countries, and universities."""
    print("=== Starting Deep Global Scholarship Search ===")
    print(f"  Searching ALL continents, countries, and universities")
    
    all_items = []
    seen_urls = set()
    db = load_universities()
    
    if not db or "continents" not in db:
        print("  [global_search] No university database found")
        return []
    
    # Phase 1: Broad field-level searches (fast, ~5 minutes)
    print("\n  Phase 1: Broad field-level searches...")
    for query in SEARCH_QUERIES:
        items = search_google_news(query)
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
        time.sleep(1)  # Rate limiting between queries
    
    print(f"    Found {len(all_items)} items from field-level searches")
    
    # Phase 2: Deep university-level searches (slow, ~2 hours)
    print("\n  Phase 2: Deep university-level searches...")
    continents = db["continents"]
    start_time = time.time()
    total_universities = 0
    total_countries = 0
    
    for i, (continent_name, continent_data) in enumerate(continents.items()):
        if i >= max_continents:
            break
        
        # Rotate through different field queries for each continent
        field_queries = SEARCH_QUERIES[i % len(SEARCH_QUERIES):i % len(SEARCH_QUERIES) + 3]
        
        print(f"\n  Searching {continent_data.get('name', continent_name)}...")
        continent_items = search_continent_scholarships(continent_data, continent_name, field_queries)
        
        # Count universities and countries in this continent
        countries_in_continent = continent_data.get("countries", {})
        unis_in_continent = sum(len(c.get("universities", [])) for c in countries_in_continent.values())
        total_countries += len(countries_in_continent)
        total_universities += unis_in_continent
        
        # Deduplicate by URL
        for item in continent_items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
        
        print(f"    Found {len(continent_items)} items ({len(seen_urls)} unique total)")
        print(f"    Searched {len(countries_in_continent)} countries, {unis_in_continent} universities")
        
        # Check if we've exceeded the time limit (1.5 hours)
        elapsed = time.time() - start_time
        if elapsed > 5400:  # 1.5 hours
            print(f"  [global_search] Time limit reached ({elapsed:.0f}s)")
            break
        
        time.sleep(1)  # Minimal rate limiting between continents
    
    elapsed = time.time() - start_time
    print(f"\n=== Global Search Complete ===")
    print(f"  Continents searched: {min(i+1, max_continents)}")
    print(f"  Countries searched: {total_countries}")
    print(f"  Universities searched: {total_universities}")
    print(f"  Total items: {len(all_items)}")
    print(f"  Unique URLs: {len(seen_urls)}")
    print(f"  Time elapsed: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    
    return all_items


def fetch(max_continents: int = 7) -> list[dict]:
    """Main fetch function for the global search fetcher."""
    return deep_global_search(max_continents)
