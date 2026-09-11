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
    lines = [
        f"{emoji} {idx+1}. {rec} ({score}/100)",
        "",
        f"\U0001f393 {s.get('title', 'Unknown')}",
        f"\U0001f3db {s.get('university', s.get('institution', 'Unknown'))}",
        "",
        f"\U0001f30d Country: {s.get('country', 'Open/Global')}",
        f"\U0001f4da Level: {s.get('level', 'Not specified')}",
        f"\U0001f4b0 Funding: {s.get('funding_type', 'Not specified')}",
        f"\u23f0 Deadline: {s.get('deadline', 'Not specified')}",
        f"\U0001f4ca Match: {score}%",
        f"\U0001f4e6 Source: {s.get('source', 'unknown')}",
    ]
    if s.get("no_ielts"):
        lines.append("\u2705 No IELTS/TOEFL required")
    if s.get("why"):
        lines.append(f"\U0001f517 Why: {', '.join(s.get('why', [])[:3])}")
    lines.append(f"\U0001f517 Apply: {s.get('url', '')}")
    return "\n".join(lines)

def build_telegram(scholarships, scan_info, stats):
    date = now_libya().strftime("%Y-%m-%d")
    time_str = now_libya().strftime("%I:%M %p Libya")
    scan_num = stats.get("total_scans", 0)
    all_count = scan_info.get("all_count", 0)
    source_count = scan_info.get("source_count", 0)

    msg = ""
    msg += f"\U0001f4cb SCHOLARSPACE-SHIPS Daily Report - {date}\n"
    msg += "=" * 36 + "\n\n"
    msg += f"Scan #{scan_num} | {time_str}\n"
    msg += f"Reviewed {all_count:,} scholarships across {source_count} sources\n\n"

    if not scholarships:
        msg += "\u2705 0 New Matches Found\n\n"
        msg += "No new scholarships passed all gates this cycle.\n"
        msg += "Gates: No IELTS/TOEFL | Libya eligible | MA+ level | Deadline valid\n"
    else:
        msg += f"\u2705 {len(scholarships)} New Match{'es' if len(scholarships)!=1 else ''} Found\n"
        msg += "-" * 36 + "\n\n"
        for i, s in enumerate(scholarships):
            msg += format_card(s, i) + "\n\n"

    msg += "-" * 36 + "\n"
    msg += "Next scan: 06:00 Libya time tomorrow\n"
    msg += "Best regards,\n"
    msg += "ScholarSpace-ships - AI Scholarship Intelligence\n"
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
        b64 = ""
        if xlsx_path and os.path.exists(xlsx_path):
            import base64
            b64 = base64.b64encode(open(xlsx_path, "rb").read()).decode()
        payload = {
            "sender": {"email": "wemekenterprise.ly@gmail.com", "name": "ScholarSpace-ships"},
            "to": [{"email": TO_EMAIL}],
            "subject": f"ScholarSpace-ships: {len(scholarships)} fresh scholarships found",
            "htmlContent": "<p>Fresh scholarship matches attached. Good luck!</p>",
        }
        if b64:
            import pathlib
            payload["attachment"] = [{"content": b64, "name": pathlib.Path(xlsx_path).name, "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}]
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
