"""The failure ladder (AD-16, SOLUTION-DESIGN 10.2) on the real runner and ledger."""

from __future__ import annotations

from pathlib import Path

from flows import edge, node
from planted import OK, Clock, Planted, fails, flow, of_kind, steps

from qmx_engine.nodes.base import NodeJob, NodeResult
from qmx_engine.runner import Classification, Consult, Verdict

WORDS = ("timeout talking upstream", "connection reset", "bad gateway", "rate limited", "eof")


class Doctor:
    def __init__(self, classification: Classification, hint: str | None = None) -> None:
        self.classification: Classification = classification
        self.hint = hint
        self.seen: list[Consult] = []

    async def classify(self, consult: Consult) -> Verdict:
        self.seen.append(consult)
        return Verdict(self.classification, self.hint)


def differently(job: NodeJob) -> NodeResult:
    return fails(WORDS[job.attempt - 1])


def test_the_ladder_walks_retry_account_model_doctor_then_parks(tmp_path: Path) -> None:
    write = node("write", "llm")
    write |= {"role": "writer", "retry": {"backoff_seconds": [0, 0]}}
    llm = Planted(differently)
    doctor = Doctor("logic")
    run = flow(
        tmp_path,
        [node("start", "trigger"), write],
        {"start": {"main": [edge("write")]}},
        executors={"llm": llm},
        doctor=doctor,
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    ladder = of_kind(events, "ladder_step")
    assert steps(events) == ["retry", "retry", "account", "model", "doctor", "park"]
    assert (ladder[2]["reason"], ladder[2]["skipped"], ladder[3]["candidate"]) == (
        "skipped: no pool",
        True,
        "gpt",
    )
    assert [job.resolved_model for job in llm.jobs] == [None, None, None, {"candidate": "gpt"}]
    assert of_kind(events, "doctor_verdict")[0]["classification"] == "logic"
    assert (outcome.status, outcome.reason) == (
        "failed",
        "node write failed: boom: rate limited; the doctor found logic: "
        "a logic failure is not retried",
    )
    assert run.items() == []


def test_each_retry_waits_its_backoff_on_the_recorded_clock(tmp_path: Path) -> None:
    clock = Clock()
    script = Planted(differently)
    run = flow(
        tmp_path,
        [node("start", "trigger"), node("step", "script", script="scripts/step.py")],
        {"start": {"main": [edge("step")]}},
        executors={"script": script},
        wall=clock,
    )

    first = run.start()
    clock.move(30)
    second = run.resume(first.run_id)
    clock.move(120)
    third = run.resume(first.run_id)

    retries = [d["resume_at"] for d in of_kind(run.events(first.run_id), "ladder_step")[:2]]
    assert retries == ["2026-10-17T09:00:30+00:00", "2026-10-17T09:02:30+00:00"]
    assert [first.status, second.status, third.status] == ["waiting", "waiting", "failed"]
    assert len(script.jobs) == 3


def test_a_runaway_breach_between_rungs_pauses_instead_of_retrying(tmp_path: Path) -> None:
    clock = Clock()

    def slow_failure(_: NodeJob) -> NodeResult:
        clock.move(120)
        return fails("too slow")

    run = flow(
        tmp_path,
        [node("start", "trigger"), node("step", "script", script="scripts/step.py")],
        {"start": {"main": [edge("step")]}},
        runaway={"wall_seconds": 60},
        executors={"script": Planted(slow_failure)},
        wall=clock,
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    assert (outcome.status, outcome.reason, steps(events)) == ("waiting", "runaway", [])
    assert [line["on_runaway"] for line in of_kind(events, "log")] == ["pause"]
    assert of_kind(events, "run_paused")[0]["reason"] == "runaway"
    assert run.items() == []


def test_the_same_failure_twice_goes_straight_to_the_doctor(tmp_path: Path) -> None:
    step = node("step", "script", script="scripts/step.py")
    step["retry"] = {"max_tries": 5, "backoff_seconds": [0]}
    run = flow(
        tmp_path,
        [node("start", "trigger"), step],
        {"start": {"main": [edge("step")]}},
        executors={"script": Planted(fails("the same thing"))},
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    assert steps(events) == ["retry", "doctor", "park"]
    assert of_kind(events, "ladder_step")[1]["reason"] == "skipped: no doctor"
    assert outcome.status == "failed"


def test_a_transient_verdict_runs_the_node_once_more(tmp_path: Path) -> None:
    step = node("step", "script", script="scripts/step.py")
    step["retry"] = {"max_tries": 1}
    doctor = Doctor("transient")
    run = flow(
        tmp_path,
        [node("start", "trigger"), step],
        {"start": {"main": [edge("step")]}},
        executors={"script": Planted(fails("flaky"), OK)},
        doctor=doctor,
    )

    outcome = run.start()

    events = run.events(outcome.run_id)
    assert (outcome.status, steps(events)) == ("passed", ["account", "doctor"])
    assert [e.kind for e in doctor.seen[0].events] == [
        "node_scheduled",
        "node_started",
        "node_failed",
        "ladder_step",
        "ladder_step",
    ]
