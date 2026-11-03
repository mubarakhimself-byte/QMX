import asyncio
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from macro_bias import latest, refresh

MARKET = "fixture/EURUSD/bar-m1/bid"


def day_ms(month: int, day: int) -> int:
    return int(datetime(2025, month, day, tzinfo=UTC).timestamp()) * 1_000


def write_month(root: Path, month: int, days: list[int], *, frozen: bool, cut: int = 1_440) -> None:
    """M1 bars for whole days, the last day cut after `cut` minutes. Every minute of day `d`
    closes at 108_000 + 100 * d, so a day's close names its day."""
    times: list[int] = []
    closes: list[int] = []
    for day in days:
        minutes = cut if day == days[-1] else 1_440
        times += [day_ms(month, day) + minute * 60_000 for minute in range(minutes)]
        closes += [108_000 + 100 * day] * minutes
    folder = root / "series" / MARKET / f"2025-{month:02d}"
    folder.mkdir(parents=True)
    name = "fp1-fixture.parquet" if frozen else "open.parquet"
    table = pa.table({"t": pa.array(times, pa.int64()), "close": pa.array(closes, pa.int64())})
    pq.write_table(table, folder / name)
    state = {"fingerprint": "fp1-fixture", "frozen": frozen}
    (folder / "state.json").write_text(json.dumps(state), encoding="utf-8")


class BiasTests(unittest.TestCase):
    def test_recorded_agent_writes_persistent_bias(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "tests"}),
        ):
            volume = Path(temporary)
            result = asyncio.run(refresh(volume))
            self.assertEqual(latest(volume), result)
            self.assertEqual(result["bias"], "neutral")
            self.assertEqual(result["source"], "recorded")
            self.assertIn("coverage", result["rationale"])
            self.assertEqual(json.loads(json.dumps(result)), result)

    def test_live_bias_reads_daily_bars_rolled_up_from_the_market_store(self) -> None:
        asked: list[str] = []

        async def model(system: str, user: str) -> str:
            asked.append(user)
            return json.dumps({"bias": "bullish", "rationale": "Fixture model read two bars."})

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "live"}),
        ):
            volume, market_root = Path(temporary) / "volume", Path(temporary) / "market"
            (volume / "data").mkdir(parents=True)
            write_month(market_root, 2, [27, 28], frozen=True)
            write_month(market_root, 3, [1, 2], frozen=False, cut=720)
            settings = {"market": MARKET, "bars": 2}
            (volume / "data/config.json").write_text(json.dumps(settings), encoding="utf-8")

            result = asyncio.run(refresh(volume, model, market_root))

            self.assertEqual(
                json.loads(asked[0]),
                {
                    "as_of": "2025-03-01T00:00Z",
                    "bars": [
                        {"t": "2025-02-28T00:00Z", "close": "1.10800"},
                        {"t": "2025-03-01T00:00Z", "close": "1.08100"},
                    ],
                    "source": MARKET,
                },
            )
            self.assertEqual(
                result,
                {
                    "bias": "bullish",
                    "rationale": "Fixture model read two bars.",
                    "as_of": "2025-03-01T00:00Z",
                    "source": "qmx-data",
                },
            )

    def test_live_bias_names_an_unset_market(self) -> None:
        async def model(system: str, user: str) -> str:
            raise AssertionError("no model call without bars")

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "live"}),
        ):
            with self.assertRaisesRegex(ValueError, "Set market to the store's bar series"):
                asyncio.run(refresh(Path(temporary), model, Path(temporary) / "market"))


if __name__ == "__main__":
    unittest.main()
