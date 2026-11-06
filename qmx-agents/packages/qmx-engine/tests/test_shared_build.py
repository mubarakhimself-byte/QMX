"""The shared pieces the build-and-prove templates call (Part B AD-213, B18a): the unit-check
step, the proposal card, the lineage writer and the conveyor.

Each block runs on the real `Engine` from its own folder under `_shared/`. A model step is planted
through the engine's `executors=` seam, so the fix is a fixed answer and every gate is the block's
own script.
"""

from __future__ import annotations

import asyncio
import copy
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from fake_library import fake_service
from flows import Script, edge, events_of, folder, node
from pydantic import JsonValue
from qmx_home import resolve
from qmx_tools.gather import template
from scheduled import Clock, fires_of

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob
from qmx_engine.ports.library import Bundle, Stored
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS
from qmx_engine.templates.catalog import SHARED
from qmx_engine.triggers import rows
from qmx_engine.triggers.ticker import Scheduler

type Answer = Callable[[NodeJob, JsonValue], Any]
T0 = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)


def qmx_home(tmp: Path) -> Path:
    return resolve(tmp / "QMX", create=True, drives=[]).home


def run_block(
    name: str, home: Path, inputs: Any, llm: Answer | None = None
) -> tuple[Outcome, list[Event]]:
    """One test run of `_shared/<name>` on `home`, with its model step answered by `llm`."""
    root = SHARED / name
    found = checked(root)
    assert not isinstance(found, list), found
    planted = {} if llm is None else {"llm": Script(llm)}
    given = cast("JsonValue", inputs)

    async def go() -> Outcome:
        with Ledger.open(home) as ledger, LibraryFake.open(home) as library:
            engine = Engine(home, ledger, settings=DEFAULTS, library=library, executors=planted)
            outcome = await engine.start(root, found[1], mode="test", inputs=given)
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


def metadata(stored: Stored) -> dict[str, Any]:
    """An artifact's metadata without the `write_key` the runner stamps on every script write."""
    found = cast("dict[str, Any]", stored.fields["metadata"])
    return {key: value for key, value in found.items() if key != "write_key"}


def landed(home: Path) -> list[Stored]:
    with LibraryFake.open(home) as library:
        return [library.get(e.object_id) for e in library.events()]


def artifacts(home: Path, type_: str) -> list[Stored]:
    return [s for s in landed(home) if s.kind == "artifact" and s.fields["type"] == type_]


def test_a_proposal_lands_as_one_card_on_the_runs_own_ref_and_moves_nothing(
    tmp_path: Path,
) -> None:
    home = qmx_home(tmp_path)
    proposal = {
        "subject": "unit-gold-pullback",
        "ask": "paper",
        "evidence": ["verdict-1", "result-1"],
        "why": "passes on 140 trades at +0.21R shrunk",
        "cost": {"backtests": 3, "tokens": 0},
    }

    outcome, _ = run_block("proposal-card", home, {"proposal": proposal})

    everything = landed(home)
    [card] = artifacts(home, "proposal-card")
    assert outcome.status == "passed"
    assert metadata(card) == {**proposal, "made_by": f"run:{outcome.run_id}"}
    assert {s.ref for s in everything} == {f"refs/runs/{outcome.run_id}"}
    assert [s.kind for s in everything].count("artifact") == 1


def test_a_proposal_missing_its_ask_and_evidence_names_both_and_lands_nothing(
    tmp_path: Path,
) -> None:
    home = qmx_home(tmp_path)

    outcome, _ = run_block("proposal-card", home, {"proposal": {"subject": "u", "ask": "promote"}})

    assert outcome.status == "failed"
    assert outcome.reason is not None
    assert "ask 'promote' is not one of paper, live" in outcome.reason
    assert "evidence lists no Library object id" in outcome.reason
    assert artifacts(home, "proposal-card") == []


def seeded(home: Path, names: tuple[str, ...]) -> dict[str, str]:
    """One Library object per stage, landed before the run that records the lineage."""
    with LibraryFake.open(home) as library:
        return {
            name: library.put_artifact(
                name.encode(), name, {}, run_id="seed", principal="run:seed"
            ).object_id
            for name in names
        }


def test_a_runs_lineage_walks_from_source_to_result(tmp_path: Path) -> None:
    home = qmx_home(tmp_path)
    ids = seeded(home, ("source", "idea", "unit", "version", "result"))

    outcome, events = run_block("lineage", home, {"lineage": ids})

    written = output(events, "lineage")["library_written"]
    with LibraryFake.open(home) as library:
        [found] = library.edges(ids["result"], "consumed", reverse=True)
        record = library.get(found.from_id)
        from_source = {e.from_id for e in library.edges(ids["source"], "consumed", reverse=True)}
    chain = cast("list[dict[str, str]]", metadata(record)["chain"])
    assert outcome.status == "passed"
    assert from_source == {record.object_id}
    assert [(s["stage"], s["object_id"]) for s in chain] == [
        ("source", ids["source"]),
        ("idea", ids["idea"]),
        ("unit", ids["unit"]),
        ("version", ids["version"]),
        ("result", ids["result"]),
    ]
    assert [w["refused"] for w in written] == [None] * 6


