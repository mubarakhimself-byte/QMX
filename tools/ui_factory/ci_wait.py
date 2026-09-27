"""Wait for named GitHub checks on an exact SHA. A push is not success."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any

REQUIRED_CHECKS = ("Skylos", "QA Battery", "UI quality")


@dataclass
class CiWatch:
    available: bool
    sha: str
    conclusion: str
    detail: str
    simulated: bool
    matched: list[str]


def _gh(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return int(proc.returncode), (proc.stdout or "") + (proc.stderr or "")


def _rows_for_sha(rows: list[dict[str, Any]], sha: str) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = []
    for row in rows:
        head = str(row.get("headSha") or "")
        if head == sha or head.startswith(sha) or sha.startswith(head):
            matched.append(row)
    return matched


def _named_status(
    rows: list[dict[str, Any]], required: list[str]
) -> tuple[str, list[str], str]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("name") or "")
        by_name[name] = row
    found: list[str] = []
    missing: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    for need in required:
        row = by_name.get(need)
        if row is None:
            missing.append(need)
            continue
        found.append(need)
        conclusion = str(row.get("conclusion") or "")
        status = str(row.get("status") or "")
        if conclusion in {"failure", "cancelled", "timed_out"}:
            failed.append(need)
        elif conclusion != "success":
            pending.append(need + ":" + (conclusion or status or "queued"))
    if failed:
        return "failure", found, "failed: " + ",".join(failed)
    if missing:
        return "incomplete", found, "missing required checks: " + ",".join(missing)
    if pending:
        return "incomplete", found, "pending: " + ",".join(pending)
    return "success", found, "required checks green on candidate SHA"


def watch_sha(
    sha: str,
    *,
    branch: str,
    timeout_seconds: int,
    simulate_conclusion: str | None = None,
    required: list[str] | None = None,
    poll_seconds: int = 15,
) -> CiWatch:
    need = list(required or REQUIRED_CHECKS)
    if simulate_conclusion is not None:
        return CiWatch(
            available=True,
            sha=sha,
            conclusion="incomplete",
            detail="simulated orchestration cannot promote; live GitHub was not queried",
            simulated=True,
            matched=[],
        )
    if shutil.which("gh") is None:
        return CiWatch(
            available=False,
            sha=sha,
            conclusion="incomplete",
            detail="gh CLI missing; live CI wait not run",
            simulated=False,
            matched=[],
        )
    deadline = time.time() + max(1, timeout_seconds)
    last_detail = "no poll yet"
    while time.time() <= deadline:
        code, text = _gh(
            [
                "run",
                "list",
                "--commit",
                sha,
                "--json",
                "databaseId,name,conclusion,status,headSha",
                "--limit",
                "50",
            ]
        )
        if code != 0:
            return CiWatch(
                False, sha, "incomplete", text.strip() or "gh run list failed", False, []
            )
        try:
            rows = json.loads(text) if text.strip().startswith("[") else []
        except json.JSONDecodeError:
            rows = []
        if not isinstance(rows, list):
            rows = []
        typed = [row for row in rows if isinstance(row, dict)]
        matched_rows = _rows_for_sha(typed, sha)
        if not matched_rows:
            last_detail = "no GitHub runs for this exact SHA; push is not a pass"
        else:
            conclusion, found, detail = _named_status(matched_rows, need)
            last_detail = detail
            if conclusion in {"success", "failure"}:
                return CiWatch(True, sha, conclusion, detail, False, found)
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, max(1, remaining)))
    return CiWatch(
        True,
        sha,
        "incomplete",
        f"timed out after {timeout_seconds}s: {last_detail}",
        False,
        [],
    )


def parse_runs(text: str) -> list[dict[str, Any]]:
    data = json.loads(text)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []
