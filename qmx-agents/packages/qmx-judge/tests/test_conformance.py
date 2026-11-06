"""The core proves a tester with its conformance pack, and only a proven tester becomes default.

Both testers are real apps in a real supervisor over a real Library store, composed as the host
composes them: the shipped QMB (`apps/qmb`) and `fixtures/variant-tester`, QMB's runner with a
trade's money cut down to the cent. The core runs the pack on each through the job path and
judges the raw rows each one left. The bars are QML's synthetic March 2025 month, so every
literal below holds on every machine.

`python packages/qmx-judge/tests/test_conformance.py` is the pack's regeneration script. It lays
the dummy's run out through the host, runs the shipped tester on the pack and writes
`fixture.json` and `golden.json` from that run. Only a PR that changes QML, the checker or QMB
runs it.
"""

from __future__ import annotations

import importlib.metadata
import json
import re
import shutil
import subprocess
import tempfile
import threading
import tomllib
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from qmx_apps.errors import Document
from qmx_apps.supervisor import RUNS, Supervisor
from qmx_apps.volume import Volume
from qmx_control.models import LibraryInput
from qmx_control.service import ControlError, ControlService
from qmx_engine.ledger import redact
from qmx_host.first_start import land_dummy  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.host import LanderLibrary, landers  # pyright: ignore[reportMissingTypeStubs]
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN, Principal, agent_ref
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

from qmx_judge.conformance import (
    CHECK,
    OUTPUT,
    ConformanceRun,
    judge_output,
    load_pack,
    run_conformance,
    write_golden,
)

HERE = Path(__file__).resolve().parent
VARIANT = HERE / "fixtures" / "variant-tester"
REPO = HERE.parents[3]
QMB = REPO / "qmx-agents" / "apps" / "qmb"
QMB_VERSION: str = tomllib.loads((QMB / "app.toml").read_text("utf-8"))["version"]
"""The shipped QMB's version, which moves with each repair to its folder."""
SLICES = REPO / "qml" / "tests" / "fixtures" / "slices"
PACK_DIR = REPO / "qmx-agents" / "packages" / "qmx-judge" / "src" / "qmx_judge" / "conformance_pack"
OPERATOR = Principal("operator")
MARCH: dict[str, Any] = {"start": "2025-03-01", "end": "2025-04-01"}
TRADES_FP = "fp1:sha256:f1f83b30c09bd87ab9ae502b22bb69b3197ab5fd47945bffa8ef481941ebf995"
"""The dummy's golden trade list on the pack, made by the shipped tester (golden.json)."""


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


class Library(LanderLibrary):
    """The host's lander port with the one read a conformance run adds: a landed object's
    fields and its report blob."""

    def read(self, object_id: str) -> tuple[Mapping[str, object], bytes | None]:
        view = self.store.get(OPERATOR, object_id)
        blob = view.blobs.get("report")
        return dict(view.fields), None if blob is None else self.store.read_blob(blob.blob_id)


@dataclass
class World:
    control: ControlService
    store: Store
    runtime: Supervisor
    library: Library
    dummy: str
    backtest: Mapping[str, Any]

    def conformance(self, app_id: str, version: str | None = None) -> ConformanceRun:
        asked = version or (QMB_VERSION if app_id == "qmb" else "1.0.0")

        def run_job(
            app: str, job: str, inputs: Mapping[str, object], principal: str
        ) -> Mapping[str, object]:
            return self.runtime.run_job(
                app, job, inputs=cast("Document", dict(inputs)), principal=principal
            )

        return run_conformance(
            app_id, asked, run_job=run_job, library=self.library, principal="operator"
        )

    def landed(self, item: str, trades: list[dict[str, Any]]) -> str:
        """A finished backtest result on `main`, as the lander leaves one."""
        draft = Draft(
            "backtest-result",
            item,
            item,
            fields={"run_id": item, "status": "finished"},
            blobs={"report": json.dumps({"trades": trades}).encode()},
        )
        return self.store.put(OPERATOR, draft, on=MAIN, expected_head=None).object_id

    def fields(self, object_id: str) -> dict[str, Any]:
        return dict(self.store.get(OPERATOR, object_id).fields)


