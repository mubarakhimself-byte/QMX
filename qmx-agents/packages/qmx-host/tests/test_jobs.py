"""Long work the host runs in the background and the UI reads by id."""

from __future__ import annotations

import threading
import time

from qmx_host.jobs import Job, Jobs, Progress, Stopped


def ended(jobs: Jobs, job_id: str) -> Job:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = jobs.get(job_id)
        assert job is not None
        if job.state != "running":
            return job
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} still running")


def test_a_job_reports_its_step_and_counts_then_finishes_with_its_result() -> None:
    jobs = Jobs()
    seen = threading.Event()
    go = threading.Event()

    def work(report: Progress) -> dict[str, object]:
        report("copying", done=3, total=10, files_copied=3)
        seen.set()
        go.wait(5)
        return {"folder": "D:/QMX"}

    started = jobs.start("bring-in", work)
    seen.wait(5)
    running = jobs.get(started.job.id)
    go.set()
    done = ended(jobs, started.job.id)

    assert started.new
    assert running is not None
    assert running.document() == {
        "id": started.job.id,
        "kind": "bring-in",
        "state": "running",
        "step": "copying",
        "done": 3,
        "total": 10,
        "progress": {"files_copied": 3},
        "line": "",
        "result": None,
    }
    assert (done.state, done.line, done.result) == ("finished", "", {"folder": "D:/QMX"})
    assert jobs.latest("bring-in") == done


def test_a_job_that_raises_ends_stopped_with_one_line() -> None:
    jobs = Jobs()

    def broken(_report: Progress) -> dict[str, object]:
        raise KeyError("listed")

    def refused(_report: Progress) -> dict[str, object]:
        raise Stopped("the drive is full; free some space", {"rows": [1]})

    first = ended(jobs, jobs.start("one", broken).job.id)
    second = ended(jobs, jobs.start("two", refused).job.id)

    assert (first.state, first.line) == ("stopped", "it stopped with an error: 'listed'")
    assert (second.state, second.line, second.result) == (
        "stopped",
        "the drive is full; free some space",
        {"rows": [1]},
    )


def test_two_starts_of_one_kind_give_one_job_and_one_refusal() -> None:
    jobs = Jobs()
    go = threading.Event()

    def work(_report: Progress) -> dict[str, object]:
        go.wait(5)
        return {}

    first = jobs.start("bring-in", work)
    second = jobs.start("bring-in", work)
    other = jobs.start("install", work, alone=False)
    go.set()

    assert (first.new, second.new, other.new) == (True, False, True)
    assert second.job.id == first.job.id
    assert ended(jobs, first.job.id).state == "finished"
    assert jobs.get("no-such-job") is None
