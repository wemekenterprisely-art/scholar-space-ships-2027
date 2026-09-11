"""global_search.py - Deep global scholarship search across 7 continents.

This module performs a comprehensive search of scholarships worldwide,
organizing results by continent > country > university hierarchy.
"""
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from ._shared import get, strip_html

DATA_DIR = Path(__file__).parent.parent / "data"
UNIVERSITIES_FILE = DATA_DIR / "global_universities.json"

# Scholarship search queries organized by field
SEARCH_QUERIES = {
    "applied_linguistics": [
        "scholarship applied linguistics no IELTS fully funded",
        "PhD scholarship linguistics no TOEFL international students",
        "MA scholarship English language teaching no English test",
        "doctoral fellowship corpus linguistics fully funded",
        "research grant discourse analysis no language requirement",
    ],
    "esl_education": [
        "scholarship ESL teaching no IELTS fully funded",
        "MA scholarship TESOL no English test international",
        "PhD fellowship language education no TOEFL",
        "teaching grant English as second language fully funded",
        "research scholarship EFL education no language certificate",
    ],
    "translation_studies": [
        "scholarship translation studies no IELTS fully funded",
        "MA translation Arabic English no English test",
        "PhD fellowship translation no TOEFL international",
        "interpretation scholarship fully funded no language requirement",
        "bilingual scholarship translation no English certificate",
    ],
    "academic_writing": [
        "scholarship academic writing no IELTS fully funded",
        "research grant academic discourse no English test",
        "PhD fellowship scholarly communication no TOEFL",
        "writing center scholarship fully funded international",
        "academic literacy research no language requirement",
    ],
    "education_general": [
        "scholarship education no IELTS fully funded",
        "MA education no TOEFL international students",
        "PhD education fully funded no English test",
        "teaching scholarship no language requirement",
        "educational research grant no IELTS",
    ],
    "linguistics_general": [
        "scholarship linguistics no IELTS fully funded",
        "MA linguistics no TOEFL international",
        "PhD linguistics fully funded no English test",
        "language research scholarship no IELTS",
        "computational linguistics grant no language requirement",
    ],
}


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
    uni_website = university.get("website", "")
    
    # Use only the most targeted query per university to avoid rate limiting
    # Pick the best query based on the university's country/region
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
    
    continents = db["continents"]
    start_time = time.time()
    total_universities = 0
    total_countries = 0
    
    for i, (continent_name, continent_data) in enumerate(continents.items()):
        if i >= max_continents:
            break
        
        # Rotate through different field queries for each continent
        field_queries = list(SEARCH_QUERIES.values())[i % len(SEARCH_QUERIES)]
        
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
