"""The stuck detector's chat rules, through the harness's public names."""

from __future__ import annotations

from qma.harness import (
    Pulse,
    Quiet,
    StuckCall,
    StuckTimeouts,
    judge_stuck,
    stuck_call,
    stuck_digest,
    watch_progress,
)


def pytest_run(failed: list[str], seconds: str, tmp: str = "C:/Temp/pytest-of-me/7") -> StuckCall:
    lines = [f"FAILED tests/test_x.py::test_{name} - assert 1 == 2" for name in failed]
    summary = f"== {len(failed)} failed, 4 passed in {seconds} =="
    text = "\n".join([f"rootdir: {tmp}", *lines, summary])
    return stuck_call("Bash", {"command": "uv run pytest"}, text, error=True, masks=[tmp])


def edit(n: int) -> StuckCall:
    return stuck_call("Edit", {"file": "src/x.py", "new": f"fix {n}"}, "ok", error=False)


def test_five_identical_calls_and_results_are_a_loop() -> None:
    calls = [stuck_call("Read", {"path": "a.txt"}, "same text", error=False) for _ in range(5)]
    assert judge_stuck(calls[:4]) == "progress"
    assert judge_stuck(calls) == "loop"


def test_a_rerun_with_the_same_failures_matches_itself_across_durations_and_temp_paths() -> None:
    first = pytest_run(["a", "b"], "0.42s", "C:/Temp/pytest-of-me/7")
    again = pytest_run(["a", "b"], "1.97s", "C:/Temp/pytest-of-me/8")
    assert first.result == again.result
    assert first.failing == frozenset({"tests/test_x.py::test_a", "tests/test_x.py::test_b"})
    assert first.failures == 2


def test_a_flailing_fixer_does_not_converge() -> None:
    calls: list[StuckCall] = []
    for n in range(6):
        calls += [edit(n), pytest_run(["a", "b"], f"0.{n}s")]
    assert judge_stuck(calls[:10]) == "progress"
    assert judge_stuck(calls) == "no_convergence"


def test_a_converging_fixer_is_progress() -> None:
    calls: list[StuckCall] = []
    for n, failed in enumerate([["a", "b", "c", "d", "e"], ["a", "b", "c"], ["a"]] * 3):
        calls += [edit(n), pytest_run(failed, "0.3s")]
    assert judge_stuck(calls) == "progress"


def test_a_pager_over_new_rows_is_progress() -> None:
    calls = [
        stuck_call(
            "Bash", {"command": f"sql page {n}"}, f"rows {n * 50}..{n * 50 + 49}", error=False
        )
        for n in range(20)
    ]
    assert judge_stuck(calls) == "progress"


def test_reading_the_same_two_files_round_and_round_is_a_loop() -> None:
    calls = [
        stuck_call("Read", {"path": name}, f"text of {name}", error=False)
        for _ in range(5)
        for name in ("a.txt", "b.txt")
    ]
    assert judge_stuck(calls) == "loop"


def test_the_stuck_digest_keeps_counts_and_masks_uuids_and_times() -> None:
    one = "run 3f2b1c4e-1111-4222-8333-944455556666 at 2026-10-18T10:00:01Z: 5 rows"
    two = "run 0a0b0c0d-1111-4222-8333-944455556666 at 2026-10-18T11:30:59Z: 5 rows"
    assert stuck_digest(one) == stuck_digest(two)
    assert stuck_digest(one) != stuck_digest(one.replace("5 rows", "6 rows"))


TIMEOUTS = StuckTimeouts(idle=300, in_tool=1_200, grace=120)


def ticks(pulses: list[Pulse], every: float = 60) -> list[str]:
    quiet, alarms = Quiet(), list[str]()
    for pulse in pulses:
        quiet, alarm = watch_progress(quiet, pulse, every, TIMEOUTS)
        alarms.append(alarm)
    return alarms


def test_silence_warns_at_80_percent_then_interrupts_then_stalls_after_grace() -> None:
    assert ticks([Pulse(1)] * 8) == [
        "none",
        "none",
        "none",
        "none",
        "warn",
        "interrupt",
        "none",
        "stalled",
    ]


def test_a_request_in_flight_is_progress_through_a_400_second_first_token_wait() -> None:
    assert set(ticks([Pulse(1, in_flight=True)] * 8)) == {"none"}


def test_a_recorded_wait_is_skipped() -> None:
    assert set(ticks([Pulse(1, waiting=True)] * 30)) == {"none"}


def test_an_open_tool_counts_only_time_without_cpu_or_io() -> None:
    busy = [Pulse(1, tool_open=True, busy=True)] * 40
    assert set(ticks(busy)) == {"none"}
    quiet = ticks([Pulse(1, tool_open=True)] * 21)
    assert quiet[16] == "warn"
    assert quiet[20] == "interrupt"
