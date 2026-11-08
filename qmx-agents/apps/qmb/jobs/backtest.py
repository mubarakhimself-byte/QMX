"""The `backtest` run kind: trade the run folder's compiled unit over its bars (Part B AD-205).

QMB's unit runner compiles the unit from its pinned blocks, refuses a compiled fingerprint other
than the one the run pins, and trades every bar through the shared unit handler. The bundle
carries each trade in money and R, each fill against its sizer receipt, the measures, and the
run's unit journal as `journal/<kind>/<YYYY-MM>` files (B9). A request with `motion = both` runs
the unit twice, motion on and motion off, and reports both: the off run's trades and measures
under `motion_off`, its journal under `journal/motion_off/`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from qmb.host.unit_handler import Fill, UnitTrade
from qmb.host.unit_runner import (
    LoadedUnit,
    UnitRunResult,
    load_unit_folder,
    parse_unit_run_request,
    run_loaded,
)
from qmb.results.journal import JournalReport, RunJournal
from qmf.core import fingerprint_bytes
from qmf.core.refusal import is_refusal

import qmb_tester as tester

_RUN_ID = re.compile(r"qmbr-(?P<machine>.+)-[0-9A-HJKMNP-TV-Z]{26}")
_OFF = "motion_off"


@dataclass(frozen=True, slots=True)
class _Ran:
    """One motion setting's run: its report section, measures and journal files."""

    result: UnitRunResult
    section: dict[str, object]
    measures: dict[str, object]
    files: list[dict[str, object]]


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
    ran = run_loaded(loaded, request, journal=opened.value)
    closed = opened.value.close()
    if is_refusal(ran):
        return tester.reason(ran)
    if is_refusal(closed):
        return f"the run's journal: {tester.reason(closed)}"
    result, journal = ran.value, closed.value
    trades = [_trade(trade) for trade in result.trades]
    section: dict[str, object] = {
        "run_id": result.run_id,
        "trades": trades,
        "fills": [_fill(fill) for fill in result.fills],
        "open_positions": sorted(result.open_positions),
        "journal": {
            "rows": dict(sorted(journal.rows.items())),
            "repeats": journal.repeats,
            "warnings": [dict(w) for w in journal.warnings],
        },
    }
    files = _journal_files(run, journal, journal_slot)
    return _Ran(result, section, measures(result, trades), files)


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    loaded = load_unit_folder(folder / "in")
    if is_refusal(loaded):
        return tester.failed(run_id, tester.reason(loaded))
    body = tester.unit_body(asked, run_id) | {"trace": asked.get("trace", "events")}
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
            "fidelity": "bars",
            "motion": asked.get("motion", "on"),
        },
        files=[tester.write(folder, "report.json", report), *files],
        versions={"qmb": tester.TESTER["version"]},
    )
