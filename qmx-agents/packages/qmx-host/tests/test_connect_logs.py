"""Deep logs on this PC and on a server (design 06 section 9): the pinned release fetched and
checked, OpenObserve run on the loopback with its telemetry off and his sizes, a span sent through
QMX's own exporter signed in and found, an approval card when it needs administrator rights, and
the server's step sent the shipped unit files and its collector."""

from __future__ import annotations

import dataclasses
import hashlib
import http.server
import io
import json
import os
import socket
import sys
import threading
import time
import tomllib
import zipfile
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import httpx
import psutil
import pytest
import qma.telemetry
from qmx_engine import telemetry
from qmx_engine.ledger.spans import Span
from test_connect import Store, qmx_folder, world
from test_connect_compute import ADDRESS, PLACE, Server, at, quiet, through_the_cards

from qmx_host.connect import KINDS, Run, World, run_kind
from qmx_host.connect_logs import (
    AGENT_KEY,
    ROOT_KEY,
    Logs,
    OpenObserveProcess,
    Pinned,
    monitoring_script,
)
from qmx_host.jobs import Stopped

STANDIN = Path(__file__).with_name("openobserve_standin.py")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def program(folder: Path, *, deny: bool = False) -> Path:
    """The stand-in as a program on disk; what it needs lives in the file itself."""
    if os.name == "nt":
        path = folder / "openobserve.cmd"
        denied = '@set "QMX_STANDIN_DENY=1"\n' if deny else ""
        path.write_text(f'{denied}@"{sys.executable}" -I "{STANDIN}" %*\n', encoding="utf-8")
        return path
    path = folder / "openobserve"
    denied = "QMX_STANDIN_DENY=1 " if deny else ""
    path.write_text(f'#!/bin/sh\n{denied}exec "{sys.executable}" -I "{STANDIN}"\n', "utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture(autouse=True)
def one_exporter() -> Iterator[None]:
    telemetry.reset()
    yield
    telemetry.reset()


def deep(tmp_path: Path, *, deny: bool = False) -> tuple[World, OpenObserveProcess]:
    layout = qmx_folder(tmp_path / "QMX")
    there = world(layout, keys=Store())
    control = there.control
    assert control is not None
    process = OpenObserveProcess(
        layout,
        there.keys,
        lambda: control.settings_get(cast("Any", "telemetry")),
        port=free_port(),
        program=str(program(tmp_path, deny=deny)),
    )
    return dataclasses.replace(there, logs=Logs(process, release=None)), process


def connect(there: World, kind: str = "deep-logs-pc") -> dict[str, Any]:
    ended = run_kind(KINDS[kind], PLACE, {}, report=quiet, world=there)
    return dict(ended)


def children(process: OpenObserveProcess) -> list[int]:
    child = process._child  # pyright: ignore[reportPrivateUsage]
    return [] if child is None else [child.pid]


def test_deep_logs_on_this_pc_run_openobserve_on_the_loopback_and_a_span_lands_signed_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    there, process = deep(tmp_path)
    try:
        ended = connect(there)
        pid = children(process)
        health = httpx.get(f"http://127.0.0.1:{process.port}/healthz", timeout=5)
        monkeypatch.setattr(
            qma.telemetry, "THIS_PC_ENDPOINT", f"http://127.0.0.1:{process.port}/api/default"
        )
        monkeypatch.setattr(telemetry, "key_of", there.keys.read, raising=False)
        exporter = telemetry.opened(there.layout.home)
        assert exporter is not None
        span = Span(
            span_id="s-1",
            trace_id="run-1",
            node_id="step",
            iteration=0,
            partition=None,
            attempt=1,
            started_at="2026-10-29T09:00:00+00:00",
            ended_at="2026-10-29T09:00:01+00:00",
            status="ok",
        )
        exporter.hand("span", json.dumps(asdict(span)))
        assert exporter.flush() is None
        found = httpx.post(
            f"http://127.0.0.1:{process.port}/api/default/_search",
            headers={"Authorization": there.keys.read(qma.telemetry.INGEST_KEY) or ""},
            json={},
            timeout=5,
        ).json()
        stats = exporter.stats()
    finally:
        process.stop()

    assert ended["needs"] is None, ended
    assert health.status_code == 200
    assert [hit["signal"] for hit in found["hits"]] == ["traces"]
    assert stats["sent"] == 1 and stats["failed"] == 0
    assert all(there.keys.read(name) for name in (ROOT_KEY, AGENT_KEY))
    settings = tomllib.loads((there.layout.home / "settings.toml").read_text(encoding="utf-8"))
    assert settings["telemetry"] == {"send_to": "this-pc"}
    assert ended["lines"][-1] == (
        f"deep logs: agents read them at http://127.0.0.1:5080/api/default/mcp with the key "
        f"{AGENT_KEY}"
    )
    assert not [p for p in pid if psutil.pid_exists(p)], "no OpenObserve is left after the stop"


def test_openobserve_binds_the_loopback_with_its_telemetry_off_and_his_sizes(
    tmp_path: Path,
) -> None:
    there, process = deep(tmp_path)
    there.keys.replace(ROOT_KEY, "planted-root")
    control = there.control
    assert control is not None
    before = process.environment()
    control.settings_put(cast("Any", "telemetry"), {"openobserve": {"cache_gb": 2, "keep_days": 7}})
    after = process.environment()

    assert {k: v for k, v in before.items() if k not in ("ZO_DATA_DIR", "ZO_HTTP_PORT")} == {
        "ZO_ROOT_USER_EMAIL": "qmx@this-pc.invalid",
        "ZO_ROOT_USER_PASSWORD": "planted-root",
        "ZO_LOCAL_MODE": "true",
        "ZO_HTTP_ADDR": "127.0.0.1",
        "ZO_GRPC_ADDR": "127.0.0.1",
        "ZO_TELEMETRY": "false",
        "ZO_DISK_CACHE_MAX_SIZE": "1024",
        "ZO_COMPACT_DATA_RETENTION_DAYS": "30",
    }
    assert Path(before["ZO_DATA_DIR"]) == there.layout.cache / "openobserve" / "data"
    assert (after["ZO_DISK_CACHE_MAX_SIZE"], after["ZO_COMPACT_DATA_RETENTION_DAYS"]) == (
        "2048",
        "7",
    )


def test_a_program_that_needs_administrator_rights_ends_at_one_approval_card(
    tmp_path: Path,
) -> None:
    there, process = deep(tmp_path, deny=True)
    ended = connect(there)

    assert ended["step"] == "start"
    assert ended["needs"]["card"] == "approval"
    assert ended["needs"]["line"] == (
        "deep logs: OpenObserve would not start as you on this PC (it ended with code 5 and said "
        "access is denied), and QMX does not give it administrator rights; answering here will "
        "not either. To keep deep logs on this PC, close QMX, start it again as administrator "
        "and connect deep logs again. Or connect deep logs on your server instead. Nothing is "
        "left running"
    )
    assert not [p for p in children(process) if psutil.pid_exists(p)]
    settings = tomllib.loads((there.layout.home / "settings.toml").read_text(encoding="utf-8"))
    assert "send_to" not in settings.get("telemetry", {}), "no sender posts to a dead address"


def test_a_host_back_after_a_crash_stops_the_openobserve_qmx_started_and_no_other(
    tmp_path: Path,
) -> None:
    there, crashed = deep(tmp_path)
    there.keys.replace(ROOT_KEY, "planted-root")
    crashed.start()
    left = children(crashed)
    again = OpenObserveProcess(
        there.layout, there.keys, crashed.settings, port=crashed.port, program=crashed.program
    )
    adopted = again.start()
    again.stop()
    stranger, _url = served(b"")
    other = OpenObserveProcess(
        there.layout, there.keys, crashed.settings, port=int(stranger.server_address[1])
    )
    try:
        with pytest.raises(Stopped) as refused:
            other.start()
    finally:
        stranger.shutdown()

    assert adopted == f"OpenObserve answers on http://127.0.0.1:{crashed.port}"
    assert left and not psutil.pid_exists(left[0])
    assert not again.healthy()
    assert refused.value.line == (
        f"another program answers on http://127.0.0.1:{stranger.server_address[1]}, where QMX "
        "runs OpenObserve; stop it, then connect deep logs again"
    )


def test_a_start_that_lands_after_the_host_stopped_starts_nothing(tmp_path: Path) -> None:
    there, process = deep(tmp_path)
    there.keys.replace(ROOT_KEY, "planted-root")
    process.close()
    with pytest.raises(Stopped) as refused:
        process.start()

    assert refused.value.line == "the host is stopping, so OpenObserve was not started"
    assert children(process) == []
    assert not process.healthy()


class Release(http.server.BaseHTTPRequestHandler):
    body = b""

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)


