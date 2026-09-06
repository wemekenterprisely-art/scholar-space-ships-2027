"""
scholarshipdb.py — ScholarshipDB public JSON API.

Endpoint: https://www.scholarshipdb.net/api/scholarships?query=<q>&page=<n>
Some networks/CA stores reject the certificate; a retry with an unverified
context keeps the source alive on GitHub runners and local dev boxes alike.
"""

import json
import ssl
import urllib.parse
import urllib.request

QUERIES = ["fully funded", "developing countries", "no ielts"]

_API = "https://www.scholarshipdb.net/api/scholarships?query={q}&page={page}"


def _fetch_json(url: str, timeout: int = 20) -> dict | None:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ScholarSpace-ships/2027"}
    last_err = None
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            last_err = e
    print(f"  [scholarshipdb] {url[:80]} failed: {last_err}")
    return None


def fetch() -> list[dict]:
    out = []
    seen = set()
    for q in QUERIES:
        for page in (1, 2):
            data = _fetch_json(_API.format(q=urllib.parse.quote(q), page=page))
            if not data:
                break
            items = data if isinstance(data, list) else data.get("results") or data.get("data") or []
            if not items:
                break
            for it in items:
                if not isinstance(it, dict):
                    continue
                title = it.get("title") or it.get("name") or ""
                url = it.get("url") or it.get("link") or ""
                if not title or url in seen:
                    continue
                seen.add(url)
                desc = " ".join(str(it.get(k, "")).strip() for k in
                                ("description", "summary", "details"))[:1200]
                out.append({
                    "title": title.strip(),
                    "url": url,
                    "source": "scholarshipdb",
                    "description": desc or title.strip(),
                    "published": None,
                    "deadline": it.get("deadline") or it.get("application_deadline"),
                })
    print(f"  [scholarshipdb] {len(out)} scholarships")
    return out