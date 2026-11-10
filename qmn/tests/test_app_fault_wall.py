"""One unit's fault costs that unit, never another unit's drive and never an exit (AD-23).

The node is the real :class:`~qmn.app.runtime.Runtime` on the fake cTrader broker: four deployments
hosted on one account in the order ``dep-1`` to ``dep-4``, every one of them holding a short from
the same first signal. A logic slot raises on ``dep-1``, a sizer raises on ``dep-3`` and ``dep-3``'s
per-bar exit raises too, so the unit behind both of them must keep being driven, keep its own exits
running and land one ``unit_fault`` row per root-cause key. Every drive is counted at
``_drive_one``, the seam a raise used to stop at, and each bar is stepped through the inner
supervisor (``Runtime.step``) so a heal is what a counting test can see.

The second test is the last fall-through: with every per-bar exit raising, the node's
``close_scope`` port closes the position and the close it sends says why.

The third hosts the shipped two-market dummy, holds one ``metal.xauusd`` position and steps the
unit once per market's bar, so a step of ``fx.eurusd`` alone falls between the failing bars of the
position's own market.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from itertools import groupby
from pathlib import Path
from typing import cast

import test_app_binding as b
import test_app_runtime as base
from qmb.host.unit_handler import UnitSliceHandler
from qmf.core.chrono import Instant
from qmf.core.refusal import is_refusal
from qml.blocks.api import EntryOrder, Signal
from qml.compile import ExitUse
from qml.protocol.exits import ExitSlot, ExitStack
from qml.protocol.unit import HostedUnit, OwnPosition, QuoteBar
from qml.unit.model import Side
from qmn.app.feed_keeper import Bar
from qmn.app.runtime import NodeUnit, Phase, Runtime, _Hosted

BAR = b.BAR
DEPLOYMENTS = ("dep-1", "dep-2", "dep-3", "dep-4")
WINDOW_BARS = 12
MARKET = "fx.eurusd"
METAL = "metal.xauusd"
"""The second market the shipped dummy names, so a step can be its bar alone."""
EXIT_FAULT_BARS = 3
"""The pinned ``exit_fault_bars``: three bars with no exit able to run close the position."""
EXIT_FAULT = "exit_fault"
"""The pinned reason the last fall-through's close carries (AD-13)."""
TARGET = Decimal("1.06853")
"""The level ``dep-2``'s held short is aimed at, a few pips under its 1.06858 entry, so a recorded
bar's low reaches the node's protective target and the node closes it (AD-13's target path)."""


class _Raising:
    """A shipped block with a bug: every call raises."""

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        raise RuntimeError("the block's own bug")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Answering:
    """A block bound to one fixed answer, so an exit fires on the bar the test wants."""

    def __init__(self, answer: object) -> None:
        self._answer = answer

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        return self._answer

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Ordering:
    """A block that names a market entry order whenever it is asked."""

    @property
    def warm_up_bars(self) -> int:
        return 0

    @property
    def state_bound(self) -> int:
        return 0

    def retained(self) -> int:
        return 0

    def update(self, evidence: Mapping[str, object]) -> object:
        del evidence
        return EntryOrder(kind="market", at="next_open")

    def export_state(self) -> Mapping[str, object]:
        return {}

    def import_state(self, state: Mapping[str, object]) -> None:
        del state


class _Port:
    """A host's last fall-through, recording every ask in the order it came."""

    def __init__(self) -> None:
        self.asks: list[str] = []

    def close_scope(self, unit: object, why: str) -> None:
        del unit
        self.asks.append(why)


