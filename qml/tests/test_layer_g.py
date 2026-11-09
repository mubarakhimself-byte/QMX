"""Layer G over a hosted unit: the unchanged ``evaluate_layer2`` and the behaviour report (A6)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qmf.core.refusal import is_refusal
from qml.check.layer_g import LayerG, layer_g
from qml.compile import CompiledUnit, compile_unit
from qml.conformance.layer2 import evaluate_layer2
from test_compile_dummy import _context, _document, _slice, _target

_CORPUS = Path(__file__).resolve().parents[1] / "tests" / "corpus"


def _g(document: dict[str, object], *, isolated: bool = True) -> LayerG:
    context = _context()
    compiled = compile_unit(document, context)
    assert isinstance(compiled, CompiledUnit), compiled
    return layer_g(
        compiled,
        context.sources,
        _slice(),
        execution_target=_target(),
        equity=Decimal("10000.00"),
        loaded_in_isolation=isolated,
    )


def test_the_dummy_passes_the_safety_half_and_fires_every_exit() -> None:
    g = _g(_document())

    assert not is_refusal(evaluate_layer2(g.observations))
    assert g.observations.restore_equivalent
    assert g.observations.state_bound_holds
    assert {k: g.report[k] for k in ("trades", "entries_long", "entries_short")} == {
        "trades": 8,
        "entries_long": 2,
        "entries_short": 6,
    }
    assert g.report["exits_fired"] == {"swing_stop": 5, "target_2r": 1, "time_out": 2}
    assert g.report["shuffled_day_control"] == {"decisions_equal_to_real": False, "trades": 84}
    safety = cast("dict[str, object]", g.report["safety"])
    assert safety["verdict"] == "pass"
    assert str(safety["layer2_verdict_fingerprint"]).startswith("fp1:sha256:")
    assert g.warnings == ()


@pytest.mark.parametrize(
    ("twin", "named"),
    [
        ("twin-one-side-only", "one_side_only"),
        ("twin-exits-unfired", "exits_unfired"),
        ("twin-signal-constant", "signal_constant"),
    ],
)
def test_each_twin_passes_evaluate_layer2_and_its_report_names_it(twin: str, named: str) -> None:
    g = _g(json.loads((_CORPUS / f"{twin}.json").read_text("utf-8")))

    assert not is_refusal(evaluate_layer2(g.observations))
    assert named in {p.kind.value for p in g.warnings}
    assert all(p.layer == "G" for p in g.warnings)


def test_the_exits_unfired_twin_names_its_target() -> None:
    g = _g(json.loads((_CORPUS / "twin-exits-unfired.json").read_text("utf-8")))

    assert g.report["exits_unfired"] == ["target_2r"]
    assert [(p.kind.value, p.where) for p in g.warnings] == [("exits_unfired", ("/exit_set/1",))]


def test_the_host_states_isolation_and_evaluate_layer2_refuses_without_it() -> None:
    g = _g(_document(), isolated=False)

    verdict = evaluate_layer2(g.observations)

    assert is_refusal(verdict)
    assert g.report["safety"] == {"verdict": "fail", "failed_check": "logic_loads_in_isolation"}
