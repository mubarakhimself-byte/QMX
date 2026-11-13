"""Rewrite ci/baselines/known-reds.txt from a GitHub Actions deep run's test shards.

    python tools/ci/pull_reds.py <run id>

Runs on a laptop with `gh` signed in. It downloads every test shard's `ci-out-*` artifact and reads
its `reds-*.txt`, so the list is exactly the reds that run saw, on Linux and Windows. A shard that
did not finish leaves no reds file; it is named in the header and its reds are not listed.
`QMX_GITHUB_REPO` names another repository (default: the QMX home on GitHub). The local checkout
also has other GitHub remotes, so the repository is always passed to `gh` by name.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

REPO = Path(__file__).resolve().parents[2]
GITHUB_REPO = os.environ.get("QMX_GITHUB_REPO", "mubarakhimself-byte/QMX")
TEST_ARTIFACTS = ("ci-out-suite-", "ci-out-tests-")
TIMEOUT_S = 600


def gh(*args: str) -> str:
    exe = shutil.which("gh") or "gh"
    done = subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT_S,
        check=True,
    )
    return done.stdout


def shard_reds(folder: Path) -> list[str] | None:
    """The reds one shard's artifact folder lists, or None when that shard did not finish. A shard
    with nothing to run writes only its plan, which lists no files."""
    reds = sorted(folder.glob("reds-*.txt"))
    if reds:
        return [line for f in reds for line in f.read_text("utf-8").splitlines() if line]
    plans = sorted(folder.glob("plan-*.json"))
    if plans and all(not json.loads(p.read_text("utf-8"))["files"] for p in plans):
        return []
    return None


def known_reds_text(run_id: str, shards: dict[str, list[str] | None]) -> str:
    read = sorted(name for name, reds in shards.items() if reds is not None)
    missing = sorted(name for name, reds in shards.items() if reds is None)
    reds = sorted({r for found in shards.values() if found for r in found})
    lines = [
        f"Tests red on GitHub Actions run {run_id}. Key: system|unit|test id.",
        "A red listed here does not block; any other red does. This list may only shrink.",
        f"Shards read: {', '.join(read) or 'none'}.",
        "Shards that did not finish, so their reds are not listed: "
        f"{', '.join(missing) or 'none'}.",
    ]
    return "".join(f"# {line}\n" for line in lines) + "".join(f"{r}\n" for r in reds)


def main(argv: list[str]) -> int:
    run_id = argv[1]
    listing = json.loads(
        gh("api", f"repos/{GITHUB_REPO}/actions/runs/{run_id}/artifacts?per_page=100")
    )
    names = sorted(
        str(a["name"])
        for a in cast("list[dict[str, object]]", listing["artifacts"])
        if str(a["name"]).startswith(TEST_ARTIFACTS)
    )
    jobs = json.loads(gh("api", f"repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs?per_page=100"))
    # A test job is named "suite-linux 3"; its artifact is "ci-out-suite-linux-3". A job that never
    # uploaded one did not finish.
    shards: dict[str, list[str] | None] = {
        str(j["name"]).replace(" ", "-"): None
        for j in cast("list[dict[str, object]]", jobs["jobs"])
        if str(j["name"]).startswith(tuple(t.removeprefix("ci-out-") for t in TEST_ARTIFACTS))
    }
    with tempfile.TemporaryDirectory(prefix="qmx-reds-") as tmp:
        for name in names:
            gh("run", "download", run_id, "-R", GITHUB_REPO, "-n", name, "-D", f"{tmp}/{name}")
            shards[name.removeprefix("ci-out-")] = shard_reds(Path(tmp) / name)
    target = REPO / "ci" / "baselines" / "known-reds.txt"
    target.write_text(known_reds_text(run_id, shards), "utf-8", newline="\n")
    total = len({r for found in shards.values() if found for r in found})
    unfinished = sum(1 for reds in shards.values() if reds is None)
    print(f"{total} known reds from {len(shards) - unfinished} shards ({unfinished} unfinished)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
