"""
Structured Data Extractor - extracts scholarship information from web pages.
Uses regex patterns and heuristics to extract structured data.
"""
import re
from datetime import datetime


# Date patterns
DATE_PATTERNS = [
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(20\d{2})",
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})",
    r"(\d{1,2})/(\d{1,2})/(20\d{2})",
    r"(\d{4})-(\d{2})-(\d{2})",
    r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})",
]

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Country patterns
COUNTRY_PATTERNS = {
    "USA": [r"united states", r"usa", r"america", r"california", r"new york"],
    "UK": [r"united kingdom", r"uk", r"britain", r"england", r"london"],
    "Canada": [r"canada", r"toronto", r"vancouver"],
    "Australia": [r"australia", r"sydney", r"melbourne"],
    "Germany": [r"germany", r"berlin", r"munich"],
    "France": [r"france", r"paris"],
    "Netherlands": [r"netherlands", r"amsterdam", r"holland"],
    "Japan": [r"japan", r"tokyo"],
    "China": [r"china", r"beijing", r"shanghai"],
    "Singapore": [r"singapore"],
    "UAE": [r"uae", r"dubai", r"abu dhabi"],
    "Malaysia": [r"malaysia", r"kuala lumpur"],
    "Turkey": [r"turkey", r"turkiye", r"istanbul"],
    "Italy": [r"italy", r"rome", r"milan"],
    "Spain": [r"spain", r"madrid", r"barcelona"],
    "Sweden": [r"sweden", r"stockholm"],
    "Norway": [r"norway", r"oslo"],
    "Denmark": [r"denmark", r"copenhagen"],
    "Finland": [r"finland", r"helsinki"],
    "New Zealand": [r"new zealand", r"auckland"],
    "South Africa": [r"south africa", r"cape town"],
    "Nigeria": [r"nigeria", r"lagos"],
    "Kenya": [r"kenya", r"nairobi"],
    "Ghana": [r"ghana", r"accra"],
    "Egypt": [r"egypt", r"cairo"],
    "Saudi Arabia": [r"saudi arabia", r"riyadh"],
    "Qatar": [r"qatar", r"doha"],
    "Belgium": [r"belgium", r"brussels"],
    "Switzerland": [r"switzerland", r"zurich"],
    "Austria": [r"austria", r"vienna"],
    "Poland": [r"poland", r"warsaw"],
    "Czech Republic": [r"czech republic", r"prague"],
    "Hungary": [r"hungary", r"budapest"],
    "Portugal": [r"portugal", r"lisbon"],
    "Greece": [r"greece", r"athens"],
    "Ireland": [r"ireland", r"dublin"],
}

# Level patterns
LEVEL_PATTERNS = {
    "PhD": [r"phd", r"doctoral", r"doctorate", r"doctoral degree"],
    "Master": [r"master", r"msc", r"ma", r"mba", r"master's"],
    "Bachelor": [r"bachelor", r"undergraduate", r"bsc", r"ba", r"bachelor's"],
    "Postdoc": [r"postdoc", r"post-doctoral", r"research fellow"],
}

# Funding patterns
FUNDING_PATTERNS = {
    "Fully Funded": [r"fully funded", r"full funding", r"full scholarship", r"tuition + stipend", r"covers tuition"],
    "Partial": [r"partial", r"tuition fee waiver", r"fee waiver", r"partial funding"],
    "Stipend Only": [r"stipend", r"living allowance", r"monthly allowance"],
    "Tuition Only": [r"tuition waiver", r"tuition free", r"fee reduction"],
}


def extract_dates(text: str) -> list[str]:
    """Extract dates from text."""
    dates = []
    text_lower = text.lower()

    for pattern in DATE_PATTERNS:
        for m in re.finditer(pattern, text_lower):
            try:
                if m.lastindex == 3:
                    # Pattern: DD Month YYYY or Month DD YYYY
                    groups = m.groups()
                    if groups[0].isdigit():
                        day, month, year = groups
                        month_num = MONTHS.get(month.lower(), 0)
                    else:
                        month, day, year = groups
                        month_num = MONTHS.get(month.lower(), 0)

                    if month_num and 1 <= int(day) <= 31:
                        date_str = f"{year}-{month_num:02d}-{int(day):02d}"
                        dates.append(date_str)
            except (ValueError, TypeError):
                continue

    return dates


def extract_country(text: str) -> str:
    """Extract country from text."""
    text_lower = text.lower()
    for country, patterns in COUNTRY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return country
    return ""


def extract_level(text: str) -> str:
    """Extract level from text."""
    text_lower = text.lower()
    for level, patterns in LEVEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return level
    return ""


def extract_funding(text: str) -> str:
    """Extract funding type from text."""
    text_lower = text.lower()
    for funding, patterns in FUNDING_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return funding
    return "Unknown"


def extract_deadline(text: str) -> str:
    """Extract deadline from text."""
    dates = extract_dates(text)
    if dates:
        # Return the earliest future date
        today = datetime.now().strftime("%Y-%m-%d")
        future_dates = [d for d in dates if d >= today]
        if future_dates:
            return min(future_dates)
    return ""


def extract_scholarship_data(text: str, url: str = "") -> dict:
    """
    Extract structured scholarship data from text.
    Returns a dict with extracted fields.
    """
    return {
        "country": extract_country(text),
        "level": extract_level(text),
        "funding": extract_funding(text),
        "deadline": extract_deadline(text),
        "dates_found": extract_dates(text),
        "url": url,
    }


def enrich_scholarship(scholarship: dict) -> dict:
    """
    Enrich a scholarship dict with extracted data.
    Only fills in empty fields.
    """
    text = f"{scholarship.get('title', '')} {scholarship.get('description', '')}"
    extracted = extract_scholarship_data(text, scholarship.get("url", ""))

    # Only fill in empty fields
    for field in ["country", "level", "funding", "deadline"]:
        if not scholarship.get(field) or scholarship.get(field) == "Unknown":
            scholarship[field] = extracted.get(field, scholarship.get(field, "Unknown"))

    return scholarship
