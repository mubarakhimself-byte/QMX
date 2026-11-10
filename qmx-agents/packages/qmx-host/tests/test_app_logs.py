"""The host's log shipper (C-04): a fake app's JSONL lines reach a stub OTLP endpoint through the
engine's exporter, nothing waits when the endpoint is down and the drops are counted, telemetry
off sends nothing and says so, secrets never leave, incidents are exported, and an outside
agent's note is stored redacted."""

from __future__ import annotations

import asyncio
import json
import socket
import sqlite3
import threading
import time
from collections.abc import Generator, Iterator
from contextlib import closing, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest
from qma.telemetry import OFF, THIS_PC
from qmx_control.service import ControlService, NoteInput
from qmx_engine import telemetry
from qmx_engine.ledger.inbox_table import INCIDENTS
from qmx_engine.telemetry import Telemetry

from qmx_host.app_logs import AppLogs

KEY = "sk-ant-" + "a1" * 12
"""A key-shaped value the engine's redaction knows; built here so no scan reads a literal."""


class Taken:
    def __init__(self) -> None:
        self.posts: list[tuple[str, bytes]] = []

    def logs(self) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for path, body in self.posts:
            if path.endswith("/v1/logs"):
                for part in json.loads(body)["resourceLogs"]:
                    for scope in part["scopeLogs"]:
                        found.extend(scope["logRecords"])
        return found


@contextmanager
def serving(taken: Taken, port: int = 0) -> Generator[str]:
    """An OTLP/HTTP endpoint on the loopback that keeps every post."""

    class Answer(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            del format, args

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            taken.posts.append((self.path, body))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

    server = ThreadingHTTPServer(("127.0.0.1", port), Answer)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def stub() -> Iterator[tuple[str, Taken]]:
    taken = Taken()
    with serving(taken) as endpoint:
        yield endpoint, taken


def exporter(endpoint: str, home: Path) -> Telemetry:
    found = Telemetry(endpoint, state=home / "logs" / "telemetry.json")
    found.start()
    return found


def app_log(home: Path, app_id: str, *lines: object, name: str = "app.jsonl") -> Path:
    path = home / "apps" / app_id / "logs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        for line in lines:
            file.write((line if isinstance(line, str) else json.dumps(line)) + "\n")
    return path


def attributes(record: dict[str, Any]) -> dict[str, object]:
    return {item["key"]: next(iter(item["value"].values())) for item in record["attributes"]}


def test_a_fake_apps_lines_reach_the_endpoint_once_across_restarts(
    tmp_path: Path, stub: tuple[str, Taken]
) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    path = app_log(
        tmp_path,
        "fake-app",
        {"at": "2026-11-01T10:00:00+00:00", "level": "warning", "message": "feed late"},
        "plain text line",
    )
    with path.open("a", encoding="utf-8") as file:
        file.write('{"message": "half writ')
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 2
    sender.flush()
    with path.open("a", encoding="utf-8") as file:
        file.write('ten"}\n')
    again = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)
    assert again.tick() == 1, "a new shipper starts where the saved cursor stopped"
    assert again.tick() == 0
    sender.close()

    shipped = taken.logs()
    assert [r["body"]["stringValue"] for r in shipped] == [
        "feed late",
        "plain text line",
        "half written",
    ]
    assert shipped[0]["severityText"] == "WARN"
    assert shipped[0]["timeUnixNano"] == "1793527200000000000"
    first = attributes(shipped[0])
    assert (first["qmx.app_id"], first["qmx.log_file"], first["qmx.record"]) == (
        "fake-app",
        "app.jsonl",
        "app_log",
    )
    assert sender.stats()["dropped"] == 0


def test_with_the_endpoint_down_nothing_waits_and_drops_are_counted(tmp_path: Path) -> None:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        down = f"http://127.0.0.1:{sock.getsockname()[1]}"
    sender = exporter(down, tmp_path)
    app_log(tmp_path, "fake-app", *({"message": f"line {n}"} for n in range(50)))
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    began = time.perf_counter()
    assert shipper.tick() == 50
    assert time.perf_counter() - began < 1.0, "handing lines never waits on the endpoint"
    sender.flush()
    app_log(tmp_path, "fake-app", {"message": "the app keeps writing"})
    assert shipper.tick() == 1
    sender.close()

    stats = sender.stats()
    assert (stats["sent"], stats["dropped"]) == (0, 51)
    saved = json.loads((tmp_path / "logs" / "telemetry.json").read_text(encoding="utf-8"))
    assert saved["dropped"] == 51