@contextmanager
def world_at(root: Path) -> Generator[World]:
    bars = root / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    control = ControlService(root / "home")
    control.settings_put("qmb", {"bars": str(bars)})
    with Store.open(root / "library", redactor=redact, wall=Clock()) as store:
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        for app in (QMB, VARIANT):
            runtime.install(app, trust="first_party")
        runtime.start("qmb")
        runtime.start("qmb-cents-down")
        dummy = land_dummy(store)
        assert dummy is not None
        context = DomainContext(root=root / "tools")
        context.control, context.library = control, control.library
        try:
            yield World(
                control,
                store,
                runtime,
                Library(store),
                dummy,
                domain_functions(context)["backtest"],
            )
        finally:
            control.close()


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Generator[World]:
    with world_at(tmp_path_factory.mktemp("conformance")) as found:
        yield found


def test_the_shipped_tester_passes_its_pack(world: World) -> None:
    pack = load_pack()

    ran = world.conformance("qmb")

    report = world.fields(ran.report_id)
    assert (report["check"], report["tester_pin"], report["verdict"]) == (
        CHECK,
        f"qmb@{QMB_VERSION}",
        "pass",
    )
    assert report["says"] == "passed all 2 cases"
    assert report["pack"] == {"id": "dummy-synthetic-2025-03", "fp": pack.fp}
    assert [case["fps"]["trades"] for case in report["cases"]] == [TRADES_FP, TRADES_FP]
    assert [case["fps"] for case in report["cases"]] == [dict(c.golden_fp) for c in pack.cases]
    assert [len(case.golden["trades"]) for case in pack.cases] == [8, 8]
    result = world.fields(ran.result_id)
    assert (result["kind"], result["status"], result["tester"]) == (
        "conformance",
        "finished",
        {"app": "qmb", "version": QMB_VERSION},
    )
    assert "measures" not in result


def test_a_variant_that_rounds_differently_fails_with_its_first_differing_trade(
    world: World,
) -> None:
    ran = world.conformance("qmb-cents-down")

    report = world.fields(ran.report_id)
    first = report["cases"][0]
    assert (report["verdict"], first["verdict"]) == ("fail", "fail")
    assert first["diff"]["says"] == "trades[6].money is -48.36, golden -48.37"
    assert first["diff"]["got_row"] == {
        "market_id": "metal.xauusd",
        "side": "long",
        "opened_at": "1742966100000000000",
        "closed_at": "1742983200000000000",
        "entry_price": "3245.944",
        "exit_price": "3240.57",
        "stop": "3240.57",
        "quantity": "0.09",
        "exit_kind": "stop",
        "money": "-48.36",
        "r": "-1.0000",
    }
    assert world.fields(ran.result_id)["labels"]["conformance"] == "pass"


def test_the_default_tester_moves_only_to_a_tester_that_passed(world: World) -> None:
    world.conformance("qmb-cents-down")

    with pytest.raises(ControlError) as refused:
        world.control.settings_put("qmb", {"default_tester": "qmb-cents-down@1.0.0"})
    with pytest.raises(ControlError) as never_run:
        world.control.settings_put("qmb", {"default_tester": "qmb-lean@2.0.0"})
    world.conformance("qmb")
    world.control.settings_put("qmb", {"default_tester": "qmb@1.0.0"})

    assert (refused.value.code, refused.value.status) == ("default_tester_unproven", 409)
    assert str(refused.value) == (
        "[qmb] default_tester stays: qmb-cents-down@1.0.0 failed its conformance check: "
        "failed motion-on: trades[6].money is -48.36, golden -48.37"
    )
    assert str(never_run.value) == (
        "[qmb] default_tester stays: qmb-lean@2.0.0 has no conformance report on the pack "
        "dummy-synthetic-2025-03; run the pack on it first"
    )
    assert world.control.settings_get("qmb")["default_tester"] == "qmb@1.0.0"