def four_units(root: Path) -> tuple[b.Bound, Runtime, int]:
    """Four copies of the dummy on the bound account, each in a short; the next bar's time."""
    rig = b.bound_rig(root)
    b.signed_in(rig)
    b.bind(rig)
    runtime = b.runtime(rig)
    feed = runtime.venues[b.ACCOUNT].feed
    for at, market, bar in base.month().bars:
        if at < base.LIVE_FROM:
            feed.recording.keep(market, bar)
    b.tick_quotes(rig)
    symbol = base.MARKETS[MARKET]
    for deployment_id in DEPLOYMENTS:
        document = base.deployment(rig.data, deployment_id)
        document["markets"] = [{"market_id": MARKET, "instrument": {"id": symbol, "version": 1}}]
        deployed = rig.node.call(
            "deploy", {"op_id": f"op-{deployment_id}", "deployment": document}
        )
        assert b.value(deployed)["state"] == "accepted", deployed
    settle(runtime)
    at = b.play_until_sent(rig)
    b.play_spots(rig, at, at + BAR)
    return rig, runtime, at + BAR


def settle(runtime: Runtime) -> None:
    """Tick until every deployment has compiled and started."""
    deadline = 900
    while True:
        runtime.tick()
        waiting = [
            deployment_id
            for deployment_id in DEPLOYMENTS
            if (hosted := runtime.hosted.get(deployment_id)) is None
            or hosted.phase in (Phase.COMPILING, Phase.WAITING)
            or hosted.unit is None
        ]
        if not waiting:
            return
        deadline -= 1
        assert deadline, f"the deployments did not compile: {waiting}"


def handler_of(runtime: Runtime, deployment_id: str) -> UnitSliceHandler:
    return cast("UnitSliceHandler", cast("NodeUnit", runtime.hosted[deployment_id].unit).handler)


def hosted_of(runtime: Runtime, deployment_id: str) -> HostedUnit:
    return cast("HostedUnit", handler_of(runtime, deployment_id)._unit)


def market_of(runtime: Runtime, deployment_id: str):  # noqa: ANN201 - the market is private
    return hosted_of(runtime, deployment_id)._core.markets[0]


def answer_every_exit(runtime: Runtime, deployment_id: str) -> None:
    """Make each held position's per-bar exit answer "close it" on the next bar."""
    market = market_of(runtime, deployment_id)
    answer = _Answering(Signal(state=True, value=Decimal(3)))
    for position_id in list(market.timers):
        held = market.timers[position_id]
        market.timers[position_id] = ExitStack(
            held.side, tuple(ExitSlot(one.key, one.pin, answer) for one in held.slots)
        )


def force_short_entries(runtime: Runtime, deployment_id: str) -> None:
    """Hold the short side's slots on every bar, so the unit proposes whenever it is flat."""
    market = market_of(runtime, deployment_id)
    for key in ("short.trend", "short.strength", "short.rsi_cross"):
        market.instances[key] = _Answering(Signal(state=True, value=Decimal(1)))
    market.instances["short.next_open"] = _Ordering()


def raise_every_exit(runtime: Runtime, deployment_id: str) -> None:
    """Make each held position's per-bar exit raise, so no exit of that unit can run."""
    hosted = hosted_of(runtime, deployment_id)
    slots = tuple(
        ExitSlot(f"exit.{e.binding.name}", e.binding.pin, _Raising())
        for e in hosted._core.plan.exits
        if e.use is ExitUse.PER_BAR
    )
    market = market_of(runtime, deployment_id)
    for position_id in list(market.timers):
        market.timers[position_id] = ExitStack(market.timers[position_id].side, slots)
    hosted._core.timer = lambda side: ExitStack(side, slots)


def aim_at(runtime: Runtime, deployment_id: str, level: Decimal) -> None:
    """Aim the held position's protective target at ``level``, as the target block could have."""
    handler = handler_of(runtime, deployment_id)
    handler._held[MARKET] = replace(handler._held[MARKET], target=level)


def count_drives(runtime: Runtime) -> dict[str, int]:
    """Count every call to ``_drive_one``, the seam a raise used to stop at."""
    drives: dict[str, int] = {}
    real = runtime._drive_one

    def counted(hosted: _Hosted, bars: Sequence[Bar], replay: bool = False) -> None:
        deployment_id = hosted.deployment.deployment_id
        drives[deployment_id] = drives.get(deployment_id, 0) + 1
        real(hosted, bars, replay=replay)

    runtime._drive_one = counted
    return drives


