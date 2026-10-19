"""The fold and `next_commands`: pure, so the same events always give the same commands (AD-6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

from flows import Flow
from pydantic import JsonValue

from qmx_engine.core.commands import Finish, Park, StartNode, encode
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.events import Event, JsonObject
from qmx_engine.ledger.memo import MemoKey
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok

NOW = "2026-10-17T09:00:00+00:00"
TRIGGER: JsonObject = {
    "id": "n1",
    "name": "N1",
    "type": "trigger",
    "typeVersion": 1,
    "parameters": {},
    "role": None,
    "effect": None,
    "retry": None,
    "timeout": None,
    "runs_on": "pc",
    "credentials": {},
    "disabled": False,
    "notes": None,
}


class Echo:
    def run(self, job: NodeJob) -> NodeResult:
        return Ok({"main": {"node": job.node_id, "upstream": job.inputs}})


@dataclass(frozen=True, slots=True)
class Seen:
    """An event as the core reads it, of a kind the ledger would refuse to store."""

    seq: int
    run_id: str
    kind: str
    data: JsonObject = field(default_factory=dict[str, JsonValue])


def chain(length: int) -> Workflow:
    names = [f"N{i}" for i in range(1, length + 1)]
    return Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "chain",
            "name": "chain",
            "nodes": [
                {
                    "id": f"n{i}",
                    "name": name,
                    "type": "trigger" if i == 1 else "script",
                    "typeVersion": 1,
                }
                for i, name in enumerate(names, start=1)
            ],
            "connections": {
                a: {"main": [[{"node": b, "port": "in", "map": "one"}]]} for a, b in pairwise(names)
            },
        }
    )


def finished_run(tmp: Path, length: int = 3) -> list[Event]:
    flow = Flow(tmp, chain(length), {"script": Echo()})
    assert flow.start({"topic": "q-fin"}).status == "passed"
    return flow.events


def test_folding_one_event_list_twice_gives_equal_commands_at_every_prefix(tmp_path: Path) -> None:
    events = finished_run(tmp_path)
    definition = chain(3)

    first = [encode(next_commands(fold(definition, events[:k]))) for k in range(len(events) + 1)]
    second = [encode(next_commands(fold(definition, events[:k]))) for k in range(len(events) + 1)]

    assert first == second
    assert next_commands(fold(definition, events[:3])) == [
        StartNode(
            run_id="run-1",
            node_id="n1",
            iteration=0,
            partition=None,
            attempt=1,
            memo_key=MemoKey.of("run-1", "n1", 0, "", {"topic": "q-fin"}, TRIGGER).fingerprint,
            idempotency_key="run-1:n1:0:1",
            node_definition=TRIGGER,
            inputs={"topic": "q-fin"},
            now=NOW,
        )
    ]


def test_a_chain_finishes_with_the_sink_outputs_and_then_says_nothing(tmp_path: Path) -> None:
    events = finished_run(tmp_path)
    kinds = [e.kind for e in events]

    assert kinds.count("node_started") == 3
    assert kinds[-1] == "run_finished"
    assert next_commands(fold(chain(3), events)) == []
    assert next_commands(fold(chain(3), events[:-1])) == [
        Finish(
            {
                "n3": {
                    "main": {
                        "node": "n3",
                        "upstream": {"in": {"node": "n2", "upstream": {"in": {"topic": "q-fin"}}}},
                    }
                }
            }
        )
    ]


def test_an_event_kind_the_core_does_not_know_parks_the_run_naming_it() -> None:
    events = [
        Seen(1, "run-1", "run_input", {"inputs": {}}),
        Seen(2, "run-1", "clock_tick", {"now": NOW}),
        Seen(3, "run-1", "node_teleported", {"node_id": "n1"}),
    ]
    parked = Seen(4, "run-1", "ladder_step", {"step": "park", "reason": "unfoldable"})

    assert next_commands(fold(chain(3), events)) == [
        Park("this core cannot fold event kind 'node_teleported' at seq 3")
    ]
    assert next_commands(fold(chain(3), [*events, parked])) == []


def test_events_read_back_from_the_ledger_fold_to_the_same_commands(tmp_path: Path) -> None:
    halfway = finished_run(tmp_path / "run")[:6]
    with Ledger.open(tmp_path / "copy") as ledger:
        for event in halfway:
            ledger.append("run-1", event.kind, event.data, at=event.at)
    with Reader.open(tmp_path / "copy") as reader:
        stored = reader.events("run-1")

    assert encode(next_commands(fold(chain(3), stored))) == encode(
        next_commands(fold(chain(3), halfway))
    )
    assert [type(c).__name__ for c in next_commands(fold(chain(3), stored))] == ["StartNode"]
