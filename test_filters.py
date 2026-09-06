"""Extra unit tests for the deterministic filters."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from filters import english_test_required, libya_eligible, funding_level, deadline_days, field_fit

CASES = [
    ("no ielts required", "exempt"),
    ("IELTS 6.5 or TOEFL 90 required", "required"),
    ("IELTS is not required", "exempt"),
    ("English test not required - medium of instruction", "exempt"),
    ("applicants must show English proficiency", "unknown"),
    ("no TOEFL", "exempt"),
]

def main():
    fails = 0
    for text, want in CASES:
        got = english_test_required(text)
        ok = got == want
        print(f"[{'PASS' if ok else 'FAIL'}] english_test_required({text!r}) -> {got} (want {want})")
        fails += 0 if ok else 1
    libya_cases = [
        ("open to all nationalities", True),
        ("Libyan students welcome", True),
        ("only open to EU citizens", False),
        ("for citizens of Germany, France, UK", False),
    ]
    for text, want in libya_cases:
        got = libya_eligible(text)
        ok = got is want
        print(f"[{'PASS' if ok else 'FAIL'}] libya_eligible({text!r}) -> {got} (want {want})")
        fails += 0 if ok else 1
    print("RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
