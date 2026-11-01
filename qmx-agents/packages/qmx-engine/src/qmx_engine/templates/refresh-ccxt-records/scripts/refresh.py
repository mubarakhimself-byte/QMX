"""Refresh instrument and venue records from CCXT's public market lists (Part C AD-312, C-02).

One run reads each exchange's markets through CCXT's public calls, with no key, and writes one
`instrument` record per market and one `venue` record per exchange as the kinds' fields under
`library/instruments/` and `library/venues/`. A perp carries its funding interval and its source,
a dated future its expiry, root and the next month it rolls to, and every record its data levels
in `qmx.data-level/1`. With `{"fixture": true}` the run reads `fixtures/<exchange>.json`, market
lists in CCXT 4.5.85's unified shape, instead of the network, so a test run is pinned.

A market whose money per price unit is not constant in its quote currency (an inverse contract)
and an option are skipped and counted by reason. Any exchange that fails fails the step, so the
records last landed stay in force.
"""

from __future__ import annotations

import json
import os
import sys
import time
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from itertools import pairwise
from pathlib import Path
from typing import Any, NoReturn

FAILURE = "[QMX_FAILURE]"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
DEFAULT_TOLERANCE = "0.001"
MARGIN_QUANTUM = Decimal("0.00000001")
"""Margin is one over the largest leverage, rounded up at this quantum so it never reads low."""
CLASSES = {"swap": "perp", "future": "future", "spot": "spot_crypto"}
CRYPTO = {"calendar_ref": "crypto-24x7@1", "zone": "UTC", "day_boundary": "00:00"}
LICENCE = "exchange-public-api"

VENUES: dict[str, dict[str, Any]] = {
    "hyperliquid": {
        "funding": ("PT1H", "hyperliquid: perps pay funding every hour"),
        "levels": {
            "perp": {"levels": [0, 1, 3, 4, 5], "volume": "exchange", "depth": "by_price",
                     "derivatives_clock": "live", "history": "provider_limited"},
            "spot_crypto": {"levels": [0, 1, 3, 4], "volume": "exchange", "depth": "by_price",
                            "history": "provider_limited"},
        },
        "venue": {
            "rate_limits": {"websockets_per_ip": 10, "subscriptions_per_ip": 1000,
                            "messages_per_minute": 2000},
            "rationed_actions": [{"action": "order_actions",
                                  "budget": "1 per USDC traded plus 10000 at start"}],
            "cancel_on_disconnect": False,
            "protective_stop_form": {"stop_market": "positionTpsl whole-position trigger"},
            "trigger_basis": "mark",
            "history_limits": {"candles": 5000},
            "unattended": "allowed",
            "needs_desktop_app": False,
            "sandbox": "testnet",
        },
    },
    "binance": {
        "funding": ("PT8H", "binance: every 8 hours unless fundingInfo lists the symbol"),
        "levels": {
            "perp": {"levels": [0, 1, 2, 3, 4, 5], "volume": "taker_split",
                     "depth": "by_price", "derivatives_clock": "live",
                     "history": "provider_limited"},
            "future": {"levels": [0, 1, 2, 3, 4, 5], "volume": "taker_split",
                       "depth": "by_price", "derivatives_clock": "live",
                       "history": "provider_limited"},
            "spot_crypto": {"levels": [0, 1, 2, 3, 4], "volume": "taker_split",
                            "depth": "by_price", "history": "complete"},
        },
        "venue": {
            "cancel_on_disconnect": False,
            "protective_stop_form": {"stop_market": "STOP_MARKET with closePosition"},
            "trigger_basis": "last",
            "unattended": "allowed",
            "needs_desktop_app": False,
            "sandbox": "testnet",
        },
    },
}  # fmt: skip
"""What each exchange states that CCXT's market list does not carry: its funding clock, the data
levels its public API offers, and its venue facts (Part C EXTERNAL.md section 3)."""


def fail(why: str) -> NoReturn:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def decimal(value: object) -> Decimal | None:
    """A positive CCXT number as an exact decimal, read from its text, never its binary float."""
    if value is None or isinstance(value, bool):
        return None
    try:
        found = Decimal(str(value))
    except InvalidOperation:
        return None
    return found if found.is_finite() and found > 0 else None


def text(number: Decimal) -> str:
    return format(number.normalize(), "f")


def places(number: Decimal) -> int:
    exponent = number.normalize().as_tuple().exponent
    return -exponent if isinstance(exponent, int) and exponent < 0 else 0


def interval(given: object) -> str | None:
    """CCXT's `4h` or `30m` as the ISO 8601 duration the record carries."""
    if not isinstance(given, str) or len(given) < 2 or given[-1] not in "hm":
        return None
    count = given[:-1]
    return f"PT{int(count)}{given[-1].upper()}" if count.isdigit() and int(count) > 0 else None


