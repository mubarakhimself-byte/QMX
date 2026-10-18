"""The fold and `next_commands`: pure, so the same events always give the same commands (AD-6)."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path
from typing import cast

from qmx_engine.core.commands import Finish, Park, StartNode, encode
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.core.simulate import Entry, Simulation
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.events import EventKind, JsonObject
from qmx_engine.ledger.memo import MemoKey
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok, step
from qmx_engine.nodes.trigger import Trigger

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


def finished_run(length: int = 3) -> Simulation:
    simulation = Simulation(chain(length), "run-1", step({"trigger": Trigger(), "script": Echo()}))
    simulation.start({"topic": "q-fin"}, NOW)
    return simulation


def test_folding_one_event_list_twice_gives_equal_commands_at_every_prefix() -> None:
    simulation = finished_run()
    events = simulation.events
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


def test_a_chain_finishes_with_the_sink_outputs_and_then_says_nothing() -> None:
    simulation = finished_run()
    kinds = [e.kind for e in simulation.events]

    assert kinds.count("node_started") == 3
    assert kinds[-1] == "run_finished"
    assert next_commands(simulation.state()) == []
    before_finish = fold(chain(3), simulation.events[:-1])
    assert next_commands(before_finish) == [
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
    simulation = Simulation(chain(3), "run-1", step({"trigger": Trigger(), "script": Echo()}))
    simulation.now = NOW
    simulation.append("run_input", {"inputs": {}})
    simulation.append("clock_tick", {"now": NOW})
    simulation.append("node_teleported", {"node_id": "n1"})

    assert next_commands(simulation.state()) == [
        Park("this core cannot fold event kind 'node_teleported' at seq 3")
    ]
    assert simulation.drive() == Park("this core cannot fold event kind 'node_teleported' at seq 3")
    assert [e.kind for e in simulation.events][-1] == "ladder_step"
    assert next_commands(simulation.state()) == []


def test_events_read_back_from_the_ledger_fold_to_the_same_commands(tmp_path: Path) -> None:
    simulation = finished_run()
    halfway: list[Entry] = simulation.events[:6]
    with Ledger.open(tmp_path) as ledger:
        for entry in halfway:
            ledger.append("run-1", cast(EventKind, entry.kind), entry.data, at=entry.at)
    with Reader.open(tmp_path) as reader:
        stored = reader.events("run-1")

    assert encode(next_commands(fold(chain(3), stored))) == encode(
        next_commands(fold(chain(3), halfway))
    )
    assert [type(c).__name__ for c in next_commands(fold(chain(3), stored))] == ["StartNode"]
