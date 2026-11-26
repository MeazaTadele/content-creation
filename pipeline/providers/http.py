"""Small HTTP helper shared by API providers: timeouts, error classification, no secrets in errors."""
from __future__ import annotations

import requests

from ..calls import FatalError, RetryableError, classify_http

TIMEOUT = (10, 180)  # connect, read seconds


def post(url: str, *, headers: dict, json: dict | None = None, data=None, files=None) -> requests.Response:
    try:
        r = requests.post(url, headers=headers, json=json, data=data, files=files, timeout=TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as e:
        raise RetryableError(f"{type(e).__name__}: network problem") from None
    if r.status_code >= 400:
        raise classify_http(r.status_code, r.text, r.headers.get("Retry-After"))
    return r


def get(url: str, *, headers: dict, params: dict | None = None) -> requests.Response:
    try:
        r = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as e:
        raise RetryableError(f"{type(e).__name__}: network problem") from None
    if r.status_code >= 400:
        raise classify_http(r.status_code, r.text, r.headers.get("Retry-After"))
    return r


def require_env(name: str, hint: str) -> str:
    import os
    v = os.environ.get(name, "").strip()
    if not v:
        raise FatalError(f"{name} is not set. {hint}")
    return v
