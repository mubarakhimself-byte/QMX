"""A second tester for the conformance tests: QMB's shared runner with one change.

A trade's money is cut down to the cent (`ROUND_DOWN`) where the shipped tester rounds half to
even. Everything else is QMB's own library, so the rows differ only where that rounding moves a
trade's money and the R computed from it. The variant also claims a pass about itself in its
labels, which the core must never read.
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import cast

from qmb.host import unit_handler
from qmb.host.unit_runner import UnitRunResult, load_unit_folder, parse_unit_run_request, run_loaded
from qmf.core import fingerprint_bytes
from qmf.core.refusal import is_refusal
from qml.numbers import InstrumentRecord
from qml.unit.model import Side

MANIFEST = cast(
    "dict[str, object]", tomllib.loads(Path(__file__).with_name("app.toml").read_text())
)
TESTER = {"app": str(MANIFEST["id"]), "version": str(MANIFEST["version"]), "contract": "qmb/1"}
CENT = Decimal("0.01")


def _money_cut_down(
    side: Side, entry: Decimal, exit_: Decimal, quantity: Decimal, record: InstrumentRecord
) -> Decimal:
    move = exit_ - entry if side is Side.LONG else entry - exit_
    return (move * quantity * record.value_per_point).quantize(CENT, rounding=ROUND_DOWN)


unit_handler._money = _money_cut_down  # pyright: ignore[reportPrivateUsage]


def rows(result: UnitRunResult) -> dict[str, object]:
    """The raw lists, in the shape the shipped tester leaves them."""
    return {
        "trades": [
            {
                "trade_id": t.trade_id,
                "market_id": t.market_id,
                "side": t.side.value,
                "opened_at": t.opened_at.value_ns,
                "closed_at": t.closed_at.value_ns,
                "entry_price": str(t.entry_price),
                "exit_price": str(t.exit_price),
                "stop": str(t.stop),
                "quantity": str(t.quantity),
                "exit_kind": t.exit_kind.value,
                "money": str(t.money),
                "r": str(t.r),
            }
            for t in result.trades
        ],
        "fills": [
            {
                "instant": f.instant.value_ns,
                "market_id": f.market_id,
                "position_id": f.position_id,
                "kind": f.kind.value,
                "side": f.side.value,
                "price": str(f.price),
                "quantity": str(f.quantity),
                "receipt_quantity": None if f.receipt_quantity is None else str(f.receipt_quantity),
                "residue_r": str(f.residue_r),
            }
            for f in result.fills
        ],
        "cash_events": [
            {
                "instant": c.instant.value_ns,
                "market_id": c.market_id,
                "kind": c.kind.value,
                "money": str(c.money),
                "detail": c.detail,
            }
            for c in result.cash_events
        ],
        "holes": [
            {
                "market_id": h.market_id,
                "after": h.after_ns,
                "before": h.before_ns,
                "bars_missing": h.bars_missing,
            }
            for h in result.holes
        ],
    }


def replay(run: Path, run_id: str) -> dict[str, object] | str:
    """Trade the folder's `in/` as the shipped tester does, or say why it could not."""
    asked = json.loads((run / "in" / "request.json").read_text("utf-8"))
    loaded = load_unit_folder(run / "in")
    if is_refusal(loaded):
        return str(loaded.context.get("reason"))
    body = {
        "run_id": run_id,
        "compiled_fingerprint": asked.get("compiled_fp"),
        "equity": asked.get("equity"),
        "execution_target": asked.get("execution_target"),
        "motion": asked.get("motion", "on"),
        "allow_gaps": asked.get("allow_gaps", False),
        "gap_bars_refuse": asked.get("gap_bars_refuse"),
        "calibrated_min_fills": asked.get("calibrated_min_fills"),
    }
    parsed = parse_unit_run_request(body)
    if is_refusal(parsed):
        return str(parsed.context.get("reason"))
    ran = run_loaded(loaded.value, parsed.value)
    if is_refusal(ran):
        return str(ran.context.get("reason"))
    return rows(ran.value)


def leave(run: Path, run_id: str, report: Mapping[str, object] | None, why: str = "") -> object:
    """The job's `qmx.qmb.result-bundle/1`, with a self-claimed pass the core ignores."""
    if report is None:
        bundle: dict[str, object] = {"run_id": run_id, "status": "failed", "reason": why}
    else:
        data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
        (run / "out").mkdir(parents=True, exist_ok=True)
        (run / "out" / "report.json").write_bytes(data)
        bundle = {
            "run_id": run_id,
            "status": "finished",
            "files": [
                {
                    "slot": "report",
                    "path": "out/report.json",
                    "fp": fingerprint_bytes(data).value,
                    "bytes": len(data),
                }
            ],
            "labels": {"conformance": "pass", "fidelity": "bars"},
        }
    return {"output": "backtest-result", "data": {"schema_version": 1, "tester": TESTER, **bundle}}
