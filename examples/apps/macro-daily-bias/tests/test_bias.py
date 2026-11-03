import asyncio
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import httpx
from qmf.core import is_refusal
from qmf.data.series import BAR_KIND, SeriesKey, SeriesStore

from macro_bias import chat_model, latest, refresh

MARKET = "fixture/EURUSD/bar-m1/bid"


def day_ms(month: int, day: int) -> int:
    return int(datetime(2025, month, day, tzinfo=UTC).timestamp()) * 1_000


def write_month(root: Path, month: int, days: list[int], cut: int = 1_440) -> None:
    """M1 bars for whole days through the store's own writer, the last day cut after `cut`
    minutes. Every minute of day `d` closes at 108_000 + 100 * d, so a day's close names it."""
    rows: list[tuple[object, ...]] = []
    for day in days:
        minutes = cut if day == days[-1] else 1_440
        price = 108_000 + 100 * day
        rows += [
            (day_ms(month, day) + minute * 60_000, price, price, price, price, 1.0)
            for minute in range(minutes)
        ]
    key = SeriesKey.try_create("fixture", "EURUSD", BAR_KIND, 2025, month, "bid")
    assert not is_refusal(key), key
    committed = SeriesStore(root / "series").commit(key.value, rows)
    assert not is_refusal(committed), committed


def answering(content: object, seen: list[httpx.Request]) -> object:
    """An OpenAI-compatible endpoint, in this process, that answers `content` once."""

    async def handle(_transport: object, request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return patch.object(httpx.AsyncHTTPTransport, "handle_async_request", handle)


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

    def test_live_bias_reads_daily_bars_from_the_market_store_and_asks_the_model_once(
        self,
    ) -> None:
        seen: list[httpx.Request] = []
        answer = json.dumps({"bias": "bullish", "rationale": "Fixture model read two bars."})
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "live", "QMX_MODEL_KEY": "fixture-model-key"}),
            answering(answer, seen),
        ):
            volume, market_root = Path(temporary) / "volume", Path(temporary) / "market"
            (volume / "data").mkdir(parents=True)
            write_month(market_root, 2, [27, 28])
            write_month(market_root, 3, [1, 2], cut=720)
            settings = {
                "market": MARKET,
                "bars": 2,
                "model": "fixture-model",
                "model_url": "http://127.0.0.1:9/v1",
            }
            (volume / "data/config.json").write_text(json.dumps(settings), encoding="utf-8")

            result = asyncio.run(refresh(volume, market_root=market_root))

        [request] = seen
        user = json.loads(request.content)["messages"][1]["content"]
        self.assertEqual(
            (str(request.url), request.headers["Authorization"]),
            ("http://127.0.0.1:9/v1/chat/completions", "Bearer fixture-model-key"),
        )
        self.assertEqual(
            json.loads(user),
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

    def test_live_bias_names_an_unset_market_a_bad_config_and_an_empty_answer(self) -> None:
        async def model(system: str, user: str) -> str:
            raise AssertionError("no model call without bars")

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"QMX_STAGE": "live", "QMX_MODEL_KEY": "fixture-model-key"}),
        ):
            volume = Path(temporary)
            with self.assertRaisesRegex(ValueError, "Set market to the store's bar series"):
                asyncio.run(refresh(volume, model, volume / "market"))
            (volume / "data").mkdir()
            (volume / "data/config.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "one JSON object of settings"):
                asyncio.run(refresh(volume, model, volume / "market"))
            ask = chat_model({"model": "fixture-model", "model_url": "http://127.0.0.1:9/v1"})
            with answering(None, []), self.assertRaisesRegex(ValueError, "no text content"):
                asyncio.run(ask("system", "user"))


if __name__ == "__main__":
    unittest.main()