def test_two_results_of_one_request_compare_trade_by_trade(world: World) -> None:
    asked = {"unit": world.dummy, "window": MARCH, "allow_gaps": True}
    left = world.runtime.run_job(
        "qmb", "jobs/backtest.py", inputs=dict(asked), principal="operator"
    )
    right = world.runtime.run_job(
        "qmb-cents-down", "jobs/backtest.py", inputs=dict(asked), principal="operator"
    )

    compared = world.backtest["backtest_compare"](
        left=world.library.find(str(left["run_id"])),
        right=world.library.find(str(right["run_id"])),
    )

    assert compared["testers"] == [
        {"app": "qmb", "version": QMB_VERSION},
        {"app": "qmb-cents-down", "version": "1.0.0"},
    ]
    assert (compared["statuses"], compared["same_request"]) == (["finished", "finished"], True)
    assert compared["same_trades"] is False
    assert compared["result"] == [
        {
            "market_id": "metal.xauusd",
            "opened_at": 1742966100000000000,
            "order": 0,
            "differs": {"money": ["-48.37", "-48.36"]},
        },
        {
            "market_id": "metal.xauusd",
            "opened_at": 1743092100000000000,
            "order": 0,
            "differs": {"money": ["95.38", "95.37"], "r": ["2.0013", "2.0010"]},
        },
    ]


def test_a_row_from_before_the_added_fields_compares_on_what_both_rows_hold(world: World) -> None:
    older = {"market_id": "fx.eurusd", "opened_at": "1740787200000000000", "money": "1.00"}
    newer = {**older, "mae_r": "0.20", "mfe_r": "0.80", "cash": "-1.00", "net_r": "0.40"}
    before = world.landed("row-before", [older])
    after = world.landed("row-after", [newer])
    charged = world.landed("row-charged", [{**newer, "cash": "-2.00"}])

    across = world.backtest["backtest_compare"](left=before, right=after)
    within = world.backtest["backtest_compare"](left=after, right=charged)

    assert (across["same_trades"], across["result"]) == (True, [])
    assert within["result"] == [
        {
            "market_id": "fx.eurusd",
            "opened_at": 1740787200000000000,
            "order": 0,
            "differs": {"cash": ["-1.00", "-2.00"]},
        },
    ]


def test_trades_at_one_market_and_instant_pair_in_order_and_a_malformed_time_is_refused(
    world: World,
) -> None:
    twin = {"market_id": "fx.eurusd", "opened_at": "1740787200000000000", "money": "1.00"}
    left = world.landed("pair-left", [twin, {**twin, "money": "2.00"}])
    right = world.landed("pair-right", [twin, {**twin, "money": "2.50"}])
    malformed = world.landed("pair-malformed", [{**twin, "opened_at": "soon"}])

    compared = world.backtest["backtest_compare"](left=left, right=right)
    with pytest.raises(ValueError, match="opens at") as refused:
        world.backtest["backtest_compare"](left=left, right=malformed)

    assert compared["result"] == [
        {
            "market_id": "fx.eurusd",
            "opened_at": 1740787200000000000,
            "order": 1,
            "differs": {"money": ["2.00", "2.50"]},
        }
    ]
    assert str(refused.value) == (
        f"{malformed}: trade 0 opens at 'soon', not a whole number of nanoseconds"
    )


def test_a_run_of_another_version_than_asked_lands_no_report_and_moves_no_default(
    world: World,
) -> None:
    with pytest.raises(ValueError, match=rf"ran qmb@{re.escape(QMB_VERSION)}") as refused:
        world.conformance("qmb", "9.9.9")
    with pytest.raises(ControlError) as stays:
        world.control.settings_put("qmb", {"default_tester": "qmb@9.9.9"})

    run_id = str(refused.value).split()[3]
    assert str(refused.value) == (
        f"the conformance run {run_id} ran qmb@{QMB_VERSION}, not qmb@9.9.9"
    )
    assert world.library.find(f"conformance/{run_id}") is None
    assert world.store.with_field("test-report", "tester_pin", "qmb@9.9.9") == []
    assert str(stays.value) == (
        "[qmb] default_tester stays: qmb@9.9.9 has no conformance report on the pack "
        "dummy-synthetic-2025-03; run the pack on it first"
    )


