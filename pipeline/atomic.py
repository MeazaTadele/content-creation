"""Atomic file writes: a crash never leaves a half-written output behind."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def tmp_path_for(final: Path) -> Path:
    """A temporary path in the same folder, so os.replace is atomic."""
    final.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=final.stem + ".", suffix=".tmp" + final.suffix, dir=final.parent)
    os.close(fd)
    return Path(name)


def commit(tmp: Path, final: Path) -> Path:
    """Move a finished temporary file into place."""
    if not tmp.exists() or tmp.stat().st_size == 0:
        raise RuntimeError(f"refusing to commit empty output {tmp}")
    os.replace(tmp, final)
    return final


def write_bytes(final: Path, data: bytes) -> Path:
    tmp = tmp_path_for(final)
    tmp.write_bytes(data)
    return commit(tmp, final)


def write_json(final: Path, obj) -> Path:
    tmp = tmp_path_for(final)
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
    return commit(tmp, final)
