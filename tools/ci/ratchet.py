"""Findings against a committed baseline: only findings the baseline does not hold block.

A finding's key leaves out its line number, so moving code does not make an old finding new. Keys
are counted, so a second copy of a known finding in the same file is new.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


@dataclasses.dataclass(frozen=True)
class Finding:
    path: str  # repo-relative, forward slashes
    line: int
    rule: str
    message: str
    blocking: bool = True

    @property
    def key(self) -> str:
        return f"{self.path}|{self.rule}|{self.message}"

    def text(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.message}"


def new_findings(current: Iterable[Finding], baseline_keys: Iterable[str]) -> list[Finding]:
    """The findings beyond the baseline's count for their key, latest lines first within a key."""
    allowed = Counter(baseline_keys)
    fresh: list[Finding] = []
    for finding in sorted(current, key=lambda f: (f.key, f.line)):
        if allowed[finding.key] > 0:
            allowed[finding.key] -= 1
        else:
            fresh.append(finding)
    return sorted(fresh, key=lambda f: (f.path, f.line, f.rule))


def read_baseline(path: Path) -> list[str]:
    """One key per line; `#` lines are comments. A missing file is an empty baseline."""
    if not path.exists():
        return []
    lines = path.read_text("utf-8").splitlines()
    return [line for line in lines if line and not line.startswith("#")]


def write_baseline(path: Path, findings: Iterable[Finding], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(f.key for f in findings)
    body = "".join(f"# {line}\n" for line in header.splitlines()) + "".join(f"{k}\n" for k in keys)
    path.write_text(body, "utf-8", newline="\n")


def write_junit(path: Path, suite: str, findings: list[Finding]) -> None:
    """One failed test case per blocking new finding, so GitLab's test report lists them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    blocking = [f for f in findings if f.blocking]
    cases = (
        "".join(
            f"<testcase classname={quoteattr(suite)} name={quoteattr(f.text())}>"
            f"<failure message={quoteattr('new finding')}>{escape(f.text())}</failure></testcase>"
            for f in blocking
        )
        or f'<testcase classname={quoteattr(suite)} name="no new findings"/>'
    )
    count = max(1, len(blocking))
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<testsuite name={quoteattr(suite)} tests="{count}" '
        f'failures="{len(blocking)}">{cases}</testsuite>\n',
        "utf-8",
    )
