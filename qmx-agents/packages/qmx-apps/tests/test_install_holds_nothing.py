"""Nothing one app does holds up a call to another. His kill goes through `call`, so it must never
wait on a build or on a road another holder has, and a build that hangs ends by name."""

from __future__ import annotations

import importlib
import shutil
import sqlite3
import stat
import sys
import threading
import time
from collections.abc import Callable, Generator
from contextlib import closing
from pathlib import Path
from typing import Any

import psutil
import pytest
from qmx_control.service import ControlService

from qmx_apps.errors import AppError
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import VolumeLease

road_history = importlib.import_module("qmx_apps.road.history")
EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
RUNNER = "runner"
OTHER = "other"
ANSWER_SECONDS = 1.0
"""The promise under test: a call answers within this while another app is busy."""
HELD_SECONDS = 4.0
"""How long the other app stays busy, so a call that waits for it shows past the promise."""


def this_interpreter(_self: Supervisor, _definition_hash: str) -> Path:
    return Path(sys.executable)


def no_build(_self: Supervisor, _definition: Definition, _image: Path) -> None:
    pass


def source(root: Path, app_id: str, *, job: bool = False) -> Path:
    folder = root / app_id
    shutil.copytree(EXAMPLE, folder, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), folder / "server.py")
    manifest = folder / "app.toml"
    text = manifest.read_text().replace('id = "exchange-status"', f'id = "{app_id}"')
    if job:
        text = text.replace('mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]')
        (folder / "job.py").write_text('def run(inputs):\n    return {"worked": True}\n')
    manifest.write_text(text)
    return folder


@pytest.fixture
def owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Supervisor]:
    monkeypatch.setattr(Supervisor, "python", this_interpreter)
    monkeypatch.setattr(Supervisor, "_install_environment", no_build)
    supervisor = Supervisor(tmp_path / "QMX" / "data", secret_getter=lambda _s, _u: "fixture")
    try:
        yield supervisor
    finally:
        supervisor.close()


def in_thread(work: Callable[[], Any]) -> tuple[threading.Thread, list[Exception]]:
    failed: list[Exception] = []

    def run() -> None:
        try:
            work()
        except Exception as error:
            failed.append(error)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, failed


def timed_ping(owner: Supervisor) -> tuple[object, float]:
    began = time.monotonic()
    answer = owner.call(RUNNER, "ping", {})["result"]
    return answer, time.monotonic() - began


