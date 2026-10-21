"""The zero-token watchdog (AD-16, SOLUTION-DESIGN 10.3). The runner calls `Watchdog.tick` on every
tick while attempts are in flight; it reads only what the attempts show and never calls a model or
counts usage.

The chat rules are the harness's (`qma.harness.stuck`), so an engine attempt and a copilot helper
are judged by the same code. Each in-flight attempt shows a `Pulse`, and an agent attempt also its
tool calls. Per attempt the watchdog keeps how long it has been quiet on a sleep-aware clock: a
tick longer than `MAX_TICKS` ticks (the host slept, or the loop was blocked) counts as that many
ticks only. It returns what to do: warn, interrupt, end as stalled, or stop a looping or flailing
agent. The worker's heartbeat is never progress.

`timeout.in_tool` counts only time in which the attempt's own processes show no CPU and no IO;
`Meter` reads that from the process tree with psutil.

The run rules live where they decide: "the same node failing twice with one signature goes to the
doctor" is the core's (`core.ladder`), and the crash-loop counter is the runner's, on resume. A
ledger write error stops the engine claiming new work and raises a `black` `system_fault`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal

import psutil
from qma.harness import (
    Pulse,
    Quiet,
    StuckCall,
    StuckRules,
    StuckTimeouts,
    judge_stuck,
    watch_progress,
)

from qmx_engine.ledger.signature import signature
from qmx_engine.ports.inbox import Category, Raise

STALLED: Final = "stalled"
STALLED_MESSAGE: Final = "the attempt stalled: no progress past its idle timeout and grace"
MAX_TICKS: Final = 2

type Kind = Literal["agent", "script", "other"]
type Act = Literal["warn", "interrupt", "stalled", "loop", "no_convergence"]


@dataclass(frozen=True, slots=True)
class Watched:
    """One attempt in flight as the watchdog sees it at a tick."""

    key: str
    kind: Kind
    pulse: Pulse
    calls: tuple[StuckCall, ...] | None = None
    """An agent attempt's finished tool calls; None for an attempt with no tool calls."""
    idle_seconds: int | None = None
    """The node's own idle window, over the kind's default."""
    in_tool_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class Action:
    key: str
    act: Act
    quiet_seconds: float


def _number(settings: Mapping[str, object], key: str, default: float) -> float:
    found = settings.get(key)
    if isinstance(found, int | float) and not isinstance(found, bool):
        return float(found)
    return default


class Watchdog:
    def __init__(self, settings: Mapping[str, object], tick_seconds: float) -> None:
        self.tick_seconds = tick_seconds
        self.idle: dict[Kind, float | None] = {
            "agent": _number(settings, "timeout.agent.idle", 300),
            "script": _number(settings, "timeout.script.idle", 600),
            "other": None,
        }
        self.in_tool = _number(settings, "timeout.in_tool", 1_200)
        self.grace = _number(settings, "timeout.grace", 120)
        self.warn_at = _number(settings, "timeout.warn_at", 0.8)
        self.rules = StuckRules(
            int(_number(settings, "loop.repeat", 5)),
            int(_number(settings, "loop.window", 8)),
            int(_number(settings, "loop.no_convergence", 6)),
        )
        self.quiet: dict[str, Quiet] = {}
        self.last: datetime | None = None

    def tick(self, now: datetime, attempts: Iterable[Watched]) -> list[Action]:
        """What to do about each attempt at `now`. An attempt not passed is forgotten."""
        elapsed = 0.0 if self.last is None else (now - self.last).total_seconds()
        elapsed = min(max(elapsed, 0.0), MAX_TICKS * self.tick_seconds)
        self.last = now
        actions: list[Action] = []
        quiet: dict[str, Quiet] = {}
        for attempt in attempts:
            if attempt.calls is not None:
                verdict = judge_stuck(attempt.calls, self.rules)
                if verdict != "progress":
                    actions.append(Action(attempt.key, verdict, 0.0))
                    continue
            idle = attempt.idle_seconds or self.idle[attempt.kind]
            if idle is None:
                continue
            timeouts = StuckTimeouts(
                idle, attempt.in_tool_seconds or self.in_tool, self.grace, self.warn_at
            )
            before = self.quiet.get(attempt.key, Quiet())
            found, alarm = watch_progress(before, attempt.pulse, elapsed, timeouts)
            quiet[attempt.key] = found
            if alarm != "none":
                actions.append(Action(attempt.key, alarm, found.seconds))
        self.quiet = quiet
        return actions


class Meter:
    """Whether a process tree used CPU or did IO since the last reading, by attempt key."""

    def __init__(self) -> None:
        self.readings: dict[str, float] = {}

    def busy(self, key: str, pid: int, *, children_only: bool = False) -> bool:
        found = work(pid, children_only=children_only)
        last = self.readings.get(key)
        self.readings[key] = found
        return last is not None and found != last

    def forget(self, keys: Iterable[str]) -> None:
        for key in set(self.readings) - set(keys):
            del self.readings[key]


def work(pid: int, *, children_only: bool) -> float:
    """CPU seconds plus bytes read and written by the tree under `pid`; 0 once it is gone."""
    try:
        root = psutil.Process(pid)
        tree = root.children(recursive=True) + ([] if children_only else [root])
    except psutil.Error:
        return 0.0
    total = 0.0
    for process in tree:
        try:
            cpu = process.cpu_times()
            total += cpu.user + cpu.system
            io = process.io_counters()
            total += io.read_bytes + io.write_bytes
        except psutil.Error, AttributeError:
            continue
    return total


def ledger_fault(run_id: str, error: Exception) -> Raise:
    message = str(error)
    return Raise(
        run_id,
        signature("ledger_write", message),
        Category.SYSTEM_FAULT,
        "the run ledger cannot be written; the engine stopped claiming work",
        message,
        severity="black",
        blocks_run=True,
    )
