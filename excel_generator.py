"""excel_generator - 5-sheet scholarship workbook (CareerOps XML quality)."""
import json
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "state" / "fresh_matches_history.json"

def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def extract_uni(s):
    import re
    university = s.get("university", s.get("institution", ""))
    if not university:
        title = s.get("title", "")
        patterns = [
            r"at\s+([\w\s,]+(?:University|Institute|College|School)[\w\s]*)",
            r"([\w\s,]+(?:University|Institute|College|School))",
            r"(CSC|Chevening|Fulbright|DAAD|Erasmus|MEXT|Turkiye|Stipendium)\s+Scholarship",
        ]
        for p in patterns:
            m = re.search(p, title, re.I)
            if m:
                university = m.group(1).strip() if m.lastindex else m.group(0).strip()
                university = re.sub(r"\s*\d{4}\s*$", "", university).strip()
                break
    return university

def get_recommendation(score):
    if score >= 85: return "STRONG MATCH - Apply now"
    if score >= 75: return "GOOD MATCH - Review and apply"
    if score >= 65: return "MODERATE - Review requirements"
    return "LOW - May not fit"

def load_fresh_history():
    try:
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

def save_fresh_history(matches):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(matches, indent=2, default=str), encoding="utf-8")

def merge_fresh_matches(current, history):
    seen = {}
    for m in history:
        url = m.get("url", "")
        if url: seen[url] = m
    for m in current:
        url = m.get("url", "")
        if url:
            existing = seen.get(url, {})
            new_date = m.get("scan_date", "")
            old_date = existing.get("scan_date", "")
            if new_date >= old_date: seen[url] = m
            else: seen[url] = existing
    return sorted(seen.values(), key=lambda x: (-x.get("final_score", 0), x.get("scan_date", "")))

