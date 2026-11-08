"""Write the golden values the beyond-FX blocks are tested against (A13c).

This script is the only QMX code that imports TA-Lib, numpy and the IANA zone data for these
blocks; QML and its tests read the committed JSON. Run it from the repository root:

    uv run --no-project --python 3.14 --with ta-lib==0.7.1 --with numpy==2.5.4 \
        --with tzdata==2025.2 python qml/tests/golden/beyond-fx/reference_run.py

It writes two fixtures. ``profile.json`` holds 30-minute bars over twenty days and the cases of
the market-profile blocks and ``bar-range-pressure``. The profile cases are TradingView's TPO
value-area algorithm with CQG's point-of-control tie rule, rebuilt from the session's bars at
every bar from a plain dictionary of rows, so no running state is shared with the blocks. The
range pressure is the first difference of TA-Lib's AD over a volume of 1. ``clocks.json`` holds
30-minute bars over the weeks around the 2026 daylight-saving changes in London and New York,
and each clock case is the nearest event built with ``zoneinfo``, so the blocks' own calendar
arithmetic meets the IANA rules. The bars are seeded and written as decimal strings, so the
fixtures are the same on every run, and the script refuses any other library version.
"""
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportAttributeAccessIssue=false

from __future__ import annotations

import json
import random
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import ROUND_FLOOR, Decimal
from importlib.metadata import version
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy
import talib

VERSIONS = {"ta-lib": "0.7.1", "numpy": "2.5.4", "tzdata": "2025.2"}
SEED = 20261104
HERE = Path(__file__).resolve().parent
DAY_NS = 86_400 * 10**9
BAR_S = 1_800
NS = 10**9

Bar = dict[str, Any]


def _walk(closes: Sequence[int], rng: random.Random, start: float, step: float) -> list[Bar]:
    """OHLC on a 0.25 grid around a seeded walk, one bar per close time."""
    bars: list[Bar] = []
    price = start
    for closed in closes:
        opened = price
        price += rng.gauss(0, step)
        high = max(opened, price) + abs(rng.gauss(0, step / 2))
        low = min(opened, price) - abs(rng.gauss(0, step / 2))

        def grid(x: float) -> str:
            return str((Decimal(round(x * 4)) / 4).quantize(Decimal("0.01")))

        o, c, h, lo = grid(opened), grid(price), grid(high), grid(low)
        h = max(o, c, h, key=Decimal)
        lo = min(o, c, lo, key=Decimal)
        bars.append({"open": o, "high": h, "low": lo, "close": c, "time": closed})
    return bars


def _ns(at: datetime) -> int:
    return int(at.timestamp()) * NS


def _profile_bars() -> list[Bar]:
    first = _ns(datetime(2026, 3, 2, 0, 30, tzinfo=UTC))
    return _walk([first + i * BAR_S * NS for i in range(20 * 48)], random.Random(SEED), 5000, 3)


def _clock_bars() -> list[Bar]:
    closes: list[int] = []
    for start, days in (
        (datetime(2026, 3, 1, tzinfo=UTC), 37),
        (datetime(2026, 10, 18, tzinfo=UTC), 23),
    ):
        first = _ns(start + timedelta(seconds=BAR_S))
        closes += [first + i * BAR_S * NS for i in range(days * 48)]
    return _walk(closes, random.Random(SEED + 1), 2400, 2)


def _row(price: str, size: Decimal) -> int:
    return int((Decimal(price) / size + Decimal("0.5")).to_integral_value(rounding=ROUND_FLOOR))


