"""EP6's live lanes for joins, loops, waits and the cartesian and keyed-join maps, driven through
`qmx_engine.core.simulate` with planted executors.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x06_joins_loops.py [lane]`
Lanes are `quorum any loop wait cartesian keyed`; none named runs all. Each lane writes
`evidence/ep6/<ENGINE_LOG_PREFIX>ep6-<lane>.log` and the script exits 1 if any lane failed. No
lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from typing import Any, cast

from common import Log, throwaway_home
from e03_chunks import NOW, Script, document, edge, node, of, simulation, validated
from ep2_lanes import git
from pydantic import JsonValue
from qmx_engine.core.commands import Finish, Wait
from qmx_engine.core.simulate import Simulation
from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import validate
from qmx_engine.nodes.base import NodeJob


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


def deliver(sim: Simulation, partition: int, value: JsonValue) -> object:
    """A slow partition's worker reports in."""
    sim.append(
        "node_finished",
        {
            "node_id": "work",
            "iteration": 0,
            "partition": partition,
            "attempt": 1,
            "outputs": {"main": value},
        },
    )
    return sim.drive()


def join_plan(sim: Simulation) -> JsonValue:
    return [e["plan"] for e in of(sim.events, "node_scheduled", "gather")]


def quorum(log: Log) -> None:
    definition = validated(log, "quorum", fan_in(mode="quorum", n=3))
    sim = simulation(definition, Script(), "run-quorum", None)
    sim.step = slowed(sim, {0, 3})
    first = sim.start(["a", "b", "c", "d", "e"], NOW)
    log(f"partitions 0 and 3 are slow; after the fast three: {first} (None: attempts in flight)")
    plan = join_plan(sim)
    log(f"join plan: {plan}")
    log.check(
        "the join fires at 3, merging 1 2 4, with 0 and 3 recorded late",
        plan == [{"join": {"mode": "quorum", "expected": 5, "merged": [1, 2, 4], "late": [0, 3]}}],
        plan,
    )
    log.check(
        "the downstream ran on the merged three", of(sim.events, "node_started", "after") != [], ""
    )
    deliver(sim, 3, "D")
    ended = deliver(sim, 0, "A")
    late = [
        e.seq for e in sim.events if e.kind == "node_finished" and e.data.get("partition") in (0, 3)
    ]
    fired = [
        e.seq
        for e in sim.events
        if e.kind == "node_scheduled" and e.data.get("node_id") == "gather"
    ]
    log(f"late arrivals at seq {late}, join scheduled at seq {fired}")
    log.check("the late two arrived after the join fired", min(late) > fired[0], (late, fired))
    log.check("the join ran once", len(of(sim.events, "node_started", "gather")) == 1, "")
    log.check(
        "late arrivals are not merged", ended == Finish({"after": {"main": ["b", "c", "e"]}}), ended
    )


def slowed(sim: Simulation, slow: set[int]) -> Any:
    run = sim.step

    def stepped(command: Any) -> Any:
        drafts = run(command)
        return drafts[:1] if command.node_id == "work" and command.partition in slow else drafts

    return stepped


def any_lane(log: Log) -> None:
    definition = validated(log, "any", fan_in(mode="any"))
    sim = simulation(definition, Script(), "run-any", None)
    sim.step = slowed(sim, {0, 1, 2, 3})
    sim.start(["a", "b", "c", "d", "e"], NOW)
    plan = join_plan(sim)
    log(f"join plan: {plan}")
    log.check(
        "any fires on the first arrival (partition 4) and the rest are late",
        plan == [{"join": {"mode": "any", "expected": 5, "merged": [4], "late": [0, 1, 2, 3]}}],
        plan,
    )
    ended = None
    for partition in (2, 0, 3, 1):
        ended = deliver(sim, partition, partition)
    log.check(
        "the run finishes on the first arrival alone",
        ended == Finish({"after": {"main": ["e"]}}),
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

    sim = simulation(definition, Script(flat, only="improve"), "run-loop", None)
    ended = sim.start({"round": 0}, NOW)
    plans = [e["plan"] for e in of(sim.events, "node_scheduled", "again")]
    for plan in plans:
        log(f"loop plan: {plan}")
    runs = [e["iteration"] for e in of(sim.events, "node_started", "improve")]
    log(f"body iterations run: {runs}; ended {ended}")
    log.check(
        "the loop stops after the second flat round (body ran 3 times, stop before iteration 3)",
        runs == [0, 1, 2] and plans[-1] == {"loop": {"iteration": 3, "stop": "no_progress_rounds"}},
        (runs, plans[-1]),
    )
    log.check(
        "the value leaves on done",
        ended == Finish({"after": {"main": {"round": 3, "score": 0.5}}}),
        ended,
    )


def wait(log: Log) -> None:
    doc = document(
        [node("start", "trigger"), node("pause", "wait", seconds=30), node("after", "script")],
        {"start": {"main": [edge("pause")]}, "pause": {"main": [edge("after")]}},
    )
    definition = validated(log, "wait", doc)
    sim = simulation(definition, Script(), "run-wait", None)
    first = sim.start({"topic": "q-fin"}, NOW)
    log(f"started at {NOW}: {first}")
    hold = of(sim.events, "node_waiting", "pause")
    log(f"hold recorded: {hold}")
    tick_1 = sim.tick("2026-10-17T09:00:20+00:00")
    log(f"tick 09:00:20: {tick_1}; pause started: {of(sim.events, 'node_started', 'pause')}")
    log.check(
        "it holds until resume_at 09:00:30 and does not start on the first tick",
        tick_1 == Wait(("pause",), "2026-10-17T09:00:30+00:00")
        and of(sim.events, "node_started", "pause") == [],
        tick_1,
    )
    tick_2 = sim.tick("2026-10-17T09:00:40+00:00")
    log(f"tick 09:00:40: {tick_2}")
    log.check(
        "it resumes on the tick past resume_at",
        tick_2 == Finish({"after": {"main": {"topic": "q-fin"}}}),
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

    sim = simulation(definition, Script(pick), "run-cartesian", None)
    ended = sim.start({"rows": [1, 2, 3], "cols": ["w", "x", "y", "z"]}, NOW)
    started = of(sim.events, "node_started", "pair")
    log(f"pair partitions run: {len(started)}; ended {ended}")
    log.check("12 partitions run", len(started) == 12, len(started))
    pairs = [[r, c] for r in (1, 2, 3) for c in "wxyz"]
    log.check(
        "the join holds every pair in row-major order",
        ended == Finish({"gather": {"main": pairs}}),
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
    sim = simulation(definition, Script(pick), "run-keyed", None)
    ended = sim.start(cast(JsonValue, papers), NOW)
    plans = [e["plan"] for e in of(sim.events, "node_scheduled", "match")]
    log(f"match plans: {plans}")
    pairs = ended.outputs["gather"]["main"] if isinstance(ended, Finish) else None  # type: ignore[index,call-overload]
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
