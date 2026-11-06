"""What he deployed runs: a reboot with no network, a new market after bind, a held market,
and one unlisted symbol that must not kill the account (C-12a to C-12d, W11).

Everything between the wire and the order path is the node's own code: the cTrader door, the
grant store, :class:`~qmn.venue.ctrader_account.CTraderVenue` and the runtime. cTrader is the
fake from ``test_app_binding``, and three of its subclasses answer one answer harsher: a refused
socket, a symbol list without a held market, and a netting account. No account and no network is
reached.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import cast

import test_app_binding as binding
import test_app_runtime as base
from qmb.host.unit_runner import load_unit_folder
from qmf.core import Instant, Result, TypedRefusal
from qml.protocol.unit import Account as UnitAccount
from qmn.app.runtime import Deployment, Phase, Runtime
from qmn.app.store import Json
from qmn.venue.conformance import submit_not_ready_refusal
from qmn.venue.ctrader_account import CTraderVenue, Wire
from test_app_binding import Bound, FakeCTrader, bound_rig, value

BAR = binding.BAR
ACCOUNT = binding.ACCOUNT
GOLD = "metal.xauusd"
"""The dummy's other market: not the self-test's, so a rig that keeps only EURUSD cannot see it."""


def runtime(rig: Bound) -> Runtime:
    return binding.runtime(rig)


def deploy(rig: Bound, document: dict[str, Json], op_id: str = "op-deploy-2") -> dict[str, Json]:
    return rig.node.call("deploy", {"op_id": op_id, "deployment": document})


def deployment_on(
    data: Path,
    deployment_id: str = "dep-1",
    market: str = "fx.eurusd",
    *,
    compiled: str | None = None,
) -> dict[str, Json]:
    """The dummy deployed on one market he chose, its files staged as the node link stages them."""
    document = base.deployment(data, deployment_id, compiled=compiled)
    document["markets"] = [
        {"market_id": market, "instrument": {"id": base.MARKETS[market], "version": 1}}
    ]
    return document


def keep_history(rig: Bound) -> None:
    """The recorded month before the live day, kept for warm-up as the node keeps its own."""
    feed = runtime(rig).venues[ACCOUNT].feed
    for at, market, bar in base.month().bars:
        if at < base.LIVE_FROM:
            feed.recording.keep(market, bar)


def settled(rig: Bound, deployment_id: str = "dep-1") -> str:
    """Tick until the deployment stops compiling and stops waiting for its account's session."""
    rt = runtime(rig)
    deadline = time.monotonic() + 180
    while True:
        rt.tick()
        hosted = rt.hosted.get(deployment_id)
        if hosted is not None and hosted.phase not in (Phase.COMPILING, Phase.WAITING):
            return hosted.phase.value
        assert time.monotonic() < deadline, "the deployment neither settled nor refused"
        time.sleep(0.02)


def compiled(rig: Bound, deployment_id: str = "dep-1") -> str:
    """Tick until the deployment's compile is done; answers the phase it then reads."""
    rt = runtime(rig)
    deadline = time.monotonic() + 180
    while True:
        rt.tick()
        hosted = rt.hosted.get(deployment_id)
        if hosted is not None and hosted.phase is not Phase.COMPILING:
            return hosted.phase.value
        assert time.monotonic() < deadline, "the compile did not finish"
        time.sleep(0.02)


def play_until_order(rig: Bound, until: int) -> int:
    """Play the recorded days a bar at a time until the node sends its first entry."""
    at = base.LIVE_FROM
    while "ProtoOANewOrderReq" not in rig.fake.requests():
        assert at < until, "the dummy sent no entry"
        binding.play_spots(rig, at, at + BAR)
        at += BAR
    return at


def xauusd_pro_record() -> dict[str, object]:
    """The gold record under the symbol a broker renames it to, which the fake does not list."""
    record = cast(
        "dict[str, object]", json.loads((base.RECORDS / "xauusd.json").read_text("utf-8"))
    )
    record["symbol"] = "XAUUSD.pro"
    return record