def served(body: bytes) -> tuple[http.server.HTTPServer, str]:
    Release.body = body
    server = http.server.HTTPServer(("127.0.0.1", 0), Release)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/openobserve.zip"


@pytest.mark.parametrize("pin", ["right", "wrong", "none"])
def test_the_pinned_release_is_fetched_checked_and_unpacked_only_when_its_sha256_matches(
    tmp_path: Path, pin: str
) -> None:
    there, process = deep(tmp_path)
    process.program = "no-such-openobserve-on-path"
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as zipped:
        zipped.writestr("openobserve.exe", b"the stand-in program")
    archive = packed.getvalue()
    server, url = served(archive)
    sha256 = {
        "right": hashlib.sha256(archive).hexdigest(),
        "wrong": "0" * 64,
        "none": None,
    }[pin]
    release = Pinned("v1.1.2", "open source", url, len(archive), sha256, "openobserve.exe")
    pinned = dataclasses.replace(there, logs=Logs(process, release=release))
    step = next(s for s in KINDS["deep-logs-pc"].steps if s.name == "openobserve")
    line = ""
    try:
        step.do(Run(KINDS["deep-logs-pc"], PLACE, {}, pinned))
    except Stopped as stopped:
        line = stopped.line
    finally:
        server.shutdown()
    folder = there.layout.cache / "openobserve"
    if pin == "right":
        assert (folder / "openobserve.exe").read_bytes() == b"the stand-in program"
        assert sorted(p.name for p in folder.iterdir()) == ["openobserve.exe"]
        return
    assert not (folder / "openobserve.exe").exists()
    assert list(folder.iterdir()) == [] if folder.exists() else True
    assert (
        line
        == {
            "wrong": "the OpenObserve v1.1.2 QMX fetched is not the one pinned (its checksum "
            "differs), so it was deleted and not run; try again later",
            "none": "the pinned OpenObserve v1.1.2 has no published checksum recorded yet, so QMX "
            "will not run a download it cannot check; put openobserve on PATH, then connect deep "
            "logs again",
        }[pin]
    )


