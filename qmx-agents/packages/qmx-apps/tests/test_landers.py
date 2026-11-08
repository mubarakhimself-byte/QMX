"""AD-33 change 2: every job of an app whose provides name a lander is opened and closed by it.

The tester is a real supervised app, and `qmb-run` is the host's own composition over a real
Library store, so each test reads what landed in the Library.
"""

from __future__ import annotations

import asyncio
import shutil
import threading
import time
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from qmx_engine.ledger import redact
from qmx_engine.nodes.app_op import AppOp
from qmx_engine.nodes.base import NodeJob, Ok
from qmx_host.host import QMB_RUN, landers  # pyright: ignore[reportMissingTypeStubs]
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_apps.artifacts import Landing
from qmx_apps.errors import AppError, Document
from qmx_apps.supervisor import Supervisor

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
OPERATOR = Principal("operator")
APP = "tester"
SETTLE_SECONDS = 60.0
"""Test bound: how long a test waits for the supervisor to restart a tripped app."""

TESTER_JOB = """\
import hashlib
import json
import os
from pathlib import Path


def run(inputs):
    mode = inputs.get("mode", "finish")
    if mode == "die":
        os._exit(3)
    if mode == "raise":
        raise RuntimeError("the tester broke")
    if mode == "nothing":
        return None
    report = json.dumps({"trades": 2}).encode()
    (Path(inputs["run_folder"]) / "report.json").write_bytes(report)
    return {
        "output": "backtest-result",
        "data": {
            "run_id": inputs["run_id"],
            "status": "finished",
            "tester": {"app": "tester"},
            "measures": {"trades": 2},
            "consumed": inputs.get("consumed", []),
            "files": [
                {
                    "slot": "report",
                    "path": "report.json",
                    "fp": "fp1:sha256:" + hashlib.sha256(report).hexdigest(),
                }
            ],
        },
    }
"""

PLAIN_JOB = """\
def run(inputs):
    if inputs.get("leave"):
        return {"output": "snapshot", "data": {"observations": []}}
    return None
"""


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 1, 9, 30, tzinfo=UTC)

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


class Plain:
    """The host's plain artifact sink, recording what it was handed."""

    def __init__(self) -> None:
        self.landed: list[Landing] = []

    def __call__(self, landing: Landing) -> str:
        self.landed.append(landing)
        return f"plain-{len(self.landed)}"


def immediately(seconds: float, cancel: threading.Event) -> bool:
    return cancel.is_set()


@pytest.fixture
def store(tmp_path: Path) -> Generator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as opened:
        yield opened


@pytest.fixture
def plain() -> Plain:
    return Plain()


@pytest.fixture
def supervisor(tmp_path: Path, store: Store, plain: Plain) -> Generator[Supervisor]:
    owner = Supervisor(tmp_path / "home", library=plain, restart_wait=immediately)
    owner.attach_landers(landers(store, owner, "pc"))
    try:
        yield owner
    finally:
        owner.close()


def app(tmp_path: Path, job: str, extra: str) -> Path:
    target = tmp_path / "source"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), target / "server.py")
    manifest = target / "app.toml"
    text = (
        manifest.read_text()
        .replace('id = "exchange-status"', f'id = "{APP}"')
        .replace('mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]')
    )
    manifest.write_text(text + extra)
    (target / "job.py").write_text(job)
    return target


TESTER = '\n[provides.backtest-result]\nlander = "qmb-run"\nschema = { type = "object" }\n'
RESTARTS = '\n[breaker]\nrestart = "backoff"\n'


def unit(store: Store) -> str:
    draft = Draft("note", "unit-1", "unit-1", fields={})
    return store.put(OPERATOR, draft, on="main", expected_head=None).object_id


def tries(store: Store, run_id: str) -> list[str]:
    found = store.with_field("try", "run_id", run_id)
    return [str(store.get(OPERATOR, object_id).fields["state"]) for object_id in found]


def result(store: Store, run_id: str) -> Document:
    head = store.head(run_id, "main")
    assert head is not None, f"no backtest-result landed for {run_id}"
    found = store.get(OPERATOR, head[0])
    assert found.kind == "backtest-result"
    return dict(found.fields)


def opened_runs(store: Store) -> list[str]:
    found = [
        store.get(OPERATOR, object_id) for object_id in store.with_field("try", "state", "opened")
    ]
    return [str(item.fields["run_id"]) for item in found]


def until(check: Callable[[], bool], what: str) -> None:
    deadline = time.monotonic() + SETTLE_SECONDS
    while not check():
        assert time.monotonic() < deadline, what
        time.sleep(0.05)


def test_an_app_with_no_lander_runs_and_lands_its_job_as_before(
    tmp_path: Path, supervisor: Supervisor, plain: Plain, store: Store
) -> None:
    supervisor.install(app(tmp_path, PLAIN_JOB, ""), trust="first_party")
    supervisor.start(APP)

    ran = supervisor.run_job(APP, "job.py")
    left = supervisor.run_job(APP, "job.py", inputs={"leave": True})

    assert sorted(ran) == ["app_id", "instance_id", "job", "profile", "version"]
    assert [(it.output, it.lander, it.run, it.fields["type"]) for it in plain.landed] == [
        ("snapshot", None, None, "snapshot")
    ]
    assert cast(Document, left["artifact_ref"])["output"] == "snapshot"
    assert opened_runs(store) == []