def rogue_document(data: Path, deployment_id: str = "dep-2") -> dict[str, Json]:
    """A deployment whose unit names gold at ``XAUUSD.pro``, which the broker does not list,
    and which chooses that market."""
    document = base.deployment(data, deployment_id)
    unit = cast("dict[str, object]", json.loads(json.dumps(document["unit_document"])))
    for market in cast("list[dict[str, object]]", unit["markets"]):
        if market["market_id"] == GOLD:
            market["market_id"] = "metal.gold2"
            cast("dict[str, object]", market["instrument_ref"])["symbol"] = "XAUUSD.pro"
    document["unit_document"] = cast("Json", unit)
    document["markets"] = [
        {"market_id": "metal.gold2", "instrument": {"id": "gold2", "version": 1}}
    ]
    document["snapshots"] = [
        *cast("list[Json]", document["snapshots"]),
        cast("Json", xauusd_pro_record()),
    ]
    return document


def shown(rig: Bound) -> dict[str, dict[str, Json]]:
    rows = cast("list[dict[str, Json]]", value(rig.node.call("deployments", {})))
    return {cast(str, row["deployment_id"]): row for row in rows}


def open_positions(rig: Bound, deployment_id: str = "dep-1") -> int:
    unit = runtime(rig).hosted[deployment_id].unit
    assert unit is not None
    return len(unit.venue_open())


def equity(rig: Bound, deployment_id: str = "dep-1") -> Decimal:
    unit = runtime(rig).hosted[deployment_id].unit
    assert unit is not None and unit.handler is not None
    account = unit.handler.read_surfaces()["account"].at(Instant(base.LIVE_FROM))
    return cast("UnitAccount", account).equity


def subscribed(rig: Bound) -> list[object]:
    return [
        body.get("symbolId")
        for name, body in rig.fake.received
        if name == "ProtoOASubscribeSpotsReq"
    ]


@dataclass
class Flaky(FakeCTrader):
    """cTrader refuses the next sockets while the internet is down."""

    down: bool = False

    def connect(self) -> Result[Wire]:
        if self.down:
            self.opened += 1
            return submit_not_ready_refusal()
        return super().connect()


@dataclass
class Forgetting(FakeCTrader):
    """cTrader answers a reconnect without one market's facts, or without the market itself."""

    forget: str = "XAUUSD"
    unlist: bool = False

    def _on_ProtoOASymbolsListReq(self, msg_id: str, _: dict[str, object]) -> None:
        listed = [
            {"symbolId": ident, "symbolName": name, "enabled": True}
            for name, (ident, *_rest) in self.SYMBOLS.items()
            if not (self.unlist and name == self.forget)
        ]
        self._say(
            "ProtoOASymbolsListRes",
            {"ctidTraderAccountId": binding.CTID, "symbol": listed},
            msg_id,
        )

    def _on_ProtoOASymbolByIdReq(self, msg_id: str, body: dict[str, object]) -> None:
        wanted = {int(str(item)) for item in cast("list[object]", body.get("symbolId", []))}
        symbols = [
            {
                "symbolId": ident,
                "digits": digits,
                "pipPosition": pip,
                "lotSize": lot,
                "stepVolume": lot // 100,
                "minVolume": lot // 100,
            }
            for name, (ident, digits, pip, lot) in self.SYMBOLS.items()
            if ident in wanted and (self.unlist or name != self.forget)
        ]
        self._say(
            "ProtoOASymbolByIdRes", {"ctidTraderAccountId": binding.CTID, "symbol": symbols}, msg_id
        )


@dataclass
class Netting(FakeCTrader):
    """cTrader states a netting account: one position per symbol, so a second unit's cancels."""

    def _on_ProtoOATraderReq(self, msg_id: str, _: dict[str, object]) -> None:
        self._say(
            "ProtoOATraderRes",
            {
                "ctidTraderAccountId": binding.CTID,
                "trader": {
                    "ctidTraderAccountId": binding.CTID,
                    "balance": 1_000_000,
                    "depositAssetId": 1,
                    "moneyDigits": 2,
                    "accountType": "NETTED",
                },
            },
            msg_id,
        )


