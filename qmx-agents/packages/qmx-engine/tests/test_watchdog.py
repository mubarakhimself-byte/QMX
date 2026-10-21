"""The stuck detector on the runner (AD-16), the crash-loop counter, a limits pause he wrote, and
the ledger-fault rule."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path

import pytest
from flows import edge, node
from planted import OK, T0, Planted, flow, of_kind
from qma.harness import Pulse

from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok
from qmx_engine.runner import Refused
from qmx_engine.settings import DEFAULTS
from qmx_engine.watchdog import Watchdog, Watched
from qmx_engine.workers.local import LocalWorker

QUICK = {"timeout.grace": 1}


def test_a_host_sleep_counts_as_two_ticks_and_nothing_else_moves_the_clock() -> None:
    dog = Watchdog(DEFAULTS, tick_seconds=60)
    quiet = [Watched("a", "agent", Pulse(3))]

    acts = [dog.tick(T0, quiet), dog.tick(T0 + timedelta(hours=2), quiet)]
    acts.append(dog.tick(T0 + timedelta(hours=2, seconds=120), quiet))

    assert [[a.act for a in found] for found in acts] == [[], [], ["warn"]]
    assert acts[2][0].quiet_seconds == 240


class Hang:
    async def run(self, job: NodeJob) -> NodeResult:
        await asyncio.sleep(3600)
        return OK


def test_a_silent_attempt_warns_then_fails_stalled_into_the_ladder_despite_heartbeats(
    tmp_path: Path,
) -> None:
    step = node("step", "script", script="scripts/step.py")
    step |= {"timeout": {"idle_seconds": 1}, "retry": {"max_tries": 1}}
    run = flow(
        tmp_path,
        [node("start", "trigger"), step],
        {"start": {"main": [edge("step")]}},
        executors={"script": Hang()},
        worker=LocalWorker(heartbeat_seconds=0.05),
        watch_every=0.2,
    )

    outcome = run.start(QUICK)

    events = run.events(outcome.run_id)
    failed = of_kind(events, "node_failed")
    assert [(f["code"], f["retryable"], f["effect_state"]) for f in failed] == [
        ("stalled", True, "unknown")
    ]
    assert [line["level"] for line in of_kind(events, "log")] == ["warn"]
    assert outcome.status == "failed"


def test_a_cpu_busy_script_runs_past_its_idle_window(tmp_path: Path) -> None:
    busy = node("busy", "script", script="scripts/busy.py")
    busy["timeout"] = {"idle_seconds": 1}
    run = flow(
        tmp_path,
        [node("start", "trigger"), busy],
        {"start": {"main": [edge("busy")]}},
        watch_every=0.2,
    )
    spin = "import json, time\nend = time.time() + 4\nwhile time.time() < end:\n    pass\n"
    (run.root / "scripts" / "busy.py").write_text(spin + "print(json.dumps(1))\n", "utf-8")

    outcome = run.start(QUICK)

    assert outcome.status == "passed"
    assert of_kind(run.events(outcome.run_id), "node_failed") == []


def test_a_turns_limit_he_wrote_pauses_with_one_info_line_and_resumes_with_a_new_allowance(
    tmp_path: Path,
) -> None:
    names = ["a", "b", "c"]
    agent = Planted(Ok({"main": "done"}, span={"turns": 2}))
    run = flow(
        tmp_path,
        [node("start", "trigger"), *(node(n, "agent") | {"role": "builder"} for n in names)],
        {"start": {"main": [edge("a")]}, "a": {"main": [edge("b")]}, "b": {"main": [edge("c")]}},
        limits={"turns": 2},
        executors={"agent": agent},
    )

    paused = run.start()
    lines = [line["line"] for line in of_kind(run.events(paused.run_id), "log")]
    resumed = run.resume(paused.run_id)
    again = run.resume(paused.run_id)

    assert (paused.status, paused.reason) == ("waiting", "limits")
    assert lines == ["limits: turns 2 of 2; the run pauses until it is resumed"]
    assert [resumed.status, again.status] == ["waiting", "passed"]
    assert [job.node_id for job in agent.jobs] == names
    assert run.items() == []


def test_the_engine_dying_mid_run_three_times_parks_with_one_inbox_item(tmp_path: Path) -> None:
    run = flow(
        tmp_path,
        [node("start", "trigger"), node("step", "script", script="scripts/step.py")],
        {"start": {"main": [edge("step")]}},
        executors={"script": Hang()},
    )

    async def die(first: bool) -> str:
        with Ledger.open(run.home) as ledger:
            engine = run.engine(ledger)
            begun = (
                engine.start(run.root, run.definition, mode="test", inputs=None, run_id="run-c")
                if first
                else engine.resume("run-c")
            )
            task = asyncio.ensure_future(begun)
            done, _ = await asyncio.wait({task}, timeout=1.0)
            if done:
                return task.result().status
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            return "killed"

    statuses = [asyncio.run(die(first)) for first in (True, False, False, False)]

    parks = [s for s in of_kind(run.events("run-c"), "ladder_step") if s["step"] == "park"]
    assert statuses == ["killed", "killed", "killed", "failed"]
    assert [park["crash_loop"] for park in parks] == [3]
    [item] = run.items()
    assert (item.category, item.blocks_run) == ("system_fault", True)


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
