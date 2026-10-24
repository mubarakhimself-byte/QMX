"""A remote attempt reads price data only through the server door, with its pass's scope (AD-70)."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping

import pytest

from qmx_remote.sidecar import Door, DoorRefused, DoorUnreachable

SERIES = "dukascopy/EURUSD/tick/-"
DOOR = "http://qmx-server:8765"


def run_pass(fields: Mapping[str, object]) -> str:
    body = base64.urlsafe_b64encode(json.dumps(fields).encode()).decode().rstrip("=")
    return f"qmx1.{body}.mac"


class Recorder:
    def __init__(self, answer: bytes = b'{"rows": 2}') -> None:
        self.answer = answer
        self.calls: list[tuple[str, dict[str, object], dict[str, str]]] = []

    def __call__(self, url: str, body: bytes, headers: Mapping[str, str]) -> bytes:
        self.calls.append((url, json.loads(body), dict(headers)))
        return self.answer


def test_a_sidecar_read_without_data_scope_is_refused() -> None:
    post = Recorder()
    door = Door(DOOR, run_pass({"run": "run-1", "placement": "contabo"}), post=post)

    with pytest.raises(DoorRefused) as refused:
        door.read(SERIES)

    assert refused.value.code == "data_scope"
    assert post.calls == []


def test_a_scoped_read_goes_through_the_door_with_the_pass_and_its_scope() -> None:
    token = run_pass({"run": "run-1", "data_scope": [SERIES]})
    post = Recorder()

    answer = Door(DOOR, token, post=post).read(SERIES)

    assert answer == {"rows": 2}
    assert post.calls == [
        (
            "http://qmx-server:8765/api/data/read",
            {"series": SERIES, "purpose": "exploration", "data_scope": [SERIES]},
            {"authorization": f"Bearer {token}", "content-type": "application/json"},
        )
    ]


def test_a_door_that_does_not_answer_is_unreachable_not_refused() -> None:
    def down(url: str, body: bytes, headers: Mapping[str, str]) -> bytes:
        raise OSError("no route to host")

    door = Door(DOOR, run_pass({"data_scope": [SERIES]}), post=down)

    with pytest.raises(DoorUnreachable):
        door.read(SERIES)
