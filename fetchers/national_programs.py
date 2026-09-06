"""
national_programs.py — curated flagship national/government scholarship schemes.

Portal-only programmes (Türkiye Bursları, Stipendium Hungaricum, CSC, MEXT,
ISFD, DAAD, Erasmus Mundus, KAUST) do not expose free RSS/JSON feeds, so the
engine keeps an authoritative registry with truthful requirement text and
official links. These entries flow through the SAME deterministic gates and
AI scorer as live-fetched items, so an incorrect language requirement is
rejected exactly like any other listing.

Add/update entries only with verified official information.
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "national_programs.json"


def fetch() -> list[dict]:
    """Return normalized national-program records."""
    try:
        entries = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [national_programs] cannot read registry: {e}")
        return []
    out = []
    for p in entries:
        out.append({
            "title": p["title"],
            "url": p["url"],
            "source": f"national_program:{p['id']}",
            "description": f"{p['program']}. {p['desc']}",
            "published": None,
            "deadline": p.get("deadline"),
        })
    print(f"  [national_programs] {len(out)} flagship programmes loaded")
    return out
