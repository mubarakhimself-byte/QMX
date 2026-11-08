"""Write the synthetic month beside this file: EURUSD and XAUUSD M15, bid and ask. Not evidence.

The bars are a seeded integer random walk with drifting trend regimes, in the CSV layout
dukascopy-node writes (timestamp in UTC milliseconds, open, high, low, close, volume), so the
test reads the real saved month and this one the same way. Rerun it to check the committed
files: ``uv run python qml/tests/fixtures/slices/make_synthetic_month.py``.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20250301
START = datetime(2025, 3, 2, 22, 0, tzinfo=UTC)
END = datetime(2025, 3, 28, 22, 0, tzinfo=UTC)
BAR = timedelta(minutes=15)

# symbol: (start price in points, decimals, step in points, drift in points, spread in points)
MARKETS = {
    "eurusd": (108_000, 5, 12, 2, 2),
    "xauusd": (2_900_000, 3, 600, 90, 250),
}


def _open_hours(at: datetime) -> bool:
    """Friday 22:00 to Sunday 22:00 UTC is the weekend gap."""
    weekday, hour = at.weekday(), at.hour
    return not (weekday == 5 or (weekday == 4 and hour >= 22) or (weekday == 6 and hour < 22))


def _text(points: int, decimals: int) -> str:
    sign = "-" if points < 0 else ""
    whole, part = divmod(abs(points), 10**decimals)
    return f"{sign}{whole}.{part:0{decimals}d}"


def write(symbol: str, rng: random.Random) -> None:
    price, decimals, step, drift, spread = MARKETS[symbol]
    rows: dict[str, list[str]] = {"bid": [], "ask": []}
    trend, left = 0, 0
    at = START
    while at < END:
        if _open_hours(at):
            if left == 0:
                trend, left = rng.choice((-drift, 0, drift)), rng.randint(60, 240)
            left -= 1
            path = [price]
            for _ in range(5):
                path.append(path[-1] + trend + rng.randint(-step, step))
            price = path[-1]
            stamp = int(at.timestamp()) * 1000
            for side, offset in (("bid", 0), ("ask", spread)):
                o, h, low, c = path[0], max(path), min(path), path[-1]
                cells = [_text(v + offset, decimals) for v in (o, h, low, c)]
                rows[side].append(",".join([str(stamp), *cells, "0"]))
        at += BAR
    for side, lines in rows.items():
        target = HERE / f"synthetic-{symbol}-m15-{side}-2025-03-01-2025-04-01.csv"
        target.write_text(
            "timestamp,open,high,low,close,volume\n" + "\n".join(lines) + "\n", "utf-8"
        )


if __name__ == "__main__":
    generator = random.Random(SEED)  # noqa: S311 - a fixture's seeded walk, not a secret
    for name in MARKETS:
        write(name, generator)