def test_a_reboot_with_no_network_waits_then_trades_at_the_real_balance(
    tmp_path: Path,
) -> None:
    fake = Flaky(binding.codec())
    rig = bound_rig(tmp_path, broker=fake)
    binding.signed_in(rig)
    binding.bind(rig)
    binding.deploy_dummy(rig)
    runtime(rig).stop()

    fake.down = True
    again = bound_rig(tmp_path, grant=rig.grants.held, broker=fake, at=rig.now[0])
    keep_history(again)
    rt = runtime(again)
    binding.compiled(rt)
    waiting = rt.hosted["dep-1"]

    assert (waiting.phase.value, waiting.detail, waiting.unit) == (
        "waiting",
        "waiting for its account's session",
        None,
    )

    fake.down = False
    binding.tick_quotes(again, 3)
    assert waiting.phase.value == "trading"
    assert equity(again) == Decimal("10000.00")

    binding.play_spots(again, base.LIVE_FROM, base.LIVE_FROM + 2 * base.DAY)

    assert (waiting.phase.value, waiting.unit is not None) == ("trading", True)
    assert fake.requests().count("ProtoOANewOrderReq") == 2
    rt.stop()


def test_a_new_market_after_bind_gets_its_bars_with_a_position_held(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)
    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    at = play_until_order(rig, base.month().bars[-1][0])
    binding.play_spots(rig, at, at + BAR)
    assert open_positions(rig) == 1
    assert len(rig.fake.held) == 1
    before = subscribed(rig)

    gold = deployment_on(rig.data, "dep-2", GOLD)
    assert value(deploy(rig, gold, "op-deploy-2")) == {
        "deployment_id": "dep-2",
        "state": "accepted",
    }
    assert settled(rig, "dep-2") in ("warming up", "trading")
    binding.play_spots(rig, at + BAR, at + 5 * BAR)

    rt = runtime(rig)
    received = [
        bar
        for bar in rt.venues[ACCOUNT].feed.recording.recent(GOLD, 10_000)
        if bar.knowable_at.value_ns >= at
    ]
    assert before == [["1"]]
    assert subscribed(rig)[-1] == ["1", "41"]
    assert len(received) >= 2
    assert rt.hosted["dep-2"].phase.value == "trading"
    assert (open_positions(rig), len(rig.fake.held)) == (1, 1)
    assert binding.node_rows(rig, "reconcile")[-1]["why"] == "reconnect"
    rt.stop()


def test_red_closes_an_orphan_on_a_market_other_than_the_self_tests(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)
    deploy(rig, deployment_on(rig.data, "dep-1", GOLD), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    at = play_until_order(rig, base.month().bars[-1][0])
    binding.play_spots(rig, at, at + BAR)
    assert len(rig.fake.held) == 1

    deploy(rig, rogue_document(rig.data), "op-deploy-2")
    runtime(rig).stop()

    again = bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    rt = runtime(again)

    def will_not_compile(_deployment: Deployment, _folder: Path) -> str:
        return "the unit did not compile: a block changed"

    rt.compile = will_not_compile
    binding.tick_quotes(again, 5)
    assert [row["state"] for row in shown(again).values()] == ["refused", "refused"]

    again.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    binding.tick_quotes(again, 3)

    assert list(rig.fake.held) == []
    assert [row["positions_closed"] for row in binding.node_rows(again, "kill_level")] == [1]
    assert len(binding.closes(again)) == 1
    rt.stop()


def test_a_held_market_keeps_its_facts_and_its_position(tmp_path: Path) -> None:
    fake = Forgetting(binding.codec())
    rig = bound_rig(tmp_path, broker=fake)
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)
    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    at = play_until_order(rig, base.month().bars[-1][0])
    binding.play_spots(rig, at, at + BAR)
    ((_, held),) = rig.fake.held.items()
    assert held.stop is not None
    broker_stop = held.stop

    rt = runtime(rig)
    venue = rt.venues[ACCOUNT]
    client = cast("CTraderVenue", venue.client)
    alarms = len(rt.alarms)
    name = binding.sent_entries(rig)[0]

    def reconnect(why: str) -> None:
        venue.feed.drop(why)
        binding.tick_quotes(rig, 3)
        read = client.read_back()
        assert not isinstance(read, TypedRefusal), read
        assert venue.feed.ready
        assert client.stop_of(name) == broker_stop
        assert client.closed(name) is None
        assert len(read.value.positions) == 1
        assert len(rt.alarms) == alarms

    fake.unlist = False
    reconnect("a reconnect without the held market's facts")

    fake.unlist = True
    reconnect("a reconnect that no longer lists the held market")

    client.markets.pop("fx.eurusd", None)
    reconnect("the held market left the session's list")

    assert open_positions(rig) == 1
    rt.stop()
    rt.stop()


