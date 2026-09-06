"""
CareerOps Metrics & Health — Prometheus-friendly + dashboard JSON
Tracks per-source success, latency, scoring funnel, and system health.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
METRICS_FILE = OUTPUT_DIR / "metrics.json"
HEALTH_FILE = OUTPUT_DIR / "health.json"

# In-memory accumulator for current run
_run_metrics = {
    "sources": defaultdict(lambda: {"fetched": 0, "matches": 0, "errors": 0, "latency_ms": []}),
    "funnel": {},
    "timings": {},
}

def record_fetch(source: str, fetched: int, matches: int = 0, latency_ms: float = 0, error: str = None):
    s = _run_metrics["sources"][source]
    s["fetched"] += fetched
    s["matches"] += matches
    if latency_ms:
        s["latency_ms"].append(latency_ms)
    if error:
        s["errors"] += 1
        s["last_error"] = error

def record_funnel(funnel: dict):
    _run_metrics["funnel"] = funnel

def record_timing(phase: str, seconds: float):
    _run_metrics["timings"][phase] = seconds

def get_health() -> dict:
    """Compute health snapshot."""
    sources = _run_metrics["sources"]
    total_fetched = sum(v["fetched"] for v in sources.values())
    total_matches = sum(v["matches"] for v in sources.values())
    total_errors = sum(v["errors"] for v in sources.values())
    avg_latency = 0
    latencies = [x for v in sources.values() for x in v["latency_ms"]]
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
    # Health score 0-100
    health = 100
    if total_errors > len(sources) * 0.3:
        health -= 30
    if total_fetched == 0:
        health = 0
    elif total_fetched < 500:
        health -= 20
    status = "healthy" if health >= 80 else "degraded" if health >= 50 else "unhealthy"
    return {
        "status": status,
        "health_score": health,
        "total_fetched": total_fetched,
        "total_matches": total_matches,
        "total_errors": total_errors,
        "avg_latency_ms": round(avg_latency, 1),
        "sources_up": sum(1 for v in sources.values() if v["fetched"] > 0),
        "sources_total": len(sources),
        "funnel": _run_metrics["funnel"],
        "timings": _run_metrics["timings"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

def persist_metrics():
    """Write metrics.json + health.json for dashboard & CI."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # Expand sources to serializable
        serial_sources = {}
        for k, v in _run_metrics["sources"].items():
            serial_sources[k] = {
                "fetched": v["fetched"],
                "matches": v["matches"],
                "errors": v["errors"],
                "avg_latency_ms": round(sum(v["latency_ms"])/len(v["latency_ms"]),1) if v["latency_ms"] else 0,
                "last_error": v.get("last_error",""),
            }
        full = {
            "run": {
                "sources": serial_sources,
                "funnel": _run_metrics["funnel"],
                "timings": _run_metrics["timings"],
            },
            "health": get_health(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        METRICS_FILE.write_text(json.dumps(full, indent=2), encoding="utf-8")
        HEALTH_FILE.write_text(json.dumps(full["health"], indent=2), encoding="utf-8")
    except Exception as e:
        print(f"metrics persist failed: {e}")

def prometheus_text() -> str:
    """Return Prometheus exposition format (for /metrics endpoint)."""
    h = get_health()
    lines = [
        "# HELP careerops_fetched_total Total jobs fetched this run",
        "# TYPE careerops_fetched_total gauge",
        f"careerops_fetched_total {h['total_fetched']}",
        "# HELP careerops_matches_total Matches after scoring",
        "# TYPE careerops_matches_total gauge",
        f"careerops_matches_total {h['total_matches']}",
        "# HELP careerops_health_score 0-100",
        "# TYPE careerops_health_score gauge",
        f"careerops_health_score {h['health_score']}",
        "# HELP careerops_sources_up Sources that returned jobs",
        "# TYPE careerops_sources_up gauge",
        f"careerops_sources_up {h['sources_up']}",
    ]
    return "\n".join(lines) + "\n"

def snapshot() -> dict:
    """Serializable snapshot of the current run's metrics."""
    return {
        "sources": {
            k: {kk: vv for kk, vv in v.items() if kk != "latency_ms"}
            for k, v in _run_metrics["sources"].items()
        },
        "funnel": _run_metrics["funnel"],
        "timings": _run_metrics["timings"],
    }
