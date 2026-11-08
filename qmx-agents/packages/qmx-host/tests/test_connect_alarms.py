"""C-18: the phone alarms' two setup cards, on the shipped step runner, against a fake HTTP
service on 127.0.0.1 made here. Nothing reaches ntfy, Healthchecks.io or a phone."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from qmx_home.rclone import Rclone
from test_connect import Store, qmx_folder

from qmx_host.connect import World, run_kind
from qmx_host.connect_node import NODE_KEYS, alarms_on_this_pc
from qmx_host.jobs import Jobs

Got = tuple[str, str, str | None, str | None, str]


class Fake:
    """One fake HTTP service on 127.0.0.1; ``got`` is every request, answered ``status``."""

    def __init__(self) -> None:
        self.status = 200
        self.got: list[Got] = []
        fake = self

        class Answer(BaseHTTPRequestHandler):
            def answer(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                fake.got.append(
                    (
                        self.command,
                        self.path,
                        self.headers.get("Title"),
                        self.headers.get("Priority"),
                        self.rfile.read(length).decode("utf-8"),
                    )
                )
                self.send_response(fake.status)
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = answer

            def log_message(self, format: str, *args: object) -> None:
                del format, args

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Answer)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}{path}"


@pytest.fixture
def fake() -> Iterator[Fake]:
    made = Fake()
    try:
        yield made
    finally:
        made.server.shutdown()
        made.server.server_close()


def test_each_card_proves_its_destination_with_one_send_and_a_rerun_sends_nothing(
    tmp_path: Path, fake: Fake
) -> None:
    keys = Store()
    layout = qmx_folder(tmp_path / "QMX")
    world = World(layout, keys, Rclone(layout, keys=keys), Jobs(), None)
    kind = alarms_on_this_pc()

    def run() -> dict[str, Any]:
        def quiet(step: str, *, done: int = 0, total: int = 0, **counts: int) -> None:
            del step, done, total, counts

        return dict(run_kind(kind, "this-pc", {}, report=quiet, world=world))

    topic, ping = fake.url("/qmx-c18-topic"), fake.url("/ping/c18-check")

    first = run()
    assert (first["needs"]["card"], first["needs"]["key"], fake.got) == (
        "push",
        "qmx/node-ntfy-topic",
        [],
    )

    fake.status = 500
    keys.replace("qmx/node-ntfy-topic", topic)
    refused = run()
    assert refused["needs"]["line"].endswith(
        "The test send did not land (HTTP 500); check it and write it again"
    )
    assert (keys.read(NODE_KEYS), keys.read("qmx/node-ntfy-topic")) == (None, topic)

    fake.status = 200
    fake.got.clear()
    named = run()
    keys.replace("qmx/node-healthchecks-ping", ping)
    both = run()
    again = run()

    assert fake.got == [
        (
            "POST",
            "/qmx-c18-topic",
            "QMX test",
            "3",
            "A test from the trading node's setup. Alarms that need you will arrive here.",
        ),
        ("GET", "/ping/c18-check", None, None, ""),
    ]
    assert json.loads(keys.read(NODE_KEYS) or "null") == {
        "schema_version": "qmx.node.keys/1",
        "alarms": {"ntfy_topic_url": topic, "healthchecks_ping_url": ping},
    }
    assert (keys.read("qmx/node-ntfy-topic"), keys.read("qmx/node-healthchecks-ping")) == (
        None,
        None,
    )
    assert (named["needs"]["card"], both.get("needs"), again.get("needs")) == (
        "liveness",
        None,
        None,
    )
    assert {"push: already done, skipped", "liveness: already done, skipped"} <= set(again["lines"])
    said = json.dumps([first, refused, named, both, again])
    assert topic not in said
    assert ping not in said
