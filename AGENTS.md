# ScholarSpace-ships 2027 — Project Instructions

## Overview
Autonomous scholarship intelligence engine. Runs 1×/day (06:00 Libya time) on
GitHub Actions with a 2-hour deep global search. Finds scholarships for a **Libyan MA holder in Applied Linguistics who
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
5. **Match threshold**: `SCHOLAR_MIN_SCORE` default 55 for Fresh Matches.
6. Rule shield: the deterministic gates always win over the AI layer.

## Global Search Algorithm
The system performs a deep search across 7 continents:
- **Africa**: Libya, Egypt, Nigeria, South Africa, Kenya, Ghana, Tanzania, Ethiopia, Morocco, Tunisia
- **Asia**: Turkey, Japan, China, South Korea, India, Malaysia, Singapore, Thailand, Indonesia, Pakistan, Bangladesh, Philippines, Vietnam
- **Europe**: Germany, UK, France, Netherlands, Italy, Spain, Hungary, Poland, Sweden, Norway, Denmark, Finland
- **North America**: USA, Canada, Mexico
- **South America**: Brazil, Argentina, Colombia, Chile
- **Oceania**: Australia, New Zealand
- **Antarctica**: No permanent universities

Search queries are organized by field:
- Applied Linguistics
- ESL/EFL Education
- Translation Studies
- Academic Writing
- General Education
- General Linguistics

## Sources
Tier 1 (Quick): scholars4dev, scholarship-positions, google-news, national-programs, web-search
Tier 2 (Medium): scholarshiproar, opportunitiescorners, internationalopportunities, opportunitieszone
Tier 3 (Deep): global-search (2-hour comprehensive worldwide search)

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
