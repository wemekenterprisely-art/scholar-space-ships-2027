# ARCHITECTURE.md

```
                GitHub Actions (2×/day: 06:00 & 18:00 Libya)
┌─────────────────────────────────────────────────────────────┐
│  checkout → setup-python → pip install → ollama install →   │
│  ollama pull qwen2.5:1.5b → python scanner.py               │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ scanner.py  (orchestrator)                                   │
│  fetch_all → normalize → dedupe → gates → det-score →       │
│  AI refine (scholar_analyzer) → threshold → Excel/JSON      │
│  → state_sync.upload_state()                                │
└─────────────────────────────────────────────────────────────┘

Modules
  fetchers/registry.py   source routing + circuit breakers
  fetchers/*.py          one file per source (RSS/JSON/search)
  filters.py             pure functions: language/nationality/level/deadline/funding/field
  scholar_analyzer.py    Ollama JSON 5-dim scoring + rule shield
  excel_generator.py     openpyxl 5-sheet workbook, hyperlinks
  dashboard/app.py       FastAPI + HTML dashboard (:8000)
  api_server.py          FastAPI read API (:8001)
  metrics.py             funnel/health/timings
  state_sync.py          contents-API persistence to state/ (CI only)
  notifier.py            optional Telegram/Brevo

State (repo state/, mirrored output/)
  all_scholarships.json · fresh_matches_history.json · applications.json
  seen_urls.json · daily_log.json · scan_history.json · metrics.json · health.json

Local run:  python scanner.py [--tier N] [--skip-ai]
Tests:      python test_filters.py · python scholar_ollama_test.py
