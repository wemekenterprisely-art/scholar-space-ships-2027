"""
ScholarSpace-ships Notifier - Professional Telegram + Email
"""
import json, os, urllib.request
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

def format_card(s, idx):
    score = s.get("final_score", s.get("score", 0))
    rec = get_recommendation(score)
    emoji = get_emoji(score)

    # Extract university from title if not in separate field
    university = s.get("university", s.get("institution", ""))
    if not university:
        # Try to extract from title (common patterns)
        import re
        title = s.get("title", "")
        patterns = [
            r"at\s+([\w\s]+(?:University|Institute|College))",
            r"([\w\s]+(?:University|Institute|College))",
        ]
        for p in patterns:
            m = re.search(p, title, re.I)
            if m:
                university = m.group(1).strip()
                break

    # Country
    country = s.get("country", "")
    if not country:
        country = "Open/Global"

    # Funding
    funding = s.get("funding", s.get("funding_type", "Unknown"))
    if not funding or funding == "Unknown":
        funding = "Check listing"

    # Level
    level = s.get("level", "")
    if not level or level == "Unknown":
        level = "Check listing"

    # Deadline
    deadline = s.get("deadline", "")
    if not deadline:
        deadline = "Check listing"

    # Clean URL
    url = s.get("url", "")

    lines = [
        f"{emoji} {idx+1}. {rec} ({score}/100)",
        "",
        f"\U0001f393 {s.get('title', 'Unknown')}",
    ]
    if university:
        lines.append(f"\U0001f3db\ufe0f {university}")
    lines.append("")
    lines.append(f"\U0001f30d \ud83d\udccc Country: {country}")
    lines.append(f"\U0001f4da \ud83d\udcdd Level: {level}")
    lines.append(f"\U0001f4b0 \ud83d\udcb0 Funding: {funding}")
    lines.append(f"\u23f0 \ud83d\udcc5 Deadline: {deadline}")
    lines.append(f"\U0001f4ca \ud83d\udcc8 Match: {score}%")
    lines.append(f"\U0001f4e6 \ud83d\udce6 Source: {s.get('source', 'unknown')}")

    # IELTS/TOEFL status
    ielts = s.get("english_requirement", "")
    if ielts == "not_required" or s.get("no_ielts"):
        lines.append("\u2705 No IELTS/TOEFL required")
    elif ielts == "required":
        lines.append("\u26a0\ufe0f IELTS/TOEFL required")
    else:
        lines.append("\U0001f50d IELTS/TOEFL status: verify")

    # Why it matches
    if s.get("why"):
        lines.append(f"\U0001f517 Why: {', '.join(s.get('why', [])[:3])}")

    lines.append(f"\U0001f517 Apply: {url}")
    return "\n".join(lines)

def build_telegram(scholarships, scan_info, stats):
    date = now_libya().strftime("%Y-%m-%d")
    time_str = now_libya().strftime("%I:%M %p Libya")
    scan_num = stats.get("total_scans", 0)
    all_count = scan_info.get("all_count", 0)
    source_count = scan_info.get("source_count", 0)

    msg = ""
    msg += f"\U0001f4cb \U0001f393 SCHOLARSPACE-SHIPS Daily Report - {date}\n"
    msg += "=" * 36 + "\n\n"
    msg += f"\U0001f4c5 Scan #{scan_num} | \U0001f552 {time_str}\n"
    msg += f"\U0001f50d Reviewed {all_count:,} scholarships across {source_count} sources\n\n"

    if not scholarships:
        msg += "\u2705 0 New Matches Found\n\n"
        msg += "\u274c No new scholarships passed all gates this cycle.\n"
        msg += "\U0001f6ab Gates: No IELTS/TOEFL | Libya eligible | MA+ level | Deadline valid\n"
    else:
        msg += f"\u2705 {len(scholarships)} New Match{'es' if len(scholarships)!=1 else ''} Found\n"
        msg += "-" * 36 + "\n\n"
        for i, s in enumerate(scholarships):
            msg += format_card(s, i) + "\n\n"

    msg += "-" * 36 + "\n"
    msg += f"\U0001f551 Next scan: 06:00 Libya time tomorrow\n"
    msg += "\U0001f4ac Best regards,\n"
    msg += "\U0001f393 ScholarSpace-ships - AI Scholarship Intelligence\n"
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