def instrument(
    venue: str, market: dict[str, Any], intervals: dict[str, Any], tolerance: str
) -> dict[str, Any] | str:
    """One market's `instrument` fields, or the reason it is skipped."""
    klass = CLASSES.get(str(market.get("type")))
    if klass is None:
        return f"{market.get('type')} markets have no record class here"
    if market.get("inverse"):
        return "inverse: money per price unit is not constant in the quote currency"
    quote, settle = market.get("quote"), market.get("settle")
    if settle is not None and settle != quote:
        return "settles in a currency other than its quote"
    precision, limits = market.get("precision") or {}, market.get("limits") or {}
    tick, step = decimal(precision.get("price")), decimal(precision.get("amount"))
    size = decimal(market.get("contractSize")) if klass != "spot_crypto" else Decimal(1)
    if tick is None or step is None or size is None:
        return "no tick size, lot step or contract size"
    amount = limits.get("amount") or {}
    levels = VENUES[venue]["levels"].get(klass)
    if levels is None:
        return f"no data levels stated for {klass} markets"
    fields: dict[str, Any] = {
        "venue": venue,
        "symbol": str(market["symbol"]),
        "market_id": str(market["base"]).casefold(),
        "class": klass,
        "currency": str(quote),
        "digits": places(tick),
        "tick_size": text(tick),
        "contract_size": text(size),
        "value_per_point": text(size),
        "value_conversion": {"symbol": str(quote), "method": "linear_in_quote"},
        "conversion_check": {
            "ways": {"contract_size": text(size)},
            "tolerance": tolerance,
            "agrees": None,
        },
        "lot_step": text(step),
        "min_lot": text(decimal(amount.get("min")) or step),
        **CRYPTO,
        "data_levels": {"schema": "qmx.data-level/1", **levels, "licence": LICENCE},
        "status": "live" if market.get("active") is not False else "delisted",
    }
    if (largest := decimal(amount.get("max"))) is not None:
        fields["max_lot"] = text(largest)
    if (leverage := decimal((limits.get("leverage") or {}).get("max"))) is not None:
        margin = text((1 / leverage).quantize(MARGIN_QUANTUM, rounding=ROUND_CEILING))
        fields["leverage"] = {"version": 1, "tiers": [{"leverage": text(leverage)}]}
        fields["margin"] = {"intraday": margin, "overnight": margin}
    if klass == "perp":
        default, source = VENUES[venue]["funding"]
        stated = interval((intervals.get(fields["symbol"]) or {}).get("interval"))
        fields["funding_interval"] = stated or default
        fields["funding_source"] = f"{venue}: fundingInfo" if stated else source
    if klass == "future":
        expiry = market.get("expiryDatetime")
        if not isinstance(expiry, str):
            return "a dated future with no expiry"
        fields |= {
            "expiry": expiry,
            "last_trade": expiry,
            "settlement": "cash",
            "at_expiry_action": "cash_settle",
            "root": fields["symbol"].split("-")[0],
        }
    return fields


def rolls(records: list[dict[str, Any]]) -> None:
    """Each dated future names the next month of its root as `rolls_to`."""
    roots: dict[str, list[dict[str, Any]]] = {}
    for found in records:
        if found["class"] == "future":
            roots.setdefault(found["root"], []).append(found)
    for months in roots.values():
        months.sort(key=lambda month: month["expiry"])
        for month, following in pairwise(months):
            month["rolls_to"] = following["symbol"]


def read(venue: str, fixture: bool) -> tuple[list[dict[str, Any]], dict[str, Any], int | None]:
    """The exchange's markets, funding intervals and CCXT rate limit, recorded or live."""
    if fixture:
        recorded = json.loads((FIXTURES / f"{venue}.json").read_text("utf-8"))
        return recorded["markets"], recorded["funding_intervals"], recorded["rateLimit"]
    try:
        import ccxt  # noqa: PLC0415 (only a live run needs it)
    except ImportError:
        fail("ccxt is not installed on this machine, so the records cannot refresh")
    exchange = getattr(ccxt, venue)({"enableRateLimit": True})
    try:
        markets = list(exchange.load_markets().values())
        intervals = (
            exchange.fetch_funding_intervals() if exchange.has.get("fetchFundingIntervals") else {}
        )
    except Exception as error:  # the exchange's own refusals reach us as exceptions
        fail(f"{venue} refused the public market read: {type(error).__name__}: {error}")
    return markets, intervals, exchange.rateLimit


def safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-." else "_" for c in name)


def main() -> None:
    given = json.load(sys.stdin).get("in") or {}
    if not isinstance(given, dict):
        fail("the run's inputs are not an object")
    venues = given.get("exchanges") or sorted(VENUES)
    unknown = [venue for venue in venues if venue not in VENUES]
    if unknown:
        fail(f"no record profile for {', '.join(map(str, unknown))}")
    tolerance = str(given.get("conversion_tolerance") or DEFAULT_TOLERANCE)
    work = Path(os.environ.get("QMX_WORK") or ".") / "library"
    folders = {"instrument": work / "instruments", "venue": work / "venues"}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    summary: dict[str, Any] = {}
    for venue in venues:
        markets, intervals, rate_limit = read(venue, bool(given.get("fixture")))
        records: list[dict[str, Any]] = []
        skipped: dict[str, int] = {}
        for market in markets:
            made = instrument(venue, market, intervals, tolerance)
            if isinstance(made, str):
                skipped[made] = skipped.get(made, 0) + 1
            else:
                records.append(made)
        rolls(records)
        for found in records:
            path = folders["instrument"] / f"{safe(venue)}__{safe(found['symbol'])}.json"
            path.write_text(json.dumps(found, indent=2, sort_keys=True), encoding="utf-8")
        facts = dict(VENUES[venue]["venue"])
        if rate_limit is not None:
            facts["rate_limits"] = {
                **facts.get("rate_limits", {}),
                "ccxt_rate_limit_ms": rate_limit,
            }
        offered = sorted({level for r in records for level in r["data_levels"]["levels"]})
        facts |= {"venue": venue, "data_levels": {"schema": "qmx.data-level/1", "levels": offered}}
        (folders["venue"] / f"{safe(venue)}.json").write_text(
            json.dumps(facts, indent=2, sort_keys=True), encoding="utf-8"
        )
        summary[venue] = {"records": len(records), "skipped": skipped}
    print(
        json.dumps(
            {
                "status": "refreshed",
                "source": "fixture" if given.get("fixture") else "live",
                "venues": summary,
                "seconds": round(time.perf_counter() - started, 3),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
