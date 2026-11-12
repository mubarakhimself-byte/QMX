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
    read: list[str] = []
    missing: list[str] = []
    for job in jobs:
        name = str(job["name"])
        if not name.startswith(("suite-", "tests-")):
            continue
        finished = job["status"] == "success" or job.get("failure_reason") == "script_failure"
        if not finished:
            missing.append(f"{name} ({job['status']}, {job.get('failure_reason')})")
            continue
        read.append(name)
        archive = zipfile.ZipFile(
            io.BytesIO(glab(f"projects/{PROJECT}/jobs/{job['id']}/artifacts"))
        )
        for entry in archive.namelist():
            if entry.startswith("ci-out/reds-") and entry.endswith(".txt"):
                text = archive.read(entry).decode("utf-8")
                reds.update(line for line in text.splitlines() if line)
    lines = [
        f"Tests red on pipeline {pipeline}. Key: system|unit|test id.",
        "A red listed here does not block; any other red does. This list may only shrink.",
        f"Shards read: {', '.join(sorted(read)) or 'none'}.",
        "Shards that did not finish, so their reds are not listed: "
        + (", ".join(sorted(missing)) or "none")
        + ".",
    ]
    header = "".join(f"# {line}\n" for line in lines)
    target = REPO / "ci" / "baselines" / "known-reds.txt"
    target.write_text(header + "".join(f"{r}\n" for r in sorted(reds)), "utf-8", newline="\n")
    print(f"{len(reds)} known reds from {len(read)} shards ({len(missing)} unfinished)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
