"""Every resumed run lands. A "Clippings into research" run killed after its write step and before
its first summary gets that summary, and a live one's clippings reach `main`, whichever path picks
it up again: the ticker at the next host start, the REST door, the command line, or a cancel. A run
that dies again during its first resume lands each clipping once. A run whose `run_created` was
written before it named its version resumes by its last summary, or logs one line naming the run.
Every run goes through the engine over `EngineLibraryAdapter(Store.open(tmp))`."""

from __future__ import annotations

import asyncio
import logging
import shutil
import sqlite3
from collections.abc import Awaitable, Generator
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.service import ControlService
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.principal import state_ref
from qmx_library.store import Store
from scheduled import Clock
from test_templates import CLIPPINGS, answers

from qmx_engine.__main__ import main
from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader, ledger_path
from qmx_engine.nodes.base import NodeJob, NodeResult
from qmx_engine.ports.library import Bundle, JsonObject, RunSummary
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.runs import RunView
from qmx_engine.triggers import rows
from qmx_engine.triggers.ticker import Scheduler

T0 = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
FIXTURE: JsonObject = {"fixture": True}
LEASE = 300


class Hangs:
    """A grade step that never answers, so the engine can be killed with the write step done."""

    def __init__(self) -> None:
        self.reached = asyncio.Event()

    async def run(self, job: NodeJob) -> NodeResult:
        self.reached.set()
        await asyncio.Event().wait()
        raise AssertionError(f"{job.node_id} answered")


@contextmanager
def service(home: Path, clock: Clock) -> Generator[EngineService]:
    with (
        Store.open(home / "library", redactor=redact) as store,
        EngineService.open(
            home, library=EngineLibraryAdapter(store), harness=answers(), clock=clock
        ) as svc,
    ):
        yield svc


@pytest.fixture(scope="module")
def made(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    """A QMX folder with "Clippings into research" tested, published and enabled, made once."""
    home = resolve(tmp_path_factory.mktemp("made") / "QMX", create=True, drives=[]).home
    with service(home, Clock(T0)) as svc:
        item = svc.drafts.put(CLIPPINGS.name, Bundle.read(CLIPPINGS), 0, caller=OPERATOR).item
        assert asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs=FIXTURE)).status == "passed"
        version = svc.versions.publish(item, "0.1.0", caller=OPERATOR)
        svc.versions.enable(version, caller=OPERATOR)
    return home, item, version


@pytest.fixture
def home(made: tuple[Path, str, str], tmp_path: Path) -> Path:
    """A copy of that folder's data; its QMX folder, the one `--home` names, is its parent."""
    return Path(shutil.copytree(made[0].parent, tmp_path / "QMX")) / made[0].name


async def killed(svc: EngineService, started: Awaitable[object]) -> None:
    """Start the work, wait until its run reaches the grade step, then kill every task."""
    hangs = Hangs()
    svc.ctx.engine.executors = {"grader": hangs}
    work = asyncio.ensure_future(started)
    await hangs.reached.wait()
    going = {work, *asyncio.all_tasks()} - {asyncio.current_task()}
    for task in going:
        task.cancel()
    await asyncio.gather(*going, return_exceptions=True)


def run_ids(home: Path, mode: str) -> list[str]:
    with Reader.open(home) as reader:
        found = reader.connection.execute(
            "SELECT run_id FROM events WHERE kind = 'run_created'"
            " AND json_extract(data, '$.mode') = ?",
            (mode,),
        ).fetchall()
    return [str(run_id) for (run_id,) in found]


def died(home: Path, clock: Clock, version: str) -> str:
    """A live run of the version killed after its write step, before its first summary."""
    before = run_ids(home, "live")
    with service(home, clock) as svc:
        asyncio.run(killed(svc, svc.runs.start(version, caller=OPERATOR, inputs=FIXTURE)))
    (run_id,) = set(run_ids(home, "live")) - set(before)
    return run_id


