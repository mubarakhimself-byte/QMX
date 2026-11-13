"""dispatch: give a slice a seat. Refuses on a hold, a pending usage reset, no free seat, an unlanded
dependency, files that overlap an in-flight slice, or a checkpoint too far ahead: only the next
checkpoint after the open one may be pre-built, and only on files the open checkpoint does not touch. A first attempt reruns the brief's facts against
the build-branch tip and parks the slice on any mismatch. A fix round or a restart saves leftovers as
a patch and resets the worktree to the last pushed sha. Records the holder in state.json."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from pathlib import Path

from ship import clock
from ship import state as st
from ship.gitx import GitError, git, run
from ship.layout import Program
from ship.plan import Fact, PlanError, normalize_output, overlaps, read_brief_facts
from ship.settings import Settings
from ship.state import IN_FLIGHT, ParkCause, Status
from ship.worktree import ensure_worktree, fetch_branch, note_leftover, save_and_reset


class Refused(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class Dispatched:
    slice: str
    dispatch_id: str
    kind: str  # first | fix | restart
    attempt: int
    restart: int
    worktree: str
    branch: str
    parent: str
    evidence: str
    leftover: str | None

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2)


def run_facts(facts: list[Fact], cwd: Path, settings: Settings) -> list[str]:
    """One PASS or FAIL line per fact."""
    lines = []
    for fact in facts:
        try:
            done = run(fact.argv, cwd, settings.fact_timeout_s, check=False)
            got, rc = normalize_output(done.stdout), done.returncode
        except GitError as exc:
            got, rc = str(exc), -1
        if got == fact.expect and rc == fact.exit_code:
            lines.append(f"PASS fact {fact.id}")
        else:
            lines.append(f"FAIL fact {fact.id} rc={rc} want rc={fact.exit_code}\n"
                         f"  want: {fact.expect!r}\n  got:  {got[:2000]!r}")
    return lines


def prebuild_problem(state: st.State, slice_id: str) -> str | None:
    """A slice of the next checkpoint may be built while the open one builds or is reviewed, but only on
    files the open checkpoint does not touch, because its review's fix batch may change those."""
    ahead, current, sl = state.ahead(slice_id), state.open_checkpoint(), state.slices[slice_id]
    if ahead > 1:
        return f"{slice_id} is in checkpoint {sl.checkpoint}, {ahead} ahead of the open checkpoint {current}"
    if ahead == 1:
        clash = overlaps(sl.files, state.checkpoint_files(current))
        if clash:
            return f"pre-build: files overlap checkpoint {current}, which is building or in review: {clash}"
    return None


def _usage_wait(state: st.State) -> str | None:
    if not state.usage_reset_at:
        return None
    reset = dt.datetime.fromisoformat(state.usage_reset_at)
    return state.usage_reset_at if reset > clock.now() else None


@dataclasses.dataclass(frozen=True)
class Parked:
    slice: str
    reason: str
    blocked: list[str]

    def to_json(self) -> str:
        return json.dumps({"parked": dataclasses.asdict(self)}, indent=2)


