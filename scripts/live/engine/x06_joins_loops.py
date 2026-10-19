"""EP6's live lanes for joins, loops, waits and the cartesian and keyed-join maps, driven through
the real `Engine` with planted executors (`e02_replay.EngineRun`).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x06_joins_loops.py [lane]`
Lanes are `quorum any loop wait cartesian keyed`; none named runs all. Each lane writes
`evidence/ep6/<ENGINE_LOG_PREFIX>ep6-<lane>.log` and the script exits 1 if any lane failed. No
lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Callable
from typing import Any, cast

from common import Log, throwaway_home
from e02_replay import EngineRun
from e03_chunks import NOW, Script, document, edge, engine_run, node, of, validated
from ep2_lanes import git
from pydantic import JsonValue
from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import validate
from qmx_engine.nodes.base import NodeJob
from qmx_engine.runner import Engine, Outcome

FIVE: JsonValue = ["a", "b", "c", "d", "e"]


def fan_in(**join: Any) -> dict[str, Any]:
    return document(
        [
            node("start", "trigger"),
            node("work", "script"),
            node("gather", "join", **join),
            node("after", "script"),
        ],
        {
            "start": {"main": [edge("work", "broadcast")]},
            "work": {"main": [edge("gather")]},
            "gather": {"main": [edge("after")]},
        },
    )


def join_plan(run: EngineRun) -> JsonValue:
    return [e["plan"] for e in of(run.events, "node_scheduled", "gather")]


def slow_fan(
    log: Log, slug: str, slow: set[int], order: tuple[int, ...], **join: Any
) -> tuple[EngineRun, Outcome, JsonValue]:
    """Run `fan_in` with the `slow` partitions of `work` held in flight; once `after` finished,
    release them in `order`, each waiting for the last to land. Returns the run, how it ended and
    the join's plan as it stood before the first release."""
    script = Script(slow={("work", p) for p in slow})
    run = engine_run(validated(log, slug, fan_in(**join)), script, f"run-{slug}")

    async def scenario(engine: Engine) -> tuple[Outcome, JsonValue]:
        going = asyncio.create_task(run.started(engine, FIVE))
        await run.seen("node_finished", "after")
        plan = join_plan(run)
        for partition in order:
            script.release("work", partition, "ABCDE"[partition])
            await run.seen("node_finished", "work", partition)
        return await going, plan

    ended, plan = run.drive(scenario)
    return run, ended, plan


def quorum(log: Log) -> None:
    run, ended, plan = slow_fan(log, "quorum", {0, 3}, (3, 0), mode="quorum", n=3)
    log("partitions 0 and 3 were slow; the join plan once the fast three were in:")
    log(f"join plan: {plan}")
    log.check(
        "the join fires at 3, merging 1 2 4, with 0 and 3 recorded late",
        plan == [{"join": {"mode": "quorum", "expected": 5, "merged": [1, 2, 4], "late": [0, 3]}}],
        plan,
    )
    events = run.events
    log.check(
        "the downstream ran on the merged three", of(events, "node_started", "after") != [], ""
    )
    late = [
        e.seq for e in events if e.kind == "node_finished" and e.data.get("partition") in (0, 3)
    ]
    fired = [
        e.seq for e in events if e.kind == "node_scheduled" and e.data.get("node_id") == "gather"
    ]
    log(f"late arrivals at seq {late}, join scheduled at seq {fired}")
    log.check("the late two arrived after the join fired", min(late) > fired[0], (late, fired))
    log.check("the join ran once", len(of(events, "node_started", "gather")) == 1, "")
    log.check(
        "late arrivals are not merged",
        (ended.status, ended.outputs) == ("passed", {"after": {"main": ["b", "c", "e"]}}),
        ended,
    )


def any_lane(log: Log) -> None:
    _, ended, plan = slow_fan(log, "any", {0, 1, 2, 3}, (2, 0, 3, 1), mode="any")
    log(f"join plan: {plan}")
    log.check(
        "any fires on the first arrival (partition 4) and the rest are late",
        plan == [{"join": {"mode": "any", "expected": 5, "merged": [4], "late": [0, 1, 2, 3]}}],
        plan,
    )
    log.check(
        "the run finishes on the first arrival alone",
        (ended.status, ended.outputs) == ("passed", {"after": {"main": ["e"]}}),
        ended,
    )


def loop(log: Log) -> None:
    doc = document(
        [
            node("start", "trigger"),
            node("again", "loop", no_progress_rounds=2, metric="score", max_iterations=20),
            node("improve", "script"),
            node("after", "script"),
        ],
        {
            "start": {"main": [edge("again")]},
            "again": {"body": [edge("improve")], "done": [edge("after")]},
            "improve": {"main": [edge("again", port="next")]},
        },
    )
    definition = validated(log, "loop", doc)

    def flat(_: NodeJob, value: JsonValue) -> JsonValue:
        rounds = cast(dict[str, Any], value).get("round", 0)
        return {"round": rounds + 1, "score": 0.5}

    run = engine_run(definition, Script(flat, only="improve"), "run-loop")
    ended = run.start({"round": 0})
    events = run.events
    plans = [e["plan"] for e in of(events, "node_scheduled", "again")]
    for plan in plans:
        log(f"loop plan: {plan}")
    runs = [e["iteration"] for e in of(events, "node_started", "improve")]
    log(f"body iterations run: {runs}; ended {ended}")
    log.check(
        "the loop stops after the second flat round (body ran 3 times, stop before iteration 3)",
        runs == [0, 1, 2] and plans[-1] == {"loop": {"iteration": 3, "stop": "no_progress_rounds"}},
        (runs, plans[-1]),
    )
    log.check(
        "the value leaves on done",
        (ended.status, ended.outputs)
        == ("passed", {"after": {"main": {"round": 3, "score": 0.5}}}),
        ended,
    )


