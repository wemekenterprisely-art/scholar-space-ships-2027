"""
State Sync — persistent memory for GitHub Actions runs.

GitHub Actions runners are ephemeral: the output/ directory is wiped
after every run, so dedup, application tracking, learning data, and the
evolution brain were lost between scans. This module syncs the scanner's
state files to a state/ folder in the repo via the GitHub Contents API,
giving the system real memory that survives from run to run.

Only active inside GitHub Actions (GITHUB_ACTIONS env var set). Locally
it is a no-op, so local scans keep working unchanged.
"""

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"

# (local file under output/, repo path under state/)
STATE_FILES = [
    "all_scholarships.json",
    "fresh_matches_history.json",
    "applications.json",
    "seen_urls.json",
    "daily_log.json",
    "scan_history.json",
    "metrics.json",
    "health.json",
]

_HEADERS = {
    "User-Agent": "scholar-space-ships-state-sync",
    "Accept": "application/vnd.github+json",
}


def _api() -> tuple[str, str] | None:
    """Return (api contents base url, token) if running in GitHub Actions."""
    ga = os.getenv("GITHUB_ACTIONS")
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not ga or not token or not repo:
        print(f"  [state] disabled: GITHUB_ACTIONS={ga!r} GITHUB_TOKEN={'set' if token else 'MISSING'} GITHUB_REPOSITORY={repo!r}")
        return None
    return f"https://api.github.com/repos/{repo}/contents", token


def _get_sha(base: str, token: str, url: str) -> str | None:
    """Fetch the current blob SHA of a repo file (None if it doesn't exist)."""
    try:
        req = urllib.request.Request(url, headers={**_HEADERS, "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("sha")
    except Exception:
        return None


def download_state() -> int:
    """Fetch state files from the repo's state/ folder into output/."""
    api = _api()
    if not api:
        return 0
    base, token = api
    restored = 0
    for rel in STATE_FILES:
        try:
            url = f"{base}/state/{rel}"
            req = urllib.request.Request(url, headers={**_HEADERS, "Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = base64.b64decode(data.get("content", ""))
            dest = OUTPUT_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            restored += 1
        except Exception as e:
            print(f"  [state] download {rel}: {e}")
    print(f"[state] restored {restored}/{len(STATE_FILES)} state files")
    return restored


def upload_state() -> int:
    """Upload local state files to the repo's state/ folder."""
    api = _api()
    if not api:
        return 0
    base, token = api
    uploaded = 0
    for rel in STATE_FILES:
        src = OUTPUT_DIR / rel
        if not src.exists():
            continue
        try:
            url = f"{base}/state/{rel}"
            body: dict = {
                "message": f"scholar: update {rel}",
                "content": base64.b64encode(src.read_bytes()).decode("ascii"),
            }
            sha = _get_sha(base, token, url)
            if sha:
                body["sha"] = sha
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                method="PUT",
                headers={**_HEADERS, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status in (200, 201):
                    uploaded += 1
        except Exception as e:
            print(f"  [state] upload {rel}: {e}")
    print(f"[state] uploaded {uploaded} state files")
    return uploaded


PROBE_FILES = ["source_probe.md", "source_probe.json"]


def upload_probe() -> int:
    """Upload the latest source-probe report (output/source_probe.*) to state/."""
    api = _api()
    if not api:
        return 0
    base, token = api
    uploaded = 0
    for rel in PROBE_FILES:
        src = OUTPUT_DIR / rel
        if not src.exists():
            continue
        try:
            url = f"{base}/state/{rel}"
            body: dict = {
                "message": f"scholar: source probe report ({rel})",
                "content": base64.b64encode(src.read_bytes()).decode("ascii"),
            }
            sha = _get_sha(base, token, url)
            if sha:
                body["sha"] = sha
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                method="PUT",
                headers={**_HEADERS, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status in (200, 201):
                    uploaded += 1
        except Exception as e:
            print(f"  [state] upload {rel}: {e}")
    print(f"[state] uploaded {uploaded} probe report files")
    return uploaded


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "download":
        sys.exit(0 if download_state() else 0)
    elif cmd == "upload":
        sys.exit(0 if upload_state() else 0)
    elif cmd == "upload-probe":
        sys.exit(0 if upload_probe() else 0)
    else:
        print("Usage: python state_sync.py [download|upload|upload-probe]")
        sys.exit(2)