def test_deep_logs_on_a_server_send_the_shipped_units_and_point_send_to_at_it(
    tmp_path: Path,
) -> None:
    server = Server()
    there = at(tmp_path, server)
    through_the_cards(there)
    ended = connect(there, "deep-logs-server")
    sent = [s for s in server.scripts() if "otelcol.yaml" in s]
    settings = tomllib.loads((there.layout.home / "settings.toml").read_text(encoding="utf-8"))

    assert ended["needs"] is None
    assert sent == [monitoring_script()]
    assert "[Unit]\nDescription=OpenObserve" in sent[0]
    assert "storage: file_storage" in sent[0] and "QMX_OTEL_QUEUE" in sent[0]
    assert 'password="$(openssl rand -base64 24)"' in sent[0], "the server makes its own"
    assert settings["telemetry"] == {"send_to": PLACE}
    assert qma.telemetry.headers(there.layout.home, there.keys.read) == {}, (
        "no key leaves this PC for a server's collector"
    )
    assert ADDRESS in json.dumps(settings["engine"]["placement"][PLACE])


def test_deep_logs_on_a_server_need_the_server_first(tmp_path: Path) -> None:
    there = at(tmp_path, Server())
    with pytest.raises(Stopped) as stopped:
        connect(there, "deep-logs-server")
    assert stopped.value.line == (
        f"{PLACE}: connect {PLACE} as your server first, then its deep logs"
    )


def test_a_host_stopped_with_deep_logs_on_leaves_no_openobserve(tmp_path: Path) -> None:
    there, process = deep(tmp_path)
    there.keys.replace(ROOT_KEY, "planted-root")
    began = time.perf_counter()
    line = process.start()
    took = time.perf_counter() - began
    pid = children(process)
    process.stop()
    process.stop()

    assert line.startswith(f"OpenObserve answers on http://127.0.0.1:{process.port} after ")
    assert took < 30
    assert pid and not psutil.pid_exists(pid[0])
    assert not process.healthy()