def wait(log: Log) -> None:
    doc = document(
        [node("start", "trigger"), node("pause", "wait", seconds=30), node("after", "script")],
        {"start": {"main": [edge("pause")]}, "pause": {"main": [edge("after")]}},
    )
    definition = validated(log, "wait", doc)
    run = engine_run(definition, Script(), "run-wait")
    first = run.start({"topic": "q-fin"})
    log(f"started at {NOW}: {first}")
    hold = of(run.events, "node_waiting", "pause")
    log(f"hold recorded: {hold}")
    tick_1 = run.tick("2026-10-17T09:00:20+00:00")
    log(f"tick 09:00:20: {tick_1}; pause started: {of(run.events, 'node_started', 'pause')}")
    log.check(
        "it holds until resume_at 09:00:30 and does not start on the first tick",
        tick_1.status == "waiting"
        and [h["resume_at"] for h in hold] == ["2026-10-17T09:00:30+00:00"]
        and of(run.events, "node_started", "pause") == [],
        tick_1,
    )
    tick_2 = run.tick("2026-10-17T09:00:40+00:00")
    log(f"tick 09:00:40: {tick_2}")
    log.check(
        "it resumes on the tick past resume_at",
        (tick_2.status, tick_2.outputs) == ("passed", {"after": {"main": {"topic": "q-fin"}}}),
        tick_2,
    )


def cartesian(log: Log) -> None:
    def doc(explicit: bool) -> dict[str, Any]:
        extra = {"explicit": True} if explicit else {}
        return document(
            [
                node("start", "trigger"),
                node("rows", "script"),
                node("cols", "script"),
                node("pair", "script"),
                node("gather", "join"),
            ],
            {
                "start": {"main": [edge("rows"), edge("cols")]},
                "rows": {"main": [edge("pair", "cartesian", **extra)]},
                "cols": {"main": [edge("pair", "cartesian", **extra)]},
                "pair": {"main": [edge("gather")]},
            },
        )

    folder = throwaway_home("ep6", "cartesian-unmarked")
    (folder / "definition.json").write_text(json.dumps(doc(explicit=False)), encoding="utf-8")
    refused = [p.code for p in validate(load(folder))]
    log(f"unmarked cartesian: {refused}")
    log.check(
        "an unmarked cartesian is refused at validation",
        refused == ["cartesian_not_explicit"] * 2,
        refused,
    )
    definition = validated(log, "cartesian", doc(explicit=True))

    def pick(job: NodeJob, value: JsonValue) -> JsonValue:
        return (
            cast(dict[str, Any], value)[job.node_id] if job.node_id in ("rows", "cols") else value
        )

    run = engine_run(definition, Script(pick), "run-cartesian")
    ended = run.start({"rows": [1, 2, 3], "cols": ["w", "x", "y", "z"]})
    started = of(run.events, "node_started", "pair")
    log(f"pair partitions run: {len(started)}; ended {ended}")
    log.check("12 partitions run", len(started) == 12, len(started))
    pairs = [[r, c] for r in (1, 2, 3) for c in "wxyz"]
    log.check(
        "the join holds every pair in row-major order",
        (ended.status, ended.outputs) == ("passed", {"gather": {"main": pairs}}),
        ended,
    )


def keyed(log: Log) -> None:
    doc = document(
        [
            node("start", "trigger"),
            node("cards", "script"),
            node("checks", "script"),
            node("match", "script"),
            node("gather", "join"),
        ],
        {
            "start": {"main": [edge("cards"), edge("checks")]},
            "cards": {"main": [edge("match", "keyed-join", key="paper_id")]},
            "checks": {"main": [edge("match", "keyed-join", key="paper_id")]},
            "match": {"main": [edge("gather")]},
        },
    )
    definition = validated(log, "keyed", doc)

    def pick(job: NodeJob, value: JsonValue) -> JsonValue:
        return (
            cast(dict[str, Any], value)[job.node_id]
            if job.node_id in ("cards", "checks")
            else value
        )

    papers = {
        "cards": [
            {"paper_id": "p1", "card": "c1"},
            {"paper_id": "p2", "card": "c2"},
            {"paper_id": "p3", "card": "c3"},
        ],
        "checks": [
            {"paper_id": "p3", "ok": True},
            {"paper_id": "p1", "ok": False},
            {"paper_id": "p9", "ok": True},
        ],
    }
    run = engine_run(definition, Script(pick), "run-keyed")
    ended = run.start(cast(JsonValue, papers))
    plans = [e["plan"] for e in of(run.events, "node_scheduled", "match")]
    log(f"match plans: {plans}")
    gather = cast(dict[str, Any], ended.outputs.get("gather") or {})
    pairs = gather.get("main") if ended.status == "passed" else None
    log(f"pairs: {pairs}")
    log.check(
        "pairs match by paper_id",
        pairs
        == [
            [{"paper_id": "p1", "card": "c1"}, {"paper_id": "p1", "ok": False}],
            [{"paper_id": "p3", "card": "c3"}, {"paper_id": "p3", "ok": True}],
        ],
        pairs,
    )
    unmatched = {json.dumps(p["unmatched"]) for p in cast(list[dict[str, Any]], plans)}
    log.check(
        "the unmatched keys p2 and p9 are reported",
        unmatched == {'["\\"p2\\"", "\\"p9\\""]'},
        unmatched,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    lanes: dict[str, Callable[[Log], None]] = {
        "quorum": quorum,
        "any": any_lane,
        "loop": loop,
        "wait": wait,
        "cartesian": cartesian,
        "keyed": keyed,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep6", f"ep6-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