def _session(bars: Sequence[Bar], i: int, start_ns: int) -> list[Bar]:
    day = (bars[i]["time"] - 1 - start_ns) // DAY_NS
    return [b for b in bars[: i + 1] if (b["time"] - 1 - start_ns) // DAY_NS == day]


def _profile(bars: Sequence[Bar], i: int, p: dict[str, Decimal]) -> tuple[int, int, int] | None:
    """The point of control and the value area's low and high rows, or None when the session
    spans more than ``max_rows`` rows."""
    size = p["row_size"]
    rows: dict[int, int] = {}
    for b in _session(bars, i, int(p["session_start"]) * NS):
        for r in range(_row(b["low"], size), _row(b["high"], size) + 1):
            rows[r] = rows.get(r, 0) + 1
    bottom, top = min(rows), max(rows)
    if top - bottom + 1 > int(p["max_rows"]):
        return None
    count = {r: rows.get(r, 0) for r in range(bottom, top + 1)}
    most = max(count.values())
    middle = Decimal(bottom + top) / 2
    poc = sorted((r for r in count if count[r] == most), key=lambda r: (abs(r - middle), -r))[0]
    target = Decimal(sum(count.values())) * p["value_area_share"] / 100
    low = high = poc
    held = count[poc]
    while held < target:
        above, below = count.get(high + 1), count.get(low - 1)
        if above is None and below is None:
            break
        go_up = below is None or (
            above is not None
            and (above > below or (above == below and high + 1 - poc <= poc - low + 1))
        )
        if go_up:
            high += 1
            held += count[high]
        else:
            low -= 1
            held += count[low]
    return poc, low, high


def _tpo(pick: int) -> Callable[[Sequence[Bar], int, dict[str, Decimal]], Decimal | None]:
    def run(bars: Sequence[Bar], i: int, p: dict[str, Decimal]) -> Decimal | None:
        found = _profile(bars, i, p)
        return None if found is None else Decimal(found[pick]) * p["row_size"]

    return run


def _balance(what: str) -> Callable[[Sequence[Bar], int, dict[str, Decimal]], Decimal | None]:
    def run(bars: Sequence[Bar], i: int, p: dict[str, Decimal]) -> Decimal | None:
        start = int(p["session_start"]) * NS
        ib = int(p["ib_seconds"]) * NS
        day = (bars[i]["time"] - 1 - start) // DAY_NS
        into = [(b, b["time"] - (day * DAY_NS + start)) for b in _session(bars, i, start)]
        inside = [b for b, t in into if t <= ib]
        after = [b for b, t in into if t > ib]
        if not inside or not (after or into[-1][1] == ib):
            return None
        high = max(Decimal(b["high"]) for b in inside)
        low = min(Decimal(b["low"]) for b in inside)
        if what == "high":
            return high
        if what == "low":
            return low
        if not after:
            return Decimal(0)
        if int(p["side"]) > 0:
            return max(max(Decimal(b["high"]) for b in after) - high, Decimal(0))
        return max(low - min(Decimal(b["low"]) for b in after), Decimal(0))

    return run


def _clock(zone: str, events: Sequence[tuple[int | None, int, int]]):
    """Seconds from the nearest event; each event is (weekday or None for every weekday, hour,
    minute) in ``zone``, Monday 0."""
    tz = ZoneInfo(zone)

    def run(bars: Sequence[Bar], i: int, p: dict[str, Decimal]) -> Decimal | None:
        closed = bars[i]["time"]
        at = datetime.fromtimestamp(closed // NS, UTC)
        found: list[int] = []
        for shift in range(-8, 9):
            local = (at + timedelta(days=shift)).astimezone(tz).date()
            for weekday, hour, minute in events:
                if (weekday is None and local.weekday() < 5) or local.weekday() == weekday:
                    event = datetime(local.year, local.month, local.day, hour, minute, tzinfo=tz)
                    found.append(_ns(event))
        nearest = min(set(found), key=lambda e: (abs(closed - e), -e))
        return Decimal(closed - nearest) / Decimal(NS)

    return run


def _funding(bars: Sequence[Bar], i: int, p: dict[str, Decimal]) -> Decimal | None:
    closed = bars[i]["time"]
    step = int(p["interval"]) * NS
    before = closed - closed % step
    nearest = min((before, before + step), key=lambda e: (abs(closed - e), -e))
    return Decimal(closed - nearest) / Decimal(NS)


def _pressure_cases(bars: Sequence[Bar]) -> list[str | None]:
    h, lo, c = (numpy.array([float(b[k]) for b in bars]) for k in ("high", "low", "close"))
    ad = talib.AD(h, lo, c, numpy.ones(len(bars)))
    return [_text(Decimal(repr(float(x)))) for x in numpy.diff(ad, prepend=0.0)]


def _text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f") if value == value.to_integral_value() else str(value)


PROFILE_DEFAULTS = {
    "session_start": "0",
    "row_size": "1",
    "value_area_share": "70",
    "max_rows": "2000",
}
BALANCE_DEFAULTS = {"session_start": "0", "ib_seconds": "3600", "side": "1"}

PROFILE_CASES: dict[str, tuple[Callable[..., Decimal | None], dict[str, str]]] = {}
for pin, pick in (
    ("tpo-point-of-control@1", 0),
    ("tpo-value-area-low@1", 1),
    ("tpo-value-area-high@1", 2),
):
    for extra in (
        "row_size=1",
        "row_size=0.5 session_start=48600 value_area_share=68",
        "row_size=0.25 max_rows=120",
    ):
        PROFILE_CASES[f"{pin} {extra}"] = (_tpo(pick), PROFILE_DEFAULTS)
for pin, what in (("initial-balance-high@1", "high"), ("initial-balance-low@1", "low")):
    for extra in ("ib_seconds=3600", "ib_seconds=1800 session_start=48600"):
        PROFILE_CASES[f"{pin} {extra}"] = (_balance(what), BALANCE_DEFAULTS)
for extra in ("side=1", "side=-1", "ib_seconds=1800 session_start=48600 side=-1"):
    PROFILE_CASES[f"initial-balance-range-extension@1 {extra}"] = (
        _balance("extension"),
        BALANCE_DEFAULTS,
    )

LONDON, NEW_YORK = "Europe/London", "America/New_York"
CLOCK_CASES: dict[str, tuple[Callable[..., Decimal | None], dict[str, str]]] = {
    "lbma-gold-auction-clock@1 auction=0": (_clock(LONDON, [(None, 10, 30), (None, 15, 0)]), {}),
    "lbma-gold-auction-clock@1 auction=1": (_clock(LONDON, [(None, 10, 30)]), {}),
    "lbma-gold-auction-clock@1 auction=2": (_clock(LONDON, [(None, 15, 0)]), {}),
    "lbma-silver-auction-clock@1": (_clock(LONDON, [(None, 12, 0)]), {}),
    "eia-petroleum-status-report-clock@1": (_clock(NEW_YORK, [(2, 10, 30)]), {}),
    "eia-natural-gas-storage-report-clock@1": (_clock(NEW_YORK, [(3, 10, 30)]), {}),
    "perp-funding-settlement-clock@1 interval=28800": (_funding, {}),
    "perp-funding-settlement-clock@1 interval=3600": (_funding, {}),
}


def _params(case: str, defaults: dict[str, str]) -> dict[str, Decimal]:
    given = dict(w.split("=", 1) for w in case.split()[1:])
    return {k: Decimal(v) for k, v in (defaults | given).items()}


def _fixture(
    bars: list[Bar], cases: dict[str, tuple[Callable[..., Decimal | None], dict[str, str]]]
) -> dict[str, Any]:
    out: dict[str, list[str | None]] = {}
    for case, (run, defaults) in sorted(cases.items()):
        p = _params(case, defaults)
        out[case] = [_text(run(bars, i, p)) for i in range(len(bars))]
    return {"bars": bars, "close": [b["close"] for b in bars], "cases": out}


def main() -> int:
    found = {"ta-lib": version("ta-lib"), "numpy": numpy.__version__, "tzdata": version("tzdata")}
    if found != VERSIONS:
        print(f"refused: needs {VERSIONS}, found {found}", file=sys.stderr)
        return 1
    header = {"generator": "qml/tests/golden/beyond-fx/reference_run.py", **VERSIONS, "seed": SEED}
    profile_bars = _profile_bars()
    profile = _fixture(profile_bars, PROFILE_CASES)
    profile["cases"]["bar-range-pressure@1"] = _pressure_cases(profile_bars)
    profile["reference"] = {
        "TradingView TPO value-area algorithm with CQG's point-of-control tie, rebuilt per bar": sorted(
            c for c in PROFILE_CASES if c.startswith("tpo-")
        ),
        "Aspen's initial balance and range extension, rebuilt per bar from the session's bars": sorted(
            c for c in PROFILE_CASES if c.startswith("initial-balance")
        ),
        "TA-Lib 0.7.1 AD over a volume of 1, first difference": ["bar-range-pressure@1"],
    }
    clocks = _fixture(_clock_bars(), CLOCK_CASES)
    clocks["reference"] = {
        "zoneinfo (IANA tz database) local event times, nearest by absolute distance, the later on a tie": sorted(
            CLOCK_CASES
        )
    }
    for name, body in (("profile.json", profile), ("clocks.json", clocks)):
        text = json.dumps({**header, **body}, indent=1, sort_keys=False) + "\n"
        (HERE / name).write_text(text, "utf-8", newline="\n")
        print(f"wrote {name}: {len(body['cases'])} cases over {len(body['bars'])} bars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
