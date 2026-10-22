"""`qmx node update` drains before it restarts (AD-65): no attempt is cut mid-node."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from qmx_control.node import drain, update


def answers(*replies: Mapping[str, object]):
    """One queued answer per call, so a test decides when the host reports `drained`."""
    queue = list(replies)

    def post(
        url: str, body: Mapping[str, object], headers: Mapping[str, str]
    ) -> Mapping[str, object]:
        return queue.pop(0)

    return post


def test_the_drain_waits_until_no_attempt_is_in_flight() -> None:
    waited: list[float] = []
    poster = answers({"drained": False, "in_flight": 1}, {"drained": True, "in_flight": 0})

    answer = drain(
        "http://node:8766",
        "token",
        timeout_s=60.0,
        poster=poster,
        sleep=waited.append,
        clock=lambda: 0.0,
    )

    assert (answer["drained"], answer["in_flight"]) == (True, 0)
    assert waited == [2.0]


def test_a_drain_that_never_finishes_restarts_nothing(tmp_path: Path) -> None:
    installed: list[str] = []
    (tmp_path / "vault").mkdir()
    (tmp_path / "vault" / "control-token").write_text("token\n", encoding="utf-8")
    moment = iter([0.0, 0.0, 1_000.0])
    done = update(
        tmp_path,
        tmp_path / "vault",
        revision="a" * 40,
        timeout_s=10.0,
        poster=answers({"drained": False, "in_flight": 1}, {"drained": False, "in_flight": 1}),
        sleep=lambda _s: None,
        clock=lambda: next(moment, 1_000.0),
        installer=installed.append,
        address_of=lambda: "100.64.0.9",
    )

    assert (done["drained"], done["restarted"]) == (False, False)
    assert installed == []
