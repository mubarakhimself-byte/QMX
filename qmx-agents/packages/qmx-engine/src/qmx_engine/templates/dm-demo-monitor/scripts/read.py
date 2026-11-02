"""Each demo unit's fills and trades for the day, counted by script before any model reads it.
Zero tokens.

Inputs, all optional: `day` (YYYY-MM-DD, UTC; the day before the run's clock by default) and
`units` (unit ids; every demo unit with rows that day by default).

It reads the unit journal's `demo` world through `journal_query`: the `fill` rows, and the `trade`
rows in the `trades_with_context` view, which sets the market journal's minute beside each trade.
Per unit and market it counts the fills, the partial fills (a fill whose `receipt_quantity` differs
from its `quantity`), the sizing residue in R the fills left, the trades and their R, the stops a
price gapped through, the exits by kind, and how many trades have a market minute recorded beside
them. It lands the counts as one `fill-quality` artifact. A day with no demo rows is quiet and asks
no model.
"""

import importlib.util
import json
import os
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

asked = door.settings(json.load(sys.stdin).get("in"))
day, window = door.day_window(asked.get("day"))
qmx_home = door.home()
try:
    fills = door.journal(
        qmx_home, stream="unit", window=window, filters={"world": "demo", "kind": "fill"}
    )
    trades = door.journal(
        qmx_home,
        stream="unit",
        window=window,
        filters={"world": "demo", "kind": "trade"},
        view="trades_with_context",
    )
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

wanted = set(asked.get("units") or [])
cells = {}


def cell(row):
    key = (row["unit_id"], row["market_id"])
    return cells.setdefault(
        key,
        {
            "fills": 0,
            "partial_fills": 0,
            "residue_r": Decimal(0),
            "trades": 0,
            "r": Decimal(0),
            "gaps_through_stop": 0,
            "exits": Counter(),
            "with_market_minute": 0,
        },
    )


for row in fills["rows"]:
    if wanted and row["unit_id"] not in wanted:
        continue
    body, found = row["body"], cell(row)
    found["fills"] += 1
    asked_size = body.get("receipt_quantity")
    found["partial_fills"] += asked_size is not None and asked_size != body.get("quantity")
    found["residue_r"] += Decimal(str(body.get("residue_r", "0")))
for row in trades["rows"]:
    if row["kind"] != "trade" or (wanted and row["unit_id"] not in wanted):
        continue
    body, found = row["body"], cell(row)
    found["trades"] += 1
    found["r"] += Decimal(str(body.get("r", "0")))
    found["gaps_through_stop"] += body.get("gap_through_stop") is True
    found["exits"][str(body.get("exit_kind", "unnamed"))] += 1
    found["with_market_minute"] += row.get("market_minute") is not None

units = {}
for (unit, market), found in sorted(cells.items()):
    units.setdefault(unit, []).append(
        {
            "market": market,
            **{k: v for k, v in found.items() if k not in ("residue_r", "r", "exits")},
            "residue_r": str(found["residue_r"]),
            "r": str(found["r"]),
            "exits": dict(sorted(found["exits"].items())),
        }
    )
reviewed = [{"unit": unit, "markets": markets} for unit, markets in units.items()]
findings = {
    "day": day,
    "window": window,
    "units": reviewed,
    "backfilled_left_out": fills["backfilled_left_out"] + trades["backfilled_left_out"],
}
note = None
if not reviewed:
    note = {
        "title": f"No demo fills or trades on {day}",
        "text": f"The unit journal holds no demo fills or trades on {day} (UTC). Nothing to check.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not reviewed,
            "note": note,
            "note_kind": "analysis",
            "about": [{"rel": "unit", "ref": u["unit"]} for u in reviewed],
            "window": window,
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "fill-quality",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"fill-quality|{day}",
                }
            ],
        }
    )
)
