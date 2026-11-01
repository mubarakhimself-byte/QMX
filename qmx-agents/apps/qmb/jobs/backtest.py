"""The `backtest` run kind: trade the run folder's compiled unit over its bars (Part B AD-205).

QMB's unit runner compiles the unit from its pinned blocks, refuses a compiled fingerprint other
than the one the run pins, and trades every bar through the shared unit handler. The bundle
carries each trade in money and R, each fill against its sizer receipt, and the measures.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import qmb_tester as tester
from qmb.host.unit_handler import Fill, UnitTrade
from qmb.host.unit_runner import UnitRunResult, parse_unit_run_request, run_unit
from qmf.core import fingerprint_bytes
from qmf.core.refusal import is_refusal


def _trade(trade: UnitTrade) -> dict[str, object]:
    return {
        "trade_id": trade.trade_id,
        "market_id": trade.market_id,
        "side": trade.side.value,
        "opened_at": trade.opened_at.value_ns,
        "closed_at": trade.closed_at.value_ns,
        "entry_price": str(trade.entry_price),
        "exit_price": str(trade.exit_price),
        "stop": str(trade.stop),
        "quantity": str(trade.quantity),
        "exit_kind": trade.exit_kind.value,
        "money": str(trade.money),
        "r": str(trade.r),
    }


def _fill(fill: Fill) -> dict[str, object]:
    return {
        "instant": fill.instant.value_ns,
        "market_id": fill.market_id,
        "position_id": fill.position_id,
        "kind": fill.kind.value,
        "side": fill.side.value,
        "price": str(fill.price),
        "quantity": str(fill.quantity),
        "receipt_quantity": None if fill.receipt_quantity is None else str(fill.receipt_quantity),
        "residue_r": str(fill.residue_r),
    }


def measures(result: UnitRunResult, trades: list[dict[str, object]]) -> dict[str, object]:
    """Money and R side by side; every amount is exact decimal text."""
    count = len(result.trades)
    wins = sum(1 for trade in result.trades if trade.r > 0)
    listed = tester.json_bytes(trades)
    return {
        "trades": count,
        "net_money": str(result.net_money),
        "total_r": str(result.total_r),
        "expectancy_r": str(result.total_r / count) if count else "0",
        "win_rate": str(Decimal(wins) / count) if count else "0",
        "trade_list_fp": fingerprint_bytes(listed).value,
    }


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    parsed = parse_unit_run_request(tester.unit_body(asked, run_id))
    if is_refusal(parsed):
        return tester.failed(run_id, tester.reason(parsed))
    ran = run_unit(folder / "in", parsed.value)
    if is_refusal(ran):
        return tester.failed(run_id, tester.reason(ran))
    result = ran.value
    trades = [_trade(trade) for trade in result.trades]
    report = {
        "run_id": run_id,
        "compiled_fp": result.compiled_fingerprint,
        "trades": trades,
        "fills": [_fill(fill) for fill in result.fills],
        "open_positions": sorted(result.open_positions),
    }
    return tester.leave(
        run_id,
        "finished",
        measures=measures(result, trades),
        labels={"zero_trades": not result.trades, "fidelity": "bars", "motion": asked.get("motion", "on")},
        files=[tester.write(folder, "report.json", report)],
        versions={"qmb": tester.TESTER["version"]},
    )
