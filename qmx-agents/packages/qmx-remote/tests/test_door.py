"""A remote attempt reads price data only through the server door, with its pass's scope (AD-70)."""

from __future__ import annotations

import base64
import json
import threading
from collections.abc import Iterator, Mapping
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from pydantic import JsonValue

from qmx_remote.sidecar import (
    Attempt,
    AttemptKeys,
    Door,
    DoorRefused,
    DoorUnreachable,
    Sidecar,
    read_data,
)

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


@pytest.fixture
def listening_door() -> Iterator[tuple[str, list[dict[str, object]]]]:
    asked: list[dict[str, object]] = []

    class Answer(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            asked.append(json.loads(self.rfile.read(int(self.headers["content-length"]))))
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"rows": 1}')

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = HTTPServer(("127.0.0.1", 0), Answer)
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", asked
    finally:
        server.shutdown()
        server.server_close()


def attempt(door_url: str, parameters: dict[str, JsonValue]) -> Attempt:
    return Attempt(
        keys=AttemptKeys("run-1", "fetch", 0, None, 1),
        node_definition={"type": "script", "parameters": parameters},
        inputs=None,
        inputs_hash="",
        placement="contabo",
        mode="test",
        resolved_model=None,
        now=None,
        run_pass=run_pass({"run": "run-1", "data_scope": [SERIES]}),
        secrets=(),
        door_url=door_url,
    )


def test_the_sidecar_forwards_the_range_a_node_declares(
    tmp_path: Path, listening_door: tuple[str, list[dict[str, object]]]
) -> None:
    url, asked = listening_door
    bounded = attempt(url, {"data_scope": [SERIES], "start_ns": 100, "end_ns": 200})
    whole = attempt(url, {"data_scope": [SERIES]})

    read_data(bounded, Sidecar(tmp_path / "a", bounded), tmp_path / "a" / "data")
    read_data(whole, Sidecar(tmp_path / "b", whole), tmp_path / "b" / "data")

    scoped = {"series": SERIES, "purpose": "exploration", "data_scope": [SERIES]}
    assert asked == [scoped | {"start_ns": 100, "end_ns": 200}, scoped]
    written = tmp_path / "a" / "data" / "dukascopy__EURUSD__tick__-.json"
    assert json.loads(written.read_text(encoding="utf-8")) == {"rows": 1}
