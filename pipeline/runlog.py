"""runs.jsonl: one line per real model call (or per attempt). Cache hits write nothing here."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone

from .config import RUNS_LOG

EAT = timezone(timedelta(hours=3))
_RUN_ID: str | None = None


def run_id() -> str:
    global _RUN_ID
    if _RUN_ID is None:
        _RUN_ID = "r_" + datetime.now(EAT).strftime("%Y%m%dT%H%M%S")
    return _RUN_ID


def now_iso() -> str:
    return datetime.now(EAT).isoformat(timespec="seconds")


def append(record: dict) -> None:
    line = {"ts": now_iso(), "run_id": run_id(), **record}
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_all() -> list[dict]:
    if not RUNS_LOG.exists():
        return []
    out = []
    with open(RUNS_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def monotonic() -> float:
    return time.monotonic()
