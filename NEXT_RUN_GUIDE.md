# NEXT RUN GUIDE

## How a scan works (06:00 / 18:00 Libya, or any push)

1. **Fetchers** pull RSS/JSON from the live registry (circuit breaker: 3 fails → 10 min off).
2. **Gates** reject: English-test-required · Libya-not-eligible · below-MA · expired deadlines.
3. **Deterministic 5-dim score** ranks every survivor.
4. **AI (optional)** refines top candidates with Ollama JSON scoring; shield enforces gates.
5. **Fresh Matches** ≥ 65 → saved to history + Excel with hyperlinks + flagged deadlines.
6. **State** (seen ids, matches, log, metrics) syncs back to `state/` in the repo.

## Check the last run
- GitHub → repo → Actions → "ScholarSpace-ships Scan"
- Or `gh run list --repo wemekenterprisely-art/scholar-space-ships-2027`
- Fresh matches: API `/api/matches` or `state/fresh_matches_history.json` in the repo.

## Common situations
- Zero matches: normal when sources are quiet; thresholds protect quality.
- Source fails: circuit breaker logs it; others keep going — no action needed.
- Many "verify" notes: nationality/language not mentioned in the listing — always check
  the official page before applying.
