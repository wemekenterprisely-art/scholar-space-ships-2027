"""
ScholarSpace-ships 2027 - Central Configuration
Single source of truth: sources, filters, scoring weights, Ollama, env overrides.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
STATE_DIR = ROOT / "state"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Matching ────────────────────────────────────────────────────────────
MIN_MATCH_SCORE = int(os.getenv("SCHOLAR_MIN_SCORE", "55"))
NEAR_MISS_MIN = 40
NEAR_MISS_MAX = 54
NEAR_MISS_LIMIT = int(os.getenv("SCHOLAR_NEAR_MISS_LIMIT", "12"))
MAX_AGE_DAYS = int(os.getenv("SCHOLAR_MAX_AGE_DAYS", "90"))      # deadline window
FRESH_DAYS = int(os.getenv("SCHOLAR_FRESH_DAYS", "7"))           # "fresh" = within 7 days
FETCH_TIMEOUT = int(os.getenv("SCHOLAR_FETCH_TIMEOUT", "15"))
FETCH_BATCH_SIZE = int(os.getenv("SCHOLAR_BATCH_SIZE", "8"))
MAX_AI_JOBS = int(os.getenv("SCHOLAR_MAX_AI_JOBS", "15"))

# ── Sources (tiered) ────────────────────────────────────────────────────
TIER_1_SOURCES = ["scholars4dev", "scholarship-positions", "google-news", "national-programs", "web-search"]
TIER_2_SOURCES = ["scholarshiproar", "opportunitiescorners", "internationalopportunities", "opportunitieszone"]

PROBE_BLOCKED_SOURCES = []
FORCE_BLOCKED_SOURCES = os.getenv("SCHOLAR_FORCE_BLOCKED", "0") == "1"

# ── Language (IELTS-free) detection ─────────────────────────────────────
# Explicit REQUIREMENT hints: scholarship asks for an English language test.
ENGLISH_TEST_HINTS = (
    "ielts", "toefl", "toefl ibt", "duolingo english test", "pte academic",
    "english proficiency test", "english language test", "english test required",
    "cambridge english", "b2 certificate", "c1 certificate", "certificate required", "language certificate", "english certificate",
)
# Negation / exemption hints: NO English test needed, or alternatives accepted.
ENGLISH_EXEMPT_HINTS = (
    "no ielts", "without ielts", "ielts not required", "no toefl", "without toefl",
    "no english test", "without english test", "english test not required",
    "not required", "exempt", "medium of instruction", "moi certificate",
    "english medium instruction", "medium-of-instruction", "english-taught",
    "previous degree in english", "taken in english",
)
# ── Nationality (Libya) ─────────────────────────────────────────────────
LIBYA_HINTS = ("libya", "libyan", "arab countries", "arab league", "mena", "islamic countries",
               "oic countries", "african countries", "developing countries")
OPEN_NATIONALITY_HINTS = ("all nationalities", "all countries", "international students",
                          "open to", "worldwide", "any nationality", "no nationality restriction")
RESTRICTIVE_NATIONALITY_HINTS = ("only for", "only open to", "residents of", "eu citizens",
                                 "european union", "uk citizens", "us citizens", "only citizens of",
                 "citizens of", "nationals of", "for citizens of", "must be a citizen of")

# ── Level / funding ─────────────────────────────────────────────────────
LEVEL_POSTGRAD_HINTS = ("master", "phd", "doctoral", "postgraduate", "graduate", "research")
LEVEL_BACHELOR_ONLY_HINTS = ("bachelor", "undergraduate", "first degree", "high school", "secondary school")
FULLY_FUNDED_HINTS = ("fully funded", "full funding", "full scholarship", "full tuition", "tuition + stipend",
                      "covers tuition", "full cost", "fully-financed", "full sallary", "living allowance included")
PARTIAL_HINTS = ("partial", "tuition fee waiver", "fee waiver", "partial funding", "50%")

# ── Profile-based field scoring ─────────────────────────────────────────
PROFILE_KEYWORDS = (
    "applied linguistics", "linguistics", "english language", "english", "esl", "efl", "tesol",
    "tefl", "language teaching", "language education", "education", "teaching", "translation",
    "arabic", "arabic-english", "academic writing", "corpus linguistics", "discourse analysis",
    "hedging", "curriculum", "supervision", "educational research", "applied linguistics phd",
)

# ── Ollama ──────────────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

# ── Scoring weights (deterministic first, AI refines) ───────────────────
W_FIELD, W_ELIG, W_LANG, W_FUND, W_DEAD = 0.35, 0.25, 0.15, 0.15, 0.10
# Junk/spam titles to reject (no real scholarship info)
JUNK_TITLE_HINTS = ("cloudflare", "wordpress", "error", "404", "untitled",
                     "home", "archive", "sample", "test", "lorem ipsum")
