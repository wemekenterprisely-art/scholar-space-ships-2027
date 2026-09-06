"""scholar_ollama_test - gate test for the deterministic shield.
No Ollama required: these assert the filters that protect every real scan.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from filters import english_test_required, libya_eligible, funding_level, score_scholarship

TESTS = [
    {
        "name": "fully-funded no-IELTS for Libyans",
        "sch": {"title": "Fully Funded MA Scholarship for Libyan Students",
                "description": "No IELTS required. Fully funded scholarship covers tuition and living costs. Open to all Libyan nationals. Deadline: 1 October 2026.",
                "url": "https://example.test/1", "deadline": "2027-10-01",
                "funding": "Fully Funded", "level": "Master", "source": "test", "country": "Libya"},
        "want_rejected": False, "want_english": "exempt",
    },
    {
        "name": "IELTS 7.0 required - must reject",
        "sch": {"title": "PhD Scholarship 2027",
                "description": "Applicants must have IELTS 7.0 or TOEFL 100. Open to international students.",
                "url": "https://example.test/2", "deadline": "2027-12-01",
                "funding": "Fully Funded", "level": "PhD", "source": "test", "country": "Germany"},
        "want_rejected": True, "want_english": "required",
    },
    {
        "name": "EU citizens only - Libya not eligible must reject",
        "sch": {"title": "Diploma Scholarship",
                "description": "Only open to EU citizens. B2 English certificate required.",
                "url": "https://example.test/3", "deadline": "2027-09-01",
                "funding": "Partial", "level": "Postgraduate", "source": "test", "country": "EU"},
        "want_rejected": True, "want_english": "required",
    },
    {
        "name": "medium-of-instruction accepted - exempt",
        "sch": {"title": "MA Scholarship - English Medium Instruction",
                "description": "No English test needed; medium of instruction certificate accepted. Open to international students.",
                "url": "https://example.test/4", "deadline": "2027-08-30",
                "funding": "Partial", "level": "Master", "source": "test", "country": "Turkey"},
        "want_rejected": False, "want_english": "exempt",
    },
    {
        "name": "deadline passed - reject",
        "sch": {"title": "Scholarship", "description": "No IELTS. Open to all. Deadline passed.",
                "url": "https://example.test/5", "deadline": "2020-01-01",
                "funding": "Fully Funded", "level": "Master", "source": "test", "country": "Any"},
        "want_rejected": True, "want_english": "exempt",
    },
]

def main():
    failed = 0
    for t in TESTS:
        s = t["sch"]
        eng = english_test_required(f"{s['title']} {s['description']}")
        scored = score_scholarship(s)
        ok = (eng == t["want_english"]) and (scored["rejected"] == t["want_rejected"])
        print(f"[{'PASS' if ok else 'FAIL'}] {t['name']}: english={eng} rejected={scored['rejected']} "
              f"score={scored['det_score']} reasons={scored['reject_reasons']}")
        if not ok:
            failed += 1
    print(f"GATE RESULT: {len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())