"""The engine behind the control app's doors, driven over REST with FastAPI's test client: the
`OPERATIONS` paths reach the engine through `attach_workflow_engine`, and the engine router adds
the inbox resolve and the run event stream."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from flows import CHAIN
from qmx_control import ControlService, create_app

from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.inbox import Category, Raise
from qmx_engine.ports.library import Bundle
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.rest import engine_router
from qmx_engine.triggers.rows import put_wake

KEY = "rest-check"
BEARER = {"Authorization": f"Bearer {KEY}"}


def chain(item: str) -> dict[str, Any]:
    bundle = Bundle.read(CHAIN)
    definition = bundle.definition | {"id": item}
    return {"definition": definition, "files": {r: b.decode() for r, b in bundle.files.items()}}


def waiting(item: str) -> dict[str, Any]:
    return {
        "schema": "qmx.workflow/1",
        "id": item,
        "name": "Wait an hour",
        "nodes": [
            {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1,
             "parameters": {"kinds": ["manual"]}},
            {"id": "pause", "name": "Pause", "type": "wait", "typeVersion": 1,
             "parameters": {"seconds": 3600}},
        ],
        "connections": {"Start": {"main": [[{"node": "Pause", "port": "in", "map": "one"}]]}},
    }  # fmt: skip


@contextmanager
def served(home: Path) -> Generator[tuple[TestClient, EngineDoor]]:
    """The control app with an engine door running on its own loop thread, as in the host."""
    control = ControlService(home)
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()

    async def main() -> None:
        async with EngineDoor.open(control, principal=lambda: OPERATOR) as door:
            opened.append(door)
            ready.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    thread = threading.Thread(target=asyncio.run, args=(main(),))
    thread.start()
    assert ready.wait(30)
    try:
        app = create_app(control, KEY, extra_routers=[engine_router(opened[0])])
        with TestClient(app) as rest:
            yield rest, opened[0]
    finally:
        stop.set()
        thread.join(30)


def test_a_draft_is_saved_tested_published_and_run_live_over_rest(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        saved = rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        checked = rest.post("/api/workflows/validate", json=chain("chain"), headers=BEARER)
        early = rest.put("/api/workflows/chain", json={}, headers=BEARER)
        tested = rest.post("/api/workflows/chain/test", headers=BEARER)
        published = rest.put("/api/workflows/chain", json={}, headers=BEARER)
        ran = rest.post("/api/workflows/chain/run", headers=BEARER)
        listed = rest.get("/api/workflow-runs", params={"workflow_id": "chain"}, headers=BEARER)
        remote = rest.get("/api/runs", headers=BEARER)

    assert (saved.json()["state"], saved.json()["revision"]) == ("validated", 1)
    assert (checked.json()["valid"], checked.json()["problems"]) == (True, [])
    assert (early.status_code, early.json()["error"]["code"]) == (409, "publish_refused")
    assert (tested.json()["run"]["mode"], tested.json()["report"]["status"]) == ("test", "passed")
    assert (published.json()["semver"], published.json()["state"]) == ("1.0.0", "published")
    assert (ran.json()["mode"], ran.json()["status"]) == ("live", "passed")
    assert [(r["mode"], r["status"]) for r in listed.json()] == [
        ("live", "passed"),
        ("test", "passed"),
    ]
    assert remote.json() == []


def test_publish_takes_only_a_semver(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        refused = rest.put("/api/workflows/chain", json=chain("chain"), headers=BEARER)

    assert (refused.status_code, refused.json()["error"]["code"]) == (422, "publish_only")


def test_a_waiting_run_is_cancelled_and_its_events_stream_in_seq_order(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/hold/draft", json=waiting("hold"), headers=BEARER)
        run = rest.post("/api/workflows/hold/test", headers=BEARER).json()["run"]
        cancelled = rest.post(f"/api/workflow-runs/{run['run_id']}/cancel", headers=BEARER)
        again = rest.post(f"/api/workflow-runs/{run['run_id']}/cancel", headers=BEARER)
        with Reader.open(tmp_path) as reader:
            written = len(reader.events(run["run_id"]))
        streamed = rest.get(
            "/api/engine/events",
            params={"run_id": run["run_id"], "max_events": written},
            headers=BEARER | {"Last-Event-ID": "0"},
        )
    frames = [json.loads(line[5:]) for line in streamed.text.splitlines() if line[:5] == "data:"]
    kinds = [frame["kind"] for frame in frames]

    assert (run["status"], run["reason"]) == ("waiting", "wait")
    assert (cancelled.json()["status"], cancelled.json()["reason"]) == ("stopped", "operator")
    assert (again.status_code, again.json()["error"]["code"]) == (409, "cancel_refused")
    assert [frame["seq"] for frame in frames] == list(range(1, written + 1))
    assert (kinds[0], kinds[-1], "node_waiting" in kinds) == ("run_created", "run_cancelled", True)


def test_explain_over_rest_redacts_a_token_echoed_by_a_failed_script(tmp_path: Path) -> None:
    leaked = "sk-" + "a1" * 12
    bundle = chain("leak")
    bundle["files"]["scripts/numbers.py"] = f"import sys\nsys.exit('{leaked}')\n"
    (tmp_path / "settings.toml").write_text(
        "[engine.retry]\nmax_tries = 1\nbackoff = [1]\n", encoding="utf-8"
    )
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/leak/draft", json=bundle, headers=BEARER)
        run = rest.post("/api/workflows/leak/test", headers=BEARER).json()["run"]
        explained = rest.get(f"/api/workflow-runs/{run['run_id']}/explain", headers=BEARER)

    assert explained.status_code == 200
    assert (leaked in explained.text, "[redacted]" in explained.text) == (False, True)


def test_only_the_bearer_reaches_the_engine_routes(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        bare = [
            rest.get("/api/workflow-runs").status_code,
            rest.get("/api/triggers").status_code,
            rest.get("/api/engine/events", params={"run_id": "x"}).status_code,
            rest.post("/api/inbox/x/resolve", json={"action": "stop"}).status_code,
        ]
        allowed = rest.get("/api/triggers", headers=BEARER).status_code

    assert (bare, allowed) == ([401, 401, 401, 401], 200)


def test_the_operator_resolves_an_inbox_item_over_rest(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, door):
        raised = asyncio.run_coroutine_threadsafe(raise_item(door), door.loop).result()
        listed = rest.get("/api/inbox", headers=BEARER).json()
        resolved = rest.post(
            f"/api/inbox/{raised}/resolve", json={"action": "stop"}, headers=BEARER
        )

    assert [item["id"] for item in listed] == [raised]
    assert (resolved.json()["resolution"], resolved.json()["resolved_by"]) == ("stop", "operator")


async def raise_item(door: EngineDoor) -> str:
    raised = Raise("run-1", "sig-1", Category.SYSTEM_FAULT, "ledger full", "disk")
    return door.svc.ctx.inbox.raise_item(raised, at="2026-10-17T09:00:00+00:00")


def test_a_run_still_going_is_listed_under_its_workflow(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/hold/draft", json=waiting("hold"), headers=BEARER)
        run = rest.post("/api/workflows/hold/test", headers=BEARER).json()["run"]
        listed = rest.get("/api/workflow-runs", params={"workflow_id": "hold"}, headers=BEARER)

    assert [(r["run_id"], r["status"]) for r in listed.json()] == [(run["run_id"], "waiting")]


def test_disabling_the_last_enabled_trigger_disables_its_version(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        rest.post("/api/workflows/chain/test", headers=BEARER)
        rest.put("/api/workflows/chain", json={}, headers=BEARER)
        ids = [
            rest.post(
                "/api/triggers",
                params={"workflow_id": "chain"},
                json={"kind": "manual"},
                headers=BEARER,
            ).json()["id"]
            for _ in range(2)
        ]
        states: list[str] = []
        for path in (
            f"{ids[0]}/enable",
            f"{ids[1]}/enable",
            f"{ids[0]}/disable",
            f"{ids[1]}/disable",
        ):
            rest.post(f"/api/triggers/{path}", headers=BEARER)
            versions = rest.get("/api/workflows/chain/versions", headers=BEARER).json()
            states.append(versions[0]["state"])

    assert states == ["enabled", "enabled", "enabled", "disabled"]


def test_a_trigger_starts_disabled_and_enabling_it_enables_its_version(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/chain/draft", json=chain("chain"), headers=BEARER)
        rest.post("/api/workflows/chain/test", headers=BEARER)
        version = rest.put("/api/workflows/chain", json={}, headers=BEARER).json()
        made = rest.post(
            "/api/triggers",
            params={"workflow_id": "chain"},
            json={"kind": "manual"},
            headers=BEARER,
        ).json()
        enabled = rest.post(f"/api/triggers/{made['id']}/enable", headers=BEARER).json()
        rest.post(f"/api/triggers/{made['id']}/run-now", headers=BEARER)
        deadline, live = time.monotonic() + 30, []
        while not live and time.monotonic() < deadline:
            time.sleep(0.2)
            found = rest.get("/api/workflow-runs", headers=BEARER).json()
            live = [r for r in found if (r["mode"], r["status"]) == ("live", "passed")]
        versions = rest.get("/api/workflows/chain/versions", headers=BEARER).json()

    assert (made["enabled"], made["pinned_object"]) == (False, version["object_id"])
    assert enabled["enabled"] is True
    assert [v["state"] for v in versions] == ["enabled"]
    assert [r["object_id"] for r in live] == [version["object_id"]]


def test_resume_is_refused_while_a_trigger_fire_drives_the_run(tmp_path: Path) -> None:
    slow = chain("slow")
    slow["files"]["scripts/numbers.py"] = "import time\ntime.sleep(4)\nprint('[1, 2]')\n"
    with served(tmp_path) as (rest, _):
        rest.put("/api/workflows/slow/draft", json=slow, headers=BEARER)
        rest.post("/api/workflows/slow/test", headers=BEARER)
        rest.put("/api/workflows/slow", json={}, headers=BEARER)
        made = rest.post(
            "/api/triggers", params={"workflow_id": "slow"}, json={"kind": "manual"}, headers=BEARER
        ).json()
        rest.post(f"/api/triggers/{made['id']}/enable", headers=BEARER)
        rest.post(f"/api/triggers/{made['id']}/run-now", headers=BEARER)
        deadline, live = time.monotonic() + 20, []
        while not live and time.monotonic() < deadline:
            time.sleep(0.1)
            found = rest.get("/api/workflow-runs", headers=BEARER).json()
            live = [r for r in found if r["mode"] == "live"]
        refused = rest.post(f"/api/workflow-runs/{live[0]['run_id']}/resume", headers=BEARER)
        deadline, ended = time.monotonic() + 30, ""
        while ended != "passed" and time.monotonic() < deadline:
            time.sleep(0.2)
            got = rest.get(f"/api/workflow-runs/{live[0]['run_id']}", headers=BEARER)
            ended = got.json()["status"]
    with Reader.open(tmp_path) as reader:
        events = reader.events(live[0]["run_id"])
    started = [e.data["attempt"] for e in events if e.kind == "node_started"]

    assert (refused.status_code, refused.json()["error"]["code"]) == (409, "resume_refused")
    assert (ended, started) == ("passed", [1, 1, 1, 1])


def test_a_door_resume_takes_the_wake_so_the_scheduler_cannot_drive_the_run_too(
    tmp_path: Path,
) -> None:
    with served(tmp_path) as (rest, door):
        rest.put("/api/workflows/hold/draft", json=waiting("hold"), headers=BEARER)
        run = rest.post("/api/workflows/hold/test", headers=BEARER).json()["run"]
        wake = put_wake(run["run_id"], "2026-10-17T09:00:00+00:00")
        asyncio.run_coroutine_threadsafe(write(door, wake), door.loop).result()
        resumed = rest.post(f"/api/workflow-runs/{run['run_id']}/resume", headers=BEARER)
    with Reader.open(tmp_path) as reader:
        wakes = reader.connection.execute("SELECT run_id FROM wakes").fetchall()
        kinds = [e.kind for e in reader.events(run["run_id"])]

    assert resumed.status_code == 200
    assert (wakes, kinds.count("run_resumed")) == ([], 1)


async def write(door: EngineDoor, operation: Any) -> None:
    door.svc.ctx.engine.ledger.write(operation)


def test_a_token_shaped_key_never_comes_back(tmp_path: Path) -> None:
    key = "ghp_" + "Ab1" * 12
    planted = chain("keyed")
    planted["definition"]["meta"] = {key: "note"}
    with served(tmp_path) as (rest, _):
        saved = rest.put("/api/workflows/keyed/draft", json=planted, headers=BEARER)
        read = rest.get("/api/workflows/keyed/draft", headers=BEARER)
        got = rest.get("/api/workflows/keyed", headers=BEARER)

    assert [key in r.text for r in (saved, read, got)] == [False, False, False]
    assert read.json()["definition"]["meta"] == {"[redacted]": "note"}