def play_supervised(rig: b.Bound, runtime: Runtime, start: int, bars: int) -> None:
    """Play ``bars`` recorded bars, each through ``Runtime.step``, the inner supervisor."""
    live = [
        item
        for item in base.month().bars
        if item[1] == MARKET and start <= item[0] < start + bars * BAR
    ]
    assert len(live) == bars, f"the recording holds {len(live)} bars from {start}"
    for at, group in groupby(live, key=lambda item: item[0]):
        closed = list(group)
        for offset in range(4):
            rig.now[0] = at - BAR + (offset + 1) * 1_000_000
            for _, market, bar in closed:
                symbol = "EURUSD" if market == "fx.eurusd" else "XAUUSD"
                bid = (bar.bid.open, bar.bid.high, bar.bid.low, bar.bid.close)[offset]
                ask = (bar.ask.open, bar.ask.high, bar.ask.low, bar.ask.close)[offset]
                rig.fake.quote(symbol, bid, ask, rig.now[0] // 1_000_000)
            if offset == 0:
                runtime.step()


def unit_rows(rig: b.Bound, kind: str, deployment_id: str | None = None) -> list[dict[str, object]]:
    """The unit journal's rows of one kind, for one deployment when it is named."""
    answer = rig.node.call("journal_tail", {"streams": ["unit"]})
    assert answer["ok"] is True, answer
    rows = cast("list[dict[str, object]]", cast("dict[str, object]", answer["value"])["rows"])
    return [
        cast("dict[str, object]", row["body"])
        for row in rows
        if row["kind"] == kind
        and (deployment_id is None or row.get("run_id") == deployment_id)
    ]


def node_orders(rig: b.Bound) -> list[dict[str, object]]:
    answer = rig.node.call("journal_tail", {"streams": ["node"]})
    assert answer["ok"] is True, answer
    rows = cast("list[dict[str, object]]", cast("dict[str, object]", answer["value"])["rows"])
    return [
        cast("dict[str, object]", row["body"]) for row in rows if row["kind"] == "order"
    ]


def test_k9_2_one_units_raise_stops_no_exit_and_no_other_unit(tmp_path: Path) -> None:
    rig, runtime, at = four_units(tmp_path)

    market_of(runtime, "dep-1").instances["long.trend"] = _Raising()
    market_of(runtime, "dep-3").instances["sizer"] = _Raising()
    for deployment_id in ("dep-1", "dep-2", "dep-4"):
        answer_every_exit(runtime, deployment_id)
    aim_at(runtime, "dep-3", TARGET)
    force_short_entries(runtime, "dep-3")
    snapshot = runtime._write_snapshot

    def breaking(hosted: _Hosted) -> None:
        if hosted.deployment.deployment_id == "dep-1":
            raise RuntimeError("the unit's own state could not be written")
        snapshot(hosted)

    runtime._write_snapshot = breaking
    drives = count_drives(runtime)

    play_supervised(rig, runtime, at, WINDOW_BARS)

    heals = list(runtime.healer.heals)
    trades = {
        deployment_id: [
            (row["exit_kind"], row["side"]) for row in unit_rows(rig, "trade", deployment_id)
        ]
        for deployment_id in DEPLOYMENTS
    }
    taken = [
        row
        for row in unit_rows(rig, "signal", "dep-1")
        if row.get("outcome") == "taken"
        and row.get("binding") is not None
        and cast("int", row["instant"]) >= at
    ]
    faults = [(row["code"], row["root"]) for row in unit_rows(rig, "risk_event")]
    runtime.stop()

    assert drives == {deployment_id: WINDOW_BARS for deployment_id in DEPLOYMENTS}
    assert heals == []
    assert trades["dep-1"] == [("close", "short")], "its own time exit still fires"
    assert trades["dep-2"] == [("close", "short")], "the unit behind dep-1 still exits"
    assert trades["dep-3"] == [("target", "short")], "the node closed its target"
    assert trades["dep-4"] == [("close", "short")], "the unit behind both raisers still exits"
    assert taken == [], "dep-1 minted no entry after its slot started raising"
    assert sorted(faults) == [
        ("unit_fault", "ema@1"),
        ("unit_fault", "fixed-fraction-at-stop@2"),
        ("unit_fault", "host:RuntimeError"),
    ]


def test_close_scope_is_the_last_fall_through(tmp_path: Path) -> None:
    rig = b.bound_rig(tmp_path)
    b.signed_in(rig)
    b.bind(rig)
    runtime = b.deploy_dummy(rig)
    at = b.play_until_sent(rig)
    b.play_spots(rig, at, at + BAR)
    name = b.sent_entries(rig)[0]
    raise_every_exit(runtime, "dep-1")

    play_supervised(rig, runtime, at + BAR, EXIT_FAULT_BARS)

    closes = [row for row in node_orders(rig) if row["step"] == "close"]
    held = list(rig.fake.held)
    heals = list(runtime.healer.heals)
    runtime.stop()

    assert [(row["event_id"], row["why"]) for row in closes] == [
        (f"{name}/close-{EXIT_FAULT}", EXIT_FAULT)
    ]
    assert held == [], "the venue closed the position the port asked about"
    assert heals == []


def test_the_exit_fault_streak_survives_a_step_of_the_other_markets_bar(tmp_path: Path) -> None:
    """Three failing bars of one market still ask the port when the other market steps between.

    The shipped dummy names two markets and the node steps the unit once per closed-bar instant,
    so a step can carry the other market's bar alone. That step must leave the held position's
    streak alone: its third failing bar still asks ``close_scope`` for ``exit_fault``.
    """
    node = base.rig(tmp_path)
    base.deploy(node, base.deployment(node.data))
    assert base.settle(node) == "trading"
    runtime = node.runtime
    hosted = hosted_of(runtime, "dep-1")
    handler = handler_of(runtime, "dep-1")
    metal = [
        (bar.knowable_at.value_ns, bar)
        for _, market, bar in base.month().bars
        if market == METAL and bar.knowable_at.value_ns >= base.LIVE_FROM
    ]
    fx = [
        (bar.knowable_at.value_ns, bar)
        for _, market, bar in base.month().bars
        if market == MARKET and bar.knowable_at.value_ns >= base.LIVE_FROM
    ]
    entry = metal[0][1].bid.close
    position = OwnPosition(
        "metal-1",
        Side.SHORT,
        Decimal("0.50"),
        entry,
        hosted.compiled.logic_fingerprint,
        Instant(metal[0][0]),
    )
    adopted = handler.adopt(
        METAL,
        position,
        stop=entry + Decimal("10"),
        entry_stop=entry + Decimal("10"),
        target=None,
        decision_row_id="row-metal",
    )
    assert not is_refusal(adopted), adopted
    port = _Port()
    hosted.attach_port(port)
    metal_market = next(one for one in hosted._core.markets if one.market_id == METAL)

    def serve(market_id: str, bar: QuoteBar) -> None:
        handler._latest[(handler._stream, market_id)] = bar

    def step(at: int) -> None:
        answer = hosted.on_instant(Instant(at))
        assert not is_refusal(answer), answer

    serve(METAL, metal[0][1])
    step(metal[0][0])  # the first bar builds the per-bar exit's timer
    built = metal_market.timers[position.position_id]
    metal_market.timers[position.position_id] = ExitStack(
        built.side, tuple(ExitSlot(one.key, one.pin, _Raising()) for one in built.slots)
    )
    serve(METAL, metal[1][1])
    step(metal[1][0])
    serve(MARKET, fx[0][1])
    step(metal[1][0] + 1_000_000_000)  # only the other market's bar is new here
    serve(METAL, metal[2][1])
    step(metal[2][0])
    serve(MARKET, fx[1][1])
    step(metal[2][0] + 1_000_000_000)
    serve(METAL, metal[3][1])
    step(metal[3][0])

    asks = port.asks
    runtime.stop()

    assert asks == [EXIT_FAULT], "three failing bars in a row ask the port once"