def test_a_call_answers_within_a_second_while_another_app_installs(
    owner: Supervisor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner.install(source(tmp_path, RUNNER), trust="first_party")
    owner.start(RUNNER)
    building, finish = threading.Event(), threading.Event()

    def build(_self: Supervisor, _definition: Definition, _image: Path) -> None:
        building.set()
        finish.wait(HELD_SECONDS)

    monkeypatch.setattr(Supervisor, "_install_environment", build)
    thread, failed = in_thread(lambda: owner.install(source(tmp_path, OTHER), trust="first_party"))
    assert building.wait(10)

    answer, seconds = timed_ping(owner)
    finish.set()
    thread.join(30)

    assert answer == {"pong": True}
    assert seconds < ANSWER_SECONDS
    assert failed == []
    assert owner.status(OTHER)["status"] == "stopped"


@pytest.mark.parametrize("step", ["start", "install"])
def test_a_call_answers_within_a_second_while_another_app_waits_for_its_road(
    owner: Supervisor, tmp_path: Path, step: str
) -> None:
    owner.install(source(tmp_path, RUNNER), trust="first_party")
    owner.start(RUNNER)
    folder = source(tmp_path, OTHER)
    owner.install(folder, trust="first_party")
    held = VolumeLease(owner.home / "road-locks", OTHER)
    threading.Timer(HELD_SECONDS, held.close).start()
    work = {
        "start": lambda: owner.start(OTHER),
        "install": lambda: owner.install(folder, trust="first_party"),
    }[step]
    thread, failed = in_thread(work)
    time.sleep(0.5)

    answer, seconds = timed_ping(owner)
    status_began = time.monotonic()
    owner.status(RUNNER)
    status_seconds = time.monotonic() - status_began
    thread.join(30)

    assert answer == {"pong": True}
    assert seconds < ANSWER_SECONDS
    assert status_seconds < ANSWER_SECONDS
    assert failed == []
    assert owner.status(OTHER)["status"] == {"start": "running", "install": "stopped"}[step]


def test_an_app_cannot_start_during_its_own_build(
    owner: Supervisor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = source(tmp_path, OTHER)
    owner.install(folder, trust="first_party")
    building, finish = threading.Event(), threading.Event()

    def build(_self: Supervisor, _definition: Definition, _image: Path) -> None:
        building.set()
        finish.wait(HELD_SECONDS)

    monkeypatch.setattr(Supervisor, "_install_environment", build)
    thread, failed = in_thread(lambda: owner.install(folder, trust="first_party"))
    assert building.wait(10)

    with pytest.raises(AppError) as refused:
        owner.start(OTHER)
    still_building = thread.is_alive()
    finish.set()
    thread.join(30)

    assert refused.value.code == "volume_busy"
    assert still_building
    assert failed == []


def test_a_start_that_waited_for_the_road_refuses_a_volume_moved_meanwhile(
    owner: Supervisor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner.install(source(tmp_path, OTHER), trust="first_party")
    owner.start(OTHER)
    owner.stop(OTHER)
    with closing(sqlite3.connect(owner.home / "apps" / OTHER / "app.db")) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS moved (id TEXT)")
    monkeypatch.setattr(road_history, "ROAD_POLL_S", HELD_SECONDS)
    held = VolumeLease(owner.home / "road-locks", OTHER)
    answered: list[object] = []

    def start() -> None:
        try:
            answered.append(owner.start(OTHER)["status"])
        except AppError as refused:
            answered.append(refused.code)

    waiting = threading.Thread(target=start, daemon=True)
    waiting.start()
    time.sleep(0.5)
    held.close()

    owner.snapshot_instance(OTHER, to="contabo")
    moved_during_the_wait = waiting.is_alive()
    waiting.join(30)

    assert moved_during_the_wait
    assert answered == ["not_home"]
    assert owner.status(OTHER)["status"] == "stopped"


TREE = """\
import os, subprocess, sys, time
from pathlib import Path

marks = Path(sys.argv[1])
if len(sys.argv) > 2:
    (marks / "grandchild.pid").write_text(str(os.getpid()))
    time.sleep(20)
    raise SystemExit(0)
(marks / "child.pid").write_text(str(os.getpid()))
subprocess.Popen([sys.executable, __file__, str(marks), "grandchild"])
print("uv is resolving", flush=True)
time.sleep(20)
"""
"""A uv that never ends: it leaves a grandchild holding its output, then sits."""


def fake_uv(root: Path, body: str) -> Path:
    """A real executable the supervisor finds as `uv`, running `body` with a marks folder."""
    script = root / "tree.py"
    script.write_text(body)
    marks = root / "marks"
    marks.mkdir()
    if sys.platform == "win32":
        program = root / "uv.cmd"
        program.write_text(f'@"{sys.executable}" "{script}" "{marks}"\n')
    else:
        program = root / "uv"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "{marks}"\n')
        program.chmod(program.stat().st_mode | stat.S_IEXEC)
    return program


def finding_uv_at(program: Path) -> Callable[[str], str | None]:
    found = shutil.which

    def which(name: str) -> str | None:
        return str(program) if name == "uv" else found(name)

    return which


def test_a_stuck_install_fails_by_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    program = fake_uv(tmp_path, TREE)
    monkeypatch.setattr(shutil, "which", finding_uv_at(program))
    home = tmp_path / "QMX" / "data"
    home.mkdir(parents=True)
    (home / "settings.toml").write_text("[apps]\ninstall_limit_s = 3\n")
    control = ControlService(home, secret_getter=lambda _s, _u: "fixture")
    try:
        began = time.monotonic()
        with pytest.raises(AppError) as stuck:
            control.app_runtime().install(source(tmp_path, OTHER), trust="first_party")
        seconds = time.monotonic() - began
    finally:
        control.close()

    log = tmp_path / "QMX" / "logs" / f"install-{OTHER}.log"
    message = str(stuck.value)
    assert stuck.value.code == "install_stuck"
    assert OTHER in message
    assert "3 s" in message
    assert str(log) in message
    assert seconds < 6
    assert log.read_text("utf-8").strip() == "uv is resolving"
    pids = [
        int((tmp_path / "marks" / name).read_text()) for name in ("child.pid", "grandchild.pid")
    ]
    deadline = time.monotonic() + 2
    while any(psutil.pid_exists(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert [psutil.pid_exists(pid) for pid in pids] == [False, False]


def test_a_failed_install_quotes_uv_from_its_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    said = 'print("Resolved 3 packages")\nprint("error: the lock is stale")\nraise SystemExit(1)\n'
    monkeypatch.setattr(shutil, "which", finding_uv_at(fake_uv(tmp_path, said)))
    supervisor = Supervisor(tmp_path / "QMX" / "data", secret_getter=lambda _s, _u: "fixture")
    try:
        with pytest.raises(AppError) as failed:
            supervisor.install(source(tmp_path, OTHER), trust="first_party")
    finally:
        supervisor.close()

    assert failed.value.code == "install_failed"
    assert str(failed.value) == (
        "uv could not install the app's lock; check its lock and sources. "
        "uv said: error: the lock is stale"
    )


def test_a_job_answer_being_replaced_is_read_again(
    owner: Supervisor, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner.install(source(tmp_path, RUNNER, job=True), trust="first_party")
    owner.start(RUNNER)
    shipped = Path.read_text
    refused: list[str] = []

    def read(path: Path, *args: Any, **kwargs: Any) -> str:
        if path.name.endswith(".done.json") and len(refused) < 2:
            refused.append(path.name)
            raise PermissionError(13, "The process cannot access the file", str(path))
        return shipped(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)

    ran = owner.run_job(RUNNER, "job.py")

    assert ran["result"] == {"worked": True}
    assert len(refused) == 2
    assert list((owner.home / "apps" / RUNNER / "data/jobs").glob("*.done.json")) == []