def test_an_unlisted_symbol_is_refused_by_name_and_the_account_keeps_trading(
    tmp_path: Path,
) -> None:
    rig = bound_rig(tmp_path)
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)
    deploy(rig, deployment_on(rig.data, "dep-1", GOLD), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    at = play_until_order(rig, base.month().bars[-1][0])
    binding.play_spots(rig, at, at + BAR)
    assert len(rig.fake.held) == 1

    rogue = rogue_document(rig.data)
    tested = compiled_fingerprint(
        cast("dict[str, object]", rogue["unit_document"]), {"metal.gold2": xauusd_pro_record()}
    )
    rogue["compiled_fingerprint"] = tested
    rogue["g_record"] = {
        **cast("dict[str, Json]", rogue["g_record"]),
        "compiled_fingerprint": tested,
    }
    deploy(rig, rogue, "op-deploy-2")
    runtime(rig).stop()

    again = bound_rig(tmp_path, grant=rig.grants.held, broker=rig.fake, at=rig.now[0])
    rt = runtime(again)
    assert settled(again, "dep-2") == "refused"
    refused = shown(again)["dep-2"]
    row = binding.ctrader_row(again)

    assert (refused["state"], refused["detail"]) == (
        "refused",
        "the account does not list XAUUSD.pro",
    )
    assert (row["session"], row["reason"]) == ("ready", "ready")
    assert shown(again)["dep-1"]["state"] in ("warming up", "trading")

    again.node.call("kill", {"op_id": "op-kill", "level": "RED", "scope": "all"})
    binding.tick_quotes(again, 3)

    assert list(rig.fake.held) == []
    assert len(binding.closes(again)) == 1
    rt.stop()


def test_a_second_unit_on_a_netting_symbol_is_refused(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path, broker=Netting(binding.codec()))
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)

    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    deploy(rig, deployment_on(rig.data, "dep-2", "fx.eurusd"), "op-deploy-2")
    assert settled(rig, "dep-2") == "refused"

    refused = shown(rig)["dep-2"]
    assert (refused["state"], refused["detail"]) == (
        "refused",
        "another unit already trades fx.eurusd on this netting account",
    )
    assert shown(rig)["dep-1"]["state"] in ("warming up", "trading")
    runtime(rig).stop()


def test_a_withdrawn_flat_unit_no_longer_blocks_its_market(tmp_path: Path) -> None:
    """A withdrawn and flat unit trades nothing from then on, so its market must come back to
    his replacement deployment instead of being held by a unit that only still has the object."""
    rig = bound_rig(tmp_path, broker=Netting(binding.codec()))
    binding.signed_in(rig)
    binding.bind(rig)
    keep_history(rig)
    binding.tick_quotes(rig)

    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert settled(rig) in ("warming up", "trading")
    assert open_positions(rig) == 0

    gone = value(rig.node.call("withdraw", {"op_id": "op-withdraw-1", "deployment_id": "dep-1"}))
    assert gone["state"] == "accepted"

    rt = runtime(rig)
    rt.tick()
    kept = rt.hosted["dep-1"]
    assert (kept.phase.value, kept.detail) == ("stopped", "withdrawn and flat")
    assert kept.unit is not None
    assert shown(rig)["dep-1"]["state"] == "withdrawing"

    deploy(rig, deployment_on(rig.data, "dep-2", "fx.eurusd"), "op-deploy-2")
    assert settled(rig, "dep-2") in ("warming up", "trading")
    assert shown(rig)["dep-2"]["state"] == "trading"
    rt.stop()


