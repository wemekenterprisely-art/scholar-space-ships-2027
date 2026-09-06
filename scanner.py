"""scanner - ScholarSpace-ships main pipeline.
fetch -> normalize -> deterministic filters -> AI refine -> Excel + state.
Runs the same way in GitHub Actions and locally (state sync only active in CI).
"""
import asyncio, json, os, sys, time, argparse
from datetime import datetime, date, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from fetchers import registry
from filters import score_scholarship
import excel_generator, metrics
try:
    import state_sync
except Exception:
    state_sync = None

OUTPUT = config.OUTPUT_DIR
TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    t0 = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None)
    parser.add_argument("--tier", type=int, default=0, help="max tier (0=all)")
    parser.add_argument("--skip-ai", action="store_true")
    args = parser.parse_args()

    # 1) restore memory from the repo (CI) or local state folder
    if state_sync:
        state_sync.download_state()
    seen = load_json(OUTPUT / "seen_urls.json", {})
    app_track = load_json(OUTPUT / "applications.json", {})
    scan_hist = load_json(OUTPUT / "scan_history.json", [])
    fresh_hist = load_json(OUTPUT / "fresh_matches_history.json", [])

    fresh_ids = {f.get("id") for f in fresh_hist}

    # 2) fetch
    print(f"=== ScholarSpace-ships scan {NOW} ===")
    raw_by_source = registry.fetch_all(tier_cap=args.tier, names=[args.source] if args.source else None)
    all_items, skipped_bad = [], 0
    for src, rows in raw_by_source.items():
        for r in rows:
            sch = registry.normalize(r, src)
            if not sch["title"] or not sch["url"]:
                skipped_bad += 1
                continue
            all_items.append(sch)
        metrics.record_fetch(src, len(rows), latency_ms=0)
    print(f"Total fetched: {len(all_items)} jobs/scholarships from {len(raw_by_source)} sources")

    # 3) dedupe + deterministic filter
    seen_ids = set()
    candidates, rejects, funnel = [], 0, {}
    for sch in all_items:
        if sch["id"] in seen_ids or sch["id"] in fresh_ids:
            rejects += 1
            continue
        seen_ids.add(sch["id"])
        det = score_scholarship(sch)
        if det["rejected"]:
            rejects += 1
            continue
        candidates.append(det)
    print(f"  after dedupe/last-seen and hard gates: {len(candidates)} candidates, {rejects} rejected")
    funnel["fetched"], funnel["candidates"], funnel["rejected"] = len(all_items), len(candidates), rejects

    # 4) rank deterministic, AI-refine top
    candidates.sort(key=lambda s: s["det_score"], reverse=True)
    if not args.skip_ai:
        try:
            candidates = asyncio.run(analyze_top(candidates))
        except Exception as e:
            print(f"  AI scoring skipped: {e}")

    for s in candidates:
        s["final_score"] = s.get("final_score") or s["det_score"]

    # 5) matches
    matches = [s for s in candidates if s.get("final_score", 0) >= config.MIN_MATCH_SCORE]
    new_this_run = 0
    for m in matches:
        if m["id"] not in fresh_ids:
            new_this_run += 1
            fresh_ids.add(m["id"])
        m["first_seen"] = m.get("first_seen", NOW)
        m["date"] = m.get("date", TODAY)
        m["applied"] = m.get("applied", False)
    match_ids = {m["id"] for m in matches}
    fresh_hist = matches + [f for f in fresh_hist if f.get("id") not in match_ids]
    save_json(OUTPUT / "fresh_matches_history.json", fresh_hist)
    seen.update({s["id"]: {"url": s["url"], "first_seen": NOW} for s in matches})
    save_json(OUTPUT / "seen_urls.json", seen)
    save_json(OUTPUT / "all_scholarships.json", candidates)

    # 6) daily log + scan history
    scan_hist.append({
        "date": TODAY, "time": NOW, "fetched": len(all_items), "candidates": len(candidates),
        "matches": len(matches), "new": new_this_run, "health": "100%", "seconds": round(time.time() - t0, 1),
        "sources": {k: len(v) for k, v in raw_by_source.items()},
    })
    save_json(OUTPUT / "scan_history.json", scan_hist[-90:])
    save_json(OUTPUT / "daily_log.json", {"last_scan": NOW, "today": TODAY, "scans": scan_hist[-30:]})

    # 7) Excel + metrics + health
    try:
        xlsx = excel_generator.make_workbook(candidates, matches, app_track, scan_hist)
        io_path = OUTPUT / f"Scholarship_Report_{TODAY}.xlsx"
        xlsx.save(str(io_path))
        metrics.record_timing("excel", 1.0)
        print(f"  Excel: {io_path.name}")
    except Exception as e:
        print(f"  Excel failed: {e}")
    metrics.record_funnel(funnel)
    metrics.record_timing("total", round(time.time() - t0, 1))
    save_json(OUTPUT / "metrics.json", metrics.snapshot())
    save_json(OUTPUT / "health.json", metrics.get_health())

    # 8) persistence
    if state_sync:
        state_sync.upload_state()

    print(f"Scan complete in {round(time.time()-t0,1)}s. Matched: {len(matches)} (new: {new_this_run}). ")
    for m in matches[:10]:
        print(f"   - [{m.get('final_score')}] {m['title'][:70]} {m.get('url','')}")
    if not matches:
        print("   (no fresh matches above threshold this run)")
    return 0


def analyze_top(candidates):
    from scholar_analyzer import analyze_many
    return analyze_many(candidates)


if __name__ == "__main__":
    sys.exit(main())