"""scholar_analyzer - Ollama-powered 5-dimension scholarship scoring.
Hardened: JSON mode, keep_alive, context tuning, retries, simple-prompt
fallback, and a deterministic rule shield that the model cannot override.
"""
import asyncio, json, re
from pathlib import Path

ROOT = Path(__file__).parent

try:
    import aiohttp
except ImportError:
    aiohttp = None

from config import OLLAMA_URL, OLLAMA_MODEL, MAX_AI_JOBS

DIMENSIONS = ["field_fit", "eligibility", "language", "funding", "deadline_urgency"]

PROFILE = {}
_profile_path = ROOT / "scholar_profile.json"
if _profile_path.exists():
    try:
        PROFILE = json.loads(_profile_path.read_text(encoding="utf-8"))
    except Exception:
        PROFILE = {}


def _profile_text() -> str:
    p = PROFILE
    deg = p.get("degrees") or ""
    thesis = p.get("thesis") or ""
    ri = ",".join(p.get("research_interests") or [])
    sk = ",".join(p.get("skills") or [])
    return (f"Scholar profile: {p.get('headline','')}. Degrees: {deg}. "
            f"Thesis: {thesis}. Research interests: {ri}. Skills: {sk}. "
            f"Nationality: Libya. Needs scholarships where IELTS/TOEFL is NOT required "
            f"or a medium-of-instruction certificate is accepted.")


def _build_prompt(sch: dict) -> str:
    desc = str(sch.get("description", ""))[:1500]
    return ("Score this scholarship for the scholar described below.\n"
            f"SCHOLAR: {_profile_text()}\n"
            f"SCHOLARSHIP: {sch['title']}\n"
            f"Description: {desc}\n"
            f"Country: {sch.get('country','')} | Funding: {sch.get('funding','')} "
            f"| Level: {sch.get('level','')} | Deadline: {sch.get('deadline','')}\n"
            f"IMPORTANT: from LIBYA; English test (IELTS/TOEFL) must NOT be required "
            f"(or medium-of-instruction certificate accepted). Score 0-100 for each "
            f"dimension: " + json.dumps({d: 0 for d in DIMENSIONS}, ensure_ascii=False) +
            " plus 'verdict' (one sentence ending PASS or FAIL). Reply pure JSON only.")


def _build_simple_prompt(sch: dict) -> str:
    desc = str(sch.get("description", ""))[:800]
    return (f"Is this scholarship suitable for a Libyan MA holder in Applied Linguistics "
            f"who cannot take IELTS/TOEFL? 0-100.\n{sch['title']} | {desc}")


async def _call_ollama(session, prompt: str, json_format: bool = False, max_retries: int = 2):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0.3, "num_predict": 700, "num_ctx": 8192},
    }
    if json_format:
        payload["format"] = "json"
    url = f"{OLLAMA_URL}/api/generate"
    for attempt in range(max_retries + 1):
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as r:
                data = await r.json()
                return (data.get("response") or "").strip()
        except Exception:
            if attempt == max_retries:
                raise
            await asyncio.sleep(2 * (attempt + 1))
    return ""


async def _check_ollama(session) -> bool:
    try:
        async with session.get(f"{OLLAMA_URL}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as r:
            data = await r.json()
            models = [m.get("name", "") for m in data.get("models", [])]
        base = OLLAMA_MODEL.split(":")[0]
        if OLLAMA_MODEL not in models and not any(base in m for m in models):
            print(f"  WARNING: configured model {OLLAMA_MODEL} is NOT pulled yet")
            return False
        return True
    except Exception:
        print("  WARNING: Ollama not reachable")
        return False


def _extract_json(raw: str) -> dict | None:
    raw = (raw or "").strip()
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    m = re.search(r"\{[^{}]+\}", raw, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return None


def _enforce_rules(sch: dict, scoring: dict) -> dict:
    """Deterministic shield - model may refine but never override gates."""
    applied = []
    dd = sch.get("det_dims") or {}
    if dd.get("language") == 0:
        scoring["language"] = min(int(scoring.get("language", 100)), 5)
        applied.append("language-gate")
    if dd.get("eligibility") == 0:
        scoring["eligibility"] = min(int(scoring.get("eligibility", 100)), 5)
        applied.append("nationality-gate")
    if dd.get("funding", 50) >= 100:
        scoring["funding"] = max(int(scoring.get("funding", 0)), 80)
    applied.append("field-anchor")
    scoring["_rules_applied"] = applied
    return scoring


_done_counter = [0]


async def analyze_many(scholarships: list[dict]) -> list[dict]:
    if aiohttp is None:
        print("  aiohttp missing - skipping AI scoring")
        return scholarships
    if not scholarships:
        return scholarships
    print(f"  Ollama available - analyzing {len(scholarships)} scholarships with {OLLAMA_MODEL}")
    async with aiohttp.ClientSession() as session:
        if not await _check_ollama(session):
            return scholarships
        sem = asyncio.Semaphore(2)
        jobs = [asyncio.ensure_future(_score_one(sem, session, s)) for s in scholarships[:MAX_AI_JOBS]]
        await asyncio.gather(*jobs, return_exceptions=True)
    return scholarships


async def _score_one(sem, session, sch: dict):
    async with sem:
        try:
            raw = await _call_ollama(session, _build_prompt(sch), json_format=True)
            scoring = _extract_json(raw)
            if scoring is None:
                raw = await _call_ollama(session, _build_simple_prompt(sch), json_format=True)
                scoring = _extract_json(raw)
                if scoring is None:
                    print(f"  [{sch['title'][:40]}] unparseable AI output - skipped")
                    return
        except Exception as e:
            print(f"  [{sch['title'][:40]}] AI error: {e}")
            return
        if not all(k in scoring for k in DIMENSIONS):
            scoring = {d: int(scoring.get(d, 0)) for d in DIMENSIONS} | {"verdict": scoring.get("verdict", "")}
        scoring = _enforce_rules(sch, scoring)
        dims = {d: int(scoring.get(d, 0)) for d in DIMENSIONS}
        weights = {"field_fit": 0.30, "eligibility": 0.25, "language": 0.20,
                   "funding": 0.15, "deadline_urgency": 0.10}
        ai_overall = round(sum(dims[d] * weights[d] for d in DIMENSIONS), 1)
        sch["ai_overall"] = ai_overall
        sch["ai_dims"] = dims
        sch["ai_verdict"] = str(scoring.get("verdict", ""))[:300]
        sch["rules_applied"] = scoring.get("_rules_applied", [])
        sch["final_score"] = round(0.6 * ai_overall + 0.4 * sch.get("det_score", 0), 1)
        _done_counter[0] += 1
        print(f"  [{_done_counter[0]}] AI {sch['title'][:48]} -> {ai_overall}/100 ({str(sch.get('ai_verdict',''))[:60]})")