def test_a_lineage_leaves_out_a_stage_it_was_not_given(tmp_path: Path) -> None:
    home = qmx_home(tmp_path)
    ids = seeded(home, ("idea", "result"))

    _, events = run_block("lineage", home, {"lineage": ids})

    assert output(events, "lineage")["chain"] == [
        {"stage": "idea", "object_id": ids["idea"]},
        {"stage": "result", "object_id": ids["result"]},
    ]


STAGE = """\
import json, os, sys
from pathlib import Path

guard = json.load(sys.stdin)["in"]["outputs"]["guard"]["main"]
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "conveyed.json").write_text(json.dumps(guard["event"]), encoding="utf-8")
write = {"op": "put_artifact", "type": "conveyed", "body": "library/conveyed.json",
         "metadata": {"from": guard["event"]["object_id"]}, "intent_key": guard["intent_key"]}
print(json.dumps({"conveyed": guard["event"]["object_id"], "library": [write]}))
"""
STAND_DOWN = """\
import json, sys

guard = json.load(sys.stdin)["in"]["outputs"]["guard"]["main"]
print(json.dumps({"stood_down": guard["why"]}))
"""


def conveyor_template(root: Path) -> Path:
    """A template that conveys every landed `conveyed` artifact into a new `conveyed` artifact:
    its stage lands exactly what its own trigger watches."""
    folder(
        root,
        [
            node("start", "trigger", kinds=["manual"]),
            node("conveyor", "subworkflow", workflow="conveyor"),
            node("go", "rule", expr="items.outputs.guard.main.go"),
            node("stage", "script", script="scripts/stage.py"),
            node("standdown", "script", script="scripts/stand_down.py"),
        ],
        {
            "start": {"main": [edge("conveyor")]},
            "conveyor": {"main": [edge("go")]},
            "go": {"true": [edge("stage")], "false": [edge("standdown")]},
        },
        {"stage": STAGE, "stand_down": STAND_DOWN},
        on_error="park",
    )
    shutil.copytree(SHARED / "conveyor", root / "conveyor")
    return root


def test_a_conveyor_whose_stage_lands_what_its_trigger_watches_fires_its_stage_once(
    tmp_path: Path,
) -> None:
    home, clock = qmx_home(tmp_path), Clock(T0)
    bundle = Bundle.read(conveyor_template(tmp_path / "template"))
    upstream: dict[str, JsonValue] = {"object_id": "o", "seq": 0, "kind": "artifact"}
    upstream |= {"output": "conveyed", "producer": "qmb"}
    with fake_service(home, clock=clock) as svc:
        item = svc.drafts.put(None, bundle, 0, caller=OPERATOR).item
        tested = asyncio.run(svc.tests.run(item, caller=OPERATOR, inputs={"event": upstream}))
        assert tested.status == "passed"
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        svc.versions.enable(version, caller=OPERATOR)
        trigger = rows.create(
            svc.ctx.engine.ledger,
            workflow_item=item,
            pinned_object=version,
            spec=rows.Event({"kind": "artifact", "output": "conveyed"}),
            caller=OPERATOR,
            now=clock.now(),
        )
        ticker = Scheduler(svc.ctx, credentials=set(), skills=set())
        seed: list[str] = []

        async def drive() -> None:
            await ticker.tick()
            seed.append(
                svc.ctx.library.put_artifact(
                    b"{}", "conveyed", {"producer_app": "qmb"}, run_id="r", principal="run:r"
                ).object_id
            )
            for _ in range(4):
                clock.move(seconds=60)
                await ticker.tick()
                await ticker.settle()

        asyncio.run(drive())

    fires = fires_of(home, trigger.id)
    runs = [fire.run_id for fire in fires]
    stage_landings = [
        s for s in artifacts(home, "conveyed") if s.principal in {f"run:{r}" for r in runs}
    ]
    assert tested.status == "passed"
    assert [fire.status for fire in fires] == ["ok", "ok"]
    assert [metadata(s) for s in stage_landings] == [{"from": seed[0]}]
    assert fires[1].delivery_id == f"event:{stage_landings[0].object_id}"
    assert output(events_of(home, str(runs[1])), "standdown") == {
        "stood_down": f"{stage_landings[0].object_id} was landed by run:{runs[0]}, a run of "
        "this conveyor; a conveyor never starts on its own landing"
    }
