"""AD-33 change 3: a tripped app that opts in starts again by itself, with back-off.

The waits are recorded, never slept, so the 5 s to 300 s schedule is checked in milliseconds.
"""

from __future__ import annotations

import importlib
import secrets
import shutil
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import cast

import psutil
import pytest

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Breaker
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Stage
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import VolumeLease

road_history = importlib.import_module("qmx_apps.road.history")
EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "exchange-status"
SETTLE_SECONDS = 2.0
"""Test bound: how long a test waits for the supervisor to act on a trip."""


class Waits:
    """The supervisor's back-off wait, recorded and returned at once."""

    def __init__(self) -> None:
        self.seconds: list[float] = []

    def __call__(self, seconds: float, cancel: threading.Event) -> bool:
        self.seconds.append(seconds)
        return cancel.is_set()


@pytest.fixture
def waits() -> Waits:
    return Waits()


@pytest.fixture
def supervisor(tmp_path: Path, waits: Waits) -> Generator[Supervisor]:
    owner = Supervisor(tmp_path / "home", restart_wait=waits)
    try:
        yield owner
    finally:
        owner.close()


def source(
    tmp_path: Path, *, breaker: str = "", version: str = "1.0.0", risk: str = "shows"
) -> Path:
    target = tmp_path / f"source-{version}"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), target / "server.py")
    manifest = target / "app.toml"
    text = (
        manifest.read_text()
        .replace('version = "1.0.0"', f'version = "{version}"')
        .replace('risk = "shows"', f'risk = "{risk}"')
    )
    manifest.write_text(text + (f"\n[breaker]\n{breaker}\n" if breaker else ""))
    return target


def until(check: Callable[[], bool], what: str) -> None:
    deadline = time.monotonic() + 60
    while not check():
        assert time.monotonic() < deadline, what
        time.sleep(0.05)


def events(owner: Supervisor) -> list[str]:
    return [str(entry["event"]) for entry in owner.logs(APP, limit=1000)]


def trip(owner: Supervisor) -> int:
    """Kill the running app's process, as a crash would, and wait for the breaker to open."""
    pid = cast(int, owner.status(APP)["pid"])
    psutil.Process(pid).kill()
    until(lambda: not psutil.pid_exists(pid), "the killed process lingered")
    return pid


def running_again(owner: Supervisor, old_pid: int) -> int:
    def fresh() -> bool:
        status = owner.status(APP)
        return status["status"] == "running" and status["pid"] not in {None, old_pid}

    until(fresh, "the app did not start again")
    return cast(int, owner.status(APP)["pid"])


def test_the_wait_starts_at_five_seconds_and_doubles_to_three_hundred() -> None:
    breaker = Breaker.model_validate({"restart": "backoff"})
    assert [breaker.backoff(trip) for trip in range(1, 10)] == [
        5,
        10,
        20,
        40,
        80,
        160,
        300,
        300,
        300,
    ]
    assert breaker.backoff(10_000) == 300
    assert Breaker().restart == "never"


def test_an_opted_in_app_starts_again_after_five_then_ten_seconds(
    supervisor: Supervisor, waits: Waits, tmp_path: Path
) -> None:
    supervisor.install(source(tmp_path, breaker='restart = "backoff"'), trust="first_party")
    supervisor.start(APP)
    running_again(supervisor, trip(supervisor))
    assert waits.seconds == [5]
    running_again(supervisor, trip(supervisor))
    assert waits.seconds == [5, 10]
    logged = [
        event
        for event in events(supervisor)
        if event in {"started", "breaker_open", "restart_scheduled", "restarted"}
    ]
    assert logged == [
        "started",
        "breaker_open",
        "restart_scheduled",
        "started",
        "restarted",
        "breaker_open",
        "restart_scheduled",
        "started",
        "restarted",
    ]


def test_a_stop_cancels_the_pending_restart(tmp_path: Path) -> None:
    held = threading.Event()

    def wait(seconds: float, cancel: threading.Event) -> bool:
        held.set()
        return cancel.wait(30)

    owner = Supervisor(tmp_path / "home", restart_wait=wait)
    try:
        owner.install(source(tmp_path, breaker='restart = "backoff"'), trust="first_party")
        owner.start(APP)
        trip(owner)
        until(held.is_set, "no restart was scheduled")
        assert owner.stop(APP)["status"] == "tripped"
        time.sleep(SETTLE_SECONDS)
        assert owner.status(APP)["status"] == "tripped"
        assert "restarted" not in events(owner)
    finally:
        owner.close()


