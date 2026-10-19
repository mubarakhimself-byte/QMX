"""BUG3: an inbox answer folds as `gate_resolved` and moves the run (B-28, B-32), the run status
is a pure fold over the ledger and the engine's live attempts (B-40, B-73), and a failed partition
walks the ladder on its own while its siblings stand (B-35)."""

from __future__ import annotations

from pathlib import Path

from flows import Flow, edge, node, of, started_slots, workflow
from pydantic import JsonValue

from qmx_engine.core.commands import Finish, Pause, StartNode
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.definition.model import Workflow
from qmx_engine.ledger.events import Event, EventKind
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult, Ok
from qmx_engine.runner import Engine, Outcome
from qmx_engine.service.runs import status_of
from qmx_engine.settings import DEFAULTS

NOW = "2026-10-17T09:00:00+00:00"
GATE_KEY = "run-1:post:0:1"


def event(seq: int, kind: EventKind, **data: JsonValue) -> Event:
    return Event(seq, "run-1", NOW, kind, data)


def slot(node_id: str, attempt: int, partition: int | None = None) -> dict[str, JsonValue]:
    return {"node_id": node_id, "iteration": 0, "partition": partition, "attempt": attempt}


def posting(*, role: bool = False) -> Workflow:
    post = node("post", "script")
    post |= {"effect": "irreversible_external"} | ({"role": "writer"} if role else {})
    return workflow(
        [node("start", "trigger"), post, node("after", "script")],
        {"start": {"main": [edge("post")]}, "post": {"main": [edge("after")]}},
    )


GATED: list[Event] = [
    event(1, "run_created", settings={"roles.writer": ["first", "second"]}),
    event(2, "run_input", inputs={}),
    event(3, "clock_tick", now=NOW),
    event(4, "node_scheduled", **slot("start", 1), memo_key="m-start"),
    event(5, "node_started", **slot("start", 1)),
    event(6, "node_finished", **slot("start", 1), outputs={"main": "go"}),
    event(7, "node_scheduled", **slot("post", 1), memo_key="m-post"),
    event(8, "node_started", **slot("post", 1)),
    event(9, "gate_opened", **slot("post", 1), idempotency_key=GATE_KEY),
    event(10, "node_waiting", **slot("post", 1), reason="gate", resume_at=None),
]


def answer(action: str) -> Event:
    return event(11, "gate_resolved", **slot("post", 1), answer=action, principal="operator")


def test_b32_retry_folds_into_a_new_attempt_of_the_gated_step() -> None:
    [command] = next_commands(fold(posting(), [*GATED, answer("retry")]))

    assert isinstance(command, StartNode)
    assert (command.node_id, command.attempt, command.idempotency_key) == (
        "post",
        2,
        "run-1:post:0:2",
    )


def test_b32_skip_node_ends_the_step_skipped_and_what_only_it_feeds_is_skipped_too() -> None:
    state = fold(posting(), [*GATED, answer("skip_node")])
    resumed = fold(posting(), [*GATED, answer("skip_node"), event(12, "run_resumed")])

    assert state.nodes[next(s for s in state.nodes if s.node_id == "post")].phase == "skipped"
    assert next_commands(state) == [Finish({})]
    assert [s.node_id for s, run in resumed.nodes.items() if run.phase == "skipped"] == ["post"]


def test_b32_stop_ends_the_run_stopped() -> None:
    events = [*GATED, answer("stop")]

    assert fold(posting(), events).ended == "stopped"
    assert next_commands(fold(posting(), events)) == []
    assert status_of(events).status == "stopped"


def test_b32_stronger_model_moves_the_step_to_its_role_s_next_candidate() -> None:
    [command] = next_commands(fold(posting(role=True), [*GATED, answer("stronger_model")]))

    assert isinstance(command, StartNode)
    assert (command.node_id, command.attempt, command.ladder) == (
        "post",
        2,
        {"candidate": "second"},
    )


def test_b32_resume_lifts_a_pause_at_a_limit_he_wrote() -> None:
    chain = workflow(
        [node("start", "trigger"), node("a", "script"), node("b", "script")],
        {"start": {"main": [edge("a")]}, "a": {"main": [edge("b")]}},
    )
    spent: list[Event] = [
        event(1, "run_created", limits={"tokens": 5}),
        event(2, "run_input", inputs={}),
        event(3, "clock_tick", now=NOW),
        event(4, "node_scheduled", **slot("start", 1), memo_key="m-start"),
        event(5, "node_finished", **slot("start", 1), outputs={"main": "go"}),
        event(6, "node_scheduled", **slot("a", 1), memo_key="m-a"),
        event(7, "node_finished", **slot("a", 1), outputs={"main": "x"}, tokens={"out": 5}),
    ]
    paused = [*spent, event(8, "run_paused", reason="limits")]
    resumed = [*paused, event(9, "gate_resolved", answer="resume", principal="operator")]

    assert next_commands(fold(chain, spent)) == [Pause("limits", None, "tokens 5 of 5")]
    assert [type(c).__name__ for c in next_commands(fold(chain, resumed))] == ["StartNode"]
    assert status_of(paused).status == "waiting"
    assert status_of(resumed).status == "waiting"


