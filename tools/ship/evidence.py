"""The END line: every evidence and verdict file a script accepts ends `END <sha> <dispatch id>`."""

from __future__ import annotations

from pathlib import Path


def end_line(sha: str, dispatch_id: str) -> str:
    return f"END {sha} {dispatch_id}"


def end_problem(path: Path, sha: str, dispatch_id: str) -> str | None:
    """None when the file's last non-blank line is exactly the END line for this head and attempt."""
    if not path.is_file():
        return f"{path.name}: missing"
    lines = [ln.strip() for ln in path.read_text("utf-8", errors="replace").splitlines() if ln.strip()]
    want = end_line(sha, dispatch_id)
    if not lines:
        return f"{path.name}: empty"
    if lines[-1] != want:
        return f"{path.name}: last line is {lines[-1][:100]!r}, want {want!r}"
    return None


CLEAN = "VERDICT: CLEAN"


def verdict_problem(path: Path, sha: str, dispatch_id: str) -> str | None:
    """None when a review verdict file ends with the right END line and holds the line VERDICT: CLEAN."""
    problem = end_problem(path, sha, dispatch_id)
    if problem:
        return problem
    lines = [ln.strip() for ln in path.read_text("utf-8", errors="replace").splitlines()]
    return None if CLEAN in lines else f"{path.name}: no line {CLEAN!r}"


def body_without_end(path: Path) -> str:
    lines = path.read_text("utf-8", errors="replace").rstrip().splitlines()
    if lines and lines[-1].startswith("END "):
        lines = lines[:-1]
    return "\n".join(lines).rstrip() + "\n"
