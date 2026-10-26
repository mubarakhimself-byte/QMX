"""Places he names instead of a fixed list (LF6, AD-72): the ledger step lets any listed place home
a trigger and keeps every row, a trigger follows its place's id through a rename and reads
`blocked_config` naming it once the place is removed, no server row ships, every attempt and run
records the place it ran on, and a node on a place this machine cannot reach waits with one line
or spills to This PC."""

from __future__ import annotations

import asyncio
import json
import platform
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from flows import ONE_TRY, Script, edge, node, workflow
from qmx_control import ControlService
from qmx_control.models import Document
from qmx_home import resolve
from test_rest import BEARER, chain, served

from qmx_engine.definition.model import Node
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.runner import Engine, Outcome, Placed, placed
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.settings import places
from qmx_engine.templates.catalog import PACK
from qmx_engine.trace_export import ran_on
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.workers.local import LocalWorker

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=UTC)
SERVER: Document = {"placement": {"home-server": {"kind": "owned", "id": "place-7"}}}
SERVER_BY_NAME: Document = {"placement": {"home-server": {"kind": "owned"}}}


def home_of(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def test_the_ledger_step_keeps_every_trigger_and_lets_a_named_place_home_one(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    path = home / "engine" / "engine.sqlite"
    path.parent.mkdir(parents=True)
    old = sqlite3.connect(path)
    for statement in (*STEPS[0], *STEPS[1], *STEPS[2]):
        old.execute(statement)
    old.execute("INSERT INTO meta VALUES ('schema_version', '3')")
    for trigger_id, place in (("trigger-pc", "pc"), ("trigger-server", "contabo")):
        old.execute(
            f"INSERT INTO triggers ({rows.COLUMNS}) VALUES"  # noqa: S608
            " (?, 'wf', 'obj', 0, ?, 'cron', '{\"expr\": \"0 * * * *\", \"zone\": \"UTC\"}', 1,"
            " NULL, '{}', NULL, 'digest', 0, 'merged', 1, 'ticker', 'operator',"
            " '2026-10-01T00:00:00.000000+00:00', NULL, 'ok', 2, NULL, NULL, NULL, 5, '07:30')",
            (trigger_id, place),
        )
    old.commit()
    old.close()

    with Ledger.open(home) as ledger:
        applied = ledger.applied
        made = rows.create(
            ledger,
            workflow_item="wf",
            pinned_object="obj",
            spec=Cron("0 * * * *", "UTC"),
            caller=OPERATOR,
            now=T0,
            place="home-server",
            places={"pc": "pc", "home-server": "home-server"},
        )
    with Ledger.open(home) as again:
        reapplied = again.applied
    with Reader.open(home) as reader:
        found = {t.id: t for t in rows.triggers(reader.connection)}

    assert (applied, reapplied) == ([4], [])
    assert [
        (t.id, t.home_engine, t.last_status, t.failure_streak, t.priority, t.ready_by)
        for t in found.values()
    ] == [
        ("trigger-pc", "pc", "ok", 2, 5, "07:30"),
        ("trigger-server", "contabo", "ok", 2, 5, "07:30"),
        (made.id, "home-server", None, 0, 0, None),
    ]


def test_a_trigger_is_written_only_onto_a_listed_place(tmp_path: Path) -> None:
    with (
        Ledger.open(home_of(tmp_path)) as ledger,
        pytest.raises(
            Refused, match=r"^place_unknown: the place 'nowhere' is not in the place list$"
        ),
    ):
        rows.create(
            ledger,
            workflow_item="wf",
            pinned_object="obj",
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
            place="nowhere",
        )


def test_a_renamed_place_keeps_its_triggers_live_because_they_follow_its_id(
    tmp_path: Path,
) -> None:
    with Ledger.open(home_of(tmp_path)) as ledger:
        made = rows.create(
            ledger,
            workflow_item="wf",
            pinned_object="obj",
            spec=rows.Manual(),
            caller=OPERATOR,
            now=T0,
            place="home-server",
            places={"pc": "pc", "home-server": "place-7"},
        )

    renamed = rows.standing(made, {"pc": "pc", "big-box": "place-7"})
    removed = rows.standing(made, {"pc": "pc", "home-server": "place-8"})

    assert made.home_engine == "place-7"
    assert (renamed.place, renamed.last_status, renamed.blocked) == ("big-box", None, None)
    assert (removed.place, removed.last_status, removed.blocked) == (
        None,
        "blocked_config",
        "the place 'place-7' was removed",
    )


def test_no_server_row_ships_and_a_place_he_adds_joins_the_list_under_its_name(
    tmp_path: Path,
) -> None:
    control = ControlService(home_of(tmp_path))
    fresh = ControlSettings(control).values()
    control.settings_put("engine", SERVER)
    added = places(ControlSettings(control).values())

    assert [key for key in fresh if "contabo" in key] == []
    assert places(fresh) == {"pc": "pc"}
    assert added == {"pc": "pc", "home-server": "place-7"}


def test_a_trigger_on_a_removed_place_reads_blocked_config_naming_the_place(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    control = ControlService(home)
    control.settings_put("engine", SERVER_BY_NAME)
    with served(home) as (rest, _):
        rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        rest.post("/api/workflows/chain/test", headers=BEARER)
        rest.put("/api/workflows/chain", json={}, headers=BEARER)
        trigger = {"kind": "manual", "place": "home-server"}
        made = rest.post(
            "/api/triggers", params={"workflow_id": "chain"}, json=trigger, headers=BEARER
        )
        unlisted = rest.post(
            "/api/triggers",
            params={"workflow_id": "chain"},
            json={"kind": "manual", "place": "nowhere"},
            headers=BEARER,
        )
        control.settings_put("engine", {})
        removed = rest.get("/api/triggers", headers=BEARER).json()
        control.settings_put("engine", SERVER_BY_NAME)
        back = rest.get("/api/triggers", headers=BEARER).json()

    assert (made.json()["home_engine"], made.json()["place"], made.json()["last_status"]) == (
        "home-server",
        "home-server",
        None,
    )
    assert (unlisted.status_code, unlisted.json()["error"]["code"]) == (409, "place_unknown")
    assert [(t["last_status"], t["blocked"]) for t in removed] == [
        ("blocked_config", "the place 'home-server' was removed")
    ]
    assert [(t["last_status"], t["blocked"]) for t in back] == [(None, None)]


def test_a_run_records_where_each_attempt_ran_and_its_card_says_ran_on_pc_by_default(
    tmp_path: Path,
) -> None:
    home = home_of(tmp_path)
    with served(home) as (rest, door):
        rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        run_id = rest.post("/api/workflows/chain/test", headers=BEARER).json()["run"]["run_id"]

        async def read() -> object:
            library = door.svc.ctx.library
            [summary] = library.objects(run_id, "workflow-run")
            return library.get(summary.object_id).fields["placement"]

        record = asyncio.run_coroutine_threadsafe(read(), door.loop).result()
    with Reader.open(home) as reader:
        started = [e.data for e in reader.events(run_id) if e.kind == "node_started"]
    here = platform.node()

    assert {(d["place"], d["place_id"], d["machine"], d["placed_by"]) for d in started} == {
        ("pc", "pc", here, "default")
    }
    assert record == {
        "place": "pc",
        "place_id": "pc",
        "machine": here,
        "placed_by": "default",
        "line": "ran on pc, by default",
    }


def test_the_run_level_place_comes_from_the_work_not_the_trigger_node() -> None:
    def started(seq: int, node_id: str, place: str, placed_by: str) -> Event:
        data: dict[str, Any] = {
            "node_id": node_id,
            "place": place,
            "place_id": place,
            "machine": "vmi-1" if place != "pc" else "desk",
            "placed_by": placed_by,
        }
        return Event(seq, "run-1", "2026-10-26T09:00:00+00:00", "node_started", data)

    record = ran_on(
        [started(1, "start", "pc", "default"), started(2, "land", "home-server", "chosen")]
    )

    assert record == {
        "place": "home-server",
        "place_id": "home-server",
        "machine": "vmi-1",
        "placed_by": "chosen",
        "line": "ran on home-server, as chosen",
    }


def test_placement_takes_only_listed_places_this_machine_reaches(tmp_path: Path) -> None:
    def named(runs_on: str | list[str]) -> Node:
        return Node.model_validate(
            {"id": "n", "name": "N", "type": "script", "typeVersion": 1, "runs_on": runs_on}
        )

    listed = {"pc": "pc", "home-server": "place-7"}

    def here(place: str) -> bool:
        return place == "pc"

    def everywhere(_: str) -> bool:
        return True

    assert placed(named("pc"), tmp_path, T0, listed, here) == Placed("pc", "pc", "default")
    assert placed(named("home-server"), tmp_path, T0, listed, everywhere) == Placed(
        "home-server", "place-7", "chosen"
    )
    assert placed(named(["home-server", "pc"]), tmp_path, T0, listed, here) == Placed(
        "pc", "pc", "spilled"
    )
    assert placed(named("home-server"), tmp_path, T0, listed, here) == (
        "the place 'home-server' cannot be reached from this machine"
    )
    assert placed(named("gpu-box"), tmp_path, T0, listed, everywhere) == (
        "the place 'gpu-box' is not in the place list"
    )


def run_on(tmp_path: Path, runs_on: str | list[str]) -> tuple[Outcome, list[Event]]:
    """A two-node run on This PC's own worker, the one a pc host has, with home-server listed."""
    home = home_of(tmp_path)
    folder = tmp_path / "flow"
    folder.mkdir()
    land: dict[str, Any] = node("land", "script") | {"runs_on": runs_on}
    definition = workflow([node("start", "trigger"), land], {"start": {"main": [edge("land")]}})
    document = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(
                home,
                ledger,
                settings={**ONE_TRY, "placement.home-server.kind": "owned"},
                worker=LocalWorker(),
                wall=lambda: T0,
                executors={"script": Script()},
            )
            return await engine.start(folder, definition, mode="test", inputs=None, run_id="run-1")

    outcome = asyncio.run(go())
    with Reader.open(home) as reader:
        return outcome, reader.events("run-1")


def test_on_this_pc_a_node_on_an_unreachable_place_waits_naming_it(tmp_path: Path) -> None:
    outcome, events = run_on(tmp_path, "home-server")

    waits = [e.data for e in events if e.kind == "node_waiting" and e.data["node_id"] == "land"]
    assert outcome.status == "waiting"
    assert [(w["reason"], w["detail"]) for w in waits] == [
        ("placement", "the place 'home-server' cannot be reached from this machine")
    ]
    assert [e.data["node_id"] for e in events if e.kind == "node_started"] == ["start"]


def test_on_this_pc_a_node_naming_an_unreachable_place_then_pc_runs_on_pc_and_says_so(
    tmp_path: Path,
) -> None:
    outcome, events = run_on(tmp_path, ["home-server", "pc"])

    [land] = [e.data for e in events if e.kind == "node_started" and e.data["node_id"] == "land"]
    assert outcome.status == "passed"
    assert (land["placement"], land["place"], land["place_id"], land["placed_by"]) == (
        "pc",
        "pc",
        "pc",
        "spilled",
    )
    assert land["machine"] == platform.node()


def test_run_on_a_machine_with_no_place_set_asks_for_one_by_name() -> None:
    found = checked(PACK / "run-on-a-machine")

    assert isinstance(found, list)
    assert [(p.code, p.path, p.message) for p in found if p.code == "place_unset"] == [
        ("place_unset", "nodes[1].runs_on", "name the place this node runs on")
    ]
