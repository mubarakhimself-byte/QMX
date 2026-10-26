"""Places he names instead of a fixed list (LF6, AD-72): the ledger step lets any listed place home
a trigger and keeps every row, a trigger on a removed place reads `blocked_config` naming it, no
server row ships, every attempt and run records where it ran, and a node on an unlisted place
waits with one line."""

from __future__ import annotations

import asyncio
import platform
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qmx_control import ControlService
from qmx_control.models import Document
from qmx_home import resolve
from test_rest import BEARER, chain, served

from qmx_engine.definition.model import Node
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.runner import Placed, placed
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.settings import places
from qmx_engine.templates.catalog import PACK
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron

T0 = datetime(2026, 10, 26, 9, 0, tzinfo=UTC)
SERVER: Document = {"placement": {"home-server": {"kind": "owned", "id": "place-7"}}}


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
            home_engine="home-server",
            places={"pc", "home-server"},
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
            home_engine="nowhere",
            places={"pc"},
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
    control.settings_put("engine", SERVER)
    with served(home) as (rest, _):
        rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        rest.post("/api/workflows/chain/test", headers=BEARER)
        rest.put("/api/workflows/chain", json={}, headers=BEARER)
        trigger = {"kind": "manual", "home_engine": "home-server"}
        made = rest.post(
            "/api/triggers", params={"workflow_id": "chain"}, json=trigger, headers=BEARER
        )
        unlisted = rest.post(
            "/api/triggers",
            params={"workflow_id": "chain"},
            json={"kind": "manual", "home_engine": "nowhere"},
            headers=BEARER,
        )
        control.settings_put("engine", {})
        removed = rest.get("/api/triggers", headers=BEARER).json()
        control.settings_put("engine", SERVER)
        back = rest.get("/api/triggers", headers=BEARER).json()

    assert (made.json()["home_engine"], made.json()["last_status"]) == ("home-server", None)
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


def test_a_node_runs_on_the_first_listed_place_it_names_and_waits_naming_an_unlisted_one(
    tmp_path: Path,
) -> None:
    def node(runs_on: str | list[str]) -> Node:
        return Node.model_validate(
            {"id": "n", "name": "N", "type": "script", "typeVersion": 1, "runs_on": runs_on}
        )

    listed = {"pc": "pc", "home-server": "place-7"}

    assert placed(node("pc"), tmp_path, T0, listed) == Placed("pc", "pc", "default")
    assert placed(node("home-server"), tmp_path, T0, listed) == Placed(
        "home-server", "place-7", "chosen"
    )
    assert placed(node(["gpu-box", "pc"]), tmp_path, T0, listed) == Placed("pc", "pc", "spilled")
    assert placed(node("gpu-box"), tmp_path, T0, listed) == (
        "the place 'gpu-box' is not in the place list"
    )


def test_run_on_a_machine_with_no_place_set_asks_for_one_by_name() -> None:
    found = checked(PACK / "run-on-a-machine")

    assert isinstance(found, list)
    assert [(p.code, p.path, p.message) for p in found if p.code == "place_unset"] == [
        ("place_unset", "nodes[1].runs_on", "name the place this node runs on")
    ]
