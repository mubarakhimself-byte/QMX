"""The shared pieces the build-and-prove templates call (Part B AD-213, B18a): the unit-check
step, the proposal card, the death certificate, the lineage writer and the conveyor.

Each block runs on the real `Engine` from its own folder under `_shared/`. A model step is planted
through the engine's `executors=` seam, so the fix and the explanation are fixed answers and every
gate is the block's own script.
"""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from flows import Script
from pydantic import JsonValue
from qmx_home import resolve
from qmx_tools.gather import template

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_engine.templates.catalog import SHARED

type Answer = Callable[[NodeJob, JsonValue], JsonValue]


def qmx_home(tmp: Path) -> Path:
    return resolve(tmp / "QMX", create=True, drives=[]).home


def run_block(
    name: str, home: Path, inputs: JsonValue, llm: Answer | None = None
) -> tuple[Outcome, list[Event]]:
    """One test run of `_shared/<name>` on `home`, with its model step answered by `llm`."""
    root = SHARED / name
    found = checked(root)
    assert not isinstance(found, list), found
    planted = {} if llm is None else {"llm": Script(llm)}

    async def go() -> Outcome:
        with Ledger.open(home) as ledger, LibraryFake.open(home) as library:
            engine = Engine(home, ledger, settings=DEFAULTS, library=library, executors=planted)
            outcome = await engine.start(root, found[1], mode="test", inputs=inputs)
            await engine.settle()
            return outcome

    outcome = asyncio.run(go())
    with Reader.open(home) as reader:
        return outcome, reader.events(outcome.run_id)


def output(events: list[Event], node_id: str) -> dict[str, Any]:
    found = [
        cast("dict[str, Any]", e.data["outputs"])["main"]
        for e in events
        if e.kind == "node_finished" and e.data["node_id"] == node_id
    ]
    assert len(found) == 1, f"{node_id} finished {len(found)} times"
    return cast("dict[str, Any]", found[0])


def finished(events: list[Event], node_id: str) -> int:
    return sum(1 for e in events if e.kind == "node_finished" and e.data["node_id"] == node_id)


def broken_twin() -> dict[str, Any]:
    """The dummy with three layer C errors at three places (A8's broken unit)."""
    document: dict[str, Any] = copy.deepcopy(template())
    document["numbers"]["ema_period"]["motion"] = {"mode": "scaled"}
    document["numbers"]["time_out_bars"]["default"] = "47.5"
    document["markets"][0]["settings"] = {"ema_periodd": "50"}
    return document


BROKEN_ERRORS = {
    ("motion_not_allowed", "/numbers/ema_period/motion/mode"),
    ("not_in_measure", "/numbers/time_out_bars/default"),
    ("undeclared_number", "/markets/0/settings/ema_periodd"),
}


def errors(report: dict[str, Any]) -> set[tuple[str, str]]:
    return {(p["kind"], where) for p in report["errors"] for where in p["where"]}


def test_the_dummys_broken_twin_loops_once_through_the_unit_check_and_passes(
    tmp_path: Path,
) -> None:
    outcome, events = run_block(
        "unit-check",
        qmx_home(tmp_path),
        {"unit": broken_twin()},
        llm=lambda _job, _value: {"unit": template()},
    )

    report = output(events, "report")
    assert outcome.status == "passed"
    assert (finished(events, "fix"), finished(events, "recheck")) == (1, 1)
    assert {k: report[k] for k in ("verdict", "rounds", "stopped", "why", "errors")} == {
        "verdict": "pass",
        "rounds": 1,
        "stopped": "passed",
        "why": "the unit passes its check",
        "errors": [],
    }
    assert report["unit"] == template()


def test_the_same_problem_set_twice_stops_the_loop_with_its_reason(tmp_path: Path) -> None:
    outcome, events = run_block(
        "unit-check",
        qmx_home(tmp_path),
        {"unit": broken_twin()},
        llm=lambda _job, _value: {"unit": broken_twin()},
    )

    report = output(events, "report")
    assert outcome.status == "passed"
    assert (finished(events, "fix"), finished(events, "recheck")) == (1, 1)
    assert (report["verdict"], report["rounds"], report["stopped"]) == ("fail", 1, "no_progress")
    assert report["why"] == (
        f"the same 3 problem(s) came back after fix round 1, problem set {report['problem_set']}"
    )
    assert errors(report) == BROKEN_ERRORS


def test_a_unit_that_passes_at_once_is_never_sent_to_the_fix_step(tmp_path: Path) -> None:
    _, events = run_block("unit-check", qmx_home(tmp_path), {"unit": template()})

    report = output(events, "report")
    assert (finished(events, "fix"), report["verdict"], report["rounds"]) == (0, "pass", 0)
