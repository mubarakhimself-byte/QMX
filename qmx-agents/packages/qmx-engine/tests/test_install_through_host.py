"""`python -m qmx_engine templates install` through a running host (loose strings P5): it posts,
reads the host's install job until it ends and prints the same rows as before. It installs in its
own process only when its first POST cannot connect; a host lost after it answered ends the
command with one line and never starts a second install."""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from qmx_home import resolve

from qmx_engine import __main__ as cli

KEY = "install-check"
PUBLISHED = {
    "id": "backup-weekly",
    "folder": "backup-weekly",
    "action": "published",
    "detail": "0.1.0 obj-1, disabled; test 1 s",
}
DRAFTED = {
    "id": "stress-tests",
    "folder": "rk5-stress-tests",
    "action": "saved draft",
    "detail": "needs: trading-node",
}
PRINTED = [
    "backup-weekly backup-weekly published: 0.1.0 obj-1, disabled; test 1 s",
    "stress-tests rk5-stress-tests saved draft: needs: trading-node",
]


def job(state: str, *rows: dict[str, str], line: str = "", code: str = "") -> dict[str, Any]:
    """The host's view of its install job, two templates long."""
    result: dict[str, Any] = {"rows": list(rows)} | ({"code": code} if code else {})
    return {
        "id": "job-1",
        "kind": "templates-install",
        "state": state,
        "step": "",
        "done": len(rows),
        "total": 2,
        "progress": {},
        "line": line,
        "result": result,
    }


class Host:
    """A stand-in for the host's install door: each request takes the next scripted answer, a
    `(status, body)` pair, or None to drop the connection with no answer at all."""

    def __init__(self, answers: list[tuple[int, object] | None]) -> None:
        self.answers = answers
        self.seen: list[tuple[str, str, str, object]] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                size = int(self.headers.get("Content-Length", "0"))
                stub.answer(self, json.loads(self.rfile.read(size)))

            def do_GET(self) -> None:
                stub.answer(self, None)

            def log_message(self, format: str, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, args=(0.05,))

    def answer(self, request: BaseHTTPRequestHandler, body: object) -> None:
        self.seen.append(
            (request.command, request.path, request.headers.get("Authorization", ""), body)
        )
        scripted = self.answers.pop(0)
        if scripted is None:
            request.close_connection = True
            request.connection.shutdown(socket.SHUT_RDWR)
            return
        status, document = scripted
        sent = json.dumps(document).encode("utf-8")
        request.send_response(status)
        request.send_header("Content-Type", "application/json")
        request.send_header("Content-Length", str(len(sent)))
        request.end_headers()
        request.wfile.write(sent)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@contextmanager
def hosted(answers: list[tuple[int, object] | None]) -> Generator[Host]:
    host = Host(answers)
    host.thread.start()
    try:
        yield host
    finally:
        if host.thread.is_alive():
            host.close()
        host.thread.join(5)


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    def token(home: Path | None = None) -> str:
        return KEY

    monkeypatch.setattr(cli, "local_token", token)
    monkeypatch.setattr(cli, "POLL_S", 0.01)

    def no_second_install(home: Path) -> None:
        raise AssertionError("the command started an install in its own process")

    monkeypatch.setattr(cli, "ControlService", no_second_install)
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def recorded(home: Path, port: int) -> list[str]:
    (home / cli.HOST_STATE).write_text(json.dumps({"pid": 1, "port": port}), "utf-8")
    return ["templates", "install", "--home", str(home.parent)]


def install(home: Path, port: int) -> int:
    return cli.main(
        [*recorded(home, port), "--template", "backup-weekly", "--template", "stress-tests"]
    )


def test_the_command_reads_the_hosts_job_until_it_ends_and_prints_its_rows(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    answers: list[tuple[int, object] | None] = [
        (202, job("running")),
        (200, job("running", PUBLISHED)),
        (200, job("finished", PUBLISHED, DRAFTED)),
    ]
    with hosted(answers) as host:
        code = install(home, host.port)

    assert (code, capsys.readouterr().out.splitlines()) == (0, PRINTED)
    assert host.seen == [
        (
            "POST",
            "/api/templates/install",
            f"Bearer {KEY}",
            {"templates": ["backup-weekly", "stress-tests"]},
        ),
        ("GET", "/api/templates/install/job-1", f"Bearer {KEY}", None),
        ("GET", "/api/templates/install/job-1", f"Bearer {KEY}", None),
    ]


def test_an_older_host_that_answers_the_rows_at_once_is_read_as_before(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with hosted([(200, [PUBLISHED, DRAFTED])]) as host:
        code = install(home, host.port)

    assert (code, capsys.readouterr().out.splitlines()) == (0, PRINTED)
    assert len(host.seen) == 1


def test_a_stopped_job_prints_its_rows_and_its_line_and_fails(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = "the install stopped at stress-tests: no draft; fix that and run the install again"
    answers: list[tuple[int, object] | None] = [
        (202, job("running")),
        (200, job("stopped", PUBLISHED, line=line, code="not_found")),
    ]
    with hosted(answers) as host:
        code = install(home, host.port)

    assert (code, capsys.readouterr().out.splitlines()) == (1, [PRINTED[0], f"stopped: {line}"])


def test_a_stopped_job_with_no_result_still_prints_its_line(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    line = "it stopped with an error: the database is locked"
    stopped = job("stopped", line=line) | {"result": None}
    with hosted([(202, job("running")), (200, stopped)]) as host:
        code = install(home, host.port)

    assert (code, capsys.readouterr().out.splitlines()) == (1, [f"stopped: {line}"])


@pytest.mark.parametrize("lost", ["no answer", "a restarted host", "nothing listening"])
def test_a_host_lost_after_it_answered_ends_the_command_and_starts_no_second_install(
    home: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, lost: str
) -> None:
    after: tuple[int, object] | None = {
        "no answer": None,
        "a restarted host": (404, {"detail": "no template install job job-1 on this host"}),
        "nothing listening": (200, job("running")),
    }[lost]
    with hosted([(202, job("running")), after]) as host:
        if lost == "nothing listening":

            def stop_the_host(_: float) -> None:
                host.close()

            monkeypatch.setattr(cli, "time", SimpleNamespace(sleep=stop_the_host))
        code = install(home, host.port)

    assert (code, capsys.readouterr().out.splitlines()) == (
        1,
        ["the host stopped during the install; start it and run the install again"],
    )


def test_a_first_post_that_cannot_connect_installs_in_this_process(home: Path) -> None:
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        port = taken.getsockname()[1]

    with pytest.raises(AssertionError, match="started an install in its own process"):
        install(home, port)
