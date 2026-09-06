# ScholarSpace-ships 2027 — Engineering Blueprint

> **Purpose of this file.** This is the master specification. Any engineer — human or AI —
> can rebuild, extend, or supercharge this system from this document alone. Follow it,
> keep it updated, and never let the repo drift far from what is written here.

---

## 1. Vision

An **autonomous scholarship intelligence engine** that runs forever on GitHub Actions for
free, scanning the world's scholarship ecosystem multiple times a day, filtering every
opportunity through one very specific personal profile (a Libyan MA holder who needs
**no IELTS/TOEFL**), and delivering a **clickable Excel report** plus live dashboard/API.

The name is a pun and a mission: *scholar-space-ships* — ships that carry scholars.

## 2. Architecture

```
            ┌──────────────────────────────────────────────────────┐
            │                GitHub Actions (2×/day)               │
            │                                                        │
  ┌───────┐ │  ┌────────────┐   ┌───────────┐   ┌───────────────┐  │
  │ RSS/  │─▶│  fetchers/   │──▶│  filters   │──▶│  scanner.py   │  │
  │ JSON  │ │  registry     │   │ (gates)    │   │  orchestrator │  │
  │ feeds │ │  5 sources    │   └─────┬─────┘   └───────┬───────┘  │
  └───────┘ └────────────┘          │              │
                                    ▼              ▼
                          ┌──────────────┐  ┌──────────────────┐
                          │ deterministic│  │ scholar_analyzer │
                          │   scoring    │  │ Ollama qwen2.5   │
                          └──────┬───────┘  │ JSON 5-dim +     │
                                 │          │ hard rule shield │
                                 │          └────────┬─────────┘
                                 ▼                   ▼
                          ┌──────────────────────────────────────┐
                          │  Excel (5 sheets) · dashboard · API  │
                          │  state/ → repo (memory across runs)  │
                          └──────────────────────────────────────┘
```

**Flow per scan:** fetch → normalize → dedupe → hard-gate filters → deterministic
5-dimension score → optional AI refinement of top candidates (rule shield ON) →
threshold cut → Excel + JSON + metrics → state synced back to the repo.

## 3. Canonical data model

Every scholarship, everywhere in the code, is this dict:

```json
{
  "id": "<sha1 12-hex of source|url>",
  "title": "Fully Funded MA Scholarship for Libyan Students",
  "source": "scholars4dev",
  "url": "https://…",
  "description": "… (truncated 2000)",
  "country": "Libya", "deadline": "2027-10-01",
  "funding": "Fully Funded", "level": "Master",
  "field": "", "posted_at": "…",
  "english_requirement": "exempt|required|unknown",
  "libya_eligible": true|false|null,
  "funding_label": "Fully Funded|Partial|Unknown",
  "level_kind": "postgrad|bachelor|school|unknown",
  "deadline_days": 24 | null,
  "field_fit_det": 72,
  "det_score": 65.0, "det_dims": {"field_fit":…,"eligibility":…,"language":…,"funding":…,"deadline":…},
  "notes": ["…","…"], "rejected": false, "reject_reasons": [],
  "ai_overall": 74.5, "ai_dims": {…}, "ai_verdict": "…", "rules_applied": ["language-gate"],
  "final_score": 70.8,
  "first_seen": "…", "applied": false
}
```

**State files** (repo `state/`, mirrored in `output/`):
`all_scholarships.json`, `fresh_matches_history.json`, `applications.json`,
`seen_urls.json`, `daily_log.json`, `scan_history.json`, `metrics.json`, `health.json`.

## 4. Scoring engine

Deterministic first (weights from `config.py`):

| Dimension | Weight | Function |
|---|---|---|
| Field fit | 0.30 | profile keyword hits in title+description |
| Eligibility | 0.25 | nationality gate (Libya) |
| Language | 0.20 | the IELTS-free gate |
| Funding | 0.15 | fully funded 100 / partial 60 / unknown 50 |
| Deadline | 0.10 | urgency curve (≤14d: 95 … none: 50) |

**Hard gates** (cannot be overridden by AI): English test required → **reject**;
Libya not eligible → **reject**; below MA level → **reject**; deadline passed → **reject**.

**AI refinement:** top candidates (<=`SCHOLAR_MAX_AI_JOBS`) get one Ollama call in JSON
mode scoring the same five dimensions 0–100. The **rule shield** clamps any dimension the
deterministic gates already decided (e.g. language stays ≤5 when English is required).
Final score = **60% AI + 40% deterministic** when AI ran, else deterministic.

## 5. The IELTS-free detector (the needle)

`filters.english_test_required(text)` returns `required | exempt | unknown`, evaluated in
this strict order:

1. **Paired exemption regex** — `(ielts|toefl|english|language|certificate) … (not
   required|not needed|not necessary|exempt|waiv)` within ~80 chars. Catches "IELTS is
   not required", "TOEFL not necessary".
2. **Direct negatives** — `no / without / exempt from` + `ielts | toefl | english test
   | english language test`.
3. **MoI certificate** — "medium of instruction", "moi certificate", "english medium
   instruction" → exempt (huge for Turkey/Europe programs).
4. **Hint table** — `ENGLISH_EXEMPT_HINTS` ("no ielts", …) then `ENGLISH_TEST_HINTS`
   ("ielts", "toefl", "b2 certificate", "certificate required", …).
5. **Fallback** — nothing matched → `unknown` → allowed but flagged *"Not mentioned —
   verify"* (60/100 language, note in Excel).

