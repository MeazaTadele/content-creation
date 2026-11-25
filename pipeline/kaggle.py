"""Run a batch of GPU work on Kaggle through the official CLI (decision 5).

1. write job.json + input files into a folder and publish it as a private Kaggle dataset version
2. push the stage's script kernel (kaggle/<stage>/run.py) with that dataset attached, on GPU T4 x2
3. poll its status until it finishes or times out
4. download the outputs; each unit has its own result file, so a job that dies part-way keeps
   every unit it finished (per-unit recovery, decision 23)

Long jobs are not retried like API calls: a failed or missing unit simply stays missing and the
next run sends only those units again; the video stage falls back to Ken Burns meanwhile.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .config import ROOT
from .stages.base import say

POLL_SEC = 60
DEFAULT_TIMEOUT = 3 * 3600


class KaggleError(RuntimeError):
    pass


def username() -> str:
    u = os.environ.get("KAGGLE_USERNAME", "").strip()
    if not u:
        raise KaggleError("KAGGLE_USERNAME is not set (see .env.example)")
    return u


def _cli(*args: str, timeout: int = 600) -> str:
    if not shutil.which("kaggle"):
        raise KaggleError("the kaggle command is not installed: pip install kaggle")
    env = dict(os.environ)
    if env.get("KAGGLE_KEY"):
        # legacy username + key: sent as Basic auth, which a header-injecting proxy can fill in
        env.pop("KAGGLE_API_TOKEN", None)
    p = subprocess.run(["kaggle", *args], capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0:
        raise KaggleError(f"kaggle {' '.join(args[:2])} failed: {(p.stderr or p.stdout).strip()[:400]}")
    return p.stdout


def _publish_inputs(stage: str, folder: Path) -> str:
    ds_id = f"{username()}/heritage-{stage}-inputs"
    (folder / "dataset-metadata.json").write_text(json.dumps(
        {"title": f"heritage {stage} inputs", "id": ds_id, "licenses": [{"name": "CC0-1.0"}]}))
    try:
        _cli("datasets", "version", "-p", str(folder), "-m", f"job {time.strftime('%Y%m%dT%H%M%S')}",
             "--dir-mode", "zip")
    except KaggleError as first:
        # a dataset that doesn't exist yet comes back as 403 or 404 depending on the endpoint: create it
        try:
            _cli("datasets", "create", "-p", str(folder), "--dir-mode", "zip")  # private by default
        except KaggleError as second:
            raise KaggleError(f"{first}\nand creating it failed too: {second}") from None
    return ds_id


def _wait_for_dataset(ds_id: str, timeout: int = 900) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if "ready" in _cli("datasets", "status", ds_id).lower():
                return
        except KaggleError:
            pass  # a brand-new dataset answers 403 for a short while before it exists everywhere
        time.sleep(15)
    raise KaggleError(f"dataset {ds_id} was not ready after {timeout} s")


def run_job(stage: str, units: list[dict], files: dict[str, Path], timeout: int = DEFAULT_TIMEOUT,
            settings: dict | None = None, gpu: bool = True, slug: str | None = None) -> tuple[str, Path]:
    """Run one batch job. Returns (job_id, folder holding the downloaded results)."""
    user = username()
    kernel_src = ROOT / "kaggle" / stage
    if not (kernel_src / "run.py").exists():
        raise KaggleError(f"no Kaggle script for stage '{stage}' at {kernel_src}/run.py")
    work = Path(tempfile.mkdtemp(prefix=f"kaggle-{stage}-"))
    inputs = work / "inputs"
    inputs.mkdir()
    for name, src in files.items():
        shutil.copy2(src, inputs / name)
    (inputs / "job.json").write_text(json.dumps({"stage": stage, "units": units, "settings": settings or {}},
                                                ensure_ascii=False, indent=1))
    say(f"  kaggle: uploading {len(units)} units ({len(files)} files)")
    ds_id = _publish_inputs(stage, inputs)
    _wait_for_dataset(ds_id)

    kernel = work / "kernel"
    kernel.mkdir()
    shutil.copy2(kernel_src / "run.py", kernel / "run.py")
    slug = slug or (f"heritage-{stage}" + ("" if gpu else "-cpu"))
    (kernel / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{slug}", "title": slug, "code_file": "run.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": gpu, "enable_internet": True,
        "dataset_sources": [ds_id], "competition_sources": [], "kernel_sources": [], "model_sources": [],
    }))
    say(f"  kaggle: pushing {user}/{slug} on " + ("GPU T4 x2" if gpu else "CPU (no GPU queue)"))
    push = ["kernels", "push", "-p", str(kernel), "-t", str(timeout)]
    if gpu:
        push += ["--accelerator", "NvidiaTeslaT4"]
    _cli(*push)
    job_id = f"{user}/{slug}@{time.strftime('%Y%m%dT%H%M%S')}"

    t0 = time.time()
    status = ""
    while time.time() - t0 < timeout + 600:
        time.sleep(POLL_SEC)
        out = _cli("kernels", "status", f"{user}/{slug}").lower()
        status = next((s for s in ("complete", "error", "cancel", "running", "queued") if s in out), out.strip())
        say(f"  kaggle: {status} ({int(time.time() - t0)} s)")
        if status in ("complete", "error", "cancel"):
            break
    results = work / "results"
    results.mkdir()
    try:
        _cli("kernels", "output", f"{user}/{slug}", "-p", str(results), timeout=1800)
    except KaggleError as e:
        say(f"  kaggle: could not download outputs: {e}")
    if status != "complete":
        say(f"  kaggle: job ended as '{status}'; finished units are kept, the rest stay missing")
    return job_id, results


def read_result(results: Path, unit_key: str) -> dict | None:
    f = results / f"{unit_key}.result.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))
