"""Exact risk, settlement and uncertainty invariants of the D010 conformance path."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from qmf.core.refusal import is_ok
from qmn.host import run_runtime_risk_gate
from test_qmn_runtime_risk_gate import fixture_runtime_risk_inputs


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping), value
    return cast("Mapping[str, object]", value)


def test_gate_keeps_entry_risk_faces_and_close_economics_source_bound() -> None:
    result = run_runtime_risk_gate(fixture_runtime_risk_inputs())
    assert is_ok(result), result
    evidence = result.value.evidence_records
    entry = _mapping(evidence["entry_preservation"])
    authorized = _mapping(entry["authorized_intent"])
    admitted = _mapping(authorized["admitted"])
    target = _mapping(admitted["execution_target"])
    faces = _mapping(authorized["faces"])
    original_risk = _mapping(faces["original_risk_amount"])
    frozen = _mapping(entry["frozen_r"])
    frozen_amount = _mapping(frozen["original_risk_amount"])
    exit_record = _mapping(entry["exit_record"])
    realized = _mapping(exit_record["realized_pnl"])
    costs = cast("list[object]", exit_record["cost_components"])

    assert entry["rebased"] is False
    assert target == {
        "class": "execution-target",
        "role": "live",
        "venue_id": "ctrader",
        "account_id": "acct-1",
        "format_version": 1,
    }
    assert original_risk["currency"] == "USD"
    assert original_risk["num"] == 1_000
    assert original_risk["den"] == 1
    assert frozen_amount == original_risk
    assert admitted["requested_r"] == admitted["proposed_r"]
    assert realized["currency"] == "USD"
    assert (realized["num"], realized["den"]) == (-100, 1)
    assert len(costs) == 1
    commission = _mapping(costs[0])
    commission_amount = _mapping(commission["amount"])
    assert commission["name"] == "commission"
    assert commission["source"] == "broker"
    assert (commission_amount["currency"], commission_amount["num"]) == ("USD", 2)
    assert exit_record["opening_bot_id"] == "bot-a"
    assert exit_record["close_reason"] == "protective_stop_fill"


def test_reconciliation_distinguishes_zero_residual_drift_and_unknown() -> None:
    result = run_runtime_risk_gate(fixture_runtime_risk_inputs())
    assert is_ok(result), result
    reconciliations = _mapping(result.value.evidence_records["four_verdict_reconciliation"])
    reconciled = _mapping(reconciliations["reconciled"])
    drift = _mapping(reconciliations["drift"])
    unknown = _mapping(reconciliations["unknown"])
    reconciled_cash = _mapping(reconciled["cash_residual"])
    drift_cash = _mapping(drift["cash_residual"])
    drift_cash_residual = _mapping(drift_cash["residual"])
    drift_quantities = cast("tuple[object, ...]", drift["quantity_residuals"])
    quantity = _mapping(drift_quantities[0])
    quantity_residual = _mapping(quantity["residual"])

    assert reconciled["verdict"] == "reconciled"
    assert reconciled_cash["is_zero"] is True
    assert drift["verdict"] == "drift"
    assert drift["operator_review"] is True
    assert quantity["is_zero"] is False
    assert (quantity_residual["num"], quantity_residual["den"]) == (1, 2)
    assert drift_cash["is_zero"] is True
    assert (drift_cash_residual["num"], drift_cash_residual["den"]) == (0, 1)
    assert unknown["verdict"] == "unknown"
    assert unknown["quantity_residuals"] == ()
    assert "arithmetic does not run" in cast("str", unknown["detail"])

    out_of_lookback = _mapping(reconciliations["out_of_lookback"])
    assert out_of_lookback["verdict"] == "out-of-lookback"
    assert out_of_lookback["quantity_residuals"] == ()


def test_same_tick_control_composition_keeps_both_required_actions() -> None:
    result = run_runtime_risk_gate(fixture_runtime_risk_inputs())
    assert is_ok(result), result
    conflict = _mapping(result.value.evidence_records["priority_compose_conflict"])
    assert set(cast("list[str]", conflict["emit"])) == {"suspend_new", "flatten"}
    assert conflict["suppressed"] == 0
    assert conflict["arrival_order_ignored"] is True