def generate_excel(candidates, matches, scan_hist, scan_time=None):
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = scan_time or now.strftime("%I:%M %p UTC")
    scan_date = now.isoformat()
    total_scanned = len(candidates)

    for s in matches:
        s["scan_date"] = scan_date

    history = load_fresh_history()
    all_fresh = merge_fresh_matches(matches, history)
    save_fresh_history(all_fresh)

    # Build rows for each sheet
    dump_rows = []
    for i, s in enumerate(candidates):
        uni = extract_uni(s)
        score = s.get("final_score", s.get("det_score", 0))
        ielts = s.get("english_requirement", "unknown")
        ielts_label = "Not Required" if ielts == "exempt" else ("Required" if ielts == "required" else "Verify")
        style = ' ss:StyleID="green"' if score >= 75 else (' ss:StyleID="red"' if score >= 50 else "")
        dump_rows.append(f'''
    <Row{style}>
      <Cell><Data ss:Type="Number">{i + 1}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("title", ""))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(uni or "Check listing")}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("country", "Open/Global"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("level", "Unknown"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("funding", "Unknown"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("deadline", "N/A"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(ielts_label)}</Data></Cell>
      <Cell><Data ss:Type="String">{score}%</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("source", ""))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("url", ""))}</Data></Cell>
    </Row>''')

    fresh_rows = []
    for i, s in enumerate(all_fresh):
        uni = extract_uni(s)
        score = s.get("final_score", s.get("det_score", 0))
        ielts = s.get("english_requirement", "unknown")
        ielts_label = "Not Required" if ielts == "exempt" else ("Required" if ielts == "required" else "Verify")
        applied = "Yes" if s.get("applied") else "No"
        scan_dt = s.get("scan_date", "")[:10]
        style = ' ss:StyleID="applied"' if s.get("applied") else ' ss:StyleID="unapplied"'
        fresh_rows.append(f'''
    <Row{style}>
      <Cell><Data ss:Type="Number">{i + 1}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("title", ""))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(uni or "Check listing")}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("country", "Open/Global"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("level", "Unknown"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("funding", "Unknown"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("deadline", "N/A"))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(ielts_label)}</Data></Cell>
      <Cell><Data ss:Type="String">{score}%</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("source", ""))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(applied)}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(scan_dt)}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(s.get("url", ""))}</Data></Cell>
    </Row>''')

    daily_rows = []
    for h in scan_hist[-30:]:
        daily_rows.append(f'''
    <Row>
      <Cell><Data ss:Type="String">{_esc(h.get("date", ""))}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(h.get("time", ""))}</Data></Cell>
      <Cell><Data ss:Type="Number">{h.get("fetched", 0)}</Data></Cell>
      <Cell><Data ss:Type="Number">{h.get("candidates", 0)}</Data></Cell>
      <Cell><Data ss:Type="Number">{h.get("matches", 0)}</Data></Cell>
      <Cell><Data ss:Type="Number">{h.get("new", 0)}</Data></Cell>
      <Cell><Data ss:Type="Number">{h.get("seconds", 0)}</Data></Cell>
      <Cell><Data ss:Type="String">{_esc(json.dumps(h.get("sources", {}), ensure_ascii=False))}</Data></Cell>
    </Row>''')

    dump_rows_str = "".join(dump_rows) if dump_rows else '<Row><Cell><Data ss:Type="String">No scholarships scanned yet.</Data></Cell></Row>'
    fresh_rows_str = "".join(fresh_rows) if fresh_rows else '<Row><Cell><Data ss:Type="String">No fresh matches yet.</Data></Cell></Row>'
    daily_rows_str = "".join(daily_rows) if daily_rows else '<Row><Cell><Data ss:Type="String">No scans yet.</Data></Cell></Row>'

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
  <Styles>
    <Style ss:ID="header"><Font ss:Bold="1" ss:Color="#FFFFFF" ss:Size="11"/><Interior ss:Color="#0d1b2a" ss:Pattern="Solid"/></Style>
    <Style ss:ID="green"><Interior ss:Color="#dcfce7" ss:Pattern="Solid"/></Style>
    <Style ss:ID="red"><Interior ss:Color="#fef2f2" ss:Pattern="Solid"/></Style>
    <Style ss:ID="unapplied"><Interior ss:Color="#fee2e2" ss:Pattern="Solid"/><Font ss:Color="#b91c1c" ss:Bold="1"/></Style>
    <Style ss:ID="applied"><Interior ss:Color="#dcfce7" ss:Pattern="Solid"/><Font ss:Color="#166534" ss:Bold="1"/></Style>
    <Style ss:ID="title"><Font ss:Bold="1" ss:Size="14" ss:Color="#0d1b2a"/></Style>
  </Styles>

  <!-- Sheet 1: All Scholarships -->
  <Worksheet ss:Name="All Scholarships">
    <Table>
      <Column ss:Width="40"/><Column ss:Width="300"/><Column ss:Width="200"/><Column ss:Width="120"/>
      <Column ss:Width="80"/><Column ss:Width="120"/><Column ss:Width="120"/><Column ss:Width="100"/>
      <Column ss:Width="60"/><Column ss:Width="120"/><Column ss:Width="400"/>
      <Row ss:StyleID="title"><Cell><Data ss:Type="String">ScholarSpace-ships Full Scan - {date_str} ({total_scanned} scholarships scanned)</Data></Cell></Row>
      <Row><Cell><Data ss:Type="String">Green = High match (75%+) | Red = Medium match (50-74%) | White = Lower match</Data></Cell></Row>
      <Row ss:StyleID="header">
        <Cell><Data ss:Type="String">#</Data></Cell><Cell><Data ss:Type="String">Scholarship</Data></Cell>
        <Cell><Data ss:Type="String">University</Data></Cell><Cell><Data ss:Type="String">Country</Data></Cell>
        <Cell><Data ss:Type="String">Level</Data></Cell><Cell><Data ss:Type="String">Funding</Data></Cell>
        <Cell><Data ss:Type="String">Deadline</Data></Cell><Cell><Data ss:Type="String">English Req</Data></Cell>
        <Cell><Data ss:Type="String">Score</Data></Cell><Cell><Data ss:Type="String">Source</Data></Cell>
        <Cell><Data ss:Type="String">Apply URL</Data></Cell>
      </Row>
      {dump_rows_str}
    </Table>
  </Worksheet>

  <!-- Sheet 2: Fresh Matches (accumulated) -->
  <Worksheet ss:Name="Fresh Matches">
    <Table>
      <Column ss:Width="40"/><Column ss:Width="300"/><Column ss:Width="200"/><Column ss:Width="120"/>
      <Column ss:Width="80"/><Column ss:Width="120"/><Column ss:Width="120"/><Column ss:Width="100"/>
      <Column ss:Width="60"/><Column ss:Width="120"/><Column ss:Width="80"/><Column ss:Width="100"/>
      <Column ss:Width="400"/>
      <Row ss:StyleID="title"><Cell><Data ss:Type="String">Fresh Matches - {date_str} (accumulated across all scans)</Data></Cell></Row>
      <Row><Cell><Data ss:Type="String">RED = Not applied (apply now!) | GREEN = Already applied. Score 55%+ matches.</Data></Cell></Row>
      <Row ss:StyleID="header">
        <Cell><Data ss:Type="String">#</Data></Cell><Cell><Data ss:Type="String">Scholarship</Data></Cell>
        <Cell><Data ss:Type="String">University</Data></Cell><Cell><Data ss:Type="String">Country</Data></Cell>
        <Cell><Data ss:Type="String">Level</Data></Cell><Cell><Data ss:Type="String">Funding</Data></Cell>
        <Cell><Data ss:Type="String">Deadline</Data></Cell><Cell><Data ss:Type="String">English Req</Data></Cell>
        <Cell><Data ss:Type="String">Score</Data></Cell><Cell><Data ss:Type="String">Source</Data></Cell>
        <Cell><Data ss:Type="String">Applied?</Data></Cell><Cell><Data ss:Type="String">Found On</Data></Cell>
        <Cell><Data ss:Type="String">Apply URL</Data></Cell>
      </Row>
      {fresh_rows_str}
    </Table>
  </Worksheet>

  <!-- Sheet 3: Applications -->
  <Worksheet ss:Name="Applications">
    <Table>
      <Column ss:Width="300"/><Column ss:Width="400"/><Column ss:Width="200"/><Column ss:Width="120"/>
      <Column ss:Width="120"/><Column ss:Width="120"/><Column ss:Width="200"/><Column ss:Width="120"/>
      <Row ss:StyleID="title"><Cell><Data ss:Type="String">Application Tracker</Data></Cell></Row>
      <Row><Cell><Data ss:Type="String">Track which scholarships you applied to. Update status in Fresh Matches sheet.</Data></Cell></Row>
      <Row ss:StyleID="header">
        <Cell><Data ss:Type="String">Scholarship</Data></Cell><Cell><Data ss:Type="String">Apply URL</Data></Cell>
        <Cell><Data ss:Type="String">University</Data></Cell><Cell><Data ss:Type="String">Country</Data></Cell>
        <Cell><Data ss:Type="String">Status</Data></Cell><Cell><Data ss:Type="String">Deadline</Data></Cell>
        <Cell><Data ss:Type="String">Notes</Data></Cell><Cell><Data ss:Type="String">Updated</Data></Cell>
      </Row>
      <Row><Cell><Data ss:Type="String">No applications tracked yet. Mark scholarships as Applied in the Fresh Matches sheet.</Data></Cell></Row>
    </Table>
  </Worksheet>

  <!-- Sheet 4: Deadlines & Notes -->
  <Worksheet ss:Name="Deadlines &amp; Notes">
    <Table>
      <Column ss:Width="300"/><Column ss:Width="400"/><Column ss:Width="120"/><Column ss:Width="80"/>
      <Column ss:Width="120"/><Column ss:Width="120"/><Column ss:Width="200"/>
      <Row ss:StyleID="title"><Cell><Data ss:Type="String">Deadlines &amp; Action Items</Data></Cell></Row>
      <Row><Cell><Data ss:Type="String">Sorted by deadline. APPLY NOW = within 21 days | This month = within 45 days | Plan ahead = later.</Data></Cell></Row>
      <Row ss:StyleID="header">
        <Cell><Data ss:Type="String">Scholarship</Data></Cell><Cell><Data ss:Type="String">Apply URL</Data></Cell>
        <Cell><Data ss:Type="String">Deadline</Data></Cell><Cell><Data ss:Type="String">Days Left</Data></Cell>
        <Cell><Data ss:Type="String">Action</Data></Cell><Cell><Data ss:Type="String">Funding</Data></Cell>
        <Cell><Data ss:Type="String">Notes</Data></Cell>
      </Row>
      {fresh_rows_str}
    </Table>
  </Worksheet>

  <!-- Sheet 5: Daily Log -->
  <Worksheet ss:Name="Daily Log">
    <Table>
      <Column ss:Width="120"/><Column ss:Width="180"/><Column ss:Width="80"/><Column ss:Width="100"/>
      <Column ss:Width="80"/><Column ss:Width="60"/><Column ss:Width="80"/><Column ss:Width="400"/>
      <Row ss:StyleID="title"><Cell><Data ss:Type="String">Daily Scan Log (last 30 scans)</Data></Cell></Row>
      <Row ss:StyleID="header">
        <Cell><Data ss:Type="String">Date</Data></Cell><Cell><Data ss:Type="String">Time</Data></Cell>
        <Cell><Data ss:Type="String">Fetched</Data></Cell><Cell><Data ss:Type="String">Candidates</Data></Cell>
        <Cell><Data ss:Type="String">Matches</Data></Cell><Cell><Data ss:Type="String">New</Data></Cell>
        <Cell><Data ss:Type="String">Seconds</Data></Cell><Cell><Data ss:Type="String">Sources</Data></Cell>
      </Row>
      {daily_rows_str}
    </Table>
  </Worksheet>

</Workbook>'''
