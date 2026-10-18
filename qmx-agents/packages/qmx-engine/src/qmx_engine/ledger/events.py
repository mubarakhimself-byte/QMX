"""The ledger's event kinds and envelope (SOLUTION-DESIGN 3.2).

`data` is a JSON object whose keys depend on the kind. `at` is an ISO-8601 instant the caller
takes from the run's recorded clock (`clock_tick`), never from the wall clock (AD-6), so a replay
writes the same envelope as the original run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, get_args

from pydantic import JsonValue

type JsonObject = dict[str, JsonValue]

type EventKind = Literal[
    "run_created",
    "run_input",
    "clock_tick",
    "node_scheduled",
    "node_started",
    "heartbeat",
    "log",
    "node_finished",
    "node_failed",
    "node_waiting",
    "gate_opened",
    "gate_resolved",
    "event_received",
    "ladder_step",
    "doctor_verdict",
    "run_paused",
    "run_resumed",
    "run_finished",
    "run_cancelled",
    "compacted",
    "memory_written",
]

KINDS: Final[frozenset[str]] = frozenset(get_args(EventKind.__value__))


@dataclass(frozen=True, slots=True)
class Event:
    """One appended event. `seq` starts at 1 and has no gap within a run."""

    seq: int
    run_id: str
    at: str
    kind: EventKind
    data: JsonObject
