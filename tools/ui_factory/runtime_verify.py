"""Running-app verification. Unknown Reticle is incomplete, never a pass."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from ui_factory.evidence import CommandResult, sha256_text


class BrowserDriver(Protocol):
    def click_and_read(
        self, url: str, control: str, storage_key: str
    ) -> dict[str, Any]:
        ...


@dataclass
class RuntimeVerdict:
    kind: str
    verified: str
    reason: str
    served_revision: str
    health_ok: bool
    log: str


def check_health(url: str, expected_revision: str) -> tuple[bool, str, str]:
    """A listening port is not enough; require revision identity."""
    if not url.startswith(("http://", "https://")):
        return False, "", f"refused URL scheme: {url}"
    try:
        req = Request(url, method="GET")  # noqa: S310
        with urlopen(req, timeout=5) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
            status = int(resp.status)
    except (URLError, OSError, TimeoutError) as exc:
        return False, "", f"health fetch failed: {exc}"
    if status != 200:
        return False, "", f"health status {status}"
    revision = ""
    if "json" in url or body.lstrip().startswith("{"):
        try:
            payload = json.loads(body)
            if isinstance(payload, dict):
                revision = str(payload.get("revision") or payload.get("sha") or "")
        except json.JSONDecodeError:
            revision = ""
    if expected_revision and revision and revision != expected_revision:
        return False, revision, "served revision does not match candidate SHA"
    if expected_revision and not revision:
        # HTML apps may embed a meta revision.
        if expected_revision not in body:
            return False, "", "served document does not identify candidate SHA"
        revision = expected_revision
    return True, revision, "ok"


def classify_reticle(raw: Mapping[str, Any] | None, *, available: bool) -> str:
    if not available:
        return "missing"
    if raw is None:
        return "unknown"
    value = str(raw.get("verified") or raw.get("verdict") or "").lower()
    if value in {"yes", "no", "unknown"}:
        return value
    return "unknown"


def persistence_check(driver: BrowserDriver, url: str, control: str, key: str) -> str:
    """Click a control and require a persisted value after reload."""
    first = driver.click_and_read(url, control, key)
    if not first.get("changed"):
        return "dead-control"
    second = driver.click_and_read(url, "__reload__", key)
    if second.get("value") != first.get("value"):
        return "wrong-persisted-outcome"
    return "ok"


def command_from_verdict(verdict: RuntimeVerdict, cwd: Path) -> CommandResult:
    missing = verdict.verified == "missing"
    skipped = verdict.verified == "unknown" and "not run" in verdict.reason
    exit_code = 0 if verdict.verified == "yes" else 1
    if missing or verdict.verified == "unknown":
        exit_code = 2
    return CommandResult(
        name=f"runtime:{verdict.kind}",
        argv=["runtime-verify", verdict.kind],
        cwd=str(cwd),
        exit_code=exit_code,
        duration_ms=0,
        stdout_sha256=sha256_text(verdict.log),
        stderr_sha256="",
        log_path="",
        missing_tool=missing,
        skipped=skipped,
        test_counts={"required": 1, "ran": 0 if missing else 1},
    )
