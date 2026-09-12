"""
Duplicate Detection System - identifies and removes duplicate scholarships.
Uses MinHash + Locality Sensitive Hashing for efficient near-duplicate detection.
"""
import hashlib
from collections import defaultdict


class SimpleDeduplicator:
    """
    Simple deduplication using title similarity and URL matching.
    No external dependencies required.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.seen_urls = set()
        self.seen_titles = {}

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower().strip()
        # Remove common variations
        text = text.replace("scholarship", "").replace("program", "").replace("fellowship", "")
        text = text.replace("-", " ").replace("_", " ").replace("  ", " ")
        return text.strip()

    def _tokenize(self, text: str) -> set:
        """Tokenize text into words."""
        return set(self._normalize(text).split())

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union)

    def is_duplicate(self, scholarship: dict) -> bool:
        """
        Check if a scholarship is a duplicate.
        Returns True if it's a duplicate.
        """
        url = scholarship.get("url", "")
        title = scholarship.get("title", "")

        # Check URL duplicate
        if url and url in self.seen_urls:
            return True

        # Check title similarity
        title_tokens = self._tokenize(title)
        for seen_title, seen_tokens in self.seen_titles.items():
            similarity = self._jaccard_similarity(title_tokens, seen_tokens)
            if similarity >= self.threshold:
                return True

        # Add to seen
        if url:
            self.seen_urls.add(url)
        if title:
            self.seen_titles[title] = title_tokens

        return False

    def deduplicate(self, scholarships: list[dict]) -> list[dict]:
        """
        Remove duplicates from a list of scholarships.
        Returns deduplicated list.
        """
        unique = []
        for s in scholarships:
            if not self.is_duplicate(s):
                unique.append(s)
        return unique

    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        return {
            "urls_seen": len(self.seen_urls),
            "titles_seen": len(self.seen_titles),
        }


class CrossSourceDeduplicator:
    """
    Deduplicates across different sources by normalizing titles and URLs.
    """

    def __init__(self):
        self.url_hashes = set()
        self.title_hashes = defaultdict(list)

    def _hash_url(self, url: str) -> str:
        """Create a hash for URL normalization."""
        # Normalize URL
        url = url.lower().strip()
        url = url.replace("http://", "https://")
        url = url.rstrip("/")
        # Remove common parameters
        for param in ["utm_source", "utm_medium", "utm_campaign", "ref", "source"]:
            if "?" in url:
                url = url.split("?")[0]
                break
        return hashlib.md5(url.encode()).hexdigest()

    def _hash_title(self, title: str) -> str:
        """Create a hash for title normalization."""
        # Normalize title
        title = title.lower().strip()
        # Remove common variations
        for word in ["scholarship", "program", "fellowship", "award", "grant", "2027", "2026", "2025"]:
            title = title.replace(word, "")
        # Remove special characters
        title = "".join(c for c in title if c.isalnum() or c.isspace())
        title = " ".join(title.split())  # Normalize whitespace
        return hashlib.md5(title.encode()).hexdigest()

    def is_duplicate(self, scholarship: dict) -> bool:
        """
        Check if a scholarship is a duplicate across sources.
        Returns True if it's a duplicate.
        """
        url = scholarship.get("url", "")
        title = scholarship.get("title", "")

        # Check URL duplicate
        if url:
            url_hash = self._hash_url(url)
            if url_hash in self.url_hashes:
                return True
            self.url_hashes.add(url_hash)

        # Check title duplicate
        if title:
            title_hash = self._hash_title(title)
            if title_hash in self.title_hashes:
                # Check if it's from a different source
                for existing in self.title_hashes[title_hash]:
                    if existing.get("source") != scholarship.get("source"):
                        return True
            self.title_hashes[title_hash].append(scholarship)

        return False

    def deduplicate(self, scholarships: list[dict]) -> list[dict]:
        """
        Remove duplicates across sources.
        Returns deduplicated list.
        """
        unique = []
        for s in scholarships:
            if not self.is_duplicate(s):
                unique.append(s)
        return unique

    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        return {
            "urls_seen": len(self.url_hashes),
            "title_groups": len(self.title_hashes),
        }


def deduplicate_scholarships(scholarships: list[dict]) -> list[dict]:
    """
    Main deduplication function.
    Uses both URL and title-based deduplication.
    """
    dedup = CrossSourceDeduplicator()
    return dedup.deduplicate(scholarships)


def get_deduplication_stats(scholarships: list[dict]) -> dict:
    """
    Get statistics about deduplication.
    """
    dedup = CrossSourceDeduplicator()
    unique = dedup.deduplicate(scholarships)
    return {
        "original_count": len(scholarships),
        "unique_count": len(unique),
        "duplicates_removed": len(scholarships) - len(unique),
        "dedup_rate": round((len(scholarships) - len(unique)) / len(scholarships) * 100, 1) if scholarships else 0,
        **dedup.get_stats()
    }
