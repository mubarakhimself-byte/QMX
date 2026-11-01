"""Layer G as QMB code: the dummy's report names no fault, each twin's names its own (B5b).

The twins are QML's corpus documents (``qml/tests/corpus``); each breaks the dummy one way.
The child-process test runs ``python -m qmb.host.behaviour`` the way QMB's job does, so the
safety half passes only there.
"""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmb.host.behaviour import BehaviourCheck, check_behaviour
from qmf.core.refusal import TypedRefusal, is_refusal
from test_unit_runner import CORPUS, make_run_folder, request


def _check(folder: Path, *, margin: Decimal = Decimal("0.20")) -> BehaviourCheck:
    checked = check_behaviour(folder, request(folder), margin=margin, loaded_in_isolation=False)
    assert not isinstance(checked, TypedRefusal), checked
    return checked.value


@pytest.mark.parametrize(
    ("twin", "fault"),
    [
        ("twin-one-side-only", "one_side_only"),
        ("twin-exits-unfired", "exits_unfired"),
        ("twin-signal-constant", "signal_constant"),
    ],
)
def test_each_twin_report_names_its_fault(tmp_path: Path, twin: str, fault: str) -> None:
    document = json.loads((CORPUS / f"{twin}.json").read_text("utf-8"))

    check = _check(make_run_folder(tmp_path, document))

    assert fault in check.faults


def test_the_dummy_report_names_no_fault_and_counts_its_trades(tmp_path: Path) -> None:
    check = _check(make_run_folder(tmp_path))

    assert check.faults == ()
    assert {k: check.report[k] for k in ("trades", "entries_long", "entries_short")} == {
        "trades": 8,
        "entries_long": 2,
        "entries_short": 6,
    }
    assert check.report["slice_bars_needed"] == 1106


def test_in_the_same_process_the_safety_half_fails_on_isolation(tmp_path: Path) -> None:
    check = _check(make_run_folder(tmp_path))

    assert not check.safety_passed
    assert check.report["safety"] == {"verdict": "fail", "failed_check": "logic_loads_in_isolation"}


def test_a_slice_shorter_than_the_warm_up_and_its_margin_is_refused(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)

    refused = check_behaviour(
        folder, request(folder), margin=Decimal("1.10"), loaded_in_isolation=False
    )

    assert is_refusal(refused)
    assert refused.context["field"] == "slice"
    assert "1935 bars" in str(refused.context["reason"])


def test_the_sandbox_child_states_isolation_and_the_safety_half_passes(tmp_path: Path) -> None:
    folder = make_run_folder(tmp_path)
    body = {
        "run_id": "run-b5b",
        "compiled_fingerprint": request(folder).compiled_fingerprint,
        "equity": "10000.00",
        "execution_target": {"role": "demo", "venue_id": "icmarkets-ctrader", "account_id": "a"},
    }
    job = {"run_folder": str(folder), "request": body, "margin": "0.20"}

    done = subprocess.run(
        [sys.executable, "-B", "-m", "qmb.host.behaviour"],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
        check=True,
    )

    answer = cast("dict[str, object]", json.loads(done.stdout))
    report = cast("dict[str, object]", answer["report"])
    safety = cast("dict[str, object]", report["safety"])
    assert safety["verdict"] == "pass"
    assert report["warnings"] == []
