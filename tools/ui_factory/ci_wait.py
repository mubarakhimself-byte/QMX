"""Wait for GitHub checks on a SHA. A push is not success."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class CiWatch:
    available: bool
    sha: str
    conclusion: str
    detail: str
    simulated: bool


def _gh(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return int(proc.returncode), (proc.stdout or "") + (proc.stderr or "")


def watch_sha(
    sha: str,
    *,
    branch: str,
    timeout_seconds: int,
    simulate_conclusion: str | None = None,
) -> CiWatch:
    if simulate_conclusion is not None:
        return CiWatch(
            available=True,
            sha=sha,
            conclusion=simulate_conclusion,
            detail="simulated orchestration; live GitHub was not queried",
            simulated=True,
        )
    if shutil.which("gh") is None:
        return CiWatch(
            available=False,
            sha=sha,
            conclusion="incomplete",
            detail="gh CLI missing; live CI wait not run",
            simulated=False,
        )
    code, text = _gh(
        [
            "run",
            "list",
            "--commit",
            sha,
            "--branch",
            branch,
            "--json",
            "databaseId,name,conclusion,status,headSha",
            "--limit",
            "20",
        ]
    )
    if code != 0:
        return CiWatch(
            available=False,
            sha=sha,
            conclusion="incomplete",
            detail=text.strip() or "gh run list failed",
            simulated=False,
        )
    try:
        rows = json.loads(text) if text.strip().startswith("[") else []
    except json.JSONDecodeError:
        rows = []
    if not isinstance(rows, list) or not rows:
        return CiWatch(
            available=True,
            sha=sha,
            conclusion="incomplete",
            detail="no GitHub runs for this SHA yet; push is not a pass",
            simulated=False,
        )
    conclusions = [
        str(r.get("conclusion") or r.get("status") or "")
        for r in rows
        if isinstance(r, dict)
    ]
    if any(c in {"failure", "cancelled", "timed_out"} for c in conclusions):
        return CiWatch(True, sha, "failure", json.dumps(rows), False)
    if all(c == "success" for c in conclusions):
        return CiWatch(True, sha, "success", json.dumps(rows), False)
    return CiWatch(
        True,
        sha,
        "incomplete",
        f"runs not finished ({timeout_seconds}s budget recorded): {conclusions}",
        False,
    )


def parse_runs(text: str) -> list[dict[str, Any]]:
    data = json.loads(text)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []
