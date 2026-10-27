"""A live run takes its inputs from the run route's body. "Clippings into research" started over
REST with a folder reads that folder and lands its clippings; an empty body runs with no inputs;
a body the workflow's inputs schema refuses, or a schema that is not JSON Schema, is refused by
name and starts no run. Only the declared inputs are checked, never a test run's."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import AbstractAsyncContextManager, asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

import pytest
from fake_library import fake_door
from fastapi.testclient import TestClient
from flows import CHAIN
from qmx_control import ControlService, create_app
from qmx_home import resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store
from test_templates import CLIPPINGS, answers

from qmx_engine.control_door import EngineDoor
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle, JsonObject
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller
from qmx_engine.service.rest import engine_router
from qmx_engine.service.runs import input_refusal
from qmx_engine.templates.catalog import CATALOG, PACK

KEY = "inputs-check"
BEARER = {"Authorization": f"Bearer {KEY}"}
FOLDER_SCHEMA: JsonObject = {"type": "object", "properties": {"folder": {"type": "string"}}}

type Opener = Callable[[ControlService], AbstractAsyncContextManager[EngineDoor]]


def workflow(item: str, inputs: JsonObject) -> dict[str, Any]:
    """The script chain under `item`, declaring `inputs`."""
    bundle = Bundle.read(CHAIN)
    definition = bundle.definition | {"id": item, "inputs": inputs}
    return {"definition": definition, "files": {r: b.decode() for r, b in bundle.files.items()}}


@contextmanager
def served(home: Path, opener: Opener | None = None) -> Generator[tuple[TestClient, EngineDoor]]:
    """The control app with an engine door on its own loop thread, as in the host."""
    control = ControlService(home)
    opened: list[EngineDoor] = []
    ready, stop = threading.Event(), threading.Event()
    opening: Opener = opener or (lambda c: fake_door(c, principal=lambda: OPERATOR))

    async def main() -> None:
        async with opening(control) as door:
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


def published(rest: TestClient, item: str, inputs: JsonObject) -> None:
    rest.put(f"/api/workflows/{item}/draft", json=workflow(item, inputs), headers=BEARER)
    tested = rest.post(f"/api/workflows/{item}/test", headers=BEARER).json()
    assert tested["report"]["status"] == "passed"
    assert rest.put(f"/api/workflows/{item}", json={}, headers=BEARER).status_code == 200


def run_input(home: Path, run_id: str) -> object:
    with Reader.open(home) as reader:
        (found,) = [e.data["inputs"] for e in reader.events(run_id) if e.kind == "run_input"]
    return found


def live_runs(home: Path) -> int:
    with Reader.open(home) as reader:
        (count,) = reader.connection.execute(
            "SELECT count(*) FROM events WHERE kind = 'run_created'"
            " AND json_extract(data, '$.mode') = 'live'"
        ).fetchone()
    return int(count)


def test_a_rest_run_of_clippings_into_research_reads_the_folder_its_body_names(
    tmp_path: Path,
) -> None:
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    folder = tmp_path / "clippings"
    folder.mkdir()
    (folder / "carry.md").write_text("# Carry trade unwind notes\n\nFunding moved.\n", "utf-8")
    (folder / "basis.md").write_text("# Basis trade crowding\n\nRepo rates rose.\n", "utf-8")

    @asynccontextmanager
    async def real(control: ControlService) -> AsyncGenerator[EngineDoor]:
        with Store.open(home / "library", redactor=redact) as store:
            library = EngineLibraryAdapter(store)
            with EngineService.open(home, library=library, harness=answers()) as svc:
                item = svc.drafts.put(CLIPPINGS.name, Bundle.read(CLIPPINGS), 0, caller=OPERATOR)
                tested = await svc.tests.run(item.item, caller=OPERATOR, inputs={"fixture": True})
                assert tested.status == "passed"
                svc.versions.publish(item.item, "0.1.0", caller=OPERATOR)
            async with EngineDoor.open(
                control, library=library, harness=answers(), principal=lambda: OPERATOR
            ) as door:
                yield door

    with served(home, real) as (rest, _):
        ran = rest.post(
            "/api/workflows/clippings-into-research/run",
            json={"folder": str(folder)},
            headers=BEARER,
        )
    run = ran.json()
    with Store.open(home / "library", redactor=redact) as store:
        landed = sorted(
            str(store.get(store.engine, object_id).fields.get("title"))
            for _, object_id in store.heads_on("main")
            if store.get(store.engine, object_id).fields.get("type") == "clipping"
        )

    assert (ran.status_code, run["mode"], run["status"]) == (200, "live", "passed")
    assert run_input(home, run["run_id"]) == {"folder": str(folder)}
    assert len(landed) == 2


def test_an_empty_body_still_runs_with_no_inputs(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        published(rest, "chain", FOLDER_SCHEMA)
        ran = rest.post("/api/workflows/chain/run", headers=BEARER)

    assert (ran.status_code, ran.json()["status"]) == (200, "passed")
    assert run_input(tmp_path, ran.json()["run_id"]) is None


def test_a_body_the_schema_refuses_is_refused_by_name_and_starts_no_run(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        published(rest, "chain", FOLDER_SCHEMA)
        refused = rest.post("/api/workflows/chain/run", json={"folder": 5}, headers=BEARER)

    assert refused.status_code == 422
    assert refused.json()["error"] == {
        "code": "inputs_invalid",
        "message": "inputs_invalid: the input 'folder' is not valid: 5 is not of type 'string'."
        " Give it a value the workflow's inputs accept.",
    }
    assert live_runs(tmp_path) == 0


def test_a_schema_that_is_not_json_schema_is_refused_by_name(tmp_path: Path) -> None:
    with served(tmp_path) as (rest, _):
        published(rest, "chain", {"type": "folder"})
        refused = rest.post("/api/workflows/chain/run", json={}, headers=BEARER)

    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "inputs_schema_invalid"
    assert refused.json()["error"]["message"].startswith(
        "inputs_schema_invalid: the workflow's inputs are not a valid JSON Schema ("
    )
    assert live_runs(tmp_path) == 0


def test_an_agents_card_for_a_live_run_carries_the_inputs_it_was_asked_with(
    tmp_path: Path,
) -> None:
    def agent(control: ControlService) -> AbstractAsyncContextManager[EngineDoor]:
        return fake_door(control, principal=lambda: Caller("agent", "chat-1"))

    with served(tmp_path, agent) as (_, door):
        card = door.control.workflows_run("chain", {"folder": "D:/clips"})

    assert card["button"] == {
        "method": "POST",
        "path": "/api/workflows/chain/run",
        "body": {"folder": "D:/clips"},
    }


SOURCE_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {"source": {"type": "object"}},
    "required": ["source"],
    "additionalProperties": False,
}
ENGINE_KEYS: JsonObject = {
    "trigger": {},
    "continuity": 1,
    "webhook": 2,
    "upstream": 3,
    "precheck": 4,
}


@pytest.mark.parametrize(
    ("inputs", "required", "refused"),
    [
        ({"source": {}} | ENGINE_KEYS, True, None),
        ({}, False, None),
        (
            {},
            True,
            "the input 'source' is missing, and the workflow needs it. Set it, then try again.",
        ),
        (
            {"source": 5},
            False,
            "the input 'source' is not valid: 5 is not of type 'object'. Give it a value the"
            " workflow's inputs accept.",
        ),
        (
            {"source": {}, "extra": 1},
            True,
            "the inputs are not valid: Additional properties are not allowed ('extra' was"
            " unexpected). Give the workflow inputs it accepts.",
        ),
    ],
)
def test_only_the_declared_inputs_are_checked_and_required_only_when_asked(
    inputs: JsonObject, required: bool, refused: str | None
) -> None:
    found = input_refusal(SOURCE_SCHEMA, inputs, required=required)

    assert found == (None if refused is None else ("inputs_invalid", refused))


def test_a_schema_whose_reference_points_at_nothing_is_refused_by_name() -> None:
    dangling: JsonObject = {"type": "object", "properties": {"folder": {"$ref": "#/defs/x"}}}

    assert input_refusal(dangling, {"folder": "D:/clips"}, required=True) == (
        "inputs_schema_invalid",
        "the workflow's inputs are not a valid JSON Schema (its reference /defs/x points at"
        " nothing). Fix its inputs and publish it again.",
    )


def schema_of(template_folder: str) -> JsonObject:
    definition = json.loads((PACK / template_folder / "definition.json").read_text("utf-8"))
    return definition.get("inputs", {})


def test_every_templates_own_test_inputs_meet_its_schema_as_a_live_run_checks_them() -> None:
    """A template with no test inputs is tested on none, and a live run of it must give what its
    schema requires; every other one's test inputs must pass the live check unchanged."""
    built = [t for t in CATALOG if t.folder]
    refused = {
        t.id: found
        for t in built
        if t.test_inputs is not None
        and (found := input_refusal(schema_of(t.folder), t.test_inputs, required=True))
    }
    broken = {
        t.id: found
        for t in built
        if (found := input_refusal(schema_of(t.folder), {}, required=False))
        and found[0] == "inputs_schema_invalid"
    }

    assert (refused, broken) == ({}, {})
    assert input_refusal(schema_of("morning-digest"), {"fixture": "replay"}, required=True) == (
        "inputs_invalid",
        "the input 'fixture' is not valid: 'replay' is not of type 'boolean'. Give it a value the"
        " workflow's inputs accept.",
    )
    assert input_refusal(schema_of("download-binance"), {}, required=True) == (
        "inputs_invalid",
        "the input 'source' is missing, and the workflow needs it. Set it, then try again.",
    )
