"""C-09: the shipped MIS app under a real supervisor, beside QMB, on the two fixture markets.

The MIS is this folder, installed with its own locked environment into a throwaway home whose
market store holds the fixture months. The test writes the host facts into the MIS's volume as
the host does. QMB is the shipped app folder, trading the dummy unit on QML's synthetic March
2025 month, as its own suite does, so a unit's run can be compared with the MIS running and
stopped (Level 0 AD-2: a unit stands alone).
"""

from __future__ import annotations

import hashlib
import shutil
import threading
import time
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from mis_fixtures import BLOCKS, configure_both, pin, records, write_facts, write_markets
from qmx_apps.errors import Document
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume
from qmx_control.service import ControlService, WorkflowEngine
from qmx_engine.ledger import redact
from qmx_host.first_start import land_dummy  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.host import landers  # pyright: ignore[reportMissingTypeStubs]
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

APP = Path(__file__).resolve().parents[1]
QMB = APP.parent / "qmb"
SLICES = APP.parents[2] / "qml" / "tests" / "fixtures" / "slices"
MARCH: dict[str, Any] = {"window": {"start": "2025-03-01", "end": "2025-04-01"}, "allow_gaps": True}
SLOW_ROUNDS: Document = {"settings": {"round_s": 86_400}}
"""Test bound: rounds only when the test asks, so every count below is the test's own."""


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


@dataclass(frozen=True)
class Caller:
    principal: str


class Chat:
    """The engine door as the host attaches it, naming one chat as the caller."""

    def principal(self) -> Caller:
        return Caller("agent:chat-c09")

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        return []


@dataclass
class World:
    runtime: Supervisor
    volume: Path
    market: Path
    dummy: str
    backtest: Mapping[str, Callable[..., dict[str, Any]]]

    def mis(self, operation: str, arguments: Mapping[str, object]) -> dict[str, Any]:
        asked = cast(Document, dict(arguments))
        answer = cast(dict[str, Any], self.runtime.call("mis", operation, asked)["result"])
        assert answer["ok"] is True, answer
        return cast(dict[str, Any], answer["value"])


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("mis")
    bars = root / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    control = ControlService(root / "home")
    control.settings_put("qmb", {"bars": str(bars)})
    control.attach_workflow_engine(cast(WorkflowEngine, Chat()))
    with Store.open(root / "library", redactor=redact, wall=Clock()) as store:
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        write_markets(runtime.home / "market")
        for folder in (QMB, APP):
            runtime.install(folder, trust="first_party")
        runtime.start("qmb")
        runtime.start("mis")
        volume = Volume(runtime.home, "mis").root
        write_facts(volume, {"on": False})
        dummy = land_dummy(store)
        assert dummy is not None
        context = DomainContext(root=root / "tools")
        context.control, context.library = control, control.library
        try:
            yield World(
                runtime,
                volume,
                runtime.home / "market",
                dummy,
                domain_functions(context)["backtest"],
            )
        finally:
            control.close()


def digest(folder: Path) -> dict[str, str]:
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def until[T](check: Callable[[], T | None], reason: str) -> T:
    """Poll `check` until it answers, so a round on its own thread is never waited for by a sleep
    that guesses how long it takes."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        found = check()
        if found is not None:
            return found
        time.sleep(0.25)
    raise AssertionError(f"within 60 s, {reason}")


def test_configured_on_two_markets_it_publishes_each_allowed_reading_from_the_market_root(
    world: World,
) -> None:
    store_before = digest(world.market)

    configured = world.mis("configure", configure_both(**SLOW_ROUNDS))
    done = world.mis("round", {})
    status = world.mis("status", {})
    board = world.mis("board", {})

    assert configured == {"configured": 2, "refused": []}
    assert sorted((str(row["market_id"]), str(row["reading"])) for row in done["published"]) == [
        *(("eurusd", block) for block in sorted(BLOCKS)),
        *(("gold", block) for block in sorted([*BLOCKS, "spread_state@v1"])),
    ]
    assert sorted((str(body["market_id"]), pin(body)) for body in records(world.volume)) == sorted(
        (str(row["market_id"]), str(row["reading"])) for row in done["published"]
    )
    assert (status["state"], status["holdout"], status["machine"]) == (
        "configured",
        {"on": False},
        "this-pc",
    )
    assert [tier["tier"] for tier in board["boards"]] == ["tick", "bar", "session", "day"]
    assert board["boards"][3]["markets"] == [
        {
            "market_id": "eurusd",
            "states": {"variance-ratio": "random", "hurst-exponent": "random"},
            "freshness": {"variance-ratio": "stale", "hurst-exponent": "stale"},
        },
        {
            "market_id": "gold",
            "states": {"variance-ratio": "random", "hurst-exponent": "random"},
            "freshness": {"variance-ratio": "stale", "hurst-exponent": "stale"},
        },
    ]
    assert (world.volume / "data" / "board.json").is_file()
    assert digest(world.market) == store_before


def test_stopping_the_mis_changes_no_unit(world: World) -> None:
    world.mis("configure", configure_both(**SLOW_ROUNDS))
    world.mis("round", {})
    with_mis = world.backtest["backtest_run"](unit=world.dummy, **MARCH)["result"]

    stopped = world.runtime.stop("mis")
    without_mis = world.backtest["backtest_run"](unit=world.dummy, **MARCH)["result"]
    world.runtime.start("mis")

    compared = world.backtest["backtest_compare"](
        left=with_mis["result_id"], right=without_mis["result_id"]
    )
    assert stopped["status"] == "stopped"
    assert (with_mis["status"], without_mis["status"]) == ("finished", "finished")
    assert (compared["same_trades"], compared["measures"]) == (True, {})


def test_a_read_error_in_a_round_leaves_the_thread_alive(world: World) -> None:
    month = world.market / "series" / "fixture" / "EURUSD" / "bar-m1" / "bid" / "2025-03"
    open_month = month / "open.parquet"
    saved = open_month.read_bytes()
    open_month.unlink()
    try:
        world.mis("configure", configure_both(op_id="c09-read-error", settings={"round_s": 1}))
        error = until(
            lambda: world.mis("status", {}).get("last_error"),
            "the read error reached status",
        )
    finally:
        open_month.write_bytes(saved)

    def eurusd_published() -> dict[str, str] | None:
        markets = cast(list[dict[str, Any]], world.mis("status", {})["markets"])
        rows: dict[str, dict[str, str]] = {
            str(row["market_id"]): row["readings"] for row in markets
        }
        readings = rows.get("eurusd") or {}
        fresh = readings and all(health == "fresh" for health in readings.values())
        return readings if fresh else None

    readings = until(eurusd_published, "the next round published EURUSD's readings")
    status = world.mis("status", {})

    assert str(error).startswith("FileNotFoundError:")
    assert sorted(readings) == [
        "cusum-change-point@1",
        "efficiency-ratio@1",
        "hurst-exponent@1",
        "variance-ratio@1",
    ]
    assert status["last_error"] == error
