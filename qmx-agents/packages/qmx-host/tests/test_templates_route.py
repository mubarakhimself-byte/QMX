"""`POST /api/templates/install` starts an install job through the host's own engine, into the
Library store the host writes, and answers at once; `GET /api/templates/install/{job_id}` reads it
(WU5, RUN1C, loose strings P5)."""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from qma.harness import QmxHome, control_service
from qmx_engine import __main__ as cli
from qmx_engine.control_door import PRINCIPAL, EngineDoor
from qmx_engine.ledger import redact
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.library import LibraryRefused as EngineRefused
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller
from qmx_engine.service.tests import TestReport as Report
from qmx_engine.templates.catalog import PACK, find
from qmx_engine.templates.install import install
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_host import host
from qmx_host.door import templates_router
from qmx_host.host import compose, store_role

KEY = "templates-check"
BEARER = {"Authorization": f"Bearer {KEY}"}
ROUTE = "/api/templates/install"


@contextmanager
def hosted(home: Path) -> Generator[tuple[TestClient, Store, EngineDoor]]:
    """The host's app over a real store, with the engine on its own loop thread."""
    control = control_service(QmxHome(home))
    opened: list[tuple[EngineDoor, Store]] = []
    ready, stop = threading.Event(), threading.Event()

    async def run() -> None:
        with Store.open(home / "library", redactor=redact) as store:
            async with EngineDoor.open(control, library=EngineLibraryAdapter(store)) as door:
                opened.append((door, store))
                ready.set()
                while not stop.is_set():
                    await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(run(),))
    thread.start()
    assert ready.wait(30)
    door, store = opened[0]
    try:
        app = compose(control, door, [], KEY, "", [templates_router(door)])
        with TestClient(app) as rest:
            yield rest, store, door
    finally:
        stop.set()
        thread.join(30)


def ended(rest: TestClient, job: dict[str, Any]) -> dict[str, Any]:
    """The job read again until it is no longer running."""
    deadline = time.monotonic() + 120
    while job["state"] == "running":
        assert time.monotonic() < deadline, job
        time.sleep(0.05)
        read = rest.get(f"{ROUTE}/{job['id']}", headers=BEARER)
        assert read.status_code == 200, read.text
        job = read.json()
    return job


def actions(job: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [(row["id"], row["folder"], row["action"]) for row in job["result"]["rows"]]


def held_tests(door: EngineDoor, monkeypatch: pytest.MonkeyPatch, gate: threading.Event) -> None:
    """Every template's test run waits for `gate`, then fails, as a slow model would."""

    async def run(item: str, *, caller: Caller, inputs: object = None) -> Report:
        await asyncio.to_thread(gate.wait, 5)
        return Report("", "held", item, "", "failed", "the model was slow", None, False)

    monkeypatch.setattr(door.svc.tests, "run", run)


def test_an_install_through_the_route_lands_in_the_hosts_store(tmp_path: Path) -> None:
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, store, _):
        answered = rest.post(ROUTE, json={"templates": ["backup-weekly"]}, headers=BEARER)
        job = ended(rest, answered.json())
        unknown = rest.post(
            ROUTE, json={"templates": ["synthetic-data", "no-such-template"]}, headers=BEARER
        )
        heads = [item for item, _ in store.heads_on("main")]

    assert answered.status_code == 202
    assert (job["state"], job["done"], job["total"], job["line"]) == ("finished", 1, 1, "")
    assert actions(job) == [("backup-weekly", "backup-weekly", "published")]
    assert "backup-weekly" in heads
    assert (unknown.status_code, unknown.json()["detail"]) == (
        404,
        "no template 'no-such-template' in the catalogue",
    )
    assert "synthetic-data" not in heads


def test_the_post_answers_before_a_slow_install_ends_and_a_second_install_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = threading.Event()
    picked = {"templates": ["backup-weekly", "connections-health"]}
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, door):
        held_tests(door, monkeypatch, gate)
        began = time.monotonic()
        answered = rest.post(ROUTE, json=picked, headers=BEARER)
        took = time.monotonic() - began
        second = rest.post(ROUTE, json=picked, headers=BEARER)
        gate.set()
        job = ended(rest, answered.json())

    assert (answered.status_code, answered.json()["state"]) == (202, "running")
    assert took < 1, took
    assert (second.status_code, second.json()["detail"]) == (
        409,
        f"a template install is already running (job {answered.json()['id']}); "
        "wait for it to end, then run the install again",
    )
    assert (job["state"], job["done"], job["total"]) == ("finished", 2, 2)
    assert [(row["id"], row["action"], row["detail"]) for row in job["result"]["rows"]] == [
        ("backup-weekly", "test failed", "run held: the model was slow"),
        ("connections-health", "test failed", "run held: the model was slow"),
    ]


def test_a_running_job_shows_the_template_it_is_on_and_the_rows_finished_so_far(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = threading.Event()
    picked = {"templates": ["stress-tests", "backup-weekly"]}
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, door):
        held_tests(door, monkeypatch, gate)
        job = rest.post(ROUTE, json=picked, headers=BEARER).json()
        deadline = time.monotonic() + 30
        while job["done"] < 1:
            assert time.monotonic() < deadline, job
            time.sleep(0.05)
            job = rest.get(f"{ROUTE}/{job['id']}", headers=BEARER).json()
        gate.set()
        ended(rest, job)

    assert (job["state"], job["step"], job["done"], job["total"]) == (
        "running",
        "installing backup-weekly",
        1,
        2,
    )
    assert actions(job) == [("stress-tests", "rk5-stress-tests", "saved draft")]


