"""The Library templates on the real store: "Clippings into research" lands what Library search
finds, the morning digest lists what moved onto `main` since his cursor, and "Replace a settled
agent step with a script" refuses rather than learn from samples. Every run goes through the
engine over `EngineLibraryAdapter(Store.open(tmp))`, with that store open the whole time, as the
host holds it; model turns come from the templates' recorded answers."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.service import ControlService
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store
from test_templates import CLIPPINGS, CRYSTALLISE, DIGEST, PACK, answers

from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle, JsonObject
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR

FIXTURE: JsonObject = {"fixture": True}


@pytest.fixture
def real(tmp_path: Path) -> Generator[tuple[EngineService, Store]]:
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    with (
        Store.open(home / "library", redactor=redact) as store,
        EngineService.open(home, library=EngineLibraryAdapter(store), harness=answers()) as svc,
    ):
        yield svc, store


def published(svc: EngineService, folder: Path) -> str:
    """The template saved, test-run on its fixture as install does, and published."""
    item = svc.drafts.put(folder.name, Bundle.read(folder), 0, caller=OPERATOR).item
    tested = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs=FIXTURE))
    assert tested.status == "passed"
    return svc.versions.publish(item, "0.1.0", caller=OPERATOR)


def finished(svc: EngineService, run_id: str, node: str) -> list[dict[str, Any]]:
    with Reader.open(svc.ctx.home) as reader:
        return [
            cast(dict[str, Any], e.data["outputs"])["main"]
            for e in reader.events(run_id)
            if e.kind == "node_finished" and e.data.get("node_id") == node
        ]


def live(svc: EngineService, version: str) -> tuple[str, dict[str, Any]]:
    view = asyncio.run(svc.runs.start(version, caller=OPERATOR, inputs=FIXTURE))
    assert view.status == "passed"
    return view.run_id, finished(svc, view.run_id, "deliver")[0]


def stored_by(svc: EngineService, run_id: str) -> list[str]:
    return [
        receipt["object_id"]
        for receipt in finished(svc, run_id, "write")[0]["library_written"]
        if receipt["op"] == "put_artifact"
    ]


def cursors(home: Path) -> dict[str, int]:
    with sqlite3.connect(home / "control.db") as db:
        return dict(db.execute("SELECT name, position FROM operator_cursor").fetchall())


def test_clippings_land_where_library_search_finds_them_and_a_second_run_links_to_them(
    real: tuple[EngineService, Store],
) -> None:
    svc, store = real
    version = published(svc, CLIPPINGS)
    first, card = live(svc, version)
    second, again = live(svc, version)
    stored = stored_by(svc, first)
    on_main = sorted(
        object_id
        for _, object_id in store.heads_on("main")
        if svc.ctx.library.get(object_id).fields.get("type") == "clipping"
    )
    found = {hit.object_id for hit in store.search(store.engine, "London breakout")}

    assert (card["figures"]["new"], card["figures"]["seen"]) == (2, 0)
    assert (again["figures"]["new"], again["figures"]["seen"]) == (0, 2)
    assert on_main == sorted(stored)
    assert len(found & set(stored)) == 1
    assert sorted(oid for held in again["held"] for oid in held["linked_to"]) == sorted(stored)
    assert [svc.ctx.library.get(o).fields["type"] for o in stored_by(svc, second)] == [
        "clipping-intake"
    ]
    assert not (svc.ctx.home / "engine" / "library-fake.sqlite").exists()


def test_the_digest_lists_what_moved_onto_main_and_only_a_live_run_moves_his_cursor(
    real: tuple[EngineService, Store],
) -> None:
    svc, store = real
    clippings = published(svc, CLIPPINGS)
    landed, _ = live(svc, clippings)
    ControlService(svc.ctx.home).close()
    with sqlite3.connect(svc.ctx.home / "control.db") as db:
        db.execute("INSERT INTO operator_cursor VALUES ('last_look', 1000000, 'from the fake')")
    digest = published(svc, DIGEST)
    after_test_run = cursors(svc.ctx.home)
    _, card = live(svc, digest)
    listed = [line["object_id"] for line in card["landed"]]

    assert after_test_run == {"last_look": 1000000, "last_look:library": 0}
    assert card["read_from"] == 0
    assert set(stored_by(svc, landed)) <= set(listed)
    assert {store.placement(object_id)[0] for object_id in listed} == {"main"}  # type: ignore[index]
    assert (
        cursors(svc.ctx.home)["last_look:library"]
        == card["cursor_to"]
        == max(line["seq"] for line in card["landed"])
    )


def test_crystallise_with_no_real_replays_refuses_and_counts_the_test_runs_it_left_out(
    real: tuple[EngineService, Store],
) -> None:
    svc, _ = real
    published(svc, CLIPPINGS)
    item = svc.drafts.put(CRYSTALLISE.name, Bundle.read(CRYSTALLISE), 0, caller=OPERATOR).item
    asked: JsonObject = {
        "workflow": "clippings-into-research",
        "node": "summarise",
        "batch": [{"item_id": "b-1", "title": "breakout entry backtest"}],
    }
    report = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs=asked))
    with Reader.open(svc.ctx.home) as reader:
        refused = [
            e.data["message"]
            for e in reader.events(report.run_id)
            if e.kind == "node_failed" and e.data.get("node_id") == "replays"
        ]

    assert report.status != "passed"
    assert refused[:1] == ["no replays yet (1 fake or test runs left out)"]


@pytest.mark.parametrize(
    ("given", "printed"),
    [
        ({}, "[QMX_FAILURE] no idea given"),
        ({"fixture": "first-pass"}, '"sources": ["fixture:revolution-loop", "brief:idea"'),
        ({"idea": "London breakout"}, '"sources": ["brief:idea", "input:idea"]'),
    ],
)
def test_the_revolution_brief_names_the_fixture_only_in_a_fixture_run_and_needs_an_idea(
    given: dict[str, str], printed: str
) -> None:
    script = PACK / "revolution-loop" / "revolution" / "scripts" / "brief.py"
    done = subprocess.run(
        [sys.executable, "-I", str(script)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        check=True,
    )

    assert printed in done.stdout
