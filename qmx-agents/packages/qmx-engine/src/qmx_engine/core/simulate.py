"""A synchronous in-memory driver for tests and the live checks. It folds, carries out the
commands, records each result as an event and folds again, until the run finishes, parks, pauses or
waits. Executors are injected as a `Step`; the real runner arrives in EP7.

The driver writes the events the core asks for: `node_scheduled` (with the core's `plan`) for
`StartNode`, a `node_waiting` with no attempt for `Hold`, a `node_finished` marked `memo: true` for
`UseMemo`, `ladder_step` for `Climb` and `Park`, `run_paused` for `Pause` and `run_finished` for
`Finish`. It has no doctor, so a doctor step is recorded as skipped.
The `Step` writes the attempt's own events (`node_started` and its ending), as a worker does; a
`Step` that returns only `node_started` leaves the attempt in flight until the test appends its
ending. A hold's `resume_at` comes from the injected `Clock`, since the core does no clock
arithmetic; `qmx_engine.nodes.wait.resume_at` is the real one.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.core.commands import (
    Climb,
    Command,
    Finish,
    Hold,
    Park,
    Pause,
    StartNode,
    UseMemo,
    Wait,
)
from qmx_engine.core.fold import fold
from qmx_engine.core.ladder import NO_DOCTOR, limits_line, step_data
from qmx_engine.core.partitions import RUN_SETTINGS
from qmx_engine.core.ready import next_commands
from qmx_engine.core.state import JsonObject, State
from qmx_engine.definition.model import Workflow

type Draft = tuple[str, JsonObject]
type Step = Callable[[StartNode], Sequence[Draft]]
type Clock = Callable[[Hold, str], str | None]
"""A hold and the run's `now` to the hold's `resume_at`."""
type Terminal = Finish | Park | Pause | Wait


def no_clock(hold: Hold, _: str) -> str | None:
    if hold.seconds is not None:
        raise ValueError("a hold of seconds needs a Clock")
    return hold.until


@dataclass(frozen=True, slots=True)
class Entry:
    seq: int
    run_id: str
    at: str
    kind: str
    data: JsonObject


class Simulation:
    def __init__(
        self,
        definition: Workflow,
        run_id: str,
        step: Step,
        *,
        settings: Mapping[str, object] | None = None,
        clock: Clock = no_clock,
    ) -> None:
        """`settings` are the engine settings in force; the run records the ones the core reads."""
        self.definition = definition
        self.run_id = run_id
        self.step = step
        self.settings: JsonObject = {
            key: value
            for key, value in (settings or {}).items()
            if key in RUN_SETTINGS and isinstance(value, int | float | str)
        }
        self.clock = clock
        self.events: list[Entry] = []
        self.now = ""

    def append(self, kind: str, data: JsonObject) -> None:
        self.events.append(Entry(len(self.events) + 1, self.run_id, self.now, kind, data))

    def state(self) -> State:
        return fold(self.definition, self.events)

    def start(self, inputs: JsonValue, now: str) -> Terminal | None:
        self.now = now
        self.append("run_created", {"mode": "test", "settings": self.settings})
        self.append("run_input", {"inputs": inputs})
        self.append("clock_tick", {"now": now})
        return self.drive()

    def resume(self, now: str, definition: Workflow | None = None) -> Terminal | None:
        """Resume under `definition` when given: an edited draft reruns what its edit changed."""
        self.now = now
        self.definition = definition or self.definition
        self.append("clock_tick", {"now": now})
        self.append("run_resumed", {"reason": "operator"})
        return self.drive()

    def tick(self, now: str) -> Terminal | None:
        """The scheduler's clock moves on within the same pass."""
        self.now = now
        self.append("clock_tick", {"now": now})
        return self.drive()

    def receive(self, event: str) -> Terminal | None:
        self.append("event_received", {"event": event})
        return self.drive()

    def drive(self) -> Terminal | None:
        """None when the core has nothing more to say, as for a run that already ended."""
        while True:
            commands = next_commands(self.state())
            if not commands:
                return None
            for command in commands:
                ended = self.carry_out(command)
                if ended is not None:
                    return ended

    def carry_out(self, command: Command) -> Terminal | None:
        match command:
            case StartNode():
                self.append(
                    "node_scheduled",
                    {
                        "node_id": command.node_id,
                        "iteration": command.iteration,
                        "partition": command.partition,
                        "attempt": command.attempt,
                        "memo_key": command.memo_key,
                        "plan": command.plan,
                    },
                )
                for kind, data in self.step(command):
                    self.append(kind, data)
                return None
            case Hold():
                self.append(
                    "node_waiting",
                    {
                        "node_id": command.node_id,
                        "iteration": command.iteration,
                        "partition": command.partition,
                        "reason": "wait",
                        "resume_at": self.clock(command, self.now),
                        "event": command.event,
                    },
                )
                return None
            case UseMemo():
                self.append(
                    "node_finished",
                    {
                        "node_id": command.node_id,
                        "iteration": command.iteration,
                        "partition": command.partition,
                        "memo": True,
                        "memo_key": command.memo_key,
                        "outputs": command.outputs,
                    },
                )
                return None
            case Climb():
                hold = Hold(command.node_id, command.iteration, command.partition, command.seconds)
                at = self.clock(hold, self.now) if command.step == "retry" else None
                data = step_data(command, at)
                if command.step == "doctor":
                    data |= {"skipped": True, "reason": NO_DOCTOR}
                self.append("ladder_step", data)
                return None
            case Park():
                self.append("ladder_step", step_data(command))
            case Pause():
                if command.detail is not None:
                    self.append("log", limits_line(command.detail))
                self.append(
                    "run_paused", {"reason": command.reason, "resume_at": command.resume_at}
                )
            case Finish():
                self.append(
                    "run_finished",
                    {"status": "passed", "outputs_hash": fingerprint(command.outputs)},
                )
            case Wait():
                pass
        return command
