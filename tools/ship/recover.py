"""recover: run at every coordinator start and after any crash, restart, usage limit or power cut.

Marks every held seat dead (a restart, never an attempt), saves each dead slice's leftovers as
evidence/<id>/<attempt>/leftover.patch, and resets its worktree to the last pushed sha (or its parent
when nothing was pushed). With --usage-reset it records when the usage limit lifts. Safe to run twice.
"""

from __future__ import annotations

from pathlib import Path

from ship import state as st
from ship.layout import Program
from ship.settings import Settings
from ship.state import Status
from ship.gitx import GitError, registered
from ship.worktree import fetch_branch, save_and_reset


def recover(program: Program, settings: Settings, usage_reset: str | None = None) -> list[str]:
    lines: list[str] = []
    with st.locked(program) as state:
        if usage_reset:
            state.usage_reset_at = usage_reset
            state.log("usage-limit", None, reset_at=usage_reset)
            lines.append(f"USAGE reset at {usage_reset}")
        repo = Path(state.repo)
        for sl in state.slices.values():
            if sl.status == Status.HELD:
                state.move(sl.id, Status.DEAD, f"holder {sl.holder.dispatch_id if sl.holder else '?'} dead")
                lines.append(f"DEAD {sl.id}")
            if sl.status != Status.DEAD:
                continue
            wt = state.worktree(sl.id)
            if not registered(repo, wt, settings.git_timeout_s):
                lines.append(f"NOWORKTREE {sl.id} {wt}")
                continue
            pushed = fetch_branch(repo, state.remote, sl.branch, settings)
            target = pushed or sl.parent
            if not target:
                lines.append(f"SKIP {sl.id}: no pushed sha and no parent")
                continue
            saved = save_and_reset(wt, target, program.evidence(sl.id, sl.attempts) / "leftover.patch", settings)
            lines.append(f"RESET {sl.id} to {target[:8]}" + (f", leftovers in {saved}" if saved else ""))
        deep = state.ci.get("deep") or {}
        if settings.ci == "github" and deep.get("run_id") and deep.get("result") is None:
            lines.append(reattach(state, settings, deep))
    return lines


def reattach(state: st.State, settings: Settings, deep: dict) -> str:
    """A GitHub run survives a power cut: point at it again, never dispatch a second one."""
    from ship.ci import gh_for, short

    level = deep.get("level", "deep")
    try:
        got = gh_for(state, settings).view(deep["run_id"])
    except GitError as exc:
        return (f"CI {level} {deep['run_id']} on {deep['tip'][:8]} recorded; GitHub unreachable "
                f"({short(exc)}); ship ci status retries, nothing new dispatched")
    said = " ".join(x for x in (got.get("status"), got.get("conclusion")) if x)
    return f"CI {level} {deep['run_id']} on {deep['tip'][:8]} re-attached: {said} {got.get('url')}; ship ci status --wait reads it"
