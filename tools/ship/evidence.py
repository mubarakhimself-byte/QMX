"""The END line: every evidence and verdict file a script accepts ends `END <sha> <dispatch id>`.

For a builder's evidence the kit writes it (`stamp`), when the builder replies `READY <sha>`: the builder
writes the evidence, the kit names the head and attempt it was accepted for. A file that holds nothing but
its END line is empty."""

from __future__ import annotations

from pathlib import Path


def end_line(sha: str, dispatch_id: str) -> str:
    return f"END {sha} {dispatch_id}"


def end_problem(path: Path, sha: str, dispatch_id: str) -> str | None:
    """None when the file's last non-blank line is exactly the END line for this head and attempt, and something
    comes before it."""
    if not path.is_file():
        return f"{path.name}: missing"
    lines = [ln.strip() for ln in path.read_text("utf-8", errors="replace").splitlines() if ln.strip()]
    want = end_line(sha, dispatch_id)
    if not lines:
        return f"{path.name}: empty"
    if lines[-1] != want:
        return f"{path.name}: last line is {lines[-1][:100]!r}, want {want!r}"
    if not [ln for ln in lines if not ln.startswith("END ")]:
        return f"{path.name}: empty but for its END line"
    return None


def stamp(path: Path, sha: str, dispatch_id: str) -> bool:
    """End an existing file with the END line for this head and attempt, replacing the END lines already at its
    end. A missing file stays missing (verify_ready reports it). True when the file was stamped."""
    if not path.is_file():
        return False
    lines = path.read_text("utf-8", errors="replace").splitlines()
    while lines and (not lines[-1].strip() or lines[-1].strip().startswith("END ")):
        lines.pop()
    path.write_text("\n".join([*lines, end_line(sha, dispatch_id)]) + "\n", "utf-8", newline="\n")
    return True


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
