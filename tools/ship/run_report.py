"""run_report: RUN-REPORT.md built only from state.json and the files under checks/.

It lists every slice's final state, every FAIL line, every NOTRUN line and every slice whose checks
never ran, and the idle time (no seat held while work remained) with its cause. Counts per status
must add up to the number of slices; the report says whether they do. The coordinator adds only a
"Waits on you" section under it.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from pathlib import Path

from ship import state as st
from ship.layout import Program
from ship.settings import Settings
from ship.state import Status

DONE = {str(Status.LANDED), str(Status.PARKED), str(Status.BLOCKED_BY)}
MIN_IDLE_S = 60


def _t(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text)


def check_lines(program: Program, verdict: str) -> list[tuple[str, str]]:
    """(line, file) for each distinct line starting with `verdict` under checks/, in path order."""
    seen: dict[str, str] = {}
    if program.checks_root.exists():
        for path in sorted(program.checks_root.rglob("*")):
            if not path.is_file() or path.suffix not in (".log", ".txt"):
                continue
            for line in path.read_text("utf-8", errors="replace").splitlines():
                if line.startswith(verdict + " ") and line not in seen:
                    seen[line] = str(path.relative_to(program.dir))
    return list(seen.items())


def idle_spans(state: st.State, end: dt.datetime) -> list[tuple[dt.datetime, dt.datetime, str]]:
    status = {sid: str(Status.PENDING) for sid in state.slices}
    hold_on = False
    usage_until: dt.datetime | None = None
    spans = []
    start: dt.datetime | None = None
    cause = ""
    for event in (e for e in state.events if e.get("at")):
        at = _t(event["at"])
        kind = event["kind"]
        if kind == "status":
            status[event["slice"]] = event["to"]
        elif kind == "hold":
            hold_on = True
        elif kind == "clear":
            hold_on = False
        elif kind == "usage-limit":
            usage_until = _t(event["reset_at"])
        held = sum(1 for s in status.values() if s == str(Status.HELD))
        idle_now = held == 0 and any(s not in DONE for s in status.values())
        now_cause = _cause(state, status, hold_on, usage_until, at) if idle_now else ""
        if start is not None and now_cause != cause:
            spans.append((start, at, cause))
            start = None
        if idle_now and start is None:
            start, cause = at, now_cause
    if start is not None:
        spans.append((start, end, cause))
    return spans


def _cause(state: st.State, status: dict[str, str], hold_on: bool, usage_until, at) -> str:
    if hold_on:
        return "power hold"
    if usage_until and usage_until > at:
        return f"usage limit until {usage_until.isoformat()}"
    busy = sorted(sid for sid, s in status.items() if s in (Status.READY, Status.CHECKED, Status.RED, Status.DEAD))
    startable = [sid for sid, s in status.items() if s == Status.PENDING
                 and all(status[d] == Status.LANDED for d in state.slices[sid].depends_on)]
    if startable:
        return f"no dispatch while {startable} could start"
    if busy:
        return f"no seat held; slices between build and landing: {busy}"
    blockers = sorted({d for sid, s in status.items() if s == Status.PENDING
                       for d in state.slices[sid].depends_on if status[d] != Status.LANDED})
    parked = sorted(sid for sid, s in status.items() if s in (Status.PARKED, Status.BLOCKED_BY))
    return f"nothing startable; pending slices wait on {blockers}; parked or blocked: {parked}"


def replayed(state: st.State) -> dict[str, str]:
    """Each slice's status as the event log tells it."""
    status = {sid: str(Status.PENDING) for sid in state.slices}
    for event in state.events:
        if event["kind"] == "status":
            status[event["slice"]] = event["to"]
    return status


def build(program: Program, settings: Settings, now: dt.datetime | None = None) -> tuple[bool, str]:
    state = st.load(program)
    now = now or dt.datetime.now(dt.timezone.utc)
    counts = Counter(str(s.status) for s in state.slices.values())
    total = len(state.slices)
    from_log = Counter(replayed(state).values())
    adds_up = sum(counts.values()) == total and from_log == counts
    out = [f"# Run report: {state.build_branch}", "",
           f"Built {now.isoformat(timespec='seconds')} from state.json and checks/. Nothing here is from memory.", "",
           "## Counts", ""]
    out += [f"- {name}: {counts.get(str(name), 0)}" for name in Status]
    out += [f"- total: {total} slices; the counts {'add up' if adds_up else 'DO NOT add up'} "
            f"({sum(counts.values())} counted, event log gives {dict(sorted(from_log.items()))})", ""]
    out += ["## Slices", "", "| id | name | state | reason | attempts | restarts | landed | PR |",
            "|---|---|---|---|---|---|---|---|"]
    for s in state.slices.values():
        reason = (s.reason or (f"needs {s.blocked_by}" if s.blocked_by else "")).replace("|", "/")
        out.append(f"| {s.id} | {s.name} | {s.status} | {reason} | {s.attempts} | {s.restarts} | "
                   f"{(s.landed_sha or '')[:8]} | {s.pr or ''} |")
    fails = check_lines(program, "FAIL")
    out += ["", f"## FAIL lines ({len(fails)})", ""]
    out += [f"- `{line}` ({path})" for line, path in fails] or ["- none"]
    notrun = check_lines(program, "NOTRUN")
    unchecked = [s.id for s in state.slices.values()
                 if s.status not in (Status.PENDING, Status.BLOCKED_BY) and not (program.checks_root / s.id).exists()]
    out += ["", f"## Checks not run ({len(notrun) + len(unchecked)})", ""]
    out += [f"- `{line}` ({path})" for line, path in notrun]
    out += [f"- slice_checks never ran for {sid}" for sid in unchecked]
    if not notrun and not unchecked:
        out.append("- none")
    spans = [(a, b, c) for a, b, c in idle_spans(state, now) if (b - a).total_seconds() >= MIN_IDLE_S]
    idle = sum(((b - a).total_seconds() for a, b, _ in spans), 0.0)
    out += ["", f"## Idle time: {idle / 3600:.1f} hours (no seat held while work remained)", ""]
    out += [f"- {a.isoformat(timespec='minutes')} to {b.isoformat(timespec='minutes')} "
            f"({(b - a).total_seconds() / 60:.0f} min): {c}" for a, b, c in spans] or ["- none"]
    if state.nightly:
        out += ["", "## Last nightly", "", f"- {state.nightly}"]
    if state.breaker_tripped(settings.breaker_parks):
        out += ["", "## Breaker", "", "- tripped: quality parks in a row"]
    return adds_up, "\n".join(out) + "\n"


def write_report(program: Program, settings: Settings) -> tuple[bool, Path]:
    ok, text = build(program, settings)
    program.report.write_text(text, "utf-8", newline="\n")
    return ok, program.report