This exact ordering is what makes "**IELTS 7.0 required**" never slip through while
"**no IELTS required**" never gets wrongly rejected — the lesson transferred from the
career-scanner's visa-negation bug (85→39 live fix).

## 6. Libya eligibility engine

Order of evaluation (restrictive wins over generic):
1. Explicit `libya/libyan` (or Arab League / OIC / MENA / African / developing-country
   phrasing) → **eligible**.
2. Restrictive clause present ("only for", "citizens of", "EU citizens", "residents of",
   …) → check the clause for Libya or "all countries" inside; otherwise **not eligible**.
3. Open phrasing ("all nationalities", "international students", "worldwide") → **eligible**.
4. Nothing → `null` → allowed but flagged "verify nationality".

## 7. Source registry

Live (tier 1, no keys): **scholars4dev RSS**, **scholarship-positions RSS**,
**scholarshipfellow RSS**, **scholarshipdb.net JSON**. Tier 2: **DuckDuckGo web search**
(queries built from the profile). Every source has a circuit breaker (3 fails → 10 min
cooldown). See `SOURCES.md` for the full expansion table.

**To add a source (the one-file contract):** write `fetchers/<name>.py` with
`def fetch(timeout=…) -> list[dict]` (keys: title, url, description, country, deadline,
funding, level, posted_at) and register it in `fetchers/registry.py`. Done. The normalizer,
filters, scoring, Excel and dashboard pick it up automatically.

## 8. Delivery

- **Excel** — `output/Scholarship_Report_<date>.xlsx`, 5 sheets: *All Scholarships*,
  *Fresh Matches*, *Applications*, *Deadlines & Notes* (with APPLY NOW flags), *Daily Log*.
  Every link is a clickable hyperlink.
- **Dashboard** :8000 — KPI cards + fresh matches table.
- **API** :8001 — `/api/health`, `/api/metrics`, `/api/scholarships`, `/api/matches`, `/api/scans`.
- **Optional notifications** — Telegram message + Brevo email with the Excel attached
  (no-op without secrets).

## 9. Reliability & memory

- Runners are ephemeral → `state_sync.py` persists `output/*.json` to `state/` in the
  repo via the GitHub Contents API (dedupe history, application tracking survive forever).
- Concurrency guard prevents overlapping scans; Ollama models cached across runs
  (`~/.ollama`, key `scholar-qwen2.5-1.5b`).
- Every failure is contained: fetcher error → skip; AI down → deterministic-only;
  Excel error → JSON still saved; scanner crash → previous state untouched.

## 10. CI/CD

`.github/workflows/scan.yml` — cron `0 4,16 * * *` UTC (**06:00 / 18:00 Libya**) + on
push. Installs Ollama on the runner, pulls `qwen2.5:1.5b`, runs the scanner.
`tests.yml` — gate + filter + import tests on every push. `ollama-test.yml` —
manual dispatch, full AI round-trip. Codespace: `.devcontainer` with Ollama preloaded.

## 11. Security & privacy (MANDATORY)

- This repo is **public** (unlimited Actions minutes). Therefore: **no phone numbers, no
  street addresses, no emails, no ID/degree serial numbers** anywhere in the repo. The
  redacted profile lives in `scholar_profile.json` / `PROFILE.md`.
- Secrets (Telegram token, Brevo key, destination email) go only in GitHub **Actions
  secrets**; `.env.example` documents them as empty placeholders.
- Future contributors MUST keep the redaction rule — if a private profile with contact
  data is needed, store it as an Actions secret or a private branch, never on main.

## 12. Testing strategy

- `test_filters.py` — pure unit tests of every gate (10+ cases currently, including the
  negation pairs and restrictive-nationality traps).
- `scholar_ollama_test.py` — 5-scenario gate test: no-IELTS fully funded for Libyans
  must PASS; IELTS-required, EU-only, expired-deadline must FAIL; MoI-accepted must PASS.
- CI runs both on every push. **Never ship a filter change without a new test case.**

## 13. Roadmap toward "the most lethal search ever built"

| Phase | What | Why it matters |
|---|---|---|
| ✅ v1 (this repo) | 5-6 sources, gates, 2×/day, Excel/dashboard/API | Operational today |
| 🚀 v2 — National programs | DAAD database, Türkiye Bursları, Stipendium Hungaricum, CSC China, MEXT Japan, KAUST, ISFD (Islamic Development Bank), Commonwealth — each a fetcher | The biggest fully funded pools live here |
| 🚀 v3 — Arabic & MENA | Arabic-language scholarship pages + OCR of PDF circulars (Libyan MoHE, embassies, Arab League) | Libya-specific opportunities rarely appear in English feeds |
| 🚀 v4 — Smarter ranking | Semantic similarity (profile → scholarship embedding), cluster duplicates, learn from "applied/ignored" feedback to reweight dimensions | Precision at scale |
| 🚀 v5 — Apply engine | Per-scholarship application checklist, document bundle builder (CV→PDF, transcripts, proposal), deadline reminders via Telegram | From "find" to "apply" in one click |

**Every phase follows the same contract: a fetcher + a test + a Source table row.**

## 14. Quickstart

```bash
pip install -r requirements.txt
python scanner.py --tier 1     # local scan (Ollama optional)
python test_filters.py && python scholar_ollama_test.py
python dashboard/app.py        # :8000
python api_server.py           # :8001
```
In GitHub: push → scan runs automatically at 06:00/18:00 Libya time.