def test_a_passing_report_the_core_did_not_land_proves_nothing(world: World) -> None:
    real = world.conformance("qmb")
    forged: JsonObject = {
        **world.fields(real.report_id),
        "tester": {"app": "qmb", "version": "9.9.9"},
        "tester_pin": "qmb@9.9.9",
    }
    agent = Principal("agent", "s1")

    def saved() -> None:
        world.control.library_save(
            LibraryInput(title="Conformance of qmb@9.9.9: pass", kind="test-report", content=forged)
        )

    def by_agent() -> None:
        on = agent_ref("s1", "forged")
        draft = Draft("test-report", "forged", "f", fields=forged)
        world.store.put(agent, draft, on=on, expected_head=None)
        world.store.merge(agent, "forged", from_ref=on, into=MAIN, strategy="ff-only")

    def over_another_testers_result() -> None:
        draft = Draft("test-report", "forged-core", "f", fields=forged)
        world.store.put(OPERATOR, draft, on=MAIN, expected_head=None)

    says: list[str] = []
    for place in (saved, by_agent, over_another_testers_result):
        place()
        with pytest.raises(ControlError) as stays:
            world.control.settings_put("qmb", {"default_tester": "qmb@9.9.9"})
        says.append(str(stays.value))

    assert says == 3 * [
        "[qmb] default_tester stays: qmb@9.9.9 has no conformance report on the pack "
        "dummy-synthetic-2025-03; run the pack on it first"
    ]
    assert len(world.store.with_field("test-report", "tester_pin", "qmb@9.9.9")) == 2


def test_nothing_a_tester_says_about_itself_counts() -> None:
    pack = load_pack()
    golden = pack.cases[0]
    claimed: dict[str, object] = {
        "schema_version": OUTPUT,
        "cases": {
            golden.case: {
                "status": "finished",
                "fps": dict(golden.golden_fp),
                "verdict": "pass",
                **{name: [dict(row) for row in rows] for name, rows in golden.golden.items()},
            }
        },
    }
    case = cast("dict[str, Any]", claimed["cases"])[golden.case]
    case["trades"][0]["money"] = 1.5

    verdict = judge_output(pack, claimed)

    assert [(c.case, c.passed) for c in verdict.cases] == [
        ("motion-on", False),
        ("motion-off", False),
    ]
    assert verdict.cases[0].reason == "trades[0].money is text or a whole number, never 1.5"
    assert verdict.cases[1].reason == "the tester left no output for motion-off"


def regenerate() -> None:
    """Remake the fixture from the host's own run layout, then the goldens from the shipped
    tester's run of the pack."""
    git = shutil.which("git")
    assert git is not None, "the regeneration names the head it ran at"
    head = subprocess.run(
        [git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=REPO
    ).stdout.strip()
    with (
        tempfile.TemporaryDirectory(prefix="b12-pack-") as scratch,
        world_at(Path(scratch)) as world,
    ):
        ran = world.runtime.run_job(
            "qmb",
            "jobs/backtest.py",
            inputs={"unit": world.dummy, "window": MARCH},
            principal="operator",
        )
        data = str(world.runtime.status("qmb").get("data") or "data")
        laid = Volume(world.runtime.home, "qmb").root / data / RUNS / str(ran["run_id"]) / "in"
        request = json.loads((laid / "request.json").read_text("utf-8"))
        fixture = {
            path.relative_to(laid).as_posix(): path.read_bytes().decode("utf-8")
            for path in sorted(laid.rglob("*"))
            if path.is_file() and path.name != "request.json"
        }
        manifest = json.loads((PACK_DIR / "pack.json").read_text("utf-8"))
        for case in manifest["cases"]:
            case["request"]["compiled_fp"] = request["compiled_fp"]
        (PACK_DIR / "pack.json").write_text(json.dumps(manifest, indent=1) + "\n", "utf-8")
        (PACK_DIR / "fixture.json").write_text(json.dumps(fixture, sort_keys=True), "utf-8")
        (PACK_DIR / "golden.json").unlink(missing_ok=True)
        made = world.conformance("qmb")
        _, report = world.library.read(made.result_id)
        assert report is not None
        write_golden(
            PACK_DIR,
            json.loads(report),
            {
                "made_by": (
                    "the shipped tester qmb@1.0.0 (qmx-agents/apps/qmb), through the core's "
                    "conformance job path, by tests/test_conformance.py's regenerate()"
                ),
                "made_at_head": head,
                "versions": {
                    name: importlib.metadata.version(name) for name in ("qml", "qmb", "qmx-judge")
                },
                "realism": (
                    "B10's rules in force: gap fills, lot rounding with residue, carry as cash "
                    "events, holes counted (this pack allows gaps and lists them)"
                ),
                "data": "QML's synthetic March 2025 month, labelled not evidence",
                "cost_profile": "none (costs_uncalibrated)",
            },
        )


if __name__ == "__main__":
    regenerate()
