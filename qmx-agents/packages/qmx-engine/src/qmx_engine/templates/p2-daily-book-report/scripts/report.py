"""The daily book report (card P2 steps 1 to 5), zero tokens: book equity, today's PnL in R and USD
per unit, exposure by instrument and by currency leg, drawdown against the account loss budget and
the kill line, and each paper unit inside or outside its Monte Carlo band. Guard fields read "could
not check: trading node" until the node's read model exists."""

import json
import sys

GUARD = "could not check: trading node"

book = json.load(sys.stdin)["in"]
units = {}
for trade in book["closed_today"]:
    unit = units.setdefault(trade["unit"], {"unit": trade["unit"], "pnl_usd": 0.0, "pnl_r": 0.0})
    unit["pnl_usd"] += trade["pnl_usd"]
    unit["pnl_r"] += trade["pnl_usd"] / trade["r_usd"]
by_instrument, by_currency = {}, {}
for held in book["positions"]:
    sign = 1 if held["side"] == "long" else -1
    by_instrument[held["instrument"]] = (
        by_instrument.get(held["instrument"], 0) + sign * held["notional_usd"]
    )
    base, quote = held["instrument"][:3], held["instrument"][3:]
    by_currency[base] = by_currency.get(base, 0) + sign * held["notional_usd"]
    by_currency[quote] = by_currency.get(quote, 0) - sign * held["notional_usd"]
account = book["account"]
drawdown = account["peak_equity"] - account["equity"]
print(
    json.dumps(
        {
            "date": book["date"],
            "equity_usd": account["equity"],
            "units": [
                u | {"pnl_usd": round(u["pnl_usd"], 2), "pnl_r": round(u["pnl_r"], 2)}
                for u in units.values()
            ],
            "exposure_by_instrument_usd": {
                k: round(v, 2) for k, v in sorted(by_instrument.items())
            },
            "exposure_by_currency_usd": {k: round(v, 2) for k, v in sorted(by_currency.items())},
            "drawdown_usd": round(drawdown, 2),
            "loss_budget_used_pct": round(100 * drawdown / account["loss_budget_usd"], 1),
            "kill_line_cushion_usd": round(account["equity"] - account["kill_line"], 2),
            "paper_units": [
                {
                    "unit": p["unit"],
                    "cum_r": p["cum_r"],
                    "band": "inside" if p["p05"] <= p["cum_r"] <= p["p95"] else "outside",
                }
                for p in book["paper"]
            ],
            "guard": GUARD,
        }
    )
)
