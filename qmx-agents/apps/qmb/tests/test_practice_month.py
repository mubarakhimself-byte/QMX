"""A first backtest from nothing (RC-17, slice 5).

`practice_start` fills an empty market store with the shipped March 2025 month under source
`practice`, and lands the shipped instrument records on `main`. Then the canary compiles, QMB
runs it over that month, and the layer G report a paper click needs exists for its compiled
fingerprint. No broker, no CSV folder, no Library item placed by hand.
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_control.service import ControlService, WorkflowEngine
from qmx_engine.ledger import redact
from qmx_host.host import LanderLibrary, landers  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.practice_start import practice_start  # pyright: ignore[reportMissingTypeStubs]
from qmx_library.principal import Principal
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

APP = Path(__file__).resolve().parents[1]
OPERATOR = Principal("operator")
CHAT = "agent:chat-17"
MARCH: dict[str, Any] = {"start": "2025-03-01", "end": "2025-04-01"}
ASKED: dict[str, Any] = {"window": MARCH, "allow_gaps": True, "source": "practice"}
"""The shipped month has a 4-bar Sunday-open hole each week, one more than `gap_bars_refuse`, and
its bars are read from the market store's `practice` source."""


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
    def principal(self) -> Caller:
        return Caller(CHAT)

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        return []


@dataclass
class World:
    control: ControlService
    store: Store
    tools: dict[str, Any]


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    root = tmp_path_factory.mktemp("practice")
    control = ControlService(root / "home")
    control.attach_workflow_engine(cast(WorkflowEngine, Chat()))
    with Store.open(root / "library", redactor=redact, wall=Clock()) as store:
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        runtime.install(APP, trust="first_party")
        runtime.start("qmb")
        context = DomainContext(root=root / "tools")
        context.control, context.library = control, control.library
        try:
            yield World(control, store, domain_functions(context))
        finally:
            control.close()


def test_a_backtest_finds_bars_from_an_empty_store(world: World) -> None:
    started = practice_start(world.control.home, world.store)
    unit = world.tools["unit"]

    made = unit["unit_new"]("canary", {})
    checked = unit["unit_check"](document=made["document"], item=made["item"])
    answer = world.tools["backtest"]["backtest_run"](unit=made["object_id"], **ASKED)["result"]
    library = LanderLibrary(world.store)
    compiled = library.compiled_fingerprint(made["object_id"])
    record = None if compiled is None else library.g_record(compiled, ("fx.eurusd", "metal.xauusd"))
    landed = dict(world.store.get(OPERATOR, answer["result_id"]).fields)

    assert (started.source, started.months) == ("practice", ("2025-03",))
    assert [(one.kind, one.outcome) for one in started.instruments] == [
        ("instrument", "landed"),
        ("instrument", "landed"),
    ]
    assert (checked["verdict"], checked["counts"]["errors"]) == ("pass", 0)
    assert answer["status"] == "finished"
    assert cast("dict[str, Any]", landed["labels"])["datasets"] == [
        "practice/EURUSD/bar-m1/bid",
        "practice/EURUSD/bar-m1/ask",
        "practice/XAUUSD/bar-m1/bid",
        "practice/XAUUSD/bar-m1/ask",
    ]
    assert record is not None and record.safety_passed
