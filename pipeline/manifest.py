"""outputs/manifest.json: what was generated, from which fingerprint, and what was measured.

Written only by the pipeline, always atomically, and updated per unit, so a crash or a
timeout part-way through a stage keeps every unit that finished.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import atomic
from .config import MANIFEST_PATH, ROOT


class Manifest:
    def __init__(self, path: Path = MANIFEST_PATH):
        self.path = path
        self.data = {"units": {}, "stage_versions": {}, "stage_sources": {}, "measured": {}}
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            for k in self.data:
                self.data[k].update(loaded.get(k, {}))

    # units -------------------------------------------------------------
    def key(self, stage: str, unit: str) -> str:
        return f"{stage}/{unit}"

    def get(self, stage: str, unit: str) -> dict | None:
        return self.data["units"].get(self.key(stage, unit))

    def is_fresh(self, stage: str, unit: str, fp: str) -> bool:
        """A cache hit: same fingerprint, and the output file is still there."""
        e = self.get(stage, unit)
        if not e or e.get("fingerprint") != fp:
            return False
        out = e.get("output")
        return bool(out) and (ROOT / out).exists()

    def put(self, stage: str, unit: str, entry: dict) -> None:
        self._update("units", self.key(stage, unit), entry)

    # measured values (timing, loudness, error rates) -------------------
    def measure(self, name: str, value) -> None:
        self._update("measured", name, value)

    def _update(self, section: str, key: str, value) -> None:
        """Re-read the file and change only this one entry, so two runs at once (for example a long
        Kaggle job and a picture stage) never overwrite each other's records."""
        self._reload()
        self.data[section][key] = value
        atomic.write_json(self.path, self.data)

    def _reload(self) -> None:
        if self.path.exists():
            disk = json.loads(self.path.read_text(encoding="utf-8"))
            for k in self.data:
                self.data[k].update(disk.get(k, {}))

    def save(self) -> None:
        self._reload_keep_sources()
        atomic.write_json(self.path, self.data)

    def _reload_keep_sources(self) -> None:
        mine = dict(self.data["stage_sources"])
        self._reload()
        self.data["stage_sources"].update(mine)
