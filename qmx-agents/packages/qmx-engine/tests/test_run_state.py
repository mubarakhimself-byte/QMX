"""BUG1: run state, waits and resume. One test per row of 40-retriage's BUG-1 packet, each named
after its row: held runs leave a wake and resume on their own (B-63, B-54), the ledger and the
fold keep one run and one attempt straight (B-25, L-28, L-31, L-32), cancels stop what they name
and nothing more (B-37, B-66, L-69), triggers apply their pins and report what a fire did (B-60,
B-72, L-65), and the rest of the row set (B-42, B-57, L-33, L-37, L-38, L-47, L-80)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fake_library import fake_service
from fake_port import CARD, FakePort, agent, agent_files
from flows import edge, events_of, folder, node, workflow
from planted import Planted, fails, flow, of_kind, steps
from pydantic import JsonValue
from scheduled import Clock, enabled, fires_of

from qmx_engine.core.fold import fold
from qmx_engine.core.state import Held as Hold
from qmx_engine.core.waits import due
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader, Transaction
from qmx_engine.nodes.base import NodeJob, Waiting
from qmx_engine.nodes.wait import utc_text
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.ports.settings import StaticSettings
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.trace_export import run_files
from qmx_engine.triggers import rows
from qmx_engine.triggers.claims import settle, settle_run
from qmx_engine.triggers.ticker import Scheduler
from qmx_engine.workers.effects import after_unknown

START = node("start", "trigger")
T0 = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)
FLAKY = """
    import json, sys
    from pathlib import Path
    counter = Path(json.load(sys.stdin)["in"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    sys.exit(1 if tries == 1 else 0)
"""
SLEEPER = """
    import json, sys, time
    from pathlib import Path
    given = json.load(sys.stdin)["in"]
    if isinstance(given, dict) and "trigger" in given:
        Path(given["trigger"]["fire_id"] + ".started").touch()
        time.sleep(60)
    if isinstance(given, str):
        Path(given).touch()
        time.sleep(60)
    print(json.dumps("done"))
"""


def settings_of(created: Event) -> dict[str, Any]:
    return cast(dict[str, Any], created.data["settings"])


def wakes(home: Path) -> list[tuple[str, str]]:
    with Reader.open(home) as reader:
        return reader.connection.execute("SELECT run_id, resume_at FROM wakes").fetchall()


async def tick_until_ended(svc: EngineService, run_id: str, ticks: int = 40) -> list[Event]:
    """Tick the scheduler every quarter second until the run's last event ends it."""
    ticker = Scheduler(svc.ctx)
    for _ in range(ticks):
        await ticker.tick()
        await ticker.settle()
        found = events_of(svc.ctx.home, run_id)
        if found[-1].kind == "run_finished":
            return found
        await asyncio.sleep(0.25)
    raise AssertionError(f"run {run_id} never resumed on its own")


type Held = tuple[Outcome, list[tuple[str, str]], list[Event]]


def held_alone(root: Path, home: Path, inputs: JsonValue = None) -> Held:
    """Start the run with nobody ticking, then let the scheduler alone carry it to its end."""
    found = checked(root)
    assert not isinstance(found, list), found

    async def go() -> Held:
        with fake_service(home) as svc:
            outcome = await svc.ctx.engine.start(root, found[1], mode="test", inputs=inputs)
            held = wakes(home)
            return outcome, held, await tick_until_ended(svc, outcome.run_id)

    return asyncio.run(go())


def test_b63_a_time_wait_writes_a_wake_and_the_ticker_resumes_it(tmp_path: Path) -> None:
    home = tmp_path / "home"
    root = folder(
        tmp_path / "wf",
        [START, node("pause", "wait", seconds=1)],
        {"start": {"main": [edge("pause")]}},
        {},
    )

    outcome, held, events = held_alone(root, home)

    hold = next(e.data for e in events if e.kind == "node_waiting")
    assert (outcome.status, held) == ("waiting", [(outcome.run_id, hold["resume_at"])])
    assert [e.data["reason"] for e in events if e.kind == "run_resumed"] == ["wake"]
    assert (events[-1].data["status"], wakes(home)) == ("passed", [])


def test_b63_a_retry_backoff_writes_a_wake_and_the_ticker_resumes_it(tmp_path: Path) -> None:
    home = tmp_path / "home"
    flaky = node("flaky", "script", script="scripts/flaky.py")
    flaky["retry"] = {"backoff_seconds": [1]}
    root = folder(
        tmp_path / "wf", [START, flaky], {"start": {"main": [edge("flaky")]}}, {"flaky": FLAKY}
    )

    outcome, held, events = held_alone(root, home, str(tmp_path / "tries.txt"))

    retry = next(e.data for e in events if e.kind == "ladder_step")
    assert (outcome.status, held) == ("waiting", [(outcome.run_id, retry["resume_at"])])
    assert (events[-1].data["status"], wakes(home)) == ("passed", [])


def test_b54_a_limit_wait_returns_waiting_at_once_and_leaves_its_wake(tmp_path: Path) -> None:
    reset = utc_text(datetime.now(UTC) + timedelta(hours=3))
    run = flow(
        tmp_path,
        [START, node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={"script": Planted(Waiting("limit", reset))},
    )
    began = datetime.now(UTC)

    outcome = run.start()

    assert (outcome.status, outcome.reason) == ("waiting", "limit")
    assert datetime.now(UTC) - began < timedelta(seconds=30)
    assert wakes(run.home) == [(outcome.run_id, reset)]


def test_b25_the_ledger_refuses_a_second_run_created_and_the_fold_keeps_the_first(
    tmp_path: Path,
) -> None:
    with Ledger.open(tmp_path) as ledger:
        ledger.append("run-1", "run_created", {"settings": {"a": 1}}, at=T0.isoformat())
        with pytest.raises(ValueError, match="already has a run_created"):
            ledger.append("run-1", "run_created", {"settings": {"a": 2}}, at=T0.isoformat())
    second = Event(2, "run-1", T0.isoformat(), "run_created", {"settings": {"a": 2}})
    first = Event(1, "run-1", T0.isoformat(), "run_created", {"settings": {"a": 1}})

    state = fold(workflow([START], {}), [first, second])

    assert (state.settings, state.unfoldable) == ({"a": 1}, None)
    assert [e.seq for e in events_of(tmp_path, "run-1")] == [1]


def test_l28_an_operation_raising_a_base_exception_does_not_kill_the_writer(
    tmp_path: Path,
) -> None:
    def leaves(txn: Transaction) -> None:
        raise SystemExit(3)

    with Ledger.open(tmp_path) as ledger:
        with pytest.raises(SystemExit):
            ledger.write(leaves)
        written = ledger.append("run-1", "log", {"line": "after"}, at=T0.isoformat())

    assert written.seq == 1


def test_l31_non_object_data_is_refused_with_a_value_error(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger, pytest.raises(ValueError, match="not a JSON object"):
        ledger.append("run-1", "node_started", [1, 2], at=T0.isoformat())  # pyright: ignore[reportArgumentType]


def test_l32_a_late_ending_of_an_earlier_attempt_settles_nothing() -> None:
    definition = workflow([START], {})
    keys: dict[str, JsonValue] = {"node_id": "start", "iteration": 0, "partition": None}
    events = [
        Event(1, "run-1", T0.isoformat(), "run_created", {"settings": {}}),
        Event(2, "run-1", T0.isoformat(), "node_scheduled", keys | {"attempt": 2}),
        Event(3, "run-1", T0.isoformat(), "node_finished", keys | {"attempt": 1, "outputs": {}}),
    ]

    state = fold(definition, events)

    assert [(run.phase, run.attempt) for run in state.nodes.values()] == [("scheduled", 2)]


def test_b37_a_reversible_attempt_cancelled_through_the_worker_is_not_retried(
    tmp_path: Path,
) -> None:
    home, marker = tmp_path / "home", tmp_path / "started"
    sleeper = node("sleeper", "script", script="scripts/sleeper.py")
    sleeper["retry"] = {"max_tries": 3, "backoff_seconds": [0]}
    root = folder(
        tmp_path / "wf",
        [START, sleeper],
        {"start": {"main": [edge("sleeper")]}},
        {"sleeper": SLEEPER},
    )
    found = checked(root)
    assert not isinstance(found, list), found

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS)
            run = asyncio.create_task(engine.start(root, found[1], mode="test", inputs=str(marker)))
            while not marker.exists():
                await asyncio.sleep(0.05)
            engine.worker.cancel(next(iter(engine.worker.running)))
            return await run

    outcome = asyncio.run(go())
    events = events_of(home, outcome.run_id)

    assert (outcome.status, steps(events)) == ("failed", ["park"])
    assert [e.data["node_id"] for e in events if e.kind == "node_scheduled"] == [
        "start",
        "sleeper",
    ]


def test_b66_cancelling_a_parent_stops_its_running_child(tmp_path: Path) -> None:
    home, marker = tmp_path / "home", tmp_path / "started"
    root = folder(
        tmp_path / "wf",
        [START, node("call", "subworkflow", workflow="child")],
        {"start": {"main": [edge("call")]}},
        {},
    )
    folder(
        root / "child",
        [START, node("sleeper", "script", script="scripts/sleeper.py")],
        {"start": {"main": [edge("sleeper")]}},
        {"sleeper": SLEEPER},
    )
    found = checked(root)
    assert not isinstance(found, list), found

    async def go() -> tuple[Outcome, list[str]]:
        with fake_service(home) as svc:
            run = asyncio.create_task(
                svc.ctx.engine.start(root, found[1], mode="test", inputs=str(marker))
            )
            while not marker.exists():
                await asyncio.sleep(0.05)
            parent = next(iter(svc.ctx.engine.live))
            stopped = svc.runs.cancel(parent)
            return await asyncio.wait_for(run, 30), stopped

    outcome, stopped = asyncio.run(go())
    child = f"{outcome.run_id}.call.0.1"

    assert (outcome.status, stopped) == ("stopped", [outcome.run_id, child])
    assert [e.kind for e in events_of(home, child)].count("run_cancelled") == 1
    assert [e.kind for e in events_of(home, outcome.run_id)].count("run_cancelled") == 1


def test_l69_a_fire_whose_run_is_cancelled_ends_cancelled_at_once(tmp_path: Path) -> None:
    bundle = folder(
        tmp_path / "bundle",
        [START, node("sleeper", "script", script="scripts/sleeper.py")],
        {"start": {"main": [edge("sleeper")]}},
        {"sleeper": SLEEPER},
    )
    with enabled(tmp_path / "home", Clock(T0), bundle) as (svc, version):
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
        )
        ticker = Scheduler(svc.ctx)

        async def go() -> dict[str, JsonValue]:
            report = await ticker.run_now(trigger.id)
            while not any(svc.ctx.engine.live):
                await asyncio.sleep(0.05)
            run_id = next(iter(svc.ctx.engine.live))
            while not any(svc.ctx.engine.worker.running):
                await asyncio.sleep(0.05)
            svc.runs.cancel(run_id)
            await asyncio.wait_for(ticker.settle(), 30)
            return report

        report = asyncio.run(go())
        found = fires_of(tmp_path / "home", trigger.id)

    assert report["status"] == "running"
    assert [(f.status, f.detail) for f in found] == [("cancelled", "the run was cancelled")]


def test_b72_run_now_says_why_a_fire_was_not_claimed(tmp_path: Path) -> None:
    with enabled(tmp_path, Clock(T0)) as (svc, version):
        ledger = svc.ctx.engine.ledger
        trigger = rows.create(
            ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
        )

        def running(txn: Transaction) -> None:
            txn.connection.execute(
                "INSERT INTO fires (id, trigger_id, occurrence_at, status, claimed_by,"
                " claimed_at, lease_until, merged) VALUES ('fire-old', ?, ?, 'running', 'other',"
                " ?, ?, 0)",
                (trigger.id, T0.isoformat(), T0.isoformat(), (T0 + timedelta(hours=1)).isoformat()),
            )

        ledger.write(running)
        report = asyncio.run(Scheduler(svc.ctx).run_now(trigger.id))

    assert (report["status"], report["detail"]) == (
        "pending",
        "the trigger already runs 1 of max_concurrent 1 fires",
    )


def test_b60_an_after_trigger_fires_on_a_run_started_by_runs_start(tmp_path: Path) -> None:
    with enabled(tmp_path, Clock(T0)) as (svc, version):
        item = svc.versions.get(version).item
        after = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=item,
            pinned_object=version,
            spec=rows.After(item),
            caller=OPERATOR,
            now=T0,
        )
        view = asyncio.run(svc.runs.start(version, caller=OPERATOR))
        found = fires_of(tmp_path, after.id)

    assert view.status == "passed"
    upstream = [cast(dict[str, Any], (f.payload or {})["upstream"])["run_id"] for f in found]
    assert ([f.status for f in found], upstream) == (["pending"], [view.run_id])


def test_b60_a_trigger_s_role_and_effort_pins_steer_its_run(tmp_path: Path) -> None:
    root = agent_files(
        folder(tmp_path / "wf", [START, agent("read")], {"start": {"main": [edge("read")]}}, {})
    )
    found = checked(root)
    assert not isinstance(found, list), found
    home = tmp_path / "home"
    pins: dict[str, JsonValue] = {"roles": {"reader": "claude/sonnet"}, "effort": "high"}

    async def go() -> Outcome:
        with fake_service(home, harness=FakePort(CARD)) as svc:
            return await svc.ctx.engine.start(root, found[1], mode="live", inputs=None, pins=pins)

    outcome = asyncio.run(go())
    events = events_of(home, outcome.run_id)
    started = next(
        e.data for e in events if e.kind == "node_started" and e.data["node_id"] == "read"
    )

    assert events[0].data["pins"] == pins
    assert settings_of(events[0])["roles.reader"] == ["claude/sonnet"]
    assert (started["model"], started["effort"]) == ("sonnet", "high")


def test_b42_settings_are_read_when_a_run_starts_not_when_the_engine_opens(
    tmp_path: Path,
) -> None:
    settings = dict(DEFAULTS) | {"retry.max_tries": 1}
    port = StaticSettings(settings)
    run = flow(tmp_path, [START], {})

    async def go() -> list[Outcome]:
        with Ledger.open(run.home) as ledger:
            engine = Engine(run.home, ledger, settings=port)
            first = await engine.start(run.root, run.definition, mode="test", inputs=None)
            settings["retry.max_tries"] = 4
            second = await engine.start(run.root, run.definition, mode="test", inputs=None)
            return [first, second]

    outcomes = asyncio.run(go())

    recorded = [settings_of(run.events(o.run_id)[0])["retry.max_tries"] for o in outcomes]
    assert recorded == [1, 4]


@pytest.mark.parametrize(
    ("definition", "decision"),
    [
        ({"type": "llm", "effect": "irreversible"}, "inbox"),
        ({"type": "agent", "effect": "irreversible_external"}, "inbox"),
        ({"type": "agent", "effect": "irreversible", "idempotent": True}, "retry"),
        ({"type": "llm", "effect": "compensable"}, "retry"),
        ({"type": "llm"}, "retry"),
    ],
)
def test_b57_a_model_node_that_declares_an_irreversible_effect_follows_that_class(
    definition: dict[str, JsonValue], decision: str
) -> None:
    assert after_unknown(definition, 0) == decision


def test_l33_an_executor_that_raises_fails_its_node_and_the_run_parks(tmp_path: Path) -> None:
    def raises(job: NodeJob) -> Any:
        raise RuntimeError("broken executor")

    run = flow(
        tmp_path,
        [START, node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={"script": Planted(raises)},
    )

    outcome = run.start()

    failed = of_kind(run.events(outcome.run_id), "node_failed")
    assert (outcome.status, [f["code"] for f in failed]) == ("failed", ["executor_error"])


def test_l37_every_instant_the_runner_writes_is_utc_in_one_form(tmp_path: Path) -> None:
    run = flow(
        tmp_path,
        [START, node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={"script": Planted(Waiting("limit", "2026-10-17T14:00:00+02:00"))},
        wall=lambda: datetime(2026, 10, 17, 9, 0),  # naive, read as UTC
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    clock = [e.data["now"] for e in events if e.kind == "clock_tick"]
    waited = [str(e.data["resume_at"]) for e in events if e.kind == "node_waiting"]
    assert (set(clock), waited) == ({"2026-10-17T09:00:00+00:00"}, ["2026-10-17T12:00:00+00:00"])
    assert due(Hold(waited[0], None, 1), "2026-10-17T11:59:59.900000+00:00", ()) is False


def test_l38_a_node_id_with_a_colon_is_refused(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("a:0", "wait", seconds=1)],
        {"start": {"main": [edge("a:0")]}},
        {},
    )

    found = checked(root)

    assert isinstance(found, list)
    assert [p.code for p in found] == ["node_id_invalid"]


def test_l47_an_inbox_item_shows_the_ladder_step_taken_for_its_failure(tmp_path: Path) -> None:
    run = flow(
        tmp_path,
        [START, node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={"script": Planted(fails("the harness broke", code="harness_error"))},
    )

    outcome = run.start()

    [item] = run.items()
    assert (outcome.status, item.tried) == ("waiting", ("retry",))


def test_l65_a_late_waiting_never_reopens_a_fire_a_wake_already_ended(tmp_path: Path) -> None:
    with enabled(tmp_path, Clock(T0)) as (svc, version):
        ledger = svc.ctx.engine.ledger
        trigger = rows.create(
            ledger,
            workflow_item=svc.versions.get(version).item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
        )
        fire_id = rows.fire_now(ledger, trigger.id, T0, {})

        def running(txn: Transaction) -> None:
            txn.connection.execute(
                "UPDATE fires SET status = 'running', run_id = 'run-x' WHERE id = ?", (fire_id,)
            )

        ledger.write(running)
        (fire,) = fires_of(tmp_path, trigger.id)
        ledger.write(settle_run("run-x", "ok", T0.isoformat(), {"done": True}))
        ledger.write(settle(fire, "waiting", T0.isoformat(), detail="late"))
        found = fires_of(tmp_path, trigger.id)

    assert [(f.status, f.detail) for f in found] == [("ok", None)]


def test_l80_an_artifact_a_later_node_removed_is_left_out_of_the_export(tmp_path: Path) -> None:
    listed = Event(
        3,
        "run-1",
        T0.isoformat(),
        "node_finished",
        {"node_id": "make", "attempt": 1, "outputs": {}, "artifacts": ["gone.txt"]},
    )
    with LibraryFake.open(tmp_path) as library:
        stored = run_files(tmp_path, "run-1", [listed], library)

    assert stored == []


def test_the_wake_rows_hold_rfc3339_utc_instants(tmp_path: Path) -> None:
    run = flow(
        tmp_path,
        [START, node("pause", "wait", until="2026-10-17T11:00:00+02:00")],
        {"start": {"main": [edge("pause")]}},
    )

    async def go() -> Outcome:
        with Ledger.open(run.home) as ledger:
            engine = Engine(run.home, ledger, wall=lambda: T0 - timedelta(hours=1))
            return await engine.start(run.root, run.definition, mode="test", inputs=None)

    outcome = asyncio.run(go())

    assert (outcome.status, outcome.reason) == ("waiting", "waiting on pause")
    assert wakes(run.home) == [(outcome.run_id, "2026-10-17T09:00:00.000000+00:00")]