def written(home: Path, run_id: str) -> list[str]:
    with Reader.open(home) as reader:
        events = reader.events(run_id)
    finished = [
        cast(dict[str, Any], e.data["outputs"])["main"]
        for e in events
        if e.kind == "node_finished" and e.data.get("node_id") == "write"
    ]
    return sorted(
        receipt["object_id"]
        for receipt in finished[0]["library_written"]
        if receipt["op"] == "put_artifact"
    )


def archived(store: Store, object_id: str) -> bool:
    item = store.get(store.engine, object_id).item
    found = store.head(item, state_ref(item))
    return found is not None and found[0] == "archived"


def landed(home: Path, run_id: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """The run's summaries as (status, version, starter), and the clippings on `main`."""
    with Store.open(home / "library", redactor=redact) as store:
        library = EngineLibraryAdapter(store)
        summaries = [
            (str(s.fields["status"]), str(s.fields["object_id"]), str(s.fields["started_by"]))
            for s in library.objects(run_id, "workflow-run")
        ]
        on_main = sorted(
            object_id
            for _, object_id in store.heads_on("main")
            if store.get(store.engine, object_id).fields.get("type") == "clipping"
        )
    return summaries, on_main


def test_a_trigger_fired_run_killed_before_its_summary_lands_when_the_ticker_resumes_it(
    made: tuple[Path, str, str], home: Path
) -> None:
    _, item, version = made
    clock = Clock(T0)
    with service(home, clock) as svc:
        ledger = svc.ctx.engine.ledger
        trigger = rows.create(
            ledger,
            workflow_item=item,
            pinned_object=version,
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
        )
        rows.fire_now(ledger, trigger.id, T0, FIXTURE)
        asyncio.run(killed(svc, Scheduler(svc.ctx, claimant="a").tick()))
    (run_id,) = run_ids(home, "live")
    before = landed(home, run_id)
    clock.move(seconds=LEASE + 1)

    async def restarted() -> None:
        with service(home, clock) as svc:
            ticker = Scheduler(svc.ctx, claimant="b")
            await ticker.tick()
            await ticker.settle()

    asyncio.run(restarted())

    assert before == ([], [])
    assert landed(home, run_id) == ([("passed", version, "operator")], written(home, run_id))
    assert len(written(home, run_id)) == 2


def test_a_run_killed_before_its_summary_lands_when_resumed_over_rest_and_a_cancel_summarizes(
    made: tuple[Path, str, str], home: Path
) -> None:
    version = made[2]
    clock = Clock(T0)
    resumed, cancelled = died(home, clock, version), died(home, clock, version)

    async def through_the_door() -> None:
        with Store.open(home / "library", redactor=redact) as store:
            async with EngineDoor.open(
                ControlService(home),
                library=EngineLibraryAdapter(store),
                harness=answers(),
                clock=clock,
                wait_seconds=60,
                principal=lambda: OPERATOR,
            ) as door:
                await asyncio.to_thread(door.workflow_runs_resume, resumed)
                await asyncio.to_thread(door.workflow_runs_cancel, cancelled)

    asyncio.run(through_the_door())

    summaries, on_main = landed(home, resumed)
    assert summaries == [("passed", version, "operator")]
    assert set(written(home, resumed)) <= set(on_main)
    assert landed(home, cancelled)[0] == [("stopped", version, "operator")]


def test_a_cancel_that_reaches_a_run_as_it_passes_summarizes_it_passed(
    made: tuple[Path, str, str], home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version = made[2]
    clock = Clock(T0)
    run_id = died(home, clock, version)
    assert main(["resume", run_id, "--home", str(home.parent)]) == 0

    async def cancelled_as_it_passed() -> None:
        with Store.open(home / "library", redactor=redact) as store:
            async with EngineDoor.open(
                ControlService(home),
                library=EngineLibraryAdapter(store),
                harness=answers(),
                clock=clock,
                principal=lambda: OPERATOR,
            ) as door:
                runs = door.svc.runs
                read = runs.get
                stale = [replace(read(run_id), status="running")]

                def first_read_predates_the_end(rid: str) -> RunView:
                    return stale.pop() if stale else read(rid)

                def reached_the_drive_as_it_ended(rid: str, reason: str = "operator") -> list[str]:
                    return [rid]

                monkeypatch.setattr(runs, "get", first_read_predates_the_end)
                monkeypatch.setattr(runs, "cancel", reached_the_drive_as_it_ended)
                await asyncio.to_thread(door.workflow_runs_cancel, run_id)

    asyncio.run(cancelled_as_it_passed())

    assert landed(home, run_id)[0] == [
        ("passed", version, "operator"),
        ("passed", version, "operator"),
    ]


def test_a_run_killed_twice_before_its_summary_lands_each_clipping_once(
    made: tuple[Path, str, str], home: Path
) -> None:
    version = made[2]
    clock = Clock(T0)
    run_id = died(home, clock, version)
    with service(home, clock) as svc:
        asyncio.run(killed(svc, svc.ctx.engine.resume(run_id)))

    assert main(["resume", run_id, "--home", str(home.parent)]) == 0
    summaries, on_main = landed(home, run_id)
    assert summaries == [("passed", version, "operator")]
    assert on_main == written(home, run_id)
    assert len(on_main) == 2


def older(home: Path, run_ids: list[str]) -> None:
    """Strip what this release adds to `run_created`, as a ledger written before it holds it."""
    with sqlite3.connect(ledger_path(home)) as db:
        for run_id in run_ids:
            db.execute(
                "UPDATE events SET data = json_remove(data, '$.object_id', '$.started_by')"
                " WHERE run_id = ? AND seq = 1",
                (run_id,),
            )


def test_an_older_run_resumes_by_its_last_summary_or_logs_one_line_naming_it(
    made: tuple[Path, str, str], home: Path, caplog: pytest.LogCaptureFixture
) -> None:
    item, version = made[1], made[2]
    clock = Clock(T0)
    summarized, bare = died(home, clock, version), died(home, clock, version)
    older(home, [summarized, bare])
    with Store.open(home / "library", redactor=redact) as store:
        earlier = RunSummary(
            summarized, item, version, "live", "interrupted", None, {}, {}, None, "chat:s1", False
        )
        EngineLibraryAdapter(store).put_run_summary(earlier, principal=f"run:{summarized}")
    with Reader.open(home) as reader:
        created = reader.events(bare)[0].data

    with caplog.at_level(logging.WARNING, logger="qmx_engine.service.runs"):
        codes = [
            main(["resume", run_id, "--home", str(home.parent)]) for run_id in (summarized, bare)
        ]

    assert "object_id" not in created
    assert codes == [0, 0]
    assert landed(home, summarized)[0] == [
        ("interrupted", version, "chat:s1"),
        ("passed", version, "chat:s1"),
    ]
    assert landed(home, bare)[0] == []
    assert not set(written(home, bare)) & set(landed(home, bare)[1])
    assert [r.getMessage() for r in caplog.records] == [
        f"run {bare} cannot land: it started before QMX recorded which version it runs and who"
        " started it, and it has no earlier summary to take them from"
    ]


def test_a_test_run_killed_before_its_summary_gets_it_and_its_samples_are_archived(
    made: tuple[Path, str, str], home: Path
) -> None:
    item = made[1]
    clock = Clock(T0)
    before = run_ids(home, "test")
    with service(home, clock) as svc:
        asyncio.run(killed(svc, svc.tests.run(item, caller=OPERATOR, inputs=FIXTURE)))
    (run_id,) = set(run_ids(home, "test")) - set(before)

    assert main(["resume", run_id, "--home", str(home.parent)]) == 0
    with Store.open(home / "library", redactor=redact) as store:
        library = EngineLibraryAdapter(store)
        summaries = [s.fields["status"] for s in library.objects(run_id, "workflow-run")]
        states = [archived(store, object_id) for object_id in written(home, run_id)]
        reports = [r.fields["run_id"] for r in library.objects(item, "test-report")]
        found = {hit.object_id for hit in store.search(store.engine, "London breakout")}

    assert summaries == ["passed"]
    assert states == [True, True]
    assert run_id not in reports
    assert not found & set(written(home, run_id))
