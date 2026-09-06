"""
CareerOps Structured Logger — enterprise observability
JSON + human-readable, per-module, with metrics hooks.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class CareerOpsFormatter(logging.Formatter):
    def format(self, record):
        # Human readable for console
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lvl = record.levelname
        msg = super().format(record)
        return f"[{ts}] {lvl:5} [{record.name}] {msg}"

def get_logger(name: str = "careerops", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    # Console
    h1 = logging.StreamHandler(sys.stdout)
    h1.setFormatter(CareerOpsFormatter("%(message)s"))
    logger.addHandler(h1)
    # File (jsonl)
    try:
        fh = logging.FileHandler(LOG_DIR / f"{name}.jsonl", encoding="utf-8")
        fh.setFormatter(logging.Formatter('%(message)s'))
        # wrap to json
        orig_emit = fh.emit
        def json_emit(rec):
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": rec.levelname,
                "logger": rec.name,
                "msg": rec.getMessage(),
                "module": rec.module,
            }
            if rec.exc_info and rec.exc_info[0]:
                payload["exc"] = logging.Formatter().formatException(rec.exc_info)
            fh.stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
            fh.flush()
        fh.emit = json_emit
        logger.addHandler(fh)
    except Exception:
        pass
    logger.propagate = False
    return logger

# Default
log = get_logger("careerops")

def log_scan_event(event: str, **kwargs):
    """Structured scan event for dashboard/metrics."""
    try:
        data = {"event": event, **kwargs, "ts": datetime.now(timezone.utc).isoformat()}
        # write to scan_events.jsonl
        p = LOG_DIR / "scan_events.jsonl"
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass
    log.info(f"{event} | " + " ".join(f"{k}={v}" for k, v in kwargs.items()))
