"""The stuck detector's chat rules (engine AD-16 a to c2): pure judgement over what an unattended
chat did, shared by engine attempts and, later, the harness's own Background and Child chats.

None of these rules counts tokens, turns, tool calls or time against a ceiling. They ask whether
the chat still moves:

- `watch_progress` is the no-progress rule. Each tick the caller passes a `Pulse` and the seconds
  the tick covered on a sleep-aware clock. A model request in flight is progress, so a slow
  prefill runs on; so is CPU or IO on the processes of an open tool call. Recorded waits are
  skipped. Silence past the window warns at `warn_at` of it, then interrupts, then after `grace`
  is stalled.
- `judge_stuck` is the loop and no-convergence rule over the chat's tool calls. A call's result is
  compared by its stuck digest, which masks only what changes on every run (uuids, timestamps,
  durations, temp paths), so a rerun `pytest` with the same failures matches itself while a fixer
  whose failures fall, or a pager over new rows, is progress.

A turn here is one step of the agent: a call that is not an edit, with the edits made just before
it, so "edit, then run the tests" is one turn whether the agent did it in one call or two.
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Final, Literal

EDITS: Final = frozenset({"Edit", "MultiEdit", "Write", "NotebookEdit"})
UUID: Final = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
STAMP: Final = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:[.,]\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|\b\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\b"
)
DURATION: Final = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:ns|us|µs|ms|s|secs?|seconds?|mins?|minutes?|h|hours?)\b", re.I
)
PYTEST_ID: Final = re.compile(r"^(?:FAILED|ERROR)\s+(\S+::\S+)", re.M)
PYTEST_COUNT: Final = re.compile(r"\b(\d+) (?:failed|errors?)\b")
TRACE_FRAME: Final = re.compile(r'File "([^"]+)", line (\d+)')
FILE_LINE: Final = re.compile(r"([\w./\\-]+\.\w+):(\d+)(?::\d+)?:")

type StuckVerdict = Literal["progress", "loop", "no_convergence"]
type Alarm = Literal["none", "warn", "interrupt", "stalled"]


@dataclass(frozen=True, slots=True)
class StuckRules:
    """Claude's defaults (plan Appendix H), each a Setting he can change."""

    repeat: int = 5
    """The same call with the same result this many times in a row is a loop."""
    window: int = 8
    """How many recent turns the window rules read."""
    no_convergence: int = 6
    """Turns of the window that carry the same failing set before the fixer is stalled."""


@dataclass(frozen=True, slots=True)
class StuckTimeouts:
    """Seconds on the sleep-aware clock (Claude's defaults: 300 agent and 600 script idle, 1,200
    in a tool, 120 grace, a warning at 80 %)."""

    idle: float = 300
    in_tool: float = 1_200
    grace: float = 120
    warn_at: float = 0.8


@dataclass(frozen=True, slots=True)
class StuckCall:
    """One finished tool call, reduced to what the rules compare."""

    key: str
    """The tool's name and a digest of its arguments."""
    result: str
    """The stuck digest of its result."""
    edit: bool = False
    error: bool = False
    failing: frozenset[str] = frozenset()
    """On an error result: the failing test ids, or the error's file and line."""
    failures: int = 0


@dataclass(frozen=True, slots=True)
class Pulse:
    """What an attempt shows at one tick."""

    progress: int
    """A count of its progress events so far: tool calls, turns, log lines, chunk events."""
    in_flight: bool = False
    """A model request is sent and streaming, or sent and awaiting its first token."""
    waiting: bool = False
    """A recorded wait: a provider wait, a capacity queue, the warm-first gate, a gate, a child."""
    tool_open: bool = False
    busy: bool = False
    """The attempt's own processes used CPU or did IO since the last tick."""


@dataclass(frozen=True, slots=True)
class Quiet:
    """How long an attempt has shown no progress, carried from tick to tick."""

    progress: int | None = None
    seconds: float = 0.0
    warned: bool = False
    interrupted: float | None = None
    """`seconds` when the interrupt went out."""


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def stuck_digest(text: str, masks: Iterable[str] = ()) -> str:
    """The digest a result is compared by. `masks` are folders whose paths change per run, such
    as the attempt's overlay root; the OS temp folder is always one."""
    found = text
    for root in sorted({tempfile.gettempdir(), *masks}, key=len, reverse=True):
        for form in {root, root.replace("\\", "/"), root.replace("/", "\\")}:
            found = re.sub(re.escape(form) + r"[^\s\"'`,;)\]}]*", "<tmp>", found, flags=re.I)
    found = UUID.sub("<uuid>", found)
    found = STAMP.sub("<time>", found)
    found = DURATION.sub("<duration>", found)
    return digest(found)


