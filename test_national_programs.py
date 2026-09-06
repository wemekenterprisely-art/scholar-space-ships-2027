"""Unit test — national-programmes registry feeds the pipeline correctly."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fetchers import registry
from fetchers.national_programs import fetch as np_fetch

def test_registered():
    assert "national-programs" in registry.REGISTRY, "national-programs not registered"
    assert "scholarshipdb" in registry.REGISTRY, "scholarshipdb not registered"

def test_fetch_shape():
    items = np_fetch()
    assert len(items) >= 8, f"expected >=8 flagship programmes, got {len(items)}"
    required = {"title", "url", "source", "description"}
    for it in items:
        assert required <= set(it), f"missing fields in {it.get('title')}"
        assert it["url"].startswith("https://"), it["url"]
        assert len(it["description"]) > 120, "description too thin for gating"

if __name__ == "__main__":
    test_registered()
    test_fetch_shape()
    print("national-programs tests: 2/2 passed")
