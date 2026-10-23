"""The `library` node is switched on, a run start pins the `@run` and `@library` references its
inputs carry, and a reference that names nothing refuses the start with one reason (engine AD-5,
AD-19, AD-63, AD-64)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import cast

import pytest

from qmx_engine.definition.registry import REGISTRY
from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library import Bundle, runs_ref
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused

EARLIER = "0192a000-0000-7000-8000-00000000e001"


def flow() -> Bundle:
    """A trigger handing the run's inputs to one `library` node, so the node reads what the run
    named."""
    definition = {
        "schema": "qmx.workflow/1",
        "id": "today",
        "name": "today",
        "nodes": [
            {
                "id": "start",
                "name": "start",
                "type": "trigger",
                "typeVersion": 1,
                "parameters": {"kinds": ["manual"]},
            },
            {
                "id": "read",
                "name": "read",
                "type": "library",
                "typeVersion": 1,
                "parameters": {},
            },
        ],
        "connections": {"start": {"main": [[{"node": "read", "port": "in", "map": "one"}]]}},
    }
    return Bundle(definition, {})


def published(svc: EngineService) -> str:
    """The flow tested and published on `main`, the one state a live run starts from."""
    draft = svc.drafts.put(None, flow(), 0, caller=OPERATOR)
    asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
    return svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)


def test_the_library_kind_is_available() -> None:
    kind = REGISTRY.kind("library")

    assert kind is not None
    assert (kind.name, kind.available, str(kind.effect)) == ("library", True, "compensable")
    assert kind.inputs == ("in",) and kind.outputs == ("main",)


def test_a_run_start_pins_its_references_on_run_created(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        version = published(svc)
        library = cast(LibraryFake, svc.ctx.library)
        earlier = library._put(  # pyright: ignore[reportPrivateUsage]
            "workflow-run",
            EARLIER,
            runs_ref(EARLIER),
            {"run_id": EARLIER},
            f"run:{EARLIER}",
        )
        ran = asyncio.run(
            svc.runs.start(
                version,
                caller=OPERATOR,
                inputs={
                    "today": f"@run:{EARLIER}",
                    "pinned": f"@library:{version}",
                },
            )
        )
        with Reader.open(svc.ctx.home) as reader:
            events = reader.events(ran.run_id)

    created = events[0]
    assert (created.kind, ran.status) == ("run_created", "passed")
    assert created.data["pins"]["references"] == [
        {"ref": f"@run:{EARLIER}", "object_id": earlier.object_id},
        {"ref": f"@library:{version}", "object_id": version},
    ]
    finished = [
        event
        for event in events
        if event.kind == "node_finished" and event.data.get("node_id") == "read"
    ]
    handed = finished[0].data["outputs"]["main"]
    assert sorted((one["ref"], one["object_id"], one["kind"]) for one in handed) == [
        (f"@library:{version}", version, "workflow"),
        (f"@run:{EARLIER}", earlier.object_id, "workflow-run"),
    ]
    assert next(one for one in handed if one["kind"] == "workflow-run")["fields"] == {
        "run_id": EARLIER
    }


def test_a_reference_that_names_nothing_refuses_the_start(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        version = published(svc)
        with pytest.raises(Refused) as refused:
            asyncio.run(
                svc.runs.start(
                    version, caller=OPERATOR, inputs={"today": "@run:no-such-run"}
                )
            )

    assert refused.value.code == "not_found"
    assert str(refused.value) == "not_found: @run:no-such-run names no run 'no-such-run'"