class Unknown:
    """The external step's first attempt ends with its outcome unknown; later ones post."""

    def __init__(self) -> None:
        self.jobs: list[NodeJob] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append(job)
        if job.node_id == "post" and job.attempt == 1:
            return Failed("timeout", "no answer", "sig", True, effect_state="unknown")
        return Ok({"main": job.node_id})


def test_b28_an_inbox_retry_on_an_unknown_external_step_wakes_the_run_and_it_posts_once_more(
    tmp_path: Path,
) -> None:
    step = Unknown()
    flow = Flow(tmp_path, posting(), {"script": step})

    async def scenario(engine: Engine) -> tuple[Outcome, str, list[str], Outcome]:
        held = await flow.started(engine, {})
        [item] = engine.inbox.list_items()
        waiting = status_of(flow.events).reason or ""
        engine.inbox.resolve(item.id, "retry", "operator", at=NOW)
        with Reader.open(flow.home) as reader:
            wakes = [r for (r,) in reader.connection.execute("SELECT run_id FROM wakes")]
        return held, waiting, wakes, await engine.resume(flow.run_id, reason="wake")

    held, waiting, wakes, ended = flow.drive(scenario)

    [answered] = of(flow.events, "gate_resolved", "post")
    assert (held.status, waiting) == ("waiting", "gate")
    assert (answered["answer"], answered["principal"], answered["attempt"]) == (
        "retry",
        "operator",
        1,
    )
    assert wakes == ["run-1"]
    assert ended.status == "passed"
    assert [(j.node_id, j.attempt) for j in step.jobs] == [("post", 1), ("post", 2), ("after", 1)]


def test_b40_status_is_a_fold_over_events_and_the_engine_s_live_attempts() -> None:
    created = [event(1, "run_created"), event(2, "run_input", inputs={})]
    running = [*created, event(3, "node_scheduled", **slot("start", 1), memo_key="m")]
    started = [*running, event(4, "node_started", **slot("start", 1))]

    assert status_of(created).status == "queued"
    assert status_of(started, frozenset({"run-1:start:0:1"})).status == "running"
    assert status_of(started).status == "running"
    dead = status_of(started, frozenset[str]())
    assert (dead.status, dead.reason) == (
        "interrupted",
        "the engine stopped with an attempt in flight",
    )


def test_b73_a_slot_waiting_on_its_gate_keeps_the_run_waiting_over_a_resume() -> None:
    resumed = [*GATED, event(11, "run_resumed", reason="operator")]

    assert (status_of(resumed).status, status_of(resumed).reason) == ("waiting", "gate")


def test_b35_a_partition_parked_alone_does_not_fail_the_run() -> None:
    events = [
        event(1, "run_created"),
        event(2, "ladder_step", **slot("read", 1, 2), step="park", scope="partition", reason="x"),
    ]

    assert status_of(events).status == "queued"


MESSAGES = ("timeout talking upstream", "connection reset", "bad gateway", "rate limited")


class Flaky:
    """Partition 2 fails `failures` times, each with its own message, then reads."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.jobs: list[NodeJob] = []

    def run(self, job: NodeJob) -> NodeResult:
        self.jobs.append(job)
        if job.partition == 2 and job.attempt <= self.failures:
            message = MESSAGES[min(job.attempt, len(MESSAGES)) - 1]
            return Failed("upstream", message, signature("upstream", message), True)
        return Ok({"main": job.partition})


def fanned(**join: JsonValue) -> Workflow:
    return workflow(
        [node("start", "trigger"), node("read", "script"), node("gather", "join", **join)],
        {"start": {"main": [edge("read", "broadcast")]}, "read": {"main": [edge("gather")]}},
    )


QUICK: dict[str, object] = {**DEFAULTS, "retry.max_tries": 3, "retry.backoff": (0,)}


def steps(events: list[Event], partition: int) -> list[JsonValue]:
    return [e["step"] for e in of(events, "ladder_step", "read") if e["partition"] == partition]


def test_b35_a_failed_partition_walks_its_own_ladder_while_its_siblings_stand(
    tmp_path: Path,
) -> None:
    flow = Flow(tmp_path, fanned(), {"script": Flaky(failures=2)}, settings=QUICK)

    ended = flow.start(["a", "b", "c", "d"])

    assert (ended.status, ended.outputs) == ("passed", {"gather": {"main": [0, 1, 2, 3]}})
    assert steps(flow.events, 2) == ["retry", "retry"]
    assert sorted(started_slots(flow.events, "read")) == [
        (0, 1),
        (1, 1),
        (2, 1),
        (2, 2),
        (2, 3),
        (3, 1),
    ]


def test_b35_a_join_counts_a_partition_failed_only_after_it_parks(tmp_path: Path) -> None:
    every = Flow(tmp_path, fanned(), {"script": Flaky(failures=9)}, settings=QUICK, run_id="all")
    anyone = Flow(
        tmp_path, fanned(mode="any"), {"script": Flaky(failures=9)}, settings=QUICK, run_id="any"
    )

    failed = every.start(["a", "b", "c", "d"])
    passed = anyone.start(["a", "b", "c", "d"])

    assert steps(every.events, 2) == ["retry", "retry", "account", "doctor", "park"]
    assert (failed.status, failed.reason) == (
        "failed",
        "join gather join_failed: all join has 3 of 4 needed partitions; 1 of 4 failed",
    )
    assert (passed.status, passed.outputs) == ("passed", {"gather": {"main": [0]}})