def test_a_tester_job_lands_one_result_and_two_tries(
    tmp_path: Path, supervisor: Supervisor, plain: Plain, store: Store
) -> None:
    supervisor.install(app(tmp_path, TESTER_JOB, TESTER), trust="first_party")
    supervisor.start(APP)
    pinned = unit(store)

    ran = supervisor.run_job(APP, "job.py", inputs={"unit": pinned}, principal="operator")

    run_id = str(ran["run_id"])
    assert run_id.startswith("qmbr-pc-")
    landed = result(store, run_id)
    assert (landed["status"], landed["unit"], landed["measures"]) == (
        "finished",
        pinned,
        {"trades": 2},
    )
    assert tries(store, run_id) == ["opened", "landed"]
    assert plain.landed == []


def test_every_door_that_starts_a_job_crosses_the_lander(
    tmp_path: Path, supervisor: Supervisor, store: Store
) -> None:
    supervisor.install(app(tmp_path, TESTER_JOB, TESTER + RESTARTS), trust="first_party")
    supervisor.start(APP)
    pinned = unit(store)
    workflow = AppOp(supervisor.run_job, dispatch=supervisor.run_job)
    node = NodeJob(
        run_id="wf1",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition={
            "type": "app_op",
            "parameters": {"app": APP, "job": "job.py", "inputs": {"unit": pinned}},
        },
        inputs={},
        now=None,
    )

    asked = asyncio.run(workflow.run(node))
    with pytest.raises(AppError) as died:
        supervisor.run_job(
            APP, "job.py", inputs={"unit": pinned, "mode": "die"}, principal="operator"
        )
    until(lambda: supervisor.status(APP)["status"] == "running", "the tester restarts")
    after = supervisor.run_job(APP, "job.py", inputs={"unit": pinned}, principal="operator")

    assert isinstance(asked, Ok)
    by_workflow = str(cast(Document, asked.outputs["main"])["run_id"])
    killed, restarted = (run for run in opened_runs(store) if run != by_workflow)
    assert died.value.code == "not_running"
    assert result(store, by_workflow)["principal"] == "run:wf1"
    assert (tries(store, by_workflow), tries(store, killed), tries(store, restarted)) == (
        ["opened", "landed"],
        ["opened", "failed"],
        ["opened", "landed"],
    )
    assert result(store, killed)["status"] == "killed"
    assert str(after["run_id"]) == restarted


def test_a_job_that_raises_or_leaves_nothing_fails_its_run(
    tmp_path: Path, supervisor: Supervisor, store: Store
) -> None:
    supervisor.install(app(tmp_path, TESTER_JOB, TESTER), trust="first_party")
    supervisor.start(APP)
    pinned = unit(store)

    codes: list[str] = []
    for mode in ("raise", "nothing"):
        with pytest.raises(AppError) as caught:
            supervisor.run_job(
                APP, "job.py", inputs={"unit": pinned, "mode": mode}, principal="operator"
            )
        codes.append(caught.value.code)

    raised, empty = opened_runs(store)
    assert codes == ["job_failed", "result_missing"]
    assert [result(store, run)["status"] for run in (raised, empty)] == ["failed", "failed"]
    assert [tries(store, run) for run in (raised, empty)] == [["opened", "failed"]] * 2


def test_refusals_come_before_any_try_opens(
    tmp_path: Path, supervisor: Supervisor, store: Store
) -> None:
    source = app(tmp_path, TESTER_JOB, TESTER)
    bare = Supervisor(tmp_path / "bare")
    try:
        with pytest.raises(AppError) as unknown:
            bare.install(source, trust="first_party")
    finally:
        bare.close()
    supervisor.install(source, trust="first_party")
    supervisor.start(APP)
    pinned = unit(store)

    with pytest.raises(AppError) as nameless:
        supervisor.run_job(APP, "job.py", inputs={"unit": pinned})
    with pytest.raises(AppError) as minted:
        supervisor.run_job(
            APP, "job.py", inputs={"unit": pinned, "run_id": "mine"}, principal="operator"
        )
    with pytest.raises(AppError) as unpinned:
        supervisor.run_job(APP, "job.py", inputs={"unit": "no-such-pin"}, principal="operator")
    with pytest.raises(AppError) as unstudied:
        supervisor.run_job(
            APP, "job.py", inputs={"unit": pinned, "study": "no-such-study"}, principal="operator"
        )
    with pytest.raises(AppError) as by_tool:
        supervisor.artifacts.save(
            supervisor._definition(APP),  # pyright: ignore[reportPrivateUsage]
            "backtest-result",
            {"run_id": "x"},
        )

    assert (unknown.value.code, str(unknown.value)) == (
        "unknown_lander",
        f"{APP} names the lander {QMB_RUN}, which this host has not registered.",
    )
    assert nameless.value.code == "principal_required"
    assert (minted.value.code, str(minted.value)) == (
        "run_refused",
        "run_id is minted by the lander, never by the request",
    )
    assert [(it.value.code, str(it.value)) for it in (unpinned, unstudied)] == [
        ("run_refused", "unit no-such-pin names no object in the Library"),
        ("run_refused", "study no-such-study names no object in the Library"),
    ]
    assert by_tool.value.code == "lander_required"
    assert opened_runs(store) == []


def test_a_close_the_library_refuses_still_ends_the_run(
    tmp_path: Path, supervisor: Supervisor, store: Store
) -> None:
    supervisor.install(app(tmp_path, TESTER_JOB, TESTER), trust="first_party")
    supervisor.start(APP)
    pinned = unit(store)

    with pytest.raises(AppError) as refused:
        supervisor.run_job(
            APP,
            "job.py",
            inputs={"unit": pinned, "consumed": ["no-such-card"]},
            principal="operator",
        )

    (run,) = opened_runs(store)
    assert (refused.value.code, str(refused.value)) == (
        "result_refused",
        "not_found: no object no-such-card",
    )
    assert tries(store, run) == ["opened", "failed"]