def send_email(xlsx_path, scholarships):
    if not BREVO_KEY or not TO_EMAIL:
        print("Email skipped: not configured")
        return False
    try:
        import base64, pathlib
        from datetime import datetime

        b64 = ""
        filename = ""
        if xlsx_path and os.path.exists(xlsx_path):
            b64 = base64.b64encode(open(xlsx_path, "rb").read()).decode()
            filename = pathlib.Path(xlsx_path).name

        date_str = now_libya().strftime("%A, %B %d, %Y")
        time_str = now_libya().strftime("%I:%M %p Libya time")

        # Build scholarship cards HTML
        cards_html = ""
        for i, s in enumerate(scholarships):
            score = s.get("final_score", s.get("score", 0))
            if score >= 85:
                badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:4px;font-size:12px">STRONG MATCH</span>'
            elif score >= 75:
                badge = '<span style="background:#2563eb;color:white;padding:2px 8px;border-radius:4px;font-size:12px">GOOD MATCH</span>'
            else:
                badge = '<span style="background:#d97706;color:white;padding:2px 8px;border-radius:4px;font-size:12px">REVIEW</span>'

            university = s.get("university", s.get("institution", ""))
            if not university:
                import re
                title = s.get("title", "")
                # Try multiple patterns
                patterns = [
                    r"at\s+([\w\s,]+(?:University|Institute|College|School)[\w\s]*)",
                    r"([\w\s,]+(?:University|Institute|College|School)[\w\s]*(?:of|at|in)[\w\s]*)",
                    r"(?:University|Institute|College)\s+of\s+([\w\s]+)",
                    r"([\w\s]+(?:University|Institute|College|School))",
                    r"(CSC|Chevening|Fulbright|DAAD|Erasmus|MEXT|Turkiye|Stipendium)\s+Scholarship",
                ]
                for p in patterns:
                    m = re.search(p, title, re.I)
                    if m:
                        university = m.group(1).strip() if m.lastindex else m.group(0).strip()
                        # Clean up common suffixes
                        university = re.sub(r"\s*\d{4}\s*$", "", university).strip()
                        break

            country = s.get("country", "") or "Open/Global"
            funding = s.get("funding", s.get("funding_type", "Unknown"))
            if not funding or funding == "Unknown":
                funding = "Check listing"
            level = s.get("level", "") or "Check listing"
            deadline = s.get("deadline", "") or "Check listing"
            url = s.get("url", "")

            cards_html += f'''
            <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;margin:16px 0;padding:20px;font-family:Arial,sans-serif">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                    <span style="font-size:16px;font-weight:bold;color:#111">{i+1}. {s.get("title", "Unknown")}</span>
                    {badge}
                </div>
                <table style="width:100%;font-size:13px;color:#333;border-collapse:collapse">
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555;width:120px">University</td><td style="padding:4px 8px">{university or "Check listing"}</td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Country</td><td style="padding:4px 8px">{country}</td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Level</td><td style="padding:4px 8px">{level}</td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Funding</td><td style="padding:4px 8px">{funding}</td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Deadline</td><td style="padding:4px 8px">{deadline}</td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Match Score</td><td style="padding:4px 8px"><strong>{score}%</strong></td></tr>
                    <tr><td style="padding:4px 8px;font-weight:bold;color:#555">Source</td><td style="padding:4px 8px">{s.get("source", "unknown")}</td></tr>'''

            # IELTS/TOEFL status
            ielts = s.get("english_requirement", "")
            if ielts == "not_required" or s.get("no_ielts"):
                cards_html += '<tr><td style="padding:4px 8px;font-weight:bold;color:#555">IELTS/TOEFL</td><td style="padding:4px 8px;color:#16a34a;font-weight:bold">Not Required</td></tr>'
            elif ielts == "required":
                cards_html += '<tr><td style="padding:4px 8px;font-weight:bold;color:#555">IELTS/TOEFL</td><td style="padding:4px 8px;color:#dc2626">Required</td></tr>'
            else:
                cards_html += '<tr><td style="padding:4px 8px;font-weight:bold;color:#555">IELTS/TOEFL</td><td style="padding:4px 8px;color:#d97706">Verify listing</td></tr>'

            # Why it matches
            if s.get("why"):
                cards_html += f'<tr><td style="padding:4px 8px;font-weight:bold;color:#555">Why it fits</td><td style="padding:4px 8px">{", ".join(s.get("why", [])[:3])}</td></tr>'

            cards_html += f'''
                </table>
                <div style="margin-top:12px">
                    <a href="{url}" style="display:inline-block;background:#2563eb;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:bold">Apply Now</a>
                </div>
            </div>'''

        html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif">
<div style="max-width:640px;margin:0 auto;padding:20px">
    <div style="background:#111;color:white;padding:20px;text-align:center;border-radius:8px 8px 0 0">
        <h1 style="margin:0;font-size:20px">SCHOLARSPACE-SHIPS</h1>
        <p style="margin:8px 0 0;font-size:12px;opacity:0.8">AI-Powered Scholarship Intelligence</p>
    </div>
    <div style="background:white;padding:20px;border-radius:0 0 8px 8px">
        <p style="color:#555;font-size:13px;margin:0">{date_str} &bull; {time_str}</p>
        <h2 style="color:#111;font-size:18px;margin:16px 0">{len(scholarships)} Fresh Scholarship Match{'es' if len(scholarships)!=1 else ''} Found</h2>
        {cards_html}
        <hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0">
        <p style="color:#555;font-size:12px;text-align:center">
            ScholarSpace-ships &mdash; AI Scholarship Intelligence<br>
            Next scan: 06:00 Libya time tomorrow
        </p>
    </div>
</div>
</body>
</html>'''

        text_body = f"ScholarSpace-ships: {len(scholarships)} fresh scholarships found\n\n"
        for i, s in enumerate(scholarships):
            score = s.get("final_score", s.get("score", 0))
            text_body += f"{i+1}. [{score}%] {s.get('title', 'Unknown')}\n"
            text_body += f"   {s.get('url', '')}\n\n"

        payload = {
            "sender": {"email": "wemekenterprise.ly@gmail.com", "name": "ScholarSpace-ships"},
            "to": [{"email": TO_EMAIL}],
            "subject": f"ScholarSpace-ships: {len(scholarships)} fresh scholarships found - {date_str}",
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
