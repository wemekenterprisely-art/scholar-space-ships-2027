# ScholarSpace-ships 2027 — Project Instructions

## Overview
Autonomous scholarship intelligence engine. Runs 2×/day (06:00 / 18:00 Libya time) on
GitHub Actions. Finds scholarships for a **Libyan MA holder in Applied Linguistics who
cannot take IELTS/TOEFL** → clickable Excel + dashboard + API.

## Scholar profile (redacted; see scholar_profile.json + PROFILE.md)
- Libyan national; MA English Language (Applied Linguistics), University of Zawia 2025
  (75.70%, thesis approved without amendments); BA English, Sabratha 2014 (87%)
- Thesis: corpus-based study of hedging in MA applied linguistics dissertations
- Skills: ESL/EFL teaching, academic supervision (15 theses), academic editing/writing,
  English–Arabic translation, SPSS/thematic analysis, AI-assisted research

## Matching rules (GATES — never loosen)
1. **English test**: IELTS/TOEFL/b2-certificate required → REJECT. "No IELTS", "IELTS not
   required", MoI certificate accepted → exempt. Not mentioned → allow + flag "verify".
2. **Nationality**: Libya not eligible (restrictive clauses) → REJECT. Libya/global/open → pass.
3. **Level**: below MA → REJECT.
4. **Deadline**: passed → REJECT. Urgency scored (≤14d = 95).
5. **Match threshold**: `SCHOLAR_MIN_SCORE` default 65 for Fresh Matches.
6. Rule shield: the deterministic gates always win over the AI layer.

## Sources
Tier 1: scholars4dev, scholarship-positions (RSS), google-news (5 targeted queries),
national-programs (curated flagship schemes: Türkiye Bursları, Stipendium Hungaricum,
CSC, MEXT, ISFD, DAAD, Erasmus Mundus, KAUST).
Tier 2: web search (DuckDuckGo HTML, no key). Add sources via one file + registry line.

## Delivery
Excel 5 sheets (All / Fresh / Applications / Deadlines&Notes / Daily Log) with hyperlinks;
dashboard :8000; API :8001; optional Telegram + Brevo email.

## Rules for AI assistant
1. Never stop the automation — it must run forever, for free, on GitHub Actions.
2. Never break a working fetcher — add, don't replace blindly.
3. Never remove the hard gates; never lower the threshold to make it look better.
4. Always run `test_filters.py` + `scholar_ollama_test.py` before pushing filter changes.
5. Log everything; a failed source is skipped, not fatal.
6. Keep the repo **public-safe**: NO phone, address, email, or serial numbers in the repo.
7. Keep docs/SCHOLARSHIP_ENGINE_PLAN.md in sync with the code.

## Emergency procedures
- Ollama down → deterministic scoring only (still green).
- Fetcher down → others continue, circuit breaker trips after 3 fails.
- Excel fails → JSON state still saved. State sync fails → scan results still local.