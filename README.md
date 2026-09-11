# ScholarSpace-ships 2027

**Autonomous scholarship intelligence for a Libyan MA holder — no IELTS/TOEFL required.**

Scans scholarship sources **once daily at 06:00 (Libya time)** on free GitHub
Actions with a **2-hour deep global search** across 7 continents, filters every opportunity through *your exact profile* (no English test,
Libya-eligible, MA-level, fully funded preferred), scores each one deterministically
**plus** a local AI referee (Ollama `qwen2.5:1.5b`), and hands you a **clickable Excel
report** with every link, deadline and an ACTION flag — plus a live dashboard and API.

## What you get every scan

- 📊 **Excel `Scholarship_Report_<date>.xlsx`** — 5 sheets: All Scholarships · Fresh
  Matches · Applications · Deadlines & Notes (APPLY NOW) · Daily Log — every link hyperlinked
- 🌐 **Dashboard** :8000 and **REST API** :8001
- 🧠 **Memory** — dedupe history and applications persist in `state/` across runs, forever
- 🤖 **AI referee** — JSON-mode 5-dimension scoring, with a deterministic *rule shield* the
  model can never override (the same hardening proven live on the career scanner)

## Gates (what the engine refuses to waste your time on)

| Gate | Rule |
|---|---|
| 🚫 IELTS/TOEFL | Required → rejected. "No IELTS" / MoI certificate → exempt. |
| 🌍 Libya | Restrictive lists without Libya → rejected. Open/global → eligible. |
| 🎓 Level | Below MA → rejected. |
| ⏰ Deadline | Expired → rejected. Urgency scored into the match. |

## Global Search

The system performs a **2-hour deep search** across 7 continents:

| Continent | Countries | Universities |
|-----------|-----------|--------------|
| 🌍 Africa | Libya, Egypt, Nigeria, South Africa, Kenya, Ghana, Tanzania, Ethiopia, Morocco, Tunisia | 100+ |
| 🌏 Asia | Turkey, Japan, China, South Korea, India, Malaysia, Singapore, Thailand, Indonesia, Pakistan, Bangladesh, Philippines, Vietnam | 130+ |
| 🌍 Europe | Germany, UK, France, Netherlands, Italy, Spain, Hungary, Poland, Sweden, Norway, Denmark, Finland | 120+ |
| 🌎 North America | USA, Canada, Mexico | 30+ |
| 🌎 South America | Brazil, Argentina, Colombia, Chile | 40+ |
| 🌏 Oceania | Australia, New Zealand | 20+ |

Search queries are organized by field:
- Applied Linguistics
- ESL/EFL Education
- Translation Studies
- Academic Writing
- General Education
- General Linguistics

## Sources

### Tier 1 (Quick - 5 sources)
- **scholars4dev** — HTML scraping
- **scholarship-positions** — Google News fallback
- **google-news** — 5 targeted RSS queries
- **national-programs** — 8 curated flagship schemes
- **web-search** — DuckDuckGo HTML

### Tier 2 (Medium - 4 sources)
- **scholarshiproar** — HTML scraping
- **opportunitiescorners** — HTML scraping
- **internationalopportunities** — HTML scraping
- **opportunitieszone** — HTML scraping

### Tier 3 (Deep - 1 source)
- **global-search** — 2-hour comprehensive worldwide search across 7 continents

## Run it

```bash
pip install -r requirements.txt
python scanner.py --tier 3
python test_filters.py && python scholar_ollama_test.py
```

Read **[docs/SCHOLARSHIP_ENGINE_PLAN.md](docs/SCHOLARSHIP_ENGINE_PLAN.md)** for the full
engineering blueprint (add sources, filters, roadmap to the *lethal* version).
See **[PROFILE.md](PROFILE.md)** for the redacted scholar profile the algorithm targets.
