"""One account feed, two streams: a 1-minute unit and a 15-minute unit on one fake broker.

RC-30's third seam. The account's feed builds one 60-second base bar and each unit's own stream
rolls up from it, keyed by its stream and its market. At the parent a feed of one size hosts only
the unit that reads exactly that size, so the second unit refuses.

The fake broker is the cTrader double behind the real ``CTraderVenue``, driven as
``test_app_broker_wins`` drives it. The bars are the conformance month's synthetic 15-minute bars
split into one-minute bars, so both units see the same prices at their own bar size.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import cast

import test_app_binding as binding
import test_app_runtime as base
from qmf.core import TypedRefusal
from qmf.core.chrono import Instant
from qml.blocks.api import EntryFace, parse_entry
from qml.compile import CompileContext, CompiledUnit, compile_unit
from qml.numbers import InstrumentRecord, parse_record
from qml.protocol.unit import OHLC, QuoteBar
from qmn.app.runtime import Phase

MINUTE_NS = 60_000_000_000
M15_NS = 900_000_000_000
WARM_BARS = 1_440
"""Ninety-six complete 15-minute buckets before the live run: enough for the 86-bar warm-up."""
LIVE_BARS = 60
"""One hour of one-minute bars: 60 bars for the m1 unit and 4 for the m15 unit."""
MARKETS = {"m1": "fx.eurusd", "m15": "metal.xauusd"}
"""Each unit trades a different market, so the fake broker's netting rule is not the refusal
this test is about."""


def _small(document: dict[str, object], *, stream: str) -> dict[str, object]:
    """The dummy's logic with number ranges small enough to warm in 86 bars, on ``stream``."""
    numbers = cast("dict[str, object]", document["numbers"])
    ranges = {
        "ema_period": ("2", "8", "4"),
        "roc_lookback": ("2", "8", "3"),
        "rsi_period": ("2", "8", "4"),
    }
    for name, (low, high, default) in ranges.items():
        spec = cast("dict[str, object]", numbers[name])
        spec["range"] = {"min": low, "max": high, "step": "1"}
        spec["default"] = default
    for name, percentile in (("rsi_low", "20"), ("rsi_high", "80")):
        spec = cast("dict[str, object]", numbers[name])
        motion = cast("dict[str, object]", spec["motion"])
        motion["rule_params"] = {"percentile": percentile, "window_bars": "4"}
    strength = cast("dict[str, object]", numbers["min_trend_strength"])
    motion = cast("dict[str, object]", strength["motion"])
    motion["rule_params"] = {"buckets": "3"}
    motion["min_count"] = 1
    motion["cadence"] = {"every_closed_trades": 1, "at": "market_day_close"}
    time_out = cast("dict[str, object]", numbers["time_out_bars"])
    time_out["range"] = {"min": "1", "max": "10", "step": "1"}
    time_out["default"] = "3"
    streams = cast("list[dict[str, object]]", document["streams"])
    streams[0]["name"] = stream
    streams[0]["bar"] = {"kind": "time", "size": "60" if stream == "m1" else "900"}
    if stream == "m1":
        return cast("dict[str, object]", json.loads(json.dumps(document).replace("m15", "m1")))
    return document


@cache
def documents() -> dict[str, dict[str, object]]:
    return {stream: _small(base.dummy_document(), stream=stream) for stream in MARKETS}


@cache
def fingerprints() -> dict[str, str]:
    sources: dict[str, bytes] = {}
    entries: dict[str, bytes] = {}
    for entry_path in sorted(base.STDLIB.glob("*/*/entry.json")):
        face = parse_entry(entry_path.read_bytes())
        assert isinstance(face, EntryFace), face
        sources[face.pin] = entry_path.with_name("block.py").read_bytes()
        entries[face.pin] = entry_path.read_bytes()
    records: dict[str, InstrumentRecord] = {}
    for market, symbol in base.MARKETS.items():
        loaded = parse_record(json.loads((base.RECORDS / f"{symbol}.json").read_text("utf-8")))
        assert not isinstance(loaded, TypedRefusal), loaded
        records[market] = loaded.value
    found: dict[str, str] = {}
    for stream, document in documents().items():
        compiled = compile_unit(
            document, CompileContext(sources=sources, entries=entries, records=records)
        )
        assert isinstance(compiled, CompiledUnit), compiled
        found[stream] = compiled.compiled_fingerprint.value
    return found