def dispatch(program: Program, slice_id: str, settings: Settings) -> Dispatched | Parked:
    if program.hold.exists():
        raise Refused(f"hold is on: {program.hold.read_text('utf-8').strip()}")
    with st.locked(program) as state:
        if slice_id not in state.slices:
            raise Refused(f"no slice {slice_id}")
        sl = state.slices[slice_id]
        waiting = _usage_wait(state)
        if waiting:
            raise Refused(f"usage limit resets at {waiting}")
        # A pending slice that was dispatched before (unparked by him) carries on from its pushed work.
        kinds = {Status.PENDING: "restart" if sl.parent else "first", Status.DEAD: "restart",
                 Status.READY: "fix", Status.RED: "fix", Status.CHECKED: "fix"}
        if sl.status not in kinds:
            raise Refused(f"{slice_id} is {sl.status}" + (f" by {sl.holder.dispatch_id}" if sl.holder else ""))
        kind = kinds[sl.status]
        if kind == "restart" and sl.status == Status.DEAD and sl.deaths >= settings.max_restarts:
            blocked = state.park(slice_id, ParkCause.MANUAL, f"its builder died {sl.deaths} times")
            return Parked(slice_id, f"its builder died {sl.deaths} times", blocked)
        if kind == "fix" and sl.attempts >= settings.max_attempts:
            blocked = state.park(slice_id, ParkCause.ROUNDS, f"{sl.attempts} rounds used")
            return Parked(slice_id, f"{sl.attempts} rounds used", blocked)
        unlanded = [d for d in sl.depends_on if state.slices[d].status != Status.LANDED]
        if unlanded:
            raise Refused(f"{slice_id} waits on {unlanded}")
        problem = prebuild_problem(state, slice_id)
        if problem:
            raise Refused(problem)
        if state.held_count() >= settings.seats:
            raise Refused(f"no free seat: {state.held_count()} of {settings.seats} held")
        clashes = [f"{other.id}: {a} ~ {b}" for other in state.slices.values()
                   if other.id != slice_id and other.status in IN_FLIGHT
                   for a, b in overlaps(sl.files, other.files)]
        if clashes:
            raise Refused("files overlap an in-flight slice (an implied dependency): " + "; ".join(clashes))

        repo = Path(state.repo)
        wt = state.worktree(slice_id)
        attempt = sl.attempts + (0 if kind == "restart" else 1)
        restart = sl.restarts + (1 if kind == "restart" else 0)
        evidence = program.evidence(slice_id, attempt)
        leftover = None
        if kind == "first":
            tip = fetch_branch(repo, state.remote, state.build_branch, settings)
            if not tip:
                raise Refused(f"build branch {state.build_branch} is not on {state.remote}")
            if fetch_branch(repo, state.remote, sl.branch, settings):
                raise Refused(f"{sl.branch} already exists on {state.remote}; a first attempt starts clean")
            ensure_worktree(repo, wt, sl.branch, tip, settings)
            save_and_reset(wt, tip, evidence / "leftover.patch", settings)
            parent = tip
            try:
                facts = read_brief_facts(program.brief(slice_id))
            except PlanError as exc:
                raise Refused(str(exc)) from exc
            lines = run_facts(facts, wt, settings)
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "facts.log").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
            failed = [ln.split()[2] for ln in lines if ln.startswith("FAIL")]
            if failed:
                blocked = state.park(slice_id, ParkCause.BRIEF_MISMATCH, f"facts {failed} at {tip[:8]}")
                _drop_unpushed_worktree(program, repo, wt, sl.branch, settings)
                return Parked(slice_id, f"brief-mismatch {failed}, see {evidence / 'facts.log'}", blocked)
        else:
            parent = sl.parent or ""
            pushed = fetch_branch(repo, state.remote, sl.branch, settings)
            ensure_worktree(repo, wt, sl.branch, pushed or parent, settings)
            saved = save_and_reset(wt, pushed or parent, program.evidence(slice_id, sl.attempts) / "leftover.patch",
                                   settings)
            leftover = str(saved) if saved else None
        evidence.mkdir(parents=True, exist_ok=True)

        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
        dispatch_id = f"{slice_id}-a{attempt}-r{restart}-{stamp}"
        state.move(slice_id, Status.HELD, f"{kind} {dispatch_id}")
        sl.attempts, sl.restarts = attempt, restart
        sl.holder = st.Holder(dispatch_id, attempt, restart, st.now_iso())
        sl.parent = parent
        sl.head = None
        return Dispatched(slice_id, dispatch_id, kind, attempt, restart, str(wt), sl.branch, parent,
                          str(evidence), leftover)



def _drop_unpushed_worktree(program: Program, repo: Path, wt: Path, branch: str, settings: Settings) -> None:
    """A slice parked before any push: its worktree holds only the tip, so it goes. A failure is noted
    in leftovers.md and never retried with --force."""
    t = settings.git_timeout_s
    try:
        git(repo, "worktree", "remove", str(wt), timeout=t)
        git(repo, "branch", "-q", "-D", branch, timeout=t)
    except GitError as exc:
        note_leftover(program.leftovers, f"{wt}: not removed after brief-mismatch: {exc}")
