"""What every QMB job shares: its run folder, the request the core wrote there, and its leave.

The core lays a run out before the job starts (Part B AD-202): ``in/request.json`` is the run
request with the core's fields filled, and ``in/`` holds the unit, its pinned blocks, its
markets' instrument records and bars. A job writes only under ``out/`` and leaves one
``qmx.qmb.result-bundle/1`` under ``provides.backtest-result``. A domain failure is a ``failed``
bundle, never a raise, because the breaker counts every raise (AD-201, AD-204).
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

from qmf.core import fingerprint_bytes
from qmf.core.refusal import TypedRefusal

if TYPE_CHECKING:
    from qmb.data.gap_check import ShortEnds
    from qmb.execution.financing import CashEvent
    from qmb.host.unit_handler import UnitTrade
    from qmb.host.unit_runner import UnitRunResult

OUTPUT: Final = "backtest-result"
CONTRACT: Final = "qmb/1"
MANIFEST: Final = cast(
    "dict[str, object]", tomllib.loads((Path(__file__).with_name("app.toml")).read_text("utf-8"))
)
TESTER: Final[dict[str, str]] = {
    "app": str(MANIFEST["id"]),
    "version": str(MANIFEST["version"]),
    "contract": CONTRACT,
}
_R_PLACES: Final = Decimal("0.0001")

type Document = dict[str, object]


def folder(inputs: Mapping[str, object]) -> Path:
    """The run's folder, as the supervisor names it inside the app's volume."""
    return Path(str(inputs["run_folder"]))


def request(run: Path) -> Document | str:
    """The run request the core wrote, or why there is none."""
    try:
        found: object = json.loads((run / "in" / "request.json").read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return f"the run folder holds no run request the core wrote: {error}"
    return cast("Document", found) if isinstance(found, dict) else "the run request is an object"


def unit_body(asked: Mapping[str, object], run_id: str) -> Document:
    """The fields QMB's unit runner reads, from the core's run request."""
    return {
        "run_id": run_id,
        "compiled_fingerprint": asked.get("compiled_fp"),
        "equity": asked.get("equity"),
        "execution_target": asked.get("execution_target"),
        "motion": asked.get("motion", "on"),
        "allow_gaps": asked.get("allow_gaps", False),
        "gap_bars_refuse": asked.get("gap_bars_refuse"),
        "calibrated_min_fills": asked.get("calibrated_min_fills"),
    }


def data_short(short: Iterable[ShortEnds]) -> list[dict[str, object]]:
    """A run's `data_short` label: each market whose bars stop short of its window."""
    return [
        {
            "market_id": ends.market_id,
            "before_first": ends.before_first,
            "after_last": ends.after_last,
        }
        for ends in short
    ]


def cash_of_trades(result: UnitRunResult) -> list[tuple[CashEvent, ...]]:
    """Each trade's cash events, in the trades' order. An event goes to the first trade of its
    position closing at or after it, so partial closes count a position's cash once."""
    waiting: dict[str, list[CashEvent]] = {}
    for event in result.cash_events:
        waiting.setdefault(event.position_id, []).append(event)
    found: list[tuple[CashEvent, ...]] = []
    for trade in result.trades:
        left = waiting.get(trade.trade_id, [])
        due = [e for e in left if e.instant.value_ns <= trade.closed_at.value_ns]
        waiting[trade.trade_id] = left[len(due) :]
        found.append(tuple(due))
    return found


def _trade_row(trade: UnitTrade, cash: Decimal) -> Document:
    net_r = (trade.money + cash) / trade.risk if trade.risk else Decimal(0)
    row: Document = {
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
        "mae_r": str(trade.mae_r),
        "mfe_r": str(trade.mfe_r),
        "cash": str(cash),
        "net_r": str(net_r.quantize(_R_PLACES, rounding=ROUND_HALF_EVEN)),
    }
    if trade.gap_through_stop:
        row["gap_through_stop"] = True
    return row


def trade_rows(result: UnitRunResult) -> list[Document]:
    """A run's trades as a report lists them, each with its cash."""
    return [
        _trade_row(trade, sum((event.money for event in events), Decimal(0)))
        for trade, events in zip(result.trades, cash_of_trades(result), strict=True)
    ]


def reason(refusal: TypedRefusal) -> str:
    context = refusal.context
    text = str(context.get("reason", refusal.category.value))
    field = context.get("field")
    return f"{field}: {text}" if field else text


def json_bytes(body: object) -> bytes:
    """The one serial form of a bundle file, so a rerun's file has the same fingerprint."""
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def write(run: Path, name: str, body: object) -> Document:
    """One bundle file under ``out/``, named by its slot's path and its fingerprint."""
    data = json_bytes(body)
    path = run / "out" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "slot": "report",
        "path": f"out/{name}",
        "fp": fingerprint_bytes(data).value,
        "bytes": len(data),
    }


def leave(
    run_id: str,
    status: str,
    *,
    why: str | None = None,
    measures: Mapping[str, object] | None = None,
    labels: Mapping[str, object] | None = None,
    files: Sequence[Mapping[str, object]] = (),
    versions: Mapping[str, object] | None = None,
) -> Document:
    bundle: Document = {
        "schema_version": 1,
        "run_id": run_id,
        "status": status,
        "tester": dict(TESTER),
        "files": [dict(file) for file in files],
    }
    optional = {"reason": why, "measures": measures, "labels": labels, "versions": versions}
    bundle.update(
        {
            name: dict(value) if isinstance(value, Mapping) else value
            for name, value in optional.items()
            if value is not None
        }
    )
    return {"output": OUTPUT, "data": bundle}


def failed(run_id: str, why: str) -> Document:
    """A domain failure: the run lands as failed with its reason, and nothing raised."""
    return leave(run_id, "failed", why=why)
