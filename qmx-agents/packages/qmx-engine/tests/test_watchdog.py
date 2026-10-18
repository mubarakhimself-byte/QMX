"""The zero-token watchdog rules (SOLUTION-DESIGN 10.3) under a recorded clock."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from flows import edge, node
from planted import OK, T0, Planted, flow, of_kind

from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import NodeJob, NodeResult
from qmx_engine.runner import Refused
from qmx_engine.watchdog import Open, stalled
from qmx_engine.workers.local import LocalWorker


def test_only_an_attempt_silent_past_its_idle_timeout_is_stalled() -> None:
    now = T0 + timedelta(seconds=300)
    attempts = [
        Open("quiet", T0, 299),
        Open("just-in-time", T0, 300),
        Open("no-timeout", T0, None),
        Open("recent", now - timedelta(seconds=5), 10),
    ]

    assert stalled(attempts, now) == ["quiet"]


class Hang:
    async def run(self, job: NodeJob) -> NodeResult:
        await asyncio.sleep(3600)
        return OK


def test_a_stalled_attempt_is_cancelled_and_fails_stalled_into_the_ladder(tmp_path: Path) -> None:
    step = node("step", "script", script="scripts/step.py")
    step |= {"timeout": {"idle_seconds": 1}, "retry": {"max_tries": 1}}
    run = flow(
        tmp_path,
        [node("start", "trigger"), step],
        {"start": {"main": [edge("step")]}},
        executors={"script": Hang()},
        worker=LocalWorker(concurrency=3, heartbeat_seconds=3600),
        watch_every=0.2,
    )

    outcome = run.start()

    failed = of_kind(run.events(outcome.run_id), "node_failed")
    assert [(f["code"], f["retryable"], f["effect_state"]) for f in failed] == [
        ("stalled", True, "unknown")
    ]
    assert outcome.status == "failed"


def agents(names: list[str]) -> list[dict[str, Any]]:
    return [node("start", "trigger"), *(node(n, "agent") | {"role": "builder"} for n in names)]


def test_a_guard_of_two_agents_never_starts_the_third(tmp_path: Path) -> None:
    agent = Planted(OK)
    run = flow(
        tmp_path,
        agents(["a", "b", "c"]),
        {"start": {"main": [edge("a"), edge("b"), edge("c")]}},
        runaway={"agents": 2},
        executors={"agent": agent},
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    assert sorted(job.node_id for job in agent.jobs) == ["a", "b"]
    assert (outcome.status, outcome.reason) == ("waiting", "runaway")
    assert [line["line"] for line in of_kind(events, "log")] == [
        "runaway guard: agents 2 of 2; the run pauses"
    ]
    assert run.items() == []


def test_degrade_goes_on_once_on_the_cheapest_candidates_then_pauses(tmp_path: Path) -> None:
    agent = Planted(OK)
    run = flow(
        tmp_path,
        agents(["a", "b", "c", "d"]),
        {"start": {"main": [edge("a"), edge("b"), edge("c")]}, "a": {"main": [edge("d")]}},
        runaway={"agents": 2, "on_runaway": "degrade"},
        executors={"agent": agent},
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    assert sorted(job.node_id for job in agent.jobs) == ["a", "b", "c"]
    assert [job.resolved_model for job in agent.jobs] == [{"degrade": True}] * 3
    assert [line["on_runaway"] for line in of_kind(events, "log")] == ["degrade", "pause"]
    assert outcome.status == "waiting"


def test_a_ledger_write_error_stops_claiming_and_raises_a_black_system_fault(
    tmp_path: Path,
) -> None:
    ledgers: list[Ledger] = []

    def close_the_ledger(_: NodeJob) -> NodeResult:
        ledgers[0].close()
        return OK

    run = flow(
        tmp_path,
        [node("start", "trigger"), node("step", "script", script="scripts/step.py")],
        {"start": {"main": [edge("step")]}},
        executors={"script": Planted(close_the_ledger)},
    )

    async def go() -> tuple[str, bool, str]:
        with Ledger.open(run.home) as ledger:
            ledgers.append(ledger)
            engine = run.engine(ledger)
            outcome = await engine.start(run.root, run.definition, mode="test", inputs=None)
            with pytest.raises(Refused) as refused:
                await engine.start(run.root, run.definition, mode="test", inputs=None)
            return outcome.status, engine.claiming, str(refused.value)

    assert asyncio.run(go()) == (
        "interrupted",
        False,
        "the engine stopped claiming work after a ledger write error",
    )
    [item] = run.items()
    assert (item.category, item.severity, item.cause) == (
        "system_fault",
        "black",
        "the ledger is closed",
    )
