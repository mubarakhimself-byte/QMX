"""APP2b: an app operation runs where its declared `state` says it belongs (AD-64)."""

from __future__ import annotations

import asyncio
from typing import cast

from pydantic import JsonValue
from qmx_control.models import Document

from qmx_engine.nodes.app_op import AppOp, Placements
from qmx_engine.nodes.base import JsonObject, NodeJob, Ok, Waiting


def job(app: str, name: str) -> NodeJob:
    definition: JsonObject = {"type": "app_op", "parameters": {"app": app, "job": name}}
    return NodeJob(
        run_id="r",
        node_id="a",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="k",
        node_definition=definition,
        inputs={},
        now=None,
    )


def test_an_instance_operation_runs_on_the_machine_that_owns_it() -> None:
    ran: list[tuple[str, str]] = []

    def run_job(app: str, name: str) -> Document:
        ran.append((app, name))
        return {"job": name}

    placements = Placements(
        state_of=lambda app, op: "instance",
        home_of=lambda app: "contabo",
        here="contabo",
        reachable=lambda placement: True,
    )
    result = asyncio.run(AppOp(run_job, placements=placements).run(job("macro-daily-bias", "d.py")))

    assert isinstance(result, Ok)
    assert result.outputs == {"main": {"job": "d.py"}}
    assert ran == [("macro-daily-bias", "d.py")]


def test_an_instance_operation_waits_placement_when_its_home_is_away() -> None:
    placements = Placements(
        state_of=lambda app, op: "instance",
        home_of=lambda app: "pc",
        here="contabo",
        reachable=lambda placement: False,
    )
    result = asyncio.run(
        AppOp(lambda app, name: {"job": name}, placements=placements).run(
            job("macro-daily-bias", "d.py")
        )
    )

    assert isinstance(result, Waiting)
    assert result.reason == "placement"
    assert result.resume_at is not None


def test_the_placement_wait_resumes_through_the_door_to_the_home() -> None:
    reachable = {"pc": False}
    asked: list[tuple[str, str, str]] = []

    def remote(placement: str, app: str, name: str, pin: object, profile: object) -> Document:
        asked.append((placement, app, name))
        return {"job": name, "home": placement}

    placements = Placements(
        state_of=lambda app, op: "instance",
        home_of=lambda app: "pc",
        here="contabo",
        reachable=lambda placement: reachable[placement],
        remote=remote,
    )
    node = AppOp(lambda app, name: {"job": name}, placements=placements)
    assert isinstance(asyncio.run(node.run(job("macro-daily-bias", "d.py"))), Waiting)

    reachable["pc"] = True
    result = asyncio.run(node.run(job("macro-daily-bias", "d.py")))

    assert isinstance(result, Ok)
    assert cast("dict[str, JsonValue]", result.outputs["main"])["home"] == "pc"
    assert asked == [("pc", "macro-daily-bias", "d.py")]


def test_a_stateless_operation_starts_the_app_on_the_calling_machine() -> None:
    started: list[str] = []

    def lazy(app: str, pin: Document | None) -> Document:
        started.append(app)
        return {"status": "running"}

    placements = Placements(
        state_of=lambda app, op: "none",
        home_of=lambda app: "pc",
        here="contabo",
        reachable=lambda placement: True,
        lazy=lazy,
    )
    result = asyncio.run(
        AppOp(lambda app, name: {"job": name}, placements=placements).run(
            job("macro-daily-bias", "d.py")
        )
    )

    assert isinstance(result, Ok)
    assert started == ["macro-daily-bias"]
