"""The `backtest` run kind: trade the run folder's compiled unit over its bars (Part B AD-205).

QMB's unit runner compiles the unit from its pinned blocks, refuses a compiled fingerprint other
than the one the run pins, and trades every bar through the shared unit handler. The bundle
carries each trade in money and R, each fill against its sizer receipt, the measures, and the
run's unit journal as `journal/<kind>/<YYYY-MM>` files (B9). A request with `motion = both` runs
the unit twice, motion on and motion off, and reports both: the off run's trades and measures
under `motion_off`, its journal under `journal/motion_off/`.

The report lists the run's cash events (swap, financing, funding, dividends, commission) and the
holes it ran over with `allow_gaps`; `net_money` holds the trades' money and the cash. Each trade
row adds, beside its `r`, how far the price went against it and for it (`mae_r`, `mfe_r`), its
`cash`, and `net_r`, its money and cash over its risk. `r` itself stays price money over risk, and
the measures add `max_drawdown_r` and `money`, the contract's money measures. The labels
say `costs_uncalibrated` until a market's costs come from enough real fills, and
`holes_unchecked` while a market's calendar is not one QMB reads (B10), `fixture_records` lists
each market with no Library record that ran on a test fixture, `placeholders` the unit's placeholder
blocks, `cost_profile` the profile a run was told to pay, and `data_short` each market whose bars
stop short of the window, with the open bars missing at each end. A hole past the request's
`gap_bars_refuse` lands a `failed` result naming it, so does a short end on a calendar that holds
closures from before the window, and so does a block that raises, with its type and message.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path
from typing import Final

from qmb.data.gap_check import HOLES_UNCHECKED
from qmb.execution.cost import COSTS_UNCALIBRATED
from qmb.execution.financing import CashEvent, CashKind
from qmb.host.unit_handler import Fill, UnitTrade
from qmb.host.unit_runner import (
    LoadedUnit,
    UnitRunRequest,
    UnitRunResult,
    load_unit_folder,
    parse_unit_run_request,
    run_loaded,
)
from qmb.results.journal import JournalReport, RunJournal
from qmb.results.measures import (
    ClosedTrade,
    MeasureSlot,
    TradeSide,
    assemble_v1_measure_set,
)
from qmf.core import fingerprint_bytes
from qmf.core.chrono import Instant, Interval
from qmf.core.exact import Money
from qmf.core.refusal import is_refusal
from qmf.risk.performance import UndefinedMeasure

import qmb_tester as tester

_RUN_ID = re.compile(r"qmbr-(?P<machine>.+)-[0-9A-HJKMNP-TV-Z]{26}")
_OFF = "motion_off"
_ACCOUNT: Final = "account"
"""The money measures' currency tag, opaque by `Money`'s rule: no record on this path names one."""
_CENT: Final = Decimal("0.01")
_R_PLACES: Final = Decimal("0.0001")
_RATIO_PLACES: Final = Decimal("0.000001")


@dataclass(frozen=True, slots=True)
class _Ran:
    """One motion setting's run: its report section, measures and journal files."""

    result: UnitRunResult
    section: dict[str, object]
    measures: dict[str, object]
    files: list[dict[str, object]]


def _cash_of_trades(result: UnitRunResult) -> list[tuple[CashEvent, ...]]:
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


