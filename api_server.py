"""api_server - read-only REST API over the scholarship state."""
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
app = FastAPI(title="ScholarSpace-ships API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def _load(name, default):
    try:
        return json.loads((OUTPUT / name).read_text(encoding="utf-8"))
    except Exception:
        return default

@app.get("/api/health")
def health():
    return _load("health.json", {"status": "unknown", "last_scan": None})

@app.get("/api/metrics")
def metrics():
    return _load("metrics.json", {})

@app.get("/api/scholarships")
def scholarships():
    return _load("all_scholarships.json", [])

@app.get("/api/matches")
def matches():
    return _load("fresh_matches_history.json", [])

@app.get("/api/scans")
def scans():
    return _load("scan_history.json", [])

if __name__ == "__main__":
    import os, uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "8001")))