def one_minute(bar: QuoteBar) -> tuple[QuoteBar, ...]:
    """The fifteen one-minute bars that roll back to ``bar``, on both sides, whose first open,
    highest high, lowest low and last close are the fifteen-minute bar's own."""
    opened = bar.knowable_at.value_ns - M15_NS
    out: list[QuoteBar] = []
    for step in range(15):
        at = opened + (step + 1) * MINUTE_NS
        if step == 0:
            bid = OHLC(bar.bid.open, bar.bid.high, bar.bid.low, bar.bid.open)
            ask = OHLC(bar.ask.open, bar.ask.high, bar.ask.low, bar.ask.open)
        else:
            bid = OHLC(bar.bid.close, bar.bid.close, bar.bid.close, bar.bid.close)
            ask = OHLC(bar.ask.close, bar.ask.close, bar.ask.close, bar.ask.close)
        out.append(QuoteBar(Instant(at), bid, ask))
    return tuple(out)


@cache
def minutes() -> dict[str, tuple[QuoteBar, ...]]:
    """Each market's warm-up buckets and then its live hour, split to one-minute bars.

    The warm-up is the ninety-six whole 15-minute buckets before ``LIVE_FROM``. The live hour is
    the next four, which is sixty one-minute bars and four fifteen-minute bars.
    """
    out: dict[str, list[QuoteBar]] = {market: [] for market in base.MARKETS}
    for market in base.MARKETS:
        series = [bar for _, name, bar in base.month().bars if name == market]
        warm = [bar for bar in series if bar.knowable_at.value_ns < base.LIVE_FROM]
        live = [bar for bar in series if bar.knowable_at.value_ns >= base.LIVE_FROM]
        chosen = warm[-(WARM_BARS // 15) :] + live[: LIVE_BARS // 15]
        out[market] = [minute for bar in chosen for minute in one_minute(bar)]
    return {market: tuple(series) for market, series in out.items()}


def deployment(rig: binding.Bound, stream: str, op_id: str) -> dict[str, base.Json]:
    """One small unit deployed on its own market, its files staged as the node link stages them."""
    document = base.deployment(rig.data, f"dep-{stream}", compiled=fingerprints()[stream])
    document["unit_document"] = cast("base.Json", documents()[stream])
    document["markets"] = [
        {
            "market_id": MARKETS[stream],
            "instrument": {"id": base.MARKETS[MARKETS[stream]], "version": 1},
        }
    ]
    return document


def deploy(rig: binding.Bound, document: dict[str, base.Json], op_id: str) -> dict[str, base.Json]:
    return rig.node.call("deploy", {"op_id": op_id, "deployment": document})


def live_start() -> int:
    """The first live minute's bucket start, on the fifteen-minute grid."""
    return minutes()[MARKETS["m1"]][WARM_BARS].knowable_at.value_ns - MINUTE_NS


def keep_warm(rig: binding.Bound) -> None:
    """The fed recording holds the warm-up buckets before the live hour, per market."""
    feed = binding.runtime(rig).venues[binding.ACCOUNT].feed
    for market, series in minutes().items():
        for bar in series[:WARM_BARS]:
            feed.recording.keep(market, bar)


def prime(rig: binding.Bound) -> None:
    """One quote per market before the live hour, so the venue's first live bucket reads whole.

    A bucket a session joined part way through is never sent as a bar. The venue cannot tell a
    session that joined on a bucket's boundary from one that joined just after it, so the quote
    here gives it a bucket to finish before the live hour starts.
    """
    for market in MARKETS.values():
        bar = minutes()[market][WARM_BARS]
        symbol = "EURUSD" if market == "fx.eurusd" else "XAUUSD"
        rig.fake.quote(symbol, bar.bid.open, bar.ask.open, rig.now[0] // 1_000_000)
    binding.runtime(rig).tick()


def settle(rig: binding.Bound, deployment_id: str) -> Phase:
    """Tick until the deployment has compiled and hosted, or refused."""
    deadline = time.monotonic() + 240
    while True:
        binding.runtime(rig).tick()
        hosted = binding.runtime(rig).hosted.get(deployment_id)
        if hosted is not None and hosted.phase not in (Phase.COMPILING, Phase.WAITING):
            return hosted.phase
        assert time.monotonic() < deadline, f"{deployment_id} neither settled nor refused"
        time.sleep(0.02)


def play_minutes(rig: binding.Bound) -> None:
    """Play the live hour as cTrader's spots, four a minute per side, and tick once a minute.

    A bar closes when the next minute's first spot arrives, so one spot after the last minute
    closes the bar that minute built.
    """
    live = {market: series[WARM_BARS:] for market, series in minutes().items()}
    for index in range(LIVE_BARS):
        for offset in range(4):
            for market, series in live.items():
                bar = series[index]
                rig.now[0] = bar.knowable_at.value_ns - MINUTE_NS + (offset + 1) * 1_000_000
                quote(rig, market, bar, offset)
            if offset == 0:
                binding.runtime(rig).tick()
    for market, series in live.items():
        bar = series[-1]
        rig.now[0] = bar.knowable_at.value_ns + 1_000_000
        quote(rig, market, bar, 3)
    binding.runtime(rig).tick()


def quote(rig: binding.Bound, market: str, bar: QuoteBar, offset: int) -> None:
    symbol = "EURUSD" if market == "fx.eurusd" else "XAUUSD"
    bid = (bar.bid.open, bar.bid.high, bar.bid.low, bar.bid.close)[offset]
    ask = (bar.ask.open, bar.ask.high, bar.ask.low, bar.ask.close)[offset]
    rig.fake.quote(symbol, bid, ask, rig.now[0] // 1_000_000)


def seen(unit: object, stream: str, market: str) -> list[int]:
    """The instants of the bars the unit's own window holds for ``(stream, market)``."""
    windows = cast("Mapping[tuple[str, str], Mapping[int, QuoteBar]]", getattr(unit, "windows"))
    return list(windows[(stream, market)])


def test_one_feed_hosts_1m_and_15m(tmp_path: Path) -> None:
    rig = binding.bound_rig(tmp_path)
    rig.door.bar_ns = MINUTE_NS
    binding.signed_in(rig)
    binding.bind(rig)
    for _ in range(4):
        binding.runtime(rig).tick()
    keep_warm(rig)
    rig.now[0] = live_start() - 1_000_000

    assert deploy(rig, deployment(rig, "m1", "op-1m"), "op-1m")["ok"] is True
    assert deploy(rig, deployment(rig, "m15", "op-15m"), "op-15m")["ok"] is True
    phases = {stream: settle(rig, f"dep-{stream}") for stream in MARKETS}
    prime(rig)
    play_minutes(rig)

    hosted = {stream: binding.runtime(rig).hosted[f"dep-{stream}"].unit for stream in MARKETS}
    assert phases == {"m1": Phase.TRADING, "m15": Phase.TRADING}
    assert all(unit is not None for unit in hosted.values())

    opened = live_start()
    assert seen(hosted["m1"], "m1", MARKETS["m1"])[-LIVE_BARS:] == [
        opened + (index + 1) * MINUTE_NS for index in range(LIVE_BARS)
    ], "the m1 unit steps on every one-minute bar of the hour"
    assert seen(hosted["m15"], "m15", MARKETS["m15"])[-4:] == [
        opened + (index + 1) * M15_NS for index in range(4)
    ], "the m15 unit steps on the four fifteen-minute bars of the same hour"
    binding.runtime(rig).stop()
