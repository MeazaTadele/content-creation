"""Fingerprints: a hash of exactly the inputs a unit of work depends on (decision 10, option b)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(stage: str, stage_version: int, inputs: dict) -> str:
    """inputs may contain Path values; they are replaced by the hash of the file's bytes."""
    def resolve(v):
        if isinstance(v, Path):
            return {"file_sha256": file_sha256(v)}
        if isinstance(v, dict):
            return {k: resolve(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [resolve(x) for x in v]
        return v
    payload = {"stage": stage, "stage_version": stage_version, "inputs": resolve(inputs)}
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def short(fp: str) -> str:
    return fp[:8]
