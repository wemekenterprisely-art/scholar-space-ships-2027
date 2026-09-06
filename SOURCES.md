# SOURCES.md — Scholarship Source Registry

## Live in v1 (no API keys)

| Source | Kind | Where | Notes |
|---|---|---|---|
| scholars4dev | RSS | `https://www.scholars4dev.com/feed/` | Large curated fund list |
| scholarship-positions | RSS | `https://scholarship-positions.com/feed/` | University scholarships |
| scholarshipfellow | RSS | `https://scholarshipfellow.com/feed/` | Fully funded listings |
| scholarshipdb | JSON | `https://scholarshipdb.net/api/scholarships.json` | Open aggregate index |
| web-search | HTML | DuckDuckGo (no key) | Profile-built queries |

## How to add a source
1. Create `fetchers/<name>.py` exposing `def fetch(timeout=…) -> list[dict]` with keys
   `title, url, description, country, deadline, funding, level, posted_at`.
2. Register: `fetchers/registry.py` → `REGISTRY["<name>"] = {"tier": N, "fn": <name>.fetch}`.
3. Add a row below and a test if the source has quirks. Nothing else changes.

## Expansion pool (roadmap v2/v3 — the "lethal" reach)

### National & government programs (fully funded pools)
- DAAD scholarship database (Germany) — `https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/` + JSON API
- Türkiye Bursları (Turkey) — applications.turkiyeburslari.gov.tr (JSON/XHR endpoints)
- Stipendium Hungaricum (Hungary) — stipendiumhungaricum.hu (fee waivers + stipend)
- CSC China — campuschina.org (PhD/full)
- MEXT Japan — studyinjapan.go.jp
- KAUST (Saudi) — kaust.edu.sa (MS/PhD, fully funded, no application fee)
- ISFD / Islamic Development Bank — isfd-isdb.org (very Libya-friendly)
- Commonwealth Scholarships — cscuk.fcdo.gov.uk (many-country scheme; check Libya list)
- King Saud / UQU / Qassim (Saudi) — deaneries' portals
- Erasmus Mundus Joint Masters — eacea.ec.europa.eu (scholarships for non-EU incl. Libya)

### Aggregators & niche
- scholarshipdb.net (done), ScholarshipPortal (portal.studyportals.com), Scholars4Dev (done),
  ScholarshipPosition (done), GrantForward (grantforward.com), Phelp (phelp.com),
  International Scholarships (internationalscholarships.in), AcademicTransfer (for research
  positions), Euraxess (euraxess.ec.europa.eu — research/PhD funding), IFAE? (no)

### Arabic / MENA (v3 — many are MoI/no-IELTS friendly)
- Libya's Ministry of Higher Education circulars (mohe.gov.ly)
- Libyan embassies (scholarship missions)
- Arab League Educational, Cultural and Scientific Organization (ALECSO)
- Qaribou (Morocco), Turkish consulates in Libya, Saudi Cultural Attaché programs

> Rule of thumb for every new source: usually one URL + one parsing function. Add it, test
> it, log its performance — the tutorial is `docs/SCHOLARSHIP_ENGINE_PLAN.md §7`.
