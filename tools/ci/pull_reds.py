"""Rewrite ci/baselines/known-reds.txt from a GitLab deep pipeline's test shards.

    python tools/ci/pull_reds.py <pipeline id>

Runs on a laptop with `glab` signed in. It reads every suite job's `ci-out/reds-*.txt` artifact,
so the list is exactly the reds that pipeline saw, on Linux and Windows.
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import cast

REPO = Path(__file__).resolve().parents[2]
PROJECT = "qmx-group1%2FQMX-project"
TIMEOUT_S = 300


def glab(path: str) -> bytes:
    exe = shutil.which("glab") or "glab"
    done = subprocess.run([exe, "api", path], capture_output=True, timeout=TIMEOUT_S, check=True)
    return done.stdout


def main(argv: list[str]) -> int:
    pipeline = argv[1]
    raw = glab(f"projects/{PROJECT}/pipelines/{pipeline}/jobs?per_page=100")
    jobs = cast("list[dict[str, object]]", json.loads(raw))
    reds: set[str] = set()
    shards = 0
    for job in jobs:
        if not str(job["name"]).startswith(("suite-", "tests-")):
            continue
        shards += 1
        archive = zipfile.ZipFile(
            io.BytesIO(glab(f"projects/{PROJECT}/jobs/{job['id']}/artifacts"))
        )
        for name in archive.namelist():
            if name.startswith("ci-out/reds-") and name.endswith(".txt"):
                text = archive.read(name).decode("utf-8")
                reds.update(line for line in text.splitlines() if line)
    header = (
        f"# Tests red on pipeline {pipeline} ({shards} shards). Key: system|unit|test id.\n"
        "# A red listed here does not block; any other red does. This list may only shrink.\n"
    )
    target = REPO / "ci" / "baselines" / "known-reds.txt"
    target.write_text(header + "".join(f"{r}\n" for r in sorted(reds)), "utf-8", newline="\n")
    print(f"{len(reds)} known reds from {shards} shards -> {target.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
