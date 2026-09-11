"""global_search.py - Deep global scholarship search using DuckDuckGo.

Uses DuckDuckGo HTML search (no rate limiting) instead of Google News RSS.
Searches broad field + region queries to find scholarships across all continents.
"""
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from ._shared import get, strip_html

DATA_DIR = Path(__file__).parent.parent / "data"
UNIVERSITIES_FILE = DATA_DIR / "global_universities.json"

# Broad search queries covering all fields and regions
SEARCH_QUERIES = [
    # Applied Linguistics - Global
    "scholarship applied linguistics no IELTS fully funded 2027",
    "PhD fellowship linguistics no TOEFL international students 2027",
    "MA scholarship English language teaching no English test 2027",
    # ESL/EFL - Global
    "scholarship ESL TESOL no IELTS fully funded 2027",
    "PhD fellowship language education no TOEFL 2027",
    # Translation - Global
    "scholarship translation studies Arabic English no IELTS 2027",
    "MA translation no English test fully funded 2027",
    # Academic Writing - Global
    "scholarship academic writing discourse analysis no IELTS 2027",
    "research grant academic communication no TOEFL 2027",
    # Education - Global
    "scholarship education no IELTS fully funded international 2027",
    "PhD education no English test developing countries 2027",
    # General Linguistics - Global
    "scholarship linguistics no IELTS fully funded 2027",
    "computational linguistics fellowship no TOEFL 2027",
    # Regional - Africa
    "scholarship Libya students no IELTS fully funded 2027",
    "African students scholarship no English test 2027",
    "Nigerian scholarship no IELTS fully funded 2027",
    "Egyptian scholarship no TOEFL international 2027",
    "South Africa scholarship no IELTS 2027",
    # Regional - Middle East
    "Middle East scholarship fully funded no IELTS 2027",
    "Turkish scholarship no English test 2027",
    "Jordanian scholarship no IELTS international 2027",
    # Regional - Asia
    "Japanese scholarship MEXT no IELTS 2027",
    "Chinese scholarship CSC no TOEFL 2027",
    "Indian scholarship no IELTS fully funded 2027",
    "Malaysian scholarship no English test 2027",
    "Thai scholarship no IELTS international 2027",
    # Regional - Europe
    "German scholarship DAAD no IELTS 2027",
    "UK scholarship no TOEFL fully funded 2027",
    "Hungarian scholarship Stipendium no IELTS 2027",
    "Swedish scholarship no TOEFL 2027",
    "Norwegian scholarship no IELTS international 2027",
    "Finnish scholarship no English test 2027",
    "Polish scholarship no IELTS 2027",
    "Italian scholarship no TOEFL 2027",
    "French scholarship no IELTS international 2027",
    "Spanish scholarship no English test 2027",
    # Regional - Americas
    "Canadian scholarship no IELTS international 2027",
    "Australian scholarship no IELTS 2027",
    "New Zealand scholarship no TOEFL 2027",
    "Mexican scholarship no IELTS 2027",
    "Brazilian scholarship no English test 2027",
    "Argentinian scholarship no IELTS 2027",
    "Colombian scholarship no TOEFL 2027",
]


def search_duckduckgo(query: str) -> list[dict]:
    """Search DuckDuckGo HTML for scholarships."""
    items = []
    seen = set()
    encoded_query = query.replace(" ", "+")
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    try:
        raw = get(url, timeout=20)
        # Extract results from DuckDuckGo HTML
        for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', raw, re.S):
            link = match.group(1)
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            if not title or not link or link in seen:
                continue
            # Skip DuckDuckGo internal links
            if "duckduckgo.com" in link:
                continue
            seen.add(link)
            items.append({
                "title": title,
                "url": link,
                "description": f"Found via global search: {query[:50]}",
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
    """Search for scholarships at a specific university using DuckDuckGo."""
    items = []
    seen = set()
    uni_name = university.get("name", "")
    
    # Use only the most targeted query per university
    best_query = field_queries[0] if field_queries else "scholarship no IELTS fully funded"
    search_query = f"{best_query} {uni_name}"
    
    try:
        raw_items = search_duckduckgo(search_query)
        for item in raw_items:
            if item["url"] not in seen:
                seen.add(item["url"])
                item["university"] = uni_name
                item["country"] = country
                items.append(item)
    except Exception:
        pass
    
    return items


def search_country_scholarships(country_data: dict, country_name: str, field_queries: list[str]) -> list[dict]:
    """Search for scholarships across all universities in a country."""
    items = []
    universities = country_data.get("universities", [])
    
    for uni in universities:  # Search ALL universities
        uni_items = search_university_scholarships(uni, country_name, field_queries)
        items.extend(uni_items)
        time.sleep(0.5)  # Rate limiting between universities
    
    return items


def search_continent_scholarships(continent_data: dict, continent_name: str, field_queries: list[str]) -> list[dict]:
    """Search for scholarships across all countries in a continent."""
    items = []
    countries = continent_data.get("countries", {})
    
    for country_name, country_data in countries.items():  # Search ALL countries
        country_items = search_country_scholarships(country_data, country_name, field_queries)
        items.extend(country_items)
        time.sleep(1)  # Rate limiting between countries
    
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
    
    # Phase 1: Broad field-level searches (fast, ~2 minutes)
    print("\n  Phase 1: Broad field-level searches...")
    for query in SEARCH_QUERIES:
        items = search_duckduckgo(query)
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
        time.sleep(0.5)  # Rate limiting between queries
    
    print(f"    Found {len(all_items)} items from field-level searches")
    
    # Phase 2: Deep university-level searches
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
        
        # Check if we've exceeded the time limit (30 minutes for Phase 2)
        elapsed = time.time() - start_time
        if elapsed > 1800:  # 30 minutes
            print(f"  [global_search] Phase 2 time limit reached ({elapsed:.0f}s)")
            break
        
        time.sleep(1)  # Rate limiting between continents
    
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