def test_an_app_that_sets_no_restart_stays_down(
    supervisor: Supervisor, waits: Waits, tmp_path: Path
) -> None:
    supervisor.install(source(tmp_path), trust="first_party")
    supervisor.start(APP)
    trip(supervisor)
    time.sleep(SETTLE_SECONDS)
    status = supervisor.status(APP)
    assert (status["status"], status["pid"]) == ("tripped", None)
    assert waits.seconds == []
    assert "restart_scheduled" not in events(supervisor)


def proved(owner: Supervisor, definition_hash: str, version: str) -> None:
    with history(owner.home, APP) as state:
        for stage in ("tests", "sandbox", "shadow"):
            state.append(
                Evidence(
                    definition_hash=definition_hash,
                    version=version,
                    stage=cast(Stage, stage),
                    passed=True,
                    inputs={"fixture": True},
                    versions={"definition": definition_hash},
                    results={"passed": True},
                    duration_seconds=0.1,
                )
            )


def test_a_money_app_restarts_only_its_active_signed_version(
    supervisor: Supervisor, waits: Waits, tmp_path: Path
) -> None:
    breaker = 'restart = "backoff"'
    signed = supervisor.install(
        source(tmp_path, breaker=breaker, risk="money"), trust="first_party"
    )
    signed_hash = str(signed["definition_hash"])
    proved(supervisor, signed_hash, "1.0.0")
    supervisor.road.signing_key(secrets.token_urlsafe(32))
    signature = supervisor.road.sign(APP, signed_hash, None)
    supervisor.road.publish(APP, signed_hash, signature=signature)
    supervisor.stop(APP)
    newer = supervisor.install(
        source(tmp_path, breaker=breaker, risk="money", version="1.1.0"),
        trust="first_party",
        expected_hash=signed_hash,
    )
    assert supervisor.get(APP)["definition_hash"] == newer["definition_hash"] != signed_hash
    supervisor.start(APP)
    running_again(supervisor, trip(supervisor))
    status = supervisor.status(APP)
    assert (status["definition_hash"], status["version"]) == (signed_hash, "1.0.0")
    assert waits.seconds == [5]


def test_a_calm_crash_waits_five_seconds_again(
    supervisor: Supervisor, waits: Waits, tmp_path: Path
) -> None:
    calm_after = 2.0
    breaker = f'restart = "backoff"\nbackoff_seconds = 1\nbackoff_max_seconds = {calm_after}'
    supervisor.install(source(tmp_path, breaker=breaker), trust="first_party")
    supervisor.start(APP)

    pid = running_again(supervisor, trip(supervisor))
    time.sleep(calm_after + 0.5)
    running_again(supervisor, trip(supervisor))

    assert pid is not None
    assert waits.seconds == [1, 1]


async def stuck_loop(seconds: float) -> None:
    time.sleep(seconds)


def test_a_tool_timeout_on_an_opted_in_app_heals(
    supervisor: Supervisor, waits: Waits, tmp_path: Path
) -> None:
    supervisor.install(source(tmp_path, breaker='restart = "backoff"'), trust="first_party")
    supervisor.start(APP)
    old = cast(int, supervisor.status(APP)["pid"])
    supervisor._submit(stuck_loop(31))  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(AppError) as timed_out:
        supervisor.call(APP, "ping", {})

    assert (timed_out.value.code, timed_out.value.status) == ("tool_timeout", 504)
    assert running_again(supervisor, old) != old
    assert waits.seconds == [5]
    assert "breaker_open" in events(supervisor)
    assert not psutil.pid_exists(old)


def test_a_crash_while_the_road_is_held_restarts_once_the_road_is_free(
    supervisor: Supervisor, waits: Waits, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor.install(source(tmp_path, breaker='restart = "backoff"'), trust="first_party")
    supervisor.start(APP)
    monkeypatch.setattr(road_history, "ROAD_WAIT_S", 0.2)
    held = VolumeLease(supervisor.home / "road-locks", APP)
    try:
        old = trip(supervisor)
        until(lambda: "restart_failed" in events(supervisor), "no failed restart was logged")
    finally:
        held.close()

    running_again(supervisor, old)

    assert waits.seconds[:2] == [5, 10]
    assert "restart_refused" not in events(supervisor)


def test_an_error_in_the_restart_loop_does_not_end_it(
    supervisor: Supervisor, waits: Waits, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor.install(source(tmp_path, breaker='restart = "backoff"'), trust="first_party")
    supervisor.start(APP)
    shipped = supervisor._log  # pyright: ignore[reportPrivateUsage]
    failed: list[str] = []

    def log(app_id: str, event: str, data: Document) -> None:
        if event == "restart_scheduled" and not failed:
            failed.append(event)
            raise OSError(28, "No space left on device")
        shipped(app_id, event, data)

    monkeypatch.setattr(supervisor, "_log", log)

    running_again(supervisor, trip(supervisor))

    assert failed == ["restart_scheduled"]
    assert supervisor.status(APP)["status"] == "running"
