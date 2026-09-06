"""dashboard - lightweight KPI dashboard served from output JSONs."""
import json, os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"

app = FastAPI(title="ScholarSpace-ships Dashboard")

def _load(name, default):
    try:
        return json.loads((OUTPUT / name).read_text(encoding="utf-8"))
    except Exception:
        return default

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

@app.get("/", response_class=HTMLResponse)
def index():
    matches = _load("fresh_matches_history.json", [])
    scans = _load("scan_history.json", [])
    metrics = _load("metrics.json", {})
    health = _load("health.json", {})
    last = scans[-1] if scans else {}
    rows = []
    for m in sorted(matches, key=lambda x: x.get("final_score", 0), reverse=True)[:50]:
        rows.append(f"<tr><td>{_esc(m['title'])}</td>"
                    f"<td><a href='{_esc(m.get('url',''))}' target='_blank'>link</a></td>"
                    f"<td>{_esc(m.get('deadline',''))}</td>"
                    f"<td>{_esc(m.get('funding_label', m.get('funding','')))}</td>"
                    f"<td>{_esc(m.get('english_requirement',''))}</td>"
                    f"<td>{_esc(m.get('libya_eligible',''))}</td>"
                    f"<td>{_esc(m.get('final_score',''))}</td></tr>")
    html = f"""<html><head><title>ScholarSpace-ships</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#0f172a;color:#e2e8f0}}
.kpis{{display:flex;gap:16px;flex-wrap:wrap}} .kpi{{background:#1e293b;border-radius:10px;padding:14px 22px;min-width:130px}}
.kpi b{{font-size:26px;display:block}} table{{border-collapse:collapse;width:100%;margin-top:18px}}
td,th{{border:1px solid #334155;padding:6px 10px;text-align:left;font-size:13px}} th{{background:#1e293b}}
a{{color:#60a5fa}}</style></head><body>
<h1>🚀 ScholarSpace-ships 2027</h1>
<div class="kpis">
<div class="kpi"><b>{len(matches)}</b>Fresh matches</div>
<div class="kpi"><b>{last.get('fetched',0)}</b>Fetched last scan</div>
<div class="kpi"><b>{last.get('matches',0)}</b>Matched last scan</div>
<div class="kpi"><b>{last.get('seconds','-')}s</b>Last scan time</div>
<div class="kpi"><b>{health.get('status','n/a')}</b>Health</div>
</div>
<table><tr><th>Title</th><th>Link</th><th>Deadline</th><th>Funding</th><th>English</th><th>Libya</th><th>Score</th></tr>
{''.join(rows) if rows else '<tr><td colspan=7>No fresh matches yet — first scan will populate.</td></tr>'}
</table></body></html>"""
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DASHBOARD_PORT", "8000")))