def failing_set(text: str) -> tuple[frozenset[str], int]:
    """The failing test ids (or the error's file and line) an error result names, and its
    failure count. A result naming neither fails as itself."""
    ids = frozenset(PYTEST_ID.findall(text))
    if ids:
        counted = PYTEST_COUNT.findall(text)
        return ids, sum(int(n) for n in counted) if counted else len(ids)
    frames = TRACE_FRAME.findall(text)
    if frames:
        file, line = frames[-1]
        return frozenset({f"{file}:{line}"}), 1
    places = frozenset(f"{file}:{line}" for file, line in FILE_LINE.findall(text))
    if places:
        return places, len(places)
    return frozenset({stuck_digest(text)}), 1


def stuck_call(
    name: str, arguments: object, result: str, *, error: bool, masks: Iterable[str] = ()
) -> StuckCall:
    """A finished tool call as the rules see it."""
    masks = tuple(masks)
    shown = json.dumps(arguments, sort_keys=True, default=str)
    failing, failures = failing_set(result) if error else (frozenset[str](), 0)
    return StuckCall(
        f"{name}:{stuck_digest(shown, masks)}",
        stuck_digest(result, masks),
        name in EDITS,
        error,
        failing,
        failures,
    )


def turns(calls: Sequence[StuckCall]) -> list[tuple[StuckCall, ...]]:
    found: list[tuple[StuckCall, ...]] = []
    pending: list[StuckCall] = []
    for one in calls:
        pending.append(one)
        if not one.edit:
            found.append(tuple(pending))
            pending = []
    if pending:
        found.append(tuple(pending))
    return found


DEFAULT_RULES: Final = StuckRules()


def judge_stuck(calls: Sequence[StuckCall], rules: StuckRules = DEFAULT_RULES) -> StuckVerdict:
    """Whether the chat's calls so far show a loop, a fixer that does not converge, or progress."""
    last = calls[-rules.repeat :]
    if len(last) == rules.repeat and len({(c.key, c.result) for c in last}) == 1:
        return "loop"
    steps = turns(calls)
    if _flailing(steps[-rules.window :], rules.no_convergence):
        return "no_convergence"
    if len(steps) > rules.window and not _new_in_window(steps, rules.window):
        return "loop"
    return "progress"


def _new_in_window(steps: list[tuple[StuckCall, ...]], window: int) -> bool:
    """Whether the last `window` turns made an edit or produced a result not seen before."""
    seen: set[str] = set()
    start = len(steps) - window
    for i, step in enumerate(steps):
        for one in step:
            if i >= start and (one.edit or one.result not in seen):
                return True
            seen.add(one.result)
    return False


def _flailing(window: Sequence[tuple[StuckCall, ...]], needed: int) -> bool:
    """The same failing set in `needed` turns of the window, a count that never falls below the
    first, while the calls that led to it differ."""
    failed = [(step, errors[-1]) for step in window if (errors := [c for c in step if c.error])]
    if len(failed) < needed:
        return False
    common, count = Counter(error.failing for _, error in failed).most_common(1)[0]
    if count < needed:
        return False
    same = [(step, error) for step, error in failed if error.failing == common]
    counts = [error.failures for _, error in same]
    tried = {tuple(c.key for c in step) for step, _ in same}
    return all(n >= counts[0] for n in counts) and len(tried) > 1


def watch_progress(
    quiet: Quiet, pulse: Pulse, elapsed: float, timeouts: StuckTimeouts
) -> tuple[Quiet, Alarm]:
    """One tick of the no-progress rule. `elapsed` is the tick's length on a sleep-aware clock."""
    moved = quiet.progress is None or pulse.progress != quiet.progress
    if pulse.waiting or moved or pulse.in_flight or pulse.busy:
        return Quiet(pulse.progress), "none"
    seconds = quiet.seconds + elapsed
    limit = timeouts.in_tool if pulse.tool_open else timeouts.idle
    if quiet.interrupted is not None:
        alarm: Alarm = "stalled" if seconds - quiet.interrupted >= timeouts.grace else "none"
        return Quiet(quiet.progress, seconds, quiet.warned, quiet.interrupted), alarm
    if seconds >= limit:
        return Quiet(quiet.progress, seconds, True, seconds), "interrupt"
    if seconds >= timeouts.warn_at * limit and not quiet.warned:
        return Quiet(quiet.progress, seconds, True), "warn"
    return Quiet(quiet.progress, seconds, quiet.warned), "none"