def _trade(trade: UnitTrade, cash: Decimal) -> dict[str, object]:
    net_r = (trade.money + cash) / trade.risk if trade.risk else Decimal(0)
    row: dict[str, object] = {
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


def _cash(event: CashEvent) -> dict[str, object]:
    return {
        "instant": event.instant.value_ns,
        "market_id": event.market_id,
        "position_id": event.position_id,
        "kind": event.kind.value,
        "money": str(event.money),
        "detail": event.detail,
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


def _account_money(amount: Decimal) -> Money:
    return Money(int(amount.quantize(_CENT, rounding=ROUND_HALF_EVEN).scaleb(2)), _ACCOUNT, 2)


def _slot_text(slot: MeasureSlot) -> object:
    """One money measure as decimal text, or the reason its arithmetic has no answer."""
    if isinstance(slot, UndefinedMeasure):
        return {"undefined": str(slot.refusal.context.get("code"))}
    held = slot.quantity
    if isinstance(held, Money):
        exact, places = held.as_fraction(), _CENT
    else:
        exact, places = Fraction(held.numerator, held.denominator), _RATIO_PLACES
        if exact.denominator == 1:
            return str(exact.numerator)
    amount = Decimal(exact.numerator) / exact.denominator
    return str(amount.quantize(places, rounding=ROUND_HALF_EVEN))


def _money_measures(result: UnitRunResult, request: UnitRunRequest) -> dict[str, object]:
    """The contract's money measures (`qmb.results.measures`), net of each trade's cash."""
    closed: list[ClosedTrade] = []
    for trade, events in zip(result.trades, _cash_of_trades(result), strict=True):
        cash = sum((e.money for e in events), Decimal(0))
        paid = sum((e.money for e in events if e.kind is CashKind.COMMISSION), Decimal(0))
        closed.append(
            ClosedTrade(
                _account_money(trade.money + cash),
                _account_money(-paid),
                TradeSide(trade.side.value),
                trade.closed_at,
            )
        )
    first, last = request.window_ns or (
        min((t.opened_at.value_ns for t in result.trades), default=0),
        max((t.closed_at.value_ns for t in result.trades), default=0),
    )
    made = assemble_v1_measure_set(
        starting_capital=_account_money(request.equity),
        period=Interval(Instant(first), Instant(last)),
        trades=closed,
    )
    if is_refusal(made):
        return {"unmeasured": tester.reason(made)}
    return {slot.measure_identity: _slot_text(slot) for slot in made.value}


def measures(
    result: UnitRunResult, trades: list[dict[str, object]], request: UnitRunRequest
) -> dict[str, object]:
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
        "max_drawdown_r": str(result.max_drawdown_r),
        "money": _money_measures(result, request),
    }


def _machine(run_id: str) -> str:
    """The machine the core named in the run id, where this journal is written."""
    named = _RUN_ID.match(run_id)
    return named["machine"] if named else "local"


def _journal_files(run: Path, report: JournalReport, slot: str) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    for part in sorted(report.parts, key=lambda p: (p.kind, p.month)):
        data = part.path.read_bytes()
        files.append(
            {
                "slot": f"{slot}/{part.kind}/{part.month}",
                "path": part.path.relative_to(run).as_posix(),
                "fp": fingerprint_bytes(data).value,
                "bytes": len(data),
                "rows": part.rows,
            }
        )
    return files


def _run(run: Path, loaded: LoadedUnit, body: dict[str, object], journal_slot: str) -> _Ran | str:
    """One motion setting's run with its journal, or why it failed."""
    parsed = parse_unit_run_request(body)
    if is_refusal(parsed):
        return tester.reason(parsed)
    request = parsed.value
    opened = RunJournal.open(
        run / "out" / journal_slot,
        loaded.compiled,
        run_id=request.run_id,
        machine=_machine(request.run_id),
        build=f"qmb-app {tester.TESTER['version']}",
    )
    if is_refusal(opened):
        return tester.reason(opened)
    try:
        ran = run_loaded(loaded, request, journal=opened.value)
    except Exception as error:
        # A block's fault is this run's result. A raise would reach the breaker and lose the reason.
        opened.value.close()
        return f"{type(error).__name__}: {error}"
    closed = opened.value.close()
    if is_refusal(ran):
        return tester.reason(ran)
    if is_refusal(closed):
        return f"the run's journal: {tester.reason(closed)}"
    result, journal = ran.value, closed.value
    trades = [
        _trade(trade, sum((event.money for event in events), Decimal(0)))
        for trade, events in zip(result.trades, _cash_of_trades(result), strict=True)
    ]
    section: dict[str, object] = {
        "run_id": result.run_id,
        "trades": trades,
        "fills": [_fill(fill) for fill in result.fills],
        "cash_events": [_cash(event) for event in result.cash_events],
        "holes": [
            {
                "market_id": hole.market_id,
                "after": hole.after_ns,
                "before": hole.before_ns,
                "bars_missing": hole.bars_missing,
            }
            for hole in result.holes
        ],
        "holes_unchecked": list(result.unchecked),
        "open_positions": sorted(result.open_positions),
        "journal": {
            "rows": dict(sorted(journal.rows.items())),
            "repeats": journal.repeats,
            "warnings": [dict(w) for w in journal.warnings],
        },
    }
    files = _journal_files(run, journal, journal_slot)
    return _Ran(result, section, measures(result, trades, request), files)


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    loaded = load_unit_folder(folder / "in")
    if is_refusal(loaded):
        return tester.failed(run_id, tester.reason(loaded))
    body = tester.unit_body(asked, run_id) | {
        "trace": asked.get("trace", "events"),
        "window": asked.get("window"),
    }
    both = body["motion"] == "both"
    main = _run(folder, loaded.value, body | {"motion": "on"} if both else body, "journal")
    if isinstance(main, str):
        return tester.failed(run_id, main)
    report = main.section | {"compiled_fp": main.result.compiled_fingerprint}
    measured, files = main.measures, main.files
    if both:
        off_body = body | {"motion": "off", "run_id": f"{run_id}/{_OFF}"}
        off = _run(folder, loaded.value, off_body, f"journal/{_OFF}")
        if isinstance(off, str):
            return tester.failed(run_id, f"{_OFF}: {off}")
        report[_OFF], measured[_OFF] = off.section, off.measures
        files = [*files, *off.files]
    return tester.leave(
        run_id,
        "finished",
        measures=measured,
        labels={
            "zero_trades": not main.result.trades,
            "costs_uncalibrated": COSTS_UNCALIBRATED in main.result.labels,
            "holes_unchecked": HOLES_UNCHECKED in main.result.labels,
            "fixture_records": asked.get("fixture_records", []),
            "placeholders": list(loaded.value.compiled.placeholders),
            "data_short": tester.data_short(main.result.short),
            **({"cost_profile": asked["cost_profile"]} if "cost_profile" in asked else {}),
            "fidelity": "quotes",
            "motion": asked.get("motion", "on"),
        },
        files=[tester.write(folder, "report.json", report), *files],
        versions={"qmb": tester.TESTER["version"]},
    )
