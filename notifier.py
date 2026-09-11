"""
ScholarSpace-ships Notifier - Professional Telegram + Email
"""
import json, os, urllib.request, re as re_mod
from datetime import datetime, timedelta, timezone

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
BREVO_KEY = os.getenv("BREVO_API_KEY", "")
TO_EMAIL = os.getenv("TO_EMAIL", "")

LIBYA_TZ = timezone(timedelta(hours=2))

def now_libya():
    return datetime.now(LIBYA_TZ)

def get_recommendation(score):
    if score >= 85: return "STRONG MATCH"
    if score >= 75: return "GOOD MATCH"
    if score >= 65: return "REVIEW"
    return "CONSIDER"

def get_emoji(score):
    if score >= 85: return "\U0001f525"
    if score >= 75: return "\u2705"
    if score >= 65: return "\U0001f50d"
    return "\U0001f4cc"

def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def extract_uni(s):
    university = s.get("university", s.get("institution", ""))
    if not university:
        title = s.get("title", "")
        patterns = [
            r"at\s+([\w\s,]+(?:University|Institute|College|School)[\w\s]*)",
            r"([\w\s,]+(?:University|Institute|College|School))",
            r"(CSC|Chevening|Fulbright|DAAD|Erasmus|MEXT|Turkiye|Stipendium)\s+Scholarship",
        ]
        for p in patterns:
            m = re_mod.search(p, title, re_mod.I)
            if m:
                university = m.group(1).strip() if m.lastindex else m.group(0).strip()
                university = re_mod.sub(r"\s*\d{4}\s*$", "", university).strip()
                break
    return university

def format_card(s, idx):
    score = s.get("final_score", s.get("score", 0))
    rec = get_recommendation(score)
    emoji = get_emoji(score)
    university = extract_uni(s)
    country = s.get("country", "") or "Open/Global"
    funding = s.get("funding", s.get("funding_type", "Unknown"))
    if not funding or funding == "Unknown":
        funding = "Check listing"
    level = s.get("level", "") or "Check listing"
    deadline = s.get("deadline", "") or "Check listing"
    url = s.get("url", "")
    source = s.get("source", "unknown")

    lines = [
        f"{emoji} {rec} \u2014 {idx+1}",
        "",
        f"\U0001f393 Scholarship: {_esc(s.get('title', 'Unknown'))}",
    ]
    if university:
        lines.append(f"\U0001f3db\ufe0f University: {_esc(university)}")
    lines.append(f"\U0001f30d Country: {_esc(country)}")
    lines.append(f"\U0001f4da Level: {_esc(level)}")
    lines.append(f"\U0001f4b0 Funding: {_esc(funding)}")
    lines.append(f"\u23f0 Deadline: {_esc(deadline)}")
    lines.append(f"\U0001f4ca Match Score: {score}%")
    lines.append(f"\U0001f4e6 Source: {_esc(source)}")

    ielts = s.get("english_requirement", "")
    if ielts == "not_required" or s.get("no_ielts"):
        lines.append("\u2705 IELTS/TOEFL: Not Required")
    elif ielts == "required":
        lines.append("\u274c IELTS/TOEFL: Required")
    else:
        lines.append("\u2753 IELTS/TOEFL: Verify listing")

    if s.get("why"):
        lines.append(f"\U0001f517 Why it fits: {', '.join(s.get('why', [])[:3])}")
    lines.append(f"\U0001f517 Apply: {url}")
    return "\n".join(lines)

def build_telegram(scholarships, scan_info, stats):
    date = now_libya().strftime("%Y-%m-%d")
    time_str = now_libya().strftime("%I:%M %p Libya")
    scan_num = stats.get("total_scans", 0)
    all_count = scan_info.get("all_count", 0)
    source_count = scan_info.get("source_count", 0)

    msg = ""
    msg += f"\U0001f4cb SCHOLARSPACE-SHIPS \u2014 AI Scholarship Intelligence\n"
    msg += f"{date} \u00b7 {time_str} \u00b7 Scan #{scan_num}\n\n"
    msg += f"This cycle we reviewed {all_count:,} scholarships across {source_count} sources.\n\n"

    if not scholarships:
        msg += "\u2705 0 New Matches Found\n\n"
        msg += "No new scholarships passed all gates this cycle.\n"
        msg += "Gates: No IELTS/TOEFL | Libya eligible | MA+ level | Deadline valid\n"
    else:
        msg += f"\u2705 {len(scholarships)} new match{'es' if len(scholarships)!=1 else ''} found.\n\n"
        for i, s in enumerate(scholarships):
            msg += format_card(s, i) + "\n\n"

    # Source Performance
    sources = scan_info.get("sources", {}) if scan_info else {}
    active = {k: v for k, v in sources.items() if v > 0}
    if active:
        msg += "\U0001f4ca Source Performance:\n"
        for k, v in sorted(active.items(), key=lambda x: -x[1]):
            msg += f"  {k}: {v} items\n"

    msg += "\nBest regards,\n"
    msg += "ScholarSpace-ships \u2014 AI Scholarship Intelligence\n"
    return msg

