"""notifier - optional Telegram / email delivery. No-op when secrets are unset."""
import json, os
from pathlib import Path

def telegram_message_summary(scan, matches):
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        return False
    try:
        import urllib.request
        text = f"ScholarSpace-ships scan done: {len(matches)} fresh scholarships (fetched {scan.get('fetched', 0)})."
        for m in matches[:8]:
            text += f"\n- {m['title'][:60]} -> {m.get('final_score')}/100 {m.get('url','')}"
        data = json.dumps({"chat_id": os.getenv("TELEGRAM_CHAT_ID"), "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
            data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        print("  Telegram failed:", e)
        return False

def send_email_report(xlsx_path, matches):
    if not (os.getenv("BREVO_API_KEY") and os.getenv("TO_EMAIL")):
        return False
    # Brevo Sendinblue API - attach xlsx
    try:
        import urllib.request
        import base64, mimetypes
        b64 = base64.b64encode(Path(xlsx_path).read_bytes()).decode()
        payload = {
            "sender": {"email": "scholar@space-ships.local", "name": "ScholarSpace-ships"},
            "to": [{"email": os.getenv("TO_EMAIL")}],
            "subject": f"ScholarSpace-ships: {len(matches)} fresh scholarships",
            "htmlContent": "<p>Fresh scholarship matches attached. Good luck!</p>",
            "attachment": [{"content": b64, "name": Path(xlsx_path).name, "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}],
        }
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode(),
            headers={"api-key": os.getenv("BREVO_API_KEY"), "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
        return True
    except Exception as e:
        print("  Email failed:", e)
        return False
