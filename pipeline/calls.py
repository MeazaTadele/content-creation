"""The one wrapper every synchronous model call goes through.

It times the call, retries transient failures (timeouts, HTTP 429, 5xx) with exponential
backoff and jitter, fails fast on other errors, and writes one runs.jsonl line per attempt.
Only the last line of a call has "final": true, so failed attempts are never mistaken for
the result. Long-running Kaggle jobs do not use this wrapper; see log_job_unit().
"""
from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import runlog

MAX_ATTEMPTS = 4
BASE_DELAY = 2.0
MAX_DELAY = 60.0
RATE_LIMIT_DELAY = 65.0  # HTTP 429 without Retry-After: wait out a per-minute window (FAILURES.md F8)

# Patterns that must never reach the log, whatever a provider puts in an error message.
_SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"AQ\.[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)(xi-api-key|x-goog-api-key|api[_-]?key|token|key)([\"'=:\s]+)[A-Za-z0-9._\-]{16,}"),
]


def redact(text: str) -> str:
    for p in _SECRET_PATTERNS:
        text = p.sub(lambda m: (m.group(1) if m.lastindex and m.lastindex >= 1 else "") + "[REDACTED]", text)
    return text


class RetryableError(Exception):
    """A transient failure worth retrying (timeout, rate limit, server error)."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class FatalError(Exception):
    """A failure that retrying will not fix (bad request, bad key, unsupported input)."""


@dataclass
class CallResult:
    value: Any
    units: dict = field(default_factory=dict)  # e.g. {"chars": 120} or {"images": 1}
    model: str | None = None                   # the model actually served, if the API says


def classify_http(status: int, body: str, retry_after: str | None = None) -> Exception:
    msg = f"HTTP {status}: {redact(body[:300])}"
    if status == 429 or status >= 500 or status == 408:
        ra = None
        if retry_after:
            try:
                ra = float(retry_after)
            except ValueError:
                ra = None
        return RetryableError(msg, ra)
    return FatalError(msg)


def call_model(*, stage: str, unit: str, provider: str, model: str, params: dict,
               seed: int | None, fn: Callable[[], CallResult], fingerprint: str,
               output: str | None = None, price: Callable[[dict], float] | None = None,
               max_attempts: int = MAX_ATTEMPTS) -> CallResult:
    attempt = 0
    while True:
        attempt += 1
        t0 = time.monotonic()
        try:
            result = fn()
        except (RetryableError, FatalError, Exception) as exc:  # noqa: BLE001 - every failure is logged
            latency = int((time.monotonic() - t0) * 1000)
            retryable = isinstance(exc, RetryableError) or _looks_transient(exc)
            last = (not retryable) or attempt >= max_attempts
            runlog.append({
                "stage": stage, "unit": unit, "provider": provider, "model": model,
                "params": params, "seed": seed, "attempt": attempt, "status": "error",
                "final": last, "error": redact(f"{type(exc).__name__}: {exc}")[:500],
                "latency_ms": latency, "fingerprint": fingerprint,
            })
            if last:
                raise
            delay = getattr(exc, "retry_after", None)
            if delay is None and "429" in str(exc):
                delay = RATE_LIMIT_DELAY  # per-minute limits need about a minute, not a few seconds
            delay = delay or min(MAX_DELAY, BASE_DELAY * 2 ** (attempt - 1))
            time.sleep(delay + random.uniform(0, delay / 4))
            continue
        latency = int((time.monotonic() - t0) * 1000)
        cost = price(result.units) if price else 0.0
        runlog.append({
            "stage": stage, "unit": unit, "provider": provider, "model": result.model or model,
            "params": params, "seed": seed, "attempt": attempt, "status": "ok", "final": True,
            "latency_ms": latency, "units": result.units, "cost_usd": 0.0,
            "list_price_usd": round(cost, 6), "gpu_seconds": 0, "fingerprint": fingerprint,
            "output": output,
        })
        return result


def _looks_transient(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return any(k in name for k in ("timeout", "connectionerror", "connectionreset"))


def log_job_unit(*, stage: str, unit: str, provider: str, model: str, params: dict,
                 seed: int | None, status: str, latency_ms: int, gpu_seconds: float,
                 fingerprint: str, output: str | None, job_id: str, error: str | None = None,
                 list_price_usd: float = 0.0) -> None:
    """One runs.jsonl line per unit of a Kaggle batch job, from the job's own result file."""
    runlog.append({
        "stage": stage, "unit": unit, "provider": provider, "model": model, "params": params,
        "seed": seed, "attempt": 1, "status": status, "final": True, "latency_ms": latency_ms,
        "units": {}, "cost_usd": 0.0, "list_price_usd": round(list_price_usd, 6),
        "gpu_seconds": round(gpu_seconds, 1), "fingerprint": fingerprint, "output": output,
        "job_id": job_id, **({"error": redact(error)[:500]} if error else {}),
    })