def test_the_jobs_rows_are_the_rows_install_gives_on_the_same_catalogue(tmp_path: Path) -> None:
    picked = ["backup-weekly", "stress-tests", "daily-book-report"]
    with hosted(resolve(tmp_path / "hosted", create=True, drives=[]).home) as (rest, _, _):
        job = ended(rest, rest.post(ROUTE, json={"templates": picked}, headers=BEARER).json())
        again = ended(rest, rest.post(ROUTE, json={"templates": picked}, headers=BEARER).json())
    direct = resolve(tmp_path / "direct", create=True, drives=[]).home
    with (
        Store.open(direct / "library", redactor=redact) as store,
        EngineService.open(direct, library=EngineLibraryAdapter(store)) as svc,
    ):
        done = asyncio.run(install(svc, [find(t) for t in picked]))

    assert actions(job) == [
        ("backup-weekly", "backup-weekly", "published"),
        ("stress-tests", "rk5-stress-tests", "saved draft"),
        ("daily-book-report", "p2-daily-book-report", "saved draft"),
    ]
    assert actions(job) == [(f.template.id, f.template.folder, f.action) for f in done]
    assert [row["action"] for row in again["result"]["rows"]] == ["unchanged"] * 3


def test_a_hop_that_raises_stops_the_job_with_its_code_and_the_rows_so_far(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def refused(item: str, *, caller: Caller, inputs: object = None) -> Report:
        raise EngineRefused("not_found", f"no draft {item} in the Library")

    picked = {"templates": ["stress-tests", "backup-weekly", "connections-health"]}
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, door):
        monkeypatch.setattr(door.svc.tests, "run", refused)
        job = ended(rest, rest.post(ROUTE, json=picked, headers=BEARER).json())

    assert (job["state"], job["done"], job["total"]) == ("stopped", 1, 3)
    assert job["line"] == (
        "the install stopped at backup-weekly: no draft backup-weekly in the Library; "
        "the templates before it are installed, so fix that and run the install again"
    )
    assert job["result"]["code"] == "not_found"
    assert actions(job) == [("stress-tests", "rk5-stress-tests", "saved draft")]


def test_any_other_error_in_a_hop_stops_the_job_with_its_line_and_the_rows_so_far(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken(item: str, *, caller: Caller, inputs: object = None) -> Report:
        raise OSError("the disk is full")

    picked = {"templates": ["stress-tests", "backup-weekly"]}
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, door):
        monkeypatch.setattr(door.svc.tests, "run", broken)
        job = ended(rest, rest.post(ROUTE, json=picked, headers=BEARER).json())

    assert (job["state"], job["done"], job["total"]) == ("stopped", 1, 2)
    assert job["line"] == (
        "the install stopped at backup-weekly with an unexpected OSError: the disk is full; "
        "the templates before it are installed, so run the install again"
    )
    assert sorted(job["result"]) == ["rows"]
    assert actions(job) == [("stress-tests", "rk5-stress-tests", "saved draft")]


def test_the_install_runs_on_the_engines_loop_with_no_request_principal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[str, str | None]] = []

    async def run(item: str, *, caller: Caller, inputs: object = None) -> Report:
        named = PRINCIPAL.get()
        seen.append((named.kind, named.id))
        return Report("", "seen", item, "", "failed", "recorded", None, False)

    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, door):
        monkeypatch.setattr(door.svc.tests, "run", run)
        ended(rest, rest.post(ROUTE, json={"templates": ["backup-weekly"]}, headers=BEARER).json())

    assert seen == [("agent", "unnamed")]


def test_a_job_this_host_never_started_answers_404_with_its_line(tmp_path: Path) -> None:
    with hosted(resolve(tmp_path / "QMX", create=True, drives=[]).home) as (rest, _, _):
        read = rest.get(f"{ROUTE}/no-such-job", headers=BEARER)

    assert (read.status_code, read.json()["detail"]) == (
        404,
        "no template install job no-such-job on this host; the host started again since it "
        "began, so run the install again",
    )


def test_the_cli_reads_the_record_the_host_writes() -> None:
    assert (cli.HOST_STATE, cli.INSTALL_ROUTE) == (host.STATE, "/api/templates/install")


def draft_on_a_pc(home: Path, primary: str) -> str:
    """One engine draft put into a store opened the way a `pc` host opens it."""
    home.mkdir(parents=True)
    (home / "settings.toml").write_text(f'[library]\nprimary = "{primary}"\n', "utf-8")
    role = store_role(home, serving=False)
    with (
        Store.open(home / "library", redactor=redact, role=role) as store,
        EngineService.open(home, library=EngineLibraryAdapter(store)) as svc,
    ):
        bundle = Bundle.read(PACK / "backup-weekly")
        return svc.drafts.put("backup-weekly", bundle, 0, caller=OPERATOR).item


def test_a_pc_host_writes_while_the_pc_is_primary_and_refuses_after_the_flip(
    tmp_path: Path,
) -> None:
    landed = draft_on_a_pc(tmp_path / "before", "pc")
    with pytest.raises(EngineRefused) as refused:
        draft_on_a_pc(tmp_path / "after", "server")

    assert landed == "backup-weekly"
    assert refused.value.code == "read_only_replica"