def test_a_deploy_before_bind_warms_once_bound(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    binding.signed_in(rig)

    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert compiled(rig) == "waiting"
    waiting = runtime(rig).hosted["dep-1"]
    assert (waiting.phase.value, waiting.detail, waiting.unit) == (
        "waiting",
        "no venue binding holds account demo-1",
        None,
    )

    binding.bind(rig)
    binding.tick_quotes(rig, 5)

    assert (waiting.phase.value, waiting.unit is not None) == ("warming up", True)
    runtime(rig).stop()


def test_a_five_minute_unit_is_refused_by_name(tmp_path: Path) -> None:
    rig = bound_rig(tmp_path)
    binding.signed_in(rig)
    rig.door.bar_ns = 300_000_000_000
    binding.bind(rig)
    binding.tick_quotes(rig)

    deploy(rig, deployment_on(rig.data, "dep-1", "fx.eurusd"), "op-deploy-1")
    assert settled(rig) == "refused"

    refused = shown(rig)["dep-1"]
    assert (refused["state"], refused["detail"]) == (
        "refused",
        "the unit reads m15 bars and this account's feed builds 5-minute bars",
    )
    runtime(rig).stop()


def faster_document() -> dict[str, object]:
    """The dummy with its one calibrated number moving after every closed trade, so a test can
    drive a real calibration instead of the twenty trades the template waits for."""
    document = base.dummy_document()
    numbers = cast("dict[str, object]", document["numbers"])
    strength = cast("dict[str, object]", numbers["min_trend_strength"])
    strength["motion"] = {
        "mode": "shrink_from_own_trades",
        "source": "own_record",
        "cadence": {"every_closed_trades": 1},
        "min_count": 1,
        "shrink_k": 0,
        "step_limit": 1,
        "rule": "trend-floor-from-record@1",
        "rule_params": {"buckets": "5"},
    }
    return document


def compiled_fingerprint(
    document: dict[str, object], extra: Mapping[str, dict[str, object]] | None = None
) -> str:
    """A unit document's compiled fingerprint, read from a real compile of its own folder.
    ``extra`` holds the instrument record of each market the standard fixtures do not cover."""
    root = Path(tempfile.mkdtemp(prefix="r22-unit-"))
    try:
        folder = root / "run"
        (folder / "records").mkdir(parents=True)
        (folder / "unit.json").write_text(json.dumps(document), "utf-8")
        for block in (p for p in base.STDLIB.iterdir() if (p / "1" / "block.py").is_file()):
            pin = folder / "blocks" / f"{block.name}@1"
            pin.mkdir(parents=True)
            for name in ("block.py", "entry.json"):
                shutil.copyfile(block / "1" / name, pin / name)
        for market, symbol in base.MARKETS.items():
            shutil.copyfile(base.RECORDS / f"{symbol}.json", folder / "records" / f"{market}.json")
            (folder / "bars" / market).mkdir(parents=True)
            for side in ("bid", "ask"):
                shutil.copyfile(
                    base.SLICES / f"synthetic-{symbol}-m15-{side}-2025-03-01-2025-04-01.csv",
                    folder / "bars" / market / f"{side}.csv",
                )
        for market, record in (extra or {}).items():
            (folder / "records" / f"{market}.json").write_text(json.dumps(record), "utf-8")
            (folder / "bars" / market).mkdir(parents=True)
            for side in ("bid", "ask"):
                shutil.copyfile(
                    base.SLICES / f"synthetic-xauusd-m15-{side}-2025-03-01-2025-04-01.csv",
                    folder / "bars" / market / f"{side}.csv",
                )
        loaded = load_unit_folder(folder)
        assert not isinstance(loaded, TypedRefusal), loaded
        return loaded.value.compiled.compiled_fingerprint.value
    finally:
        shutil.rmtree(root, ignore_errors=True)


@cache
def faster_fingerprint() -> str:
    """The compiled fingerprint of ``faster_document``, read once for the file."""
    return compiled_fingerprint(faster_document())


def test_a_restart_restores_a_moved_number_or_writes_its_cold_reason(tmp_path: Path) -> None:
    node = base.rig(tmp_path)
    document = base.deployment(node.data, compiled=faster_fingerprint())
    document["unit_document"] = cast("Json", faster_document())
    base.deploy(node, document)
    assert base.settle(node) == "trading"
    base.play(node, base.LIVE_FROM + 2 * base.DAY)

    unit = node.runtime.hosted["dep-1"].unit
    assert unit is not None
    snapshot = node.data / "deployments" / "dep-1" / "snapshot.json"
    saved = cast("dict[str, object]", json.loads(snapshot.read_text("utf-8")))
    slow = cast("dict[str, dict[str, object]]", saved["slow"])
    assert slow["min_trend_strength"]["value"] == "0.0002"
    node.runtime.stop()

    again = base.rig(tmp_path)
    base.settle(again)
    restored = again.runtime.hosted["dep-1"].unit
    assert restored is not None and restored.hosted_unit is not None
    assert dict(restored.hosted_unit.calibrated_values) == {"min_trend_strength": Decimal("0.0002")}
    again.runtime.stop()
