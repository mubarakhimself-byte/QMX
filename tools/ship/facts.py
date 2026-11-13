"""facts: rerun every brief's facts at a given commit, the target tip at arm time (edge case 28).

The briefs were written against the target as it was at planning. When the target moved since, a fact
may no longer hold. `facts_at` checks every brief (or the ones named) in a frozen checkout of the tip
and writes `checks/_facts/<tip8>/summary.txt`: one PASS or FAIL line per fact, `FAIL <slice> <fact>`
for each mismatch, with the want and got lines under it.
"""

from __future__ import annotations

from pathlib import Path

from ship import state as st
from ship.dispatch import run_facts
from ship.gitx import git
from ship.layout import Program
from ship.plan import PlanError, parse_slices, read_brief_facts
from ship.settings import Settings
from ship.worktree import checkout_copy, drop_copy


def slice_ids(program: Program) -> list[str]:
    if program.state.exists():
        return list(st.load(program).slices)
    return [s.id for s in parse_slices(program.slices_md.read_text("utf-8"))]


def facts_at(program: Program, tip: str, settings: Settings, only: list[str] | None = None,
             repo: Path | None = None, remote: str | None = None) -> tuple[bool, list[str]]:
    if repo is None or remote is None:
        state = st.load(program)
        repo, remote = Path(state.repo), state.remote
    t = settings.git_timeout_s
    git(repo, "fetch", "-q", remote, timeout=t)
    sha = git(repo, "rev-parse", "--verify", f"{tip}^{{commit}}", timeout=t).strip()
    ids = [sid for sid in slice_ids(program) if not only or sid in only]
    copy = checkout_copy(repo, program.tmp / "facts", sha, settings)
    lines: list[str] = []
    try:
        for sid in ids:
            try:
                facts = read_brief_facts(program.brief(sid))
            except PlanError as exc:
                lines.append(f"FAIL {sid} brief: {exc}")
                continue
            for line in run_facts(facts, copy, settings):
                verdict, _, rest = line.partition(" fact ")
                fact, _, detail = rest.partition(" ")
                lines.append(f"{verdict} {sid} {fact}" + (f" {detail}" if detail else ""))
    finally:
        drop_copy(repo, copy, settings)
    out = program.checks_root / "_facts" / sha[:8]
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.txt").write_text(f"# facts at {sha}\n" + "\n".join(lines) + "\n", "utf-8", newline="\n")
    failed = [ln.splitlines()[0] for ln in lines if ln.startswith("FAIL ")]
    return not failed, failed or [f"PASS {len(lines)} facts of {len(ids)} briefs at {sha[:8]}; {out / 'summary.txt'}"]
