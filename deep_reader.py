"""
Deep Page Reader - reads individual scholarship pages and extracts detailed information.
Uses web search module to fetch and parse web pages.
"""
import re
import json
from typing import Optional
from web_search import web_fetch, verify_scholarship
from extractor import extract_scholarship_data, enrich_scholarship


class DeepPageReader:
    """
    Reads individual scholarship pages and extracts detailed information.
    """

    def __init__(self, timeout: int = 15, max_chars: int = 8000):
        """
        Initialize the deep page reader.
        
        Args:
            timeout: Timeout for web requests in seconds
            max_chars: Maximum characters to fetch from each page
        """
        self.timeout = timeout
        self.max_chars = max_chars
        self.cache = {}

    def read_scholarship_page(self, url: str) -> dict:
        """
        Read a scholarship page and extract detailed information.
        
        Returns:
            dict with extracted information:
            - title: Scholarship title
            - description: Full description
            - country: Country/region
            - level: Academic level
            - funding: Funding type
            - deadline: Application deadline
            - eligibility: Eligibility criteria
            - requirements: Requirements
            - application_process: How to apply
            - contact: Contact information
            - is_valid: Whether the page was successfully read
        """
        if url in self.cache:
            return self.cache[url]

        result = {
            "url": url,
            "is_valid": False,
            "title": "",
            "description": "",
            "country": "",
            "level": "",
            "funding": "",
            "deadline": "",
            "eligibility": "",
            "requirements": "",
            "application_process": "",
            "contact": "",
        }

        try:
            # Fetch the page content
            content = web_fetch(url, self.max_chars)
            if content.startswith("Error fetching URL"):
                return result

            result["is_valid"] = True
            result["description"] = content[:2000]

            # Extract structured data
            extracted = extract_scholarship_data(content, url)
            result.update(extracted)

            # Extract specific sections
            result["eligibility"] = self._extract_section(content, ["eligibility", "who can apply", "requirements", "criteria"])
            result["requirements"] = self._extract_section(content, ["requirements", "documents needed", "application requirements"])
            result["application_process"] = self._extract_section(content, ["how to apply", "application process", "apply now", "submit"])
            result["contact"] = self._extract_contact(content)

            # Extract deadline if not found
            if not result["deadline"]:
                result["deadline"] = self._extract_deadline(content)

            # Extract the actual application URL
            actual_url = self._extract_application_url(content, url)
            if actual_url and actual_url != url:
                result["actual_application_url"] = actual_url

            # Cache the result
            self.cache[url] = result

        except Exception as e:
            print(f"  [deep-reader] Error reading {url}: {e}")

        return result

    def _extract_section(self, content: str, keywords: list[str]) -> str:
        """Extract a section based on keywords."""
        content_lower = content.lower()

        for keyword in keywords:
            # Find the section
            patterns = [
                rf"{keyword}[:\s]*(.*?)(?:\n\n|\n#|\n[A-Z]|\Z)",
                rf"{keyword}[:\s]*(.*?)(?:\n\n|\Z)",
            ]

            for pattern in patterns:
                m = re.search(pattern, content_lower, re.S)
                if m:
                    section = m.group(1).strip()
                    if len(section) > 20:  # Minimum length
                        return section[:500]

        return ""

    def _extract_contact(self, content: str) -> str:
        """Extract contact information."""
        # Email pattern
        email_m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
        if email_m:
            return f"Email: {email_m.group(0)}"

        # Phone pattern
        phone_m = re.search(r"[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}", content)
        if phone_m:
            return f"Phone: {phone_m.group(0)}"

        return ""

    def _extract_deadline(self, content: str) -> str:
        """Extract deadline from content."""
        # Look for deadline patterns
        deadline_patterns = [
            r"deadline[:\s]*([\w\s,./-]+\d{4})",
            r"apply by[:\s]*([\w\s,./-]+\d{4})",
            r"closing date[:\s]*([\w\s,./-]+\d{4})",
            r"due date[:\s]*([\w\s,./-]+\d{4})",
        ]

        for pattern in deadline_patterns:
            m = re.search(pattern, content, re.I)
            if m:
                return m.group(1).strip()[:100]

        return ""

    def _extract_application_url(self, content: str, original_url: str) -> str:
        """Extract the actual application URL from the page content."""
        # Look for application links
        apply_patterns = [
            r'href="(https?://[^"]*(?:apply|application|submit|register|sign-up|signup)[^"]*)"',
            r'href="(https?://[^"]*(?:scholarship|fellowship|grant|award)[^"]*)"',
            r'href="(https?://[^"]*(?:portal|apply-now|how-to-apply)[^"]*)"',
            r'(https?://[^\s]*(?:apply|application|submit|register)[^\s]*)',
        ]

        for pattern in apply_patterns:
            matches = re.findall(pattern, content, re.I)
            for url in matches:
                # Filter out social media and generic links
                if any(skip in url.lower() for skip in ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'google.com/maps']):
                    continue
                # Prefer official university/organization domains
                if any(domain in url.lower() for domain in ['.edu', '.ac.', '.org', '.gov', 'university', 'scholarship']):
                    return url
            # If no official domain found, return first valid URL
            if matches:
                return matches[0]

        # Fallback: try to extract from the original URL
        if "news.google.com" not in original_url:
            return original_url

        return original_url

    def batch_read(self, urls: list[str], max_concurrent: int = 3) -> dict[str, dict]:
        """
        Read multiple scholarship pages.
        
        Args:
            urls: List of URLs to read
            max_concurrent: Maximum concurrent requests
            
        Returns:
            dict mapping URL to extracted information
        """
        results = {}
        for i, url in enumerate(urls):
            if i % 10 == 0:
                print(f"  [deep-reader] Processing {i+1}/{len(urls)}...")
            results[url] = self.read_scholarship_page(url)
        return results


def enrich_scholarships_with_deep_read(scholarships: list[dict], max_deep_reads: int = 50) -> list[dict]:
    """
    Enrich scholarships by reading their pages.
    
    Args:
        scholarships: List of scholarship dicts
        max_deep_reads: Maximum number of deep reads to perform
        
    Returns:
        Enriched list of scholarships
    """
    reader = DeepPageReader()
    enriched = []

    # Sort by score (highest first)
    sorted_scholarships = sorted(scholarships, key=lambda s: s.get("final_score", 0), reverse=True)

    # Read top scholarships
    for i, s in enumerate(sorted_scholarships[:max_deep_reads]):
        url = s.get("url", "")
        if not url:
            enriched.append(s)
            continue

        print(f"  [deep-reader] Reading {i+1}/{min(max_deep_reads, len(sorted_scholarships))}: {s.get('title', '')[:60]}...")
        deep_data = reader.read_scholarship_page(url)

        # Merge deep data into scholarship
        if deep_data.get("is_valid"):
            for field in ["country", "level", "funding", "deadline", "eligibility", "requirements", "application_process", "contact"]:
                if deep_data.get(field) and not s.get(field):
                    s[field] = deep_data[field]

            # Use the actual application URL if found
            if deep_data.get("actual_application_url"):
                s["url"] = deep_data["actual_application_url"]
                s["original_url"] = s.get("url", "")

            # Add deep read metadata
            s["deep_read"] = True
            s["deep_read_data"] = deep_data

        enriched.append(s)

    # Add remaining scholarships without deep read
    for s in sorted_scholarships[max_deep_reads:]:
        s["deep_read"] = False
        enriched.append(s)

    return enriched