def test_a_full_exporter_leaves_the_rest_on_disk(tmp_path: Path) -> None:
    sender = Telemetry("http://127.0.0.1:9", post=lambda _url, _body: None)
    app_log(tmp_path, "fake-app", *({"message": f"line {n}"} for n in range(600)))
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 512, "no more than the exporter holds (CAPACITY 512)"
    assert shipper.tick() == 0, "nothing is handed while the exporter is full"
    sender.flush()
    assert shipper.tick() == 88
    assert sender.stats()["dropped"] == 0


def test_telemetry_off_sends_nothing_and_says_off(tmp_path: Path, stub: tuple[str, Taken]) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    app_log(tmp_path, "fake-app", {"message": "stays home"})
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: OFF)

    assert shipper.tick() == 0
    sender.close()

    assert taken.posts == []
    line = shipper.doctor_line()
    assert (line.name, line.ok) == ("deep logs", True)
    assert line.detail.startswith("Telemetry off")


def test_a_secret_looking_field_never_leaves(tmp_path: Path, stub: tuple[str, Taken]) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    app_log(
        tmp_path,
        "fake-app",
        {
            "message": f"signed in with {KEY}",
            "password": "hunter2-correct-horse",
            "headers": {"X-Auth-Token": "short1"},
            "tokens_in": 120,
        },
    )
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 1
    sender.close()

    sent = b"".join(body for _path, body in taken.posts)
    for secret in (KEY, "hunter2-correct-horse", "short1"):
        assert secret.encode() not in sent
    record = taken.logs()[0]
    assert record["body"]["stringValue"] == "signed in with [redacted]"
    fields = attributes(record)
    assert fields["qmx.password"] == "[redacted]"
    assert json.loads(cast("str", fields["qmx.headers"])) == {"X-Auth-Token": "[redacted]"}
    assert fields["qmx.tokens_in"] == "120"


def posts_reach(taken: Taken, count: int) -> bool:
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if len(taken.posts) >= count:
            return True
        time.sleep(0.05)
    return False


def test_a_non_finite_number_arrives_as_text_and_the_sender_keeps_sending(
    tmp_path: Path, stub: tuple[str, Taken]
) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    app_log(
        tmp_path,
        "fake-app",
        '{"message": "odd numbers", "n": NaN, "low": -Infinity, "big": 1e400, "ok": 1.5}',
    )
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 1
    assert posts_reach(taken, 1), "the sender thread posts the batch that held the odd numbers"
    app_log(tmp_path, "fake-app", {"message": "the next line"})
    assert shipper.tick() == 1
    assert posts_reach(taken, 2), "the sender thread is still alive for the next batch"
    sender.close()

    shipped = taken.logs()
    assert [r["body"]["stringValue"] for r in shipped] == ["odd numbers", "the next line"]
    fields = attributes(shipped[0])
    assert (fields["qmx.n"], fields["qmx.low"], fields["qmx.big"]) == ("NaN", "-Infinity", "1e400")
    assert fields["qmx.ok"] == 1.5
    stats = sender.stats()
    assert (stats["sent"], stats["dropped"], stats["failed"]) == (2, 0, 0)


def test_a_200000_deep_line_ships_as_text_and_the_next_line_ships(
    tmp_path: Path, stub: tuple[str, Taken]
) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    deep = "[" * 200_000 + "]" * 200_000
    deep_in_a_field = '{"message": "too deep to walk", "n": ' + "[" * 3_000 + "]" * 3_000 + "}"
    app_log(tmp_path, "fake-app", deep, deep_in_a_field, {"message": "the next line"})
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 3
    sender.close()

    assert [r["body"]["stringValue"] for r in taken.logs()] == [
        deep,
        deep_in_a_field,
        "the next line",
    ]
    assert AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC).tick() == 0


def test_a_breaker_line_reads_as_an_error(tmp_path: Path, stub: tuple[str, Taken]) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    app_log(
        tmp_path,
        "fake-app",
        {"at": "2026-11-01T10:00:00+00:00", "event": "breaker_open", "reason": "errors"},
        {"at": "2026-11-01T10:00:01+00:00", "event": "installed", "version": "1.0.0"},
        {"at": "2026-11-01T10:00:02+00:00", "event": "stderr", "message": "a warning it printed"},
        name="supervisor.jsonl",
    )
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 3
    sender.close()

    assert [(r["severityText"], r["body"]["stringValue"]) for r in taken.logs()] == [
        ("ERROR", "breaker_open"),
        ("INFO", "installed"),
        ("INFO", "a warning it printed"),
    ]
    fields = attributes(taken.logs()[0])
    assert (fields["qmx.event"], fields["qmx.reason"]) == ("breaker_open", "errors")


