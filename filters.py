"""Deterministic scholarship filters - the rule shield.
Every decision here is explainable and unit-tested. The AI layer can refine
scores but can never override these gates.
"""
import re
from datetime import date
from config import (
    JUNK_TITLE_HINTS,
    ENGLISH_TEST_HINTS, ENGLISH_EXEMPT_HINTS, LIBYA_HINTS, OPEN_NATIONALITY_HINTS,
    RESTRICTIVE_NATIONALITY_HINTS, LEVEL_POSTGRAD_HINTS, LEVEL_BACHELOR_ONLY_HINTS,
    FULLY_FUNDED_HINTS, PARTIAL_HINTS, PROFILE_KEYWORDS,
    W_FIELD, W_ELIG, W_LANG, W_FUND, W_DEAD,
)
from fetchers._shared import parse_date


def english_test_required(text: str) -> str:
    """Gateway: is an English language test required?
    Returns 'required' | 'exempt' | 'unknown'. Negation-aware first."""
    t = (text or "").lower()
    if not t:
        return "unknown"
    # Paired exemptions: "IELTS ... not required", "no English test", etc.
    pair = re.compile(
        r"(ielts|toefl|english|language|certificate)[^.]{0,80}"
        r"(not required|not needed|not necessary|exempt|waiv)"
    )
    if pair.search(t):
        return "exempt"
    if re.search(r"(no|without|exempt from)s+(ielts|toefl|english test|english language test)", t):
        return "exempt"
    if "medium of instruction" in t or "moi certificate" in t or "english medium instruction" in t:
        return "exempt"
    for h in ENGLISH_EXEMPT_HINTS:
        if h in t:
            return "exempt"
    for h in ENGLISH_TEST_HINTS:
        if h in t:
            return "required"
    return "unknown"


def libya_eligible(text: str) -> bool | None:
    """Gateway: is a Libyan applicant eligible? True / False / None(unknown).
    Order matters: restrictive clauses win over generic 'open to' phrasing."""
    t = (text or "").lower()
    if not t:
        return None
    # 1) explicit Libya mention -> eligible
    if any(h in t for h in LIBYA_HINTS):
        return True
    # 2) restrictive clauses -> eligible only if Libya inside the clause
    for h in RESTRICTIVE_NATIONALITY_HINTS:
        i = t.find(h)
        if i >= 0:
            clause = t[i:i + 300]
            if "libya" in clause or "libyan" in clause:
                return True
            if any(open_h in clause for open_h in ("all countries", "any country", "all nationalities", "worldwide")):
                return True
            return False
    # 3) open phrasing -> eligible
    if any(h in t for h in OPEN_NATIONALITY_HINTS):
        return True
    return None


def funding_level(text: str) -> tuple[str, int]:
    """Return (label, score) for funding."""
    t = (text or "").lower()
    if any(h in t for h in FULLY_FUNDED_HINTS):
        return "Fully Funded", 100
    if any(h in t for h in PARTIAL_HINTS):
        return "Partial", 60
    return "Unknown", 50


def level_kind(text: str) -> str:
    """Return 'postgrad' | 'bachelor' | 'school' | 'unknown'."""
    t = (text or "").lower()
    if any(h in t for h in LEVEL_POSTGRAD_HINTS):
        return "postgrad"
    if any(h in t for h in ("high school", "secondary school")):
        return "school"
    if any(h in t for h in LEVEL_BACHELOR_ONLY_HINTS):
        return "bachelor"
    return "unknown"


def deadline_days(deadline: str) -> int | None:
    """Days from today until deadline. Negative = expired. None = no date."""
    iso = parse_date(deadline or "")
    if not iso:
        return None
    try:
        d = date.fromisoformat(iso)
        return (d - date.today()).days
    except Exception:
        return None


def field_fit(title: str, description: str) -> int:
    """0-100: how well the scholarship matches the scholar profile keywords."""
    hay = f"{title or ''} {description or ''}".lower()
    hits = sum(1 for k in PROFILE_KEYWORDS if k in hay)
    return min(100, hits * 12)


def english_score(status: str) -> tuple[int, str]:
    if status == "exempt":
        return 100, "No English test required"
    if status == "required":
        return 0, "English test required - REJECTED"
    return 60, "Not mentioned - verify"


def eligibility_score(ok: bool | None) -> tuple[int, str]:
    if ok is False:
        return 0, "Libya not eligible - REJECTED"
    if ok is True:
        return 100, "Libyan students eligible"
    return 70, "Nationality not mentioned - verify"


def funding_score(label: str) -> int:
    return {"Fully Funded": 100, "Partial": 60, "Unknown": 50}.get(label, 50)


def deadline_score(days: int | None) -> tuple[int, str]:
    if days is None:
        return 50, "No deadline found"
    if days < 0:
        return 0, "Deadline PASSED"
    if days <= 14:
        return 95, f"Deadline in {days}d - act fast"
    if days <= 30:
        return 85, f"Deadline in {days}d"
    if days <= 90:
        return 70, f"Deadline in {days}d"
    return 50, f"Deadline in {days}d - long window"


def score_scholarship(s: dict) -> dict:
    """Full deterministic scoring of one scholarship dict (in-place augments)."""
    text = f"{s.get('title','')} {s.get('description','')} "
    text += f"{s.get('country','')} {s.get('funding','')} {s.get('level','')} {s.get('field','')}"

    eng = english_test_required(text)
    s["english_requirement"] = eng
    lang_score, lang_note = english_score(eng)

    elig = libya_eligible(text)
    s["libya_eligible"] = elig
    elig_score, elig_note = eligibility_score(elig)

    fund_label, _fund_raw = funding_level(text)
    s["funding_label"] = fund_label
    s["funding"] = fund_label  # Also set for email/Excel
    fund_sc = funding_score(fund_label)

    lvl = level_kind(text)
    s["level_kind"] = lvl
    s["level"] = lvl  # Also set for email/Excel

    days = deadline_days(s.get("deadline", ""))
    s["deadline_days"] = days
    dead_sc, dead_note = deadline_score(days)

    fit = field_fit(s.get("title", ""), s.get("description", ""))
    s["field_fit_det"] = fit

    overall = round(W_FIELD * fit + W_ELIG * elig_score + W_LANG * lang_score
                    + W_FUND * fund_sc + W_DEAD * dead_sc, 1)

    rejected = False
    reasons = []
    if eng == "required":
        rejected = True
        reasons.append("English test required")
    if elig is False:
        rejected = True
        reasons.append("Libya not eligible")
    if lvl == "school":
        rejected = True
        reasons.append("Below MA level")
    if days is not None and days < 0:
        rejected = True
        reasons.append("Deadline passed")

    s["det_score"] = overall
    s["det_dims"] = {
        "field_fit": fit, "eligibility": elig_score, "language": lang_score,
        "funding": fund_sc, "deadline": dead_sc,
    }
    s["notes"] = [lang_note, elig_note, dead_note]
    s["rejected"] = rejected
    s["reject_reasons"] = reasons
    return s