def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        print("Telegram skipped: not configured")
        return False
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    chunks = []
    remaining = text
    while len(remaining) > 4000:
        split_at = remaining.rfind("\n", 0, 4000)
        chunks.append(remaining[:split_at if split_at > 0 else 4000])
        remaining = remaining[split_at+1:] if split_at > 0 else remaining[4000:]
    chunks.append(remaining)
    ok = True
    for chunk in chunks:
        try:
            data = json.dumps({"chat_id": TG_CHAT, "text": chunk}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=15)
            if resp.status == 200:
                print("Telegram message sent")
            else:
                print(f"Telegram HTTP {resp.status}")
                ok = False
        except Exception as e:
            print(f"Telegram error: {e}")
            ok = False
    return ok

def send_email(xlsx_path, scholarships, scan_info=None):
    if not BREVO_KEY or not TO_EMAIL:
        print("Email skipped: not configured")
        return False
    try:
        import base64, pathlib

        b64 = ""
        filename = ""
        if xlsx_path and os.path.exists(xlsx_path):
            b64 = base64.b64encode(open(xlsx_path, "rb").read()).decode()
            filename = pathlib.Path(xlsx_path).name

        date_str = now_libya().strftime("%A, %B %d, %Y")
        time_str = now_libya().strftime("%I:%M %p UTC")
        all_count = scan_info.get("all_count", 0) if scan_info else 0
        source_count = scan_info.get("source_count", 0) if scan_info else 0

        def scholarship_card_html(s, i):
            score = s.get("final_score", s.get("score", 0))
            if score >= 85:
                badge = '<span style="background:#16a34a;color:white;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold">STRONG MATCH</span>'
            elif score >= 75:
                badge = '<span style="background:#2563eb;color:white;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold">GOOD MATCH</span>'
            else:
                badge = '<span style="background:#d97706;color:white;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:bold">REVIEW</span>'

            university = extract_uni(s)
            country = s.get("country", "") or "Open/Global"
            funding = s.get("funding", s.get("funding_type", "Unknown"))
            if not funding or funding == "Unknown":
                funding = "Check listing"
            level = s.get("level", "") or "Check listing"
            deadline = s.get("deadline", "") or "Check listing"
            url = s.get("url", "")
            source = s.get("source", "unknown")

            # IELTS status
            ielts = s.get("english_requirement", "")
            if ielts == "not_required" or s.get("no_ielts"):
                ielts_html = '<span style="color:#16a34a;font-weight:bold">&#10003; Not Required</span>'
            elif ielts == "required":
                ielts_html = '<span style="color:#dc2626">&#10007; Required</span>'
            else:
                ielts_html = '<span style="color:#d97706">? Verify listing</span>'

            # Why it matches
            why_html = ""
            if s.get("why"):
                why_items = ", ".join(s.get("why", [])[:3])
                why_html = f'<tr><td style="padding:6px 8px;font-weight:bold;color:#555;vertical-align:top;width:120px">Why it fits</td><td style="padding:6px 8px">{why_items}</td></tr>'

            return f'''
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #d0d0d0;border-radius:6px;margin:14px 0;font-family:Arial,Helvetica,sans-serif">
        <tr><td style="padding:14px 16px 10px;border-bottom:1px solid #e0e0e0">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-size:16px;font-weight:bold;color:#0d1b2a">{_esc(s.get("title", "Unknown"))}</td>
            <td style="text-align:right">{badge}</td>
          </tr></table>
        </td></tr>
        <tr><td style="padding:10px 16px">
          <table width="100%" cellpadding="4" cellspacing="0" style="font-size:13px;color:#333">
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top;width:120px">University</td><td style="padding:4px 8px;color:#111;font-weight:bold">{_esc(university or "Check listing")}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Country</td><td style="padding:4px 8px;color:#111">{_esc(country)}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Level</td><td style="padding:4px 8px;color:#111">{_esc(level)}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Funding</td><td style="padding:4px 8px;color:#111;font-weight:bold">{_esc(funding)}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Deadline</td><td style="padding:4px 8px;color:#111">{_esc(deadline)}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Match Score</td><td style="padding:4px 8px;color:#111"><strong>{score}%</strong></td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">Source</td><td style="padding:4px 8px;color:#111">{_esc(source)}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold;color:#555;vertical-align:top">IELTS/TOEFL</td><td style="padding:4px 8px">{ielts_html}</td></tr>
            {why_html}
          </table>
        </td></tr>
        <tr><td style="padding:0 16px 14px">
          <a href="{_esc(url)}" style="display:inline-block;background:#2563eb;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:bold;font-size:13px">Apply for this scholarship &rarr;</a>
        </td></tr>
      </table>'''

        # Source Performance
        sources = scan_info.get("sources", {}) if scan_info else {}
        active = {k: v for k, v in sources.items() if v > 0}
        source_html = ""
        if active:
            rows = "".join([f'<tr><td style="padding:4px 8px;color:#333">{k}</td><td style="padding:4px 8px;color:#111;font-weight:bold;text-align:right">{v}</td></tr>' for k, v in sorted(active.items(), key=lambda x: -x[1])])
            source_html = f'''
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;margin:16px 0;font-family:Arial,Helvetica,sans-serif">
        <tr><td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-weight:bold;color:#111;font-size:13px">\U0001f4ca Source Performance Report</td></tr>
        <tr><td style="padding:6px 12px">
          <table width="100%" cellpadding="2" cellspacing="0" style="font-size:12px">
            <tr style="background:#f3f4f6"><td style="padding:4px 8px;font-weight:bold;color:#555">Source</td><td style="padding:4px 8px;font-weight:bold;color:#555;text-align:right">Items</td></tr>
            {rows}
          </table>
        </td></tr>
      </table>'''

        # Build cards
        cards_html = "".join([scholarship_card_html(s, i) for i, s in enumerate(scholarships)])

        html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f7f7f7;font-family:Arial,Helvetica,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f7f7f7">
    <tr><td align="center" style="padding:24px 12px">
      <table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #e0e0e0">
        <tr><td style="padding:22px 28px 10px;border-bottom:2px solid #111">
          <span style="font-size:20px;font-weight:bold;color:#111;letter-spacing:1px">SCHOLARSPACE-SHIPS</span>
          <span style="font-size:11px;color:#888;letter-spacing:2px;margin-left:10px">AI SCHOLARSHIP INTELLIGENCE</span>
        </td></tr>
        <tr><td style="padding:18px 28px 0">
          <p style="font-size:12px;color:#555;margin:0">{_esc(date_str)} \u00b7 {_esc(time_str)} \u00b7 Scan #1</p>
          <p style="font-size:16px;color:#111;margin:14px 0 0;line-height:1.6">
            This cycle we reviewed <b>{all_count:,} scholarships</b> across {source_count} sources.
            <b>{len(scholarships)} new match{'es' if len(scholarships) != 1 else ''}</b> passed all filters.
          </p>
        </td></tr>
        <tr><td style="padding:6px 28px 20px">
          {cards_html}
          {source_html}
        </td></tr>
        <tr><td style="padding:16px 28px 20px;border-top:1px solid #e0e0e0">
          <p style="font-size:13px;color:#333;margin:0;line-height:1.6">
            <b>About the workbook:</b> The attached Excel file contains all scholarship details, match scores, and application links.
          </p>
          <p style="font-size:14px;color:#111;margin:16px 0 0;line-height:1.6">
            The next scan is at <b>06:00 Libya time tomorrow</b>.
          </p>
          <p style="font-size:14px;color:#111;margin:16px 0 0;line-height:1.6">
            Best regards,<br>
            <b>ScholarSpace-ships</b><br>
            <span style="font-size:12px;color:#888">AI-Powered Scholarship Intelligence \u2014 always verify details before applying.</span>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>'''

        # Text version
        text_body = f"SCHOLARSPACE-SHIPS \u2014 AI Scholarship Intelligence\n"
        text_body += f"{date_str} \u00b7 {time_str} \u00b7 Scan #1\n\n"
        text_body += f"This cycle we reviewed {all_count:,} scholarships across {source_count} sources. {len(scholarships)} matches found.\n\n"
        for i, s in enumerate(scholarships):
            score = s.get("final_score", s.get("score", 0))
            text_body += f"{'*' if score >= 85 else '+'} {'STRONG' if score >= 85 else 'GOOD' if score >= 75 else 'REVIEW'} MATCH \u2014 {i+1}\n"
            text_body += f"  Scholarship: {s.get('title', 'Unknown')}\n"
            text_body += f"  University: {extract_uni(s) or 'Check listing'}\n"
            text_body += f"  Country: {s.get('country', 'Open/Global')}\n"
            text_body += f"  Level: {s.get('level', 'Check listing')}\n"
            text_body += f"  Funding: {s.get('funding', 'Check listing')}\n"
            text_body += f"  Deadline: {s.get('deadline', 'Check listing')}\n"
            text_body += f"  Match Score: {score}%\n"
            text_body += f"  Source: {s.get('source', 'unknown')}\n"
            text_body += f"  Apply: {s.get('url', '')}\n\n"

        payload = {
            "sender": {"email": "wemekenterprise.ly@gmail.com", "name": "ScholarSpace-ships"},
            "to": [{"email": TO_EMAIL}],
            "subject": f"SCHOLARSPACE-SHIPS: {len(scholarships)} Fresh Match{'es' if len(scholarships)!=1 else ''} Found \u2014 {date_str}",
            "textContent": text_body,
            "htmlContent": html,
        }
        if b64 and filename:
            payload["attachment"] = [{"content": b64, "name": filename, "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}]

        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode(),
            headers={"api-key": BREVO_KEY, "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
