"""Shared fetch helpers - stdlib only, no external deps for fetchers."""
import json, re, urllib.request, email.utils
from datetime import datetime
from html import unescape

UA = "Mozilla/5.0 (X11; Linux x86_64) ScholarSpace-ships/2027 (+github.com/wemekenterprisely-art)"

def get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def get_json(url: str, timeout: int = 15):
    return json.loads(get(url, timeout))

def parse_rss(xml: str) -> list[dict]:
    """Minimal RSS/Atom parser - no external deps."""
    items = []
    for chunk in re.split(r"</item>|</entry>", xml):
        if "<item" not in chunk and "<entry" not in chunk:
            continue
        if "<title>" not in chunk:
            continue
        t = _tag(chunk, "title")
        desc = _tag(chunk, "description") or _tag(chunk, "summary")
        link = _tag(chunk, "link", attr="href") or _tag(chunk, "link")
        pub = _tag(chunk, "pubDate") or _tag(chunk, "published") or _tag(chunk, "updated")
        if not t or not link:
            continue
        items.append({"title": unescape(t).strip(), "description": unescape(desc or "").strip(),
                      "url": unescape(link).strip(), "posted_at": pub})
    return items

def _tag(xml: str, name: str, attr: str | None = None) -> str:
    if attr:
        m = re.search(r"<" + name + r'[^>]*' + attr + r'="([^"]*)"', xml)
        return m.group(1) if m else ""
    m = re.search(r"<" + name + r"[^>]*>(.*?)</" + name + r">", xml, re.S)
    if not m:
        return ""
    return re.sub(r"<![CDATA[|]]>", "", m.group(1)).strip()

def strip_html(text: str, limit: int = 2000) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text[:limit]

def parse_date(s: str) -> str | None:
    """Best-effort ISO date parse. Returns ISO date string or None."""
    if not s:
        return None
    try:
        if re.match(r"\d{4}-\d{2}-\d{2}", s):
            return s[:10]
        dt = email.utils.parsedate_to_datetime(s)
        return dt.date().isoformat()
    except Exception:
        m = re.search(r"(20\d{2})[-/.]?(\d{1,2})[-/.]?(\d{1,2})", s)
        if m:
            y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            try:
                datetime(int(y), int(mo), int(d)); return f"{y}-{mo}-{d}"
            except Exception:
                return None
        m2 = re.search(r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(20\d{2})", s, re.I)
        if m2:
            months = ["january","february","march","april","may","june","july","august","september","october","november","december"]
            mo = months.index(m2.group(2).lower()) + 1
            return f"{m2.group(3)}-{mo:02d}-{int(m2.group(1)):02d}"
    return None