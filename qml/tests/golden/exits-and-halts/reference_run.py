"""Write the exit and halt family's golden cases (A13d): ``reference.json`` beside this script.

    uv run --no-sync python qml/tests/golden/exits-and-halts/reference_run.py

The bars are a seeded walk of 800 bars whose drift turns every 100 bars, wide enough that each
exit's default trigger is reached on both sides. A run gives the exit ``entry_price`` only inside
its position windows, so each case also proves the exit is silent with no position and starts
afresh for the next one. The halts read seeded sequences of the statistics a host passes.

Each value here is computed from its source's rule over the whole history up to that bar, never
carried from the bar before, so it shares no running state with the blocks. Rerunning the script
rewrites the file byte for byte.
"""

from __future__ import annotations

import json
import random
from collections.abc import Callable, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

OUT = Path(__file__).resolve().parent / "reference.json"
SEED = 20261102
BARS = 800
WINDOWS = ((50, 250), (300, 500), (600, 780))
"""Bar index ranges, both ends held, where a position is given; its entry is the bar before's
close."""

Bar = dict[str, Decimal]
Path_ = list[Bar]


def walk() -> Path_:
    rng = random.Random(SEED)
    drifts = (Decimal("0.004"), Decimal("-0.004"), Decimal("0"), Decimal("0.003"))
    price, bars = Decimal(100), list[Bar]()
    for i in range(BARS):
        drift = drifts[(i // 100) % len(drifts)]
        step = drift + Decimal(str(round(rng.gauss(0, 0.012), 6)))
        close = (price * (1 + step)).quantize(Decimal("0.0001"))
        wick = Decimal(str(round(abs(rng.gauss(0, 0.004)), 6)))
        high = (max(price, close) * (1 + wick)).quantize(Decimal("0.0001"))
        low = (min(price, close) * (1 - wick)).quantize(Decimal("0.0001"))
        bars.append({"open": price, "high": high, "low": low, "close": close})
        price = close
    return bars


def held(bar_index: int) -> tuple[int, Decimal] | None:
    """The window a bar sits in, as (its first bar, its entry), or None outside every window."""
    for first, last in WINDOWS:
        if first <= bar_index <= last:
            return first, PATH[first - 1]["close"]
    return None


PATH = walk()


def profit(entry: Decimal, rate: Decimal, long: bool) -> Decimal:
    return (rate - entry if long else entry - rate) / entry


def favourable(bar: Bar, long: bool) -> Decimal:
    return bar["high"] if long else bar["low"]


def roi_table(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    first, entry = window
    table = [(0, p["roi_0"])] + [(int(p[f"bars_{k}"]), p[f"roi_{k}"]) for k in (1, 2, 3)]
    wanted = [roi for bars, roi in table if bars <= t - first][-1]
    return [profit(entry, PATH[t]["close"], long) >= wanted, wanted]


def profit_cap(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    gain = profit(window[1], PATH[t]["close"], long)
    return [gain > p["cap"], gain]


def giveback(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    first, entry = window
    before = [entry] + [PATH[s]["close"] for s in range(first, t)]
    best = max(before) if long else min(before)
    close = PATH[t]["close"]
    if (close > best) if long else (close < best):
        return [False, Decimal(0)]
    drawdown = abs(best - close) / best
    return [drawdown > p["giveback"], drawdown]


def fraction_trail(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    first, entry = window
    levels = list[Decimal]()
    for s in range(first, t + 1):
        rate = favourable(PATH[s], long)
        gain = profit(entry, rate, long)
        if gain >= p["offset"]:
            distance = min(p["max_distance"], max(p["min_distance"], p["share"] * gain))
            levels.append(rate * (1 - distance) if long else rate * (1 + distance))
    return (max(levels) if long else min(levels)) if levels else None


def stepped(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    first, entry = window
    levels = list[Decimal]()
    for s in range(first, t + 1):
        gain = profit(entry, favourable(PATH[s], long), long)
        passed = [p[f"lock_{k}"] for k in (1, 2, 3) if gain > p[f"trigger_{k}"]]
        if passed:
            lock = passed[-1]
            levels.append(entry * (1 + lock) if long else entry * (1 - lock))
    return (max(levels) if long else min(levels)) if levels else None


def gated(p: dict[str, Decimal], t: int, long: bool) -> object:
    window = held(t)
    if window is None:
        return None
    first, entry = window
    rates = [favourable(PATH[s], long) for s in range(first, t + 1)]
    best = max(rates) if long else min(rates)
    armed = best >= entry * (1 + p["offset"]) if long else best <= entry * (1 - p["offset"])
    if not armed:
        return None
    return best * (1 - p["distance"]) if long else best * (1 + p["distance"])


Rule = Callable[[dict[str, Decimal], int, bool], object]
EXITS: dict[str, tuple[Rule, dict[str, str], list[dict[str, str]]]] = {
    "roi-table-exit": (
        roi_table,
        {
            "roi_0": "0.04",
            "bars_1": "20",
            "roi_1": "0.02",
            "bars_2": "30",
            "roi_2": "0.01",
            "bars_3": "40",
            "roi_3": "0",
        },
        [{"roi_0": "0.1", "bars_1": "5", "roi_3": "-1"}],
    ),
    "unrealised-profit-cap": (profit_cap, {"cap": "0.05"}, [{"cap": "0.2"}]),
    "peak-holdings-giveback-exit": (giveback, {"giveback": "0.05"}, [{"giveback": "0.15"}]),
    "profit-fraction-trailing-stop": (
        fraction_trail,
        {"offset": "0.04", "share": "0.5", "min_distance": "0.025", "max_distance": "0.05"},
        [{"offset": "0.1", "share": "0.25", "max_distance": "0.1"}],
    ),
    "stepped-profit-stop": (
        stepped,
        {
            "trigger_1": "0.20",
            "lock_1": "0.07",
            "trigger_2": "0.25",
            "lock_2": "0.15",
            "trigger_3": "0.40",
            "lock_3": "0.25",
        },
        [{"trigger_1": "0.05", "lock_1": "0", "trigger_2": "0.1", "lock_2": "0.05"}],
    ),
    "offset-gated-trailing-stop": (
        gated,
        {"offset": "0.03", "distance": "0.02"},
        [{"offset": "0", "distance": "0.1"}],
    ),
}


def statistics() -> list[dict[str, Decimal]]:
    """120 updates in six sessions of 20, each a day; the session statistics reset at its start
    and the losing-day streak counts the sessions that ended below their start."""
    rng = random.Random(SEED + 1)
    rows: list[dict[str, Decimal]] = []
    session_r, fills, streak = Decimal(0), Decimal(0), Decimal(0)
    equity = day_start = Decimal(10000)
    for i in range(120):
        if i % 20 == 0:
            if i:
                streak = streak + 1 if equity < day_start else Decimal(0)
            session_r, fills, day_start = Decimal(0), Decimal(0), equity
        session_r += Decimal(str(round(rng.gauss(-0.1, 0.8), 2)))
        fills += rng.choice((0, 1, 2, 3))
        move = Decimal(str(round(rng.gauss(-0.002, 0.012), 5)))
        equity = (equity * (1 + move)).quantize(Decimal("0.01"))
        rows.append(
            {
                "session_loss_r": session_r,
                "session_fills": fills,
                "losing_day_streak": streak,
                "equity": equity,
                "day_start_equity": day_start,
            }
        )
    return rows


STATS = statistics()


def session_loss(p: dict[str, Decimal], t: int) -> object:
    return "flatten unit" if STATS[t]["session_loss_r"] <= -p["limit"] else None


def losing_days(p: dict[str, Decimal], t: int) -> object:
    return "flatten unit" if STATS[t]["losing_day_streak"] >= p["days"] else None


def session_fills(p: dict[str, Decimal], t: int) -> object:
    return "flatten unit" if STATS[t]["session_fills"] > p["fills"] else None


def equity_drawdown(p: dict[str, Decimal], t: int) -> object:
    seen = [STATS[s]["equity"] for s in range(t + 1)]
    for s in range(1, t + 1):
        if p["trailing"] == 1 and seen[s] > max(seen[:s]):
            continue
        base = max(seen[:s]) if p["trailing"] == 1 else seen[0]
        if seen[s] / base - 1 < -p["max_drawdown"]:
            return "flatten account"
    return None


def daily_loss(p: dict[str, Decimal], t: int) -> object:
    equity, start = STATS[t]["equity"], STATS[t]["day_start_equity"]
    return "flatten account" if equity / start - 1 <= -p["limit"] else None


HaltRule = Callable[[dict[str, Decimal], int], object]
HALTS: dict[str, tuple[HaltRule, dict[str, str], list[dict[str, str]]]] = {
    "session-loss-limit-halt": (session_loss, {"limit": "3"}, [{"limit": "1.5"}]),
    "losing-days-halt": (losing_days, {"days": "3"}, [{"days": "1"}]),
    "session-fill-limit-halt": (session_fills, {"fills": "20"}, [{"fills": "10"}]),
    "equity-drawdown-halt": (
        equity_drawdown,
        {"max_drawdown": "0.05", "trailing": "0"},
        [{"trailing": "1"}, {"max_drawdown": "0.08", "trailing": "1"}],
    ),
    "account-daily-loss-halt": (daily_loss, {"limit": "0.05"}, [{"limit": "0.02"}]),
}


def text(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return [text(v) for v in cast("list[object]", value)]
    return value


def name(pin: str, changed: dict[str, str]) -> str:
    return " ".join([pin, *(f"{k}={v}" for k, v in sorted(changed.items()))])


def cases() -> dict[str, object]:
    found: dict[str, object] = {}
    for entry_id, (rule, defaults, variants) in EXITS.items():
        for changed in [{}, *variants]:
            p = {k: Decimal(v) for k, v in (defaults | changed).items()}
            found[name(f"{entry_id}@1", changed)] = {
                side: [text(rule(p, t, side == "long")) for t in range(BARS)]
                for side in ("long", "short")
            }
    for entry_id, (halt, defaults, variants) in HALTS.items():
        for changed in [{}, *variants]:
            p = {k: Decimal(v) for k, v in (defaults | changed).items()}
            found[name(f"{entry_id}@1", changed)] = [halt(p, t) for t in range(len(STATS))]
    return found


def rows(items: Sequence[dict[str, Decimal]]) -> list[dict[str, object]]:
    return [{k: text(v) for k, v in item.items()} for item in items]


def main() -> None:
    document = {
        "generator": "qml/tests/golden/exits-and-halts/reference_run.py",
        "seed": SEED,
        "windows": [list(w) for w in WINDOWS],
        "bars": rows(PATH),
        "statistics": rows(STATS),
        "cases": cases(),
    }
    OUT.write_text(json.dumps(document, indent=1) + "\n", "utf-8")


if __name__ == "__main__":
    main()
