"""excel_generator - 5-sheet scholarship workbook, hyperlinked."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
LINK_FONT = Font(color="0563C1", underline="single")
WRAP = Alignment(wrap_text=True, vertical="top")

COLUMNS = ["Title", "Link", "Source", "Country", "Deadline", "Funding", "Level",
           "English Req", "Libya", "Field Fit", "Score", "Verdict/Notes"]


def _write_rows(ws, rows, start=2):
    for i, r in enumerate(rows, start=start):
        for j, val in enumerate(r, start=1):
            cell = ws.cell(row=i, column=j, value=val)
            cell.alignment = WRAP
        ws.row_dimensions[i].height = 30


def _style(ws, widths):
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for j in range(1, len(widths) + 1):
        c = ws.cell(row=1, column=j)
        c.fill, c.font = HEADER_FILL, HEADER_FONT
    ws.freeze_panes = "A2"


def make_workbook(candidates, matches, app_track, scan_hist):
    wb = Workbook()

    # 1 All Scholarships
    ws = wb.active; ws.title = "All Scholarships"
    ws.append(COLUMNS)
    rows = []
    for s in sorted(candidates, key=lambda x: x.get("final_score", 0), reverse=True):
        rows.append([s["title"], s["url"], s["source"], s.get("country", ""), s.get("deadline", ""),
                     s.get("funding_label", s.get("funding", "")), s.get("level_kind", ""),
                     s.get("english_requirement", ""), str(s.get("libya_eligible", "")),
                     s.get("field_fit_det", ""), s.get("final_score", s.get("det_score")),
                     " | ".join(s.get("notes", []))][:len(COLUMNS)])
    _write_rows(ws, rows); _style(ws, [45, 40, 16, 14, 12, 14, 10, 12, 8, 8, 8, 50])
    for r in range(2, len(rows) + 2):
        c = ws.cell(row=r, column=2)
        if c.value: c.hyperlink, c.font = c.value, LINK_FONT

    # 2 Fresh Matches
    ws2 = wb.create_sheet("Fresh Matches")
    cols2 = COLUMNS + ["AI Verdict"]
    ws2.append(cols2)
    rows2 = []
    for s in sorted(matches, key=lambda x: x.get("final_score", 0), reverse=True):
        rows2.append([s["title"], s["url"], s["source"], s.get("country", ""), s.get("deadline", ""),
                      s.get("funding_label", s.get("funding", "")), s.get("level_kind", ""),
                      s.get("english_requirement", ""), str(s.get("libya_eligible", "")),
                      s.get("field_fit_det", ""), s.get("final_score", s.get("det_score")),
                      " | ".join(s.get("notes", [])), s.get("ai_verdict", "")])
    _write_rows(ws2, rows2); _style(ws2, [45, 40, 16, 14, 12, 14, 10, 12, 8, 8, 8, 50, 40])
    for r in range(2, len(rows2) + 2):
        c = ws2.cell(row=r, column=2)
        if c.value: c.hyperlink, c.font = c.value, LINK_FONT

    # 3 Applications
    ws3 = wb.create_sheet("Applications")
    ws3.append(["Title", "Link", "Status", "Deadline", "Notes", "Updated"])
    rows3 = []
    for sid, a in (app_track or {}).items():
        rows3.append([a.get("title", sid), a.get("url", ""), a.get("status", "Apply"),
                      a.get("deadline", ""), a.get("notes", ""), a.get("updated", "")])
    _write_rows(ws3, rows3); _style(ws3, [50, 40, 14, 12, 50, 20])
    for r in range(2, len(rows3) + 2):
        c = ws3.cell(row=r, column=2)
        if c.value: c.hyperlink, c.font = c.value, LINK_FONT

    # 4 Deadlines & Notes
    ws4 = wb.create_sheet("Deadlines & Notes")
    ws4.append(["Title", "Link", "Deadline", "Days Left", "Action Needed", "Notes"])
    rows4 = []
    for s in sorted(matches, key=lambda x: x.get("deadline_days") if x.get("deadline_days") is not None else 9999):
        d = s.get("deadline_days")
        rows4.append([s["title"], s["url"], s.get("deadline", ""), d if d is not None else "N/A",
                      "APPLY NOW" if (d is not None and d <= 21) else ("This month" if d is not None and d <= 45 else "Plan ahead"),
                      " | ".join(s.get("notes", []))])
    _write_rows(ws4, rows4); _style(ws4, [50, 40, 14, 10, 14, 50])
    for r in range(2, len(rows4) + 2):
        c = ws4.cell(row=r, column=2)
        if c.value: c.hyperlink, c.font = c.value, LINK_FONT

    # 5 Daily Log
    ws5 = wb.create_sheet("Daily Log")
    ws5.append(["Date", "Time", "Fetched", "Candidates", "Matches", "New", "Seconds", "Sources"])
    rows5 = [[h.get("date"), h.get("time"), h.get("fetched"), h.get("candidates"), h.get("matches"),
              h.get("new"), h.get("seconds"), json_dumps(h.get("sources", {}))] for h in scan_hist[-30:]]
    _write_rows(ws5, rows5); _style(ws5, [12, 24, 10, 12, 10, 8, 10, 60])

    return wb


def json_dumps(o):
    import json
    try:
        return json.dumps(o)
    except Exception:
        return ""