def test_outage_then_recovery_leaves_the_doctor_green_with_the_count(tmp_path: Path) -> None:
    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    endpoint = f"http://127.0.0.1:{port}"
    telemetry.reset()
    sender = telemetry.configure(endpoint, state=tmp_path / "logs" / "telemetry.json")
    shipper = AppLogs(tmp_path, switch=lambda: THIS_PC)
    taken = Taken()
    try:
        app_log(tmp_path, "fake-app", {"message": "during the outage"})
        assert shipper.tick() == 1
        sender.flush()

        down = shipper.doctor_line()
        assert (down.name, down.ok, down.detail) == (
            "deep logs",
            False,
            f"Telemetry on to {endpoint}: 1 app log lines and incidents shipped since the host "
            "started from 1 files; 1 records dropped; the last post failed",
        )

        with serving(taken, port):
            app_log(tmp_path, "fake-app", {"message": "after the outage"})
            assert shipper.tick() == 1
            sender.flush()
            back = shipper.doctor_line()

        assert (back.name, back.ok, back.detail) == (
            "deep logs",
            True,
            f"Telemetry on to {endpoint}: 2 app log lines and incidents shipped since the host "
            "started from 1 files; 1 records dropped",
        )
        assert [r["body"]["stringValue"] for r in taken.logs()] == ["after the outage"]
    finally:
        telemetry.reset()


def test_a_pass_that_raises_does_not_end_the_shipper(
    tmp_path: Path, stub: tuple[str, Taken], capsys: pytest.CaptureFixture[str]
) -> None:
    endpoint, taken = stub
    sender = exporter(endpoint, tmp_path)
    passes: list[int] = []

    def fails_once() -> Telemetry:
        passes.append(1)
        if len(passes) == 1:
            raise RuntimeError("the first pass broke")
        return sender

    app_log(tmp_path, "fake-app", {"message": "still ships"})
    shipper = AppLogs(tmp_path, exporter=fails_once, switch=lambda: THIS_PC)

    async def run_until_shipped() -> None:
        running = asyncio.create_task(shipper.run())
        deadline = time.monotonic() + 10.0
        while shipper.shipped == 0 and not running.done() and time.monotonic() < deadline:
            await asyncio.sleep(0.05)
        alive = not running.done()
        running.cancel()
        await asyncio.gather(running, return_exceptions=True)
        assert alive, "the shipping task is still running after the pass that raised"

    asyncio.run(run_until_shipped())
    sender.close()

    assert [r["body"]["stringValue"] for r in taken.logs()] == ["still ships"]
    assert "app logs: a shipping pass was skipped: the first pass broke" in capsys.readouterr().err


def test_an_open_incident_is_exported_once_until_it_changes(
    tmp_path: Path, stub: tuple[str, Taken]
) -> None:
    endpoint, taken = stub
    inbox = tmp_path / "engine" / "inbox.sqlite"
    inbox.parent.mkdir(parents=True)
    with closing(sqlite3.connect(inbox)) as db, db:
        db.execute(INCIDENTS)
        db.execute(
            "INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                "inc-1",
                "nightly",
                "sig",
                "a storage refused",
                f"bucket said {KEY}",
                1,
                "2026-11-01T09:00:00+00:00",
                "2026-11-01T09:00:00+00:00",
                None,
                None,
            ),
        )
    sender = exporter(endpoint, tmp_path)
    shipper = AppLogs(tmp_path, exporter=lambda: sender, switch=lambda: THIS_PC)

    assert shipper.tick() == 1
    assert shipper.tick() == 0
    with closing(sqlite3.connect(inbox)) as db, db:
        db.execute("UPDATE incidents SET count = 2, last_seen = '2026-11-01T09:05:00+00:00'")
    assert shipper.tick() == 1
    sender.close()

    shipped = taken.logs()
    assert [r["body"]["stringValue"] for r in shipped] == ["a storage refused"] * 2
    assert shipped[0]["severityText"] == "ERROR"
    fields = attributes(shipped[1])
    assert (fields["qmx.record"], fields["qmx.count"]) == ("incident", "2")
    assert fields["qmx.cause"] == "bucket said [redacted]"


def test_an_outside_agents_note_is_stored_redacted(tmp_path: Path) -> None:
    control = ControlService(tmp_path, secret_getter=lambda _s, _n: None)

    saved = control.ops_note(NoteInput(body=f"the feed key is {KEY}"), observer="observer-1")

    with closing(sqlite3.connect(tmp_path / "control.db")) as db:
        stored = db.execute("SELECT body FROM observer_notes").fetchall()
    assert stored == [("the feed key is [redacted]",)]
    assert saved["body"] == "the feed key is [redacted]"
