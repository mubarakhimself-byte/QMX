"""The cTrader demo probes (C-15, `EXTERNAL.md` section 2). Rehearsed now, run on demo at G-DEMO.

    uv run --no-sync python qmn/probes/ctrader_demo/run.py --rehearsal
    uv run --no-sync python qmn/probes/ctrader_demo/run.py --rehearsal --shared
    uv run --no-sync python qmn/probes/ctrader_demo/run.py --rehearsal --fault <mark>
    uv run --no-sync python qmn/probes/ctrader_demo/run.py --plan
    uv run --no-sync python qmn/probes/ctrader_demo/run.py --home <his QMX folder>   # after G-DEMO

Each mark is its own script beside this one and prints one PASS or FAIL line. The rehearsal runs the
real node code, its real cTrader codec and the harsher fake broker on a throwaway folder, so no
account and no network is reached. `--rehearsal` builds a fresh rig per mark; `--rehearsal --shared`
builds one rig and runs every mark over it, as the demo run has one account for all six, so there
the marks meet each other's positions. `--fault <mark>` runs the same crossing with that mark's
fault in: the fake answers worse and the mark must read FAIL.

The demo run reads the trading app's key and the node's own grant from the node's stores, never
prints either, and asks cTrader's demo broker what only it can answer. It sends demo orders and
closes what it opened. It waits for his sign-in (G-DEMO).
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Final, cast

from qmf.core import (
    Account,
    AccountRole,
    PriceDelta,
    Quantity,
    TypedRefusal,
    VenueId,
    is_refusal,
)
from qmf.venue.commands import Command, OrderParameters, OrderType, TimeInForce
from qml.unit.model import Side
from qmn.app.grants import Grant, Grants, Registration, TokenEndpoint, grant_store, registration
from qmn.app.runtime import Ticket
from qmn.app.server import DEFINITIONS
from qmn.venue import order_tags
from qmn.venue.ctrader_account import DEMO_HOST, Codec, CTraderVenue, Frame, FramedWire

PROBES: Final = Path(__file__).resolve().parent
sys.path.insert(0, str(PROBES))

import attribution as attribution_mark  # noqa: E402
import label_survives  # noqa: E402
import network_cut  # noqa: E402
import partial_keeps_label  # noqa: E402
import refresh  # noqa: E402
import repeated_client_order_id  # noqa: E402

TAG: Final = "probe24x"
"""This probe's own node tag, in the node's eight-letter base32 shape, so its orders never read as
the practice node's."""
LABEL: Final = f"qmx:{TAG}:demo-probe"
"""The probe's label, and the head of each mark's own: a mark adds its name, so a count, a close
and a part close see only the position that mark opened."""
MARKET: Final = "fx.eurusd"
SYMBOL: Final = "EURUSD"
LOTS: Final = Decimal("0.01")
WHOLE: Final = 100_000
"""One 0.01 lot of EURUSD, in the venue's volume units."""
HALF: Final = 50_000
STOP_POINTS: Final = 500
DEMO_HOME: Final = "data/apps/trading-node/data"
PASSPORT: Final = "data/trading-node-passport.json"
KEYS: Final = "qmx/trading-node-keys"
BAR: Final = 900_000_000_000
FILL_QUESTION: Final = "whether a fill, a non-closing event, carries its stop and its clientMsgId"
PASSPORT_QUESTION: Final = "the six literal facts the node's passport holds"
MARK_MODULES: Final = (
    label_survives,
    partial_keeps_label,
    repeated_client_order_id,
    attribution_mark,
    network_cut,
    refresh,
)


def label_for(mark: str) -> str:
    """One mark's own label, so none of its counts or its closes reaches another mark's position."""
    return f"{LABEL}-{mark}"


def say(ok: bool, mark: str, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'} {mark}" + (f" ({detail})" if detail and not ok else ""))
    sys.stdout.flush()
    return ok


def reasons(done: Any) -> str:
    """A refusal's own words, for a line that has to say why."""
    context: Mapping[str, object] = getattr(done, "context", {})
    code = context.get("code")
    return f"{code}: {done}" if code else str(done)


def one_by_one(
    session: Any, chosen: Sequence[Any], cross: Callable[[Any, Any], tuple[bool, str]]
) -> int:
    """Run each mark on one session, in `MARK_MODULES` order, under its own label and closing what
    it opened before the next starts, so no mark counts or closes another mark's position."""
    failures = 0
    for module in chosen:
        session.label = label_for(module.MARK)
        session.begin()
        try:
            ok, said = cross(module, session)
        finally:
            left = session.release()
        failures += not say(ok, module.MARK, said)
        if left is not None:
            failures += not say(False, f"{module.MARK} left open", left)
    return failures


def _filled(one: Frame) -> bool:
    """A frame is the answer to one order: its fill, or the broker's refusal."""
    return one.name == "ProtoOAOrderErrorEvent" or (
        one.name == "ProtoOAExecutionEvent"
        and one.body.get("executionType") in {"ORDER_FILLED", "ORDER_PARTIAL_FILL"}
    )


def _spot(one: Frame) -> bool:
    return one.name == "ProtoOASpotEvent"


def _answered(one: Frame) -> bool:
    return one.name in {"ProtoOAExecutionEvent", "ProtoOAOrderErrorEvent", "ProtoOAErrorRes"}


def _observed(one: Frame) -> dict[str, object]:
    """What one order answer carries, field by field, so the demo run says what it saw and never
    what it expected."""
    body: Mapping[str, object] = one.body
    order = body.get("order")
    nested: Mapping[str, object] = (
        cast("Mapping[str, object]", order) if isinstance(order, dict) else {}
    )
    return {
        "event": one.name,
        "fields on the event": sorted(body),
        "fields on its order": sorted(nested),
        "stopLoss on the event": "stopLoss" in body,
        "stopLoss on its order": "stopLoss" in nested,
        "clientMsgId on the event": "clientMsgId" in body,
        "clientMsgId on its order": "clientMsgId" in nested,
    }


class Crossing:
    """One mark's crossing over a real cTrader session: the node's venue over the fake broker in a
    rehearsal, and the same venue over his demo account after G-DEMO."""

    venue: Any
    ctid: int
    label: str = LABEL
    observations: dict[str, object]

    def new_name(self, seed: str) -> str:
        return f"q{TAG}-{time.time_ns() // 1_000_000}-{seed}"[:36]

    def tick(self, ticks: int = 2) -> None:
        raise NotImplementedError

    def price(self, side: str = "buy") -> Decimal:
        raise NotImplementedError

    def read_back(self) -> Any:
        return self.venue.read_back()

    def symbols(self) -> Any:
        return self.venue.symbols[MARKET]

    def entry(self, client_order_id: str, *, label: str | None = None) -> Any:
        """One market order with its label and relative stop, through the node's order path."""
        symbol = self.symbols()
        gap = PriceDelta.try_create(STOP_POINTS, symbol.instrument, symbol.digits)
        size = Quantity.try_create(1, "lot", 2)
        tags = order_tags(client_order_id, self.label if label is None else label)
        if (
            isinstance(gap, TypedRefusal)
            or isinstance(size, TypedRefusal)
            or isinstance(tags, TypedRefusal)
        ):
            return next(built for built in (gap, size, tags) if isinstance(built, TypedRefusal))
        params = OrderParameters.try_create(
            OrderType.MARKET,
            TimeInForce.IMMEDIATE_OR_CANCEL,
            size.value,
            protective_stop_distance=gap.value,
            instrument=symbol.instrument,
            trade_side="buy",
        )
        if isinstance(params, TypedRefusal):
            return params
        command = Command.place_order(
            self.venue.account.venue, self.venue.account, "probe", 1, params.value
        )
        if isinstance(command, TypedRefusal):
            return command
        return self.venue.send(
            Ticket(command.value, MARKET, Side.LONG, self.price(), LOTS, LOTS, tags.value)
        )

    def positions(self) -> list[Any]:
        """The positions the node reads back from the broker."""
        read = self.read_back()
        if not hasattr(read, "value"):
            return []
        return list(read.value.positions)

    def broker_positions(self) -> list[tuple[str | None, Decimal, Decimal | None]]:
        """The broker's own rows: each open position's label, its size in lots and its stop."""
        raise NotImplementedError

    def refresh(self) -> tuple[bool, str]:
        """The TN-05 drill on this session's account: only a demo run has a store to refresh."""
        raise NotImplementedError

    def adopted(self, name: str) -> Any:
        """A second session over the same account, as the node's reconcile reads it after a
        restart: this session holds nothing yet, so it adopts the position by its opening order."""
        venue = CTraderVenue(
            account=self.venue.account,
            ctid=self.ctid,
            host=self.venue.host,
            markets=dict(self.venue.markets),
            codec=self.venue.codec,
            open_wire=self.venue.open_wire,
            credentials=self.venue.credentials,
            clock_ns=self.venue.clock_ns,
            steady_ns=self.venue.steady_ns,
            session_epoch=f"{self.venue.session_epoch}-read",
        )
        opened = venue.connect()
        if is_refusal(opened):
            return opened
        verified = venue.verify()
        if is_refusal(verified):
            return verified
        return venue.read_back()

    def order(self, client_order_id: str, *, volume: int = WHOLE) -> Any:
        """One market order down the wire, over the real codec, and its fill or refusal."""
        pushed = self.push_order(client_order_id, volume=volume)
        if pushed is None or is_refusal(pushed):
            return pushed
        api = self.venue.api
        if api is None:
            return None
        found = api.wait(_filled)
        answered = getattr(found, "value", None)
        if answered is not None and not is_refusal(found):
            self.observations[FILL_QUESTION] = _observed(answered)
        return found

    def push_order(self, client_order_id: str, *, volume: int = WHOLE) -> Any:
        """One market order down the wire, over the real codec, without waiting for the answer."""
        api = self.venue.api
        if api is None:
            return None
        frame = self.venue.codec.encode(
            "ProtoOANewOrderReq",
            {
                "ctidTraderAccountId": str(self.ctid),
                "symbolId": str(self.symbols().symbol_id),
                "orderType": "MARKET",
                "tradeSide": "BUY",
                "volume": str(volume),
                "relativeStopLoss": str(STOP_POINTS),
                "label": self.label,
                "clientOrderId": client_order_id,
            },
            "",
        )
        if isinstance(frame, TypedRefusal):
            return frame
        return api.push(frame.value)

    def duplicate(self, client_order_id: str) -> str:
        """Send one client order id twice and say what the broker did with the second."""
        first = self.order(client_order_id)
        if first is None:
            return "no answer to the first order"
        if is_refusal(first):
            return f"no answer to the first order ({reasons(first)})"
        opened = first.value
        if opened is None or opened.name == "ProtoOAOrderErrorEvent":
            return "no answer to the first order"
        second = self.order(client_order_id)
        if second is None:
            return "no answer to the second order"
        if is_refusal(second):
            return f"the wire refused the second order ({reasons(second)})"
        answer = second.value
        if answer is None:
            return "no answer to the second order"
        if answer.name == "ProtoOAOrderErrorEvent":
            return f"refused by the broker ({answer.body.get('errorCode')})"
        return "accepted, and the broker filled a second order"

    def close_part(self, position: str, *, volume: int = HALF) -> Any:
        """Ask the broker to close part of a position, over the real codec, then read it back."""
        position_id = self.position_id(position)
        if position_id is None:
            return None
        pushed = self.close_at(position_id, volume)
        if pushed is None or is_refusal(pushed):
            return pushed
        return self.read_back()

    def close_at(self, position_id: int, volume: int) -> Any:
        """Close a position by the broker's id and volume, over the real codec."""
        api = self.venue.api
        if api is None:
            return None
        frame = self.venue.codec.encode(
            "ProtoOAClosePositionReq",
            {
                "ctidTraderAccountId": str(self.ctid),
                "positionId": str(position_id),
                "volume": str(volume),
            },
            "",
        )
        if is_refusal(frame):
            return frame
        return api.push(frame.value)

    def begin(self) -> None:
        """A mark starts on this session, so a session shared with the marks before it counts only
        this mark's own orders from here."""

    def mine(self) -> list[tuple[int, int]] | None:
        """Each position carrying this mark's own label, as the broker's id and volume; None when
        the session could not be read."""
        raise NotImplementedError

    def release(self) -> str | None:
        """Close what this mark opened, so the next mark starts on an account without it. None when
        nothing of this mark's is left, else what is, so a run that could not clean up after itself
        never reads green."""
        open_now = self.mine()
        if open_now is None:
            return "the session could not be read back, so nothing of this mark's was closed"
        for position_id, volume in open_now:
            self.close_at(position_id, volume)
        self.read_back()
        left = self.mine()
        if left is None:
            return f"the session could not be read back after the close, so {self.label} is unknown"
        if left:
            return f"{len(left)} position(s) still carry {self.label!r} after the close"
        return None

    def position_id(self, position: str) -> int | None:
        """The broker's id for the node's name of a position."""
        raise NotImplementedError

    def held(self) -> list[Any]:
        raise NotImplementedError


@dataclass
class Rehearsal(Crossing):
    """The real node over the fake broker, on a throwaway folder."""

    rig: Any
    venue: Any
    fake: Any
    fault: bool = False
    observations: dict[str, object] = field(default_factory=dict[str, object])
    ctid: int = 4401
    heard: int = 0
    """The order requests the broker had already heard when this mark started."""

    def tick(self, ticks: int = 2) -> None:
        binding: Any = cast(Any, importlib.import_module("test_app_binding"))
        binding.tick_quotes(self.rig, ticks)

    def price(self, side: str = "buy") -> Decimal:
        bid, ask = self.fake.quotes[self.symbols().symbol_id]
        return ask if side == "buy" else bid

    def held(self) -> list[Any]:
        return list(self.fake.held.values())

    def broker_positions(self) -> list[tuple[str | None, Decimal, Decimal | None]]:
        lot = Decimal(self.symbols().lot_size)
        return [
            (one.label or None, Decimal(one.volume) / lot, one.stop)
            for one in self.fake.held.values()
        ]

    def position_id(self, position: str) -> int | None:
        return next(
            (int(one.position_id) for one in self.held() if one.client_order_id == position), None
        )

    def entries(self) -> int:
        """The order requests this mark sent: those the broker heard since it started, so a
        session shared with the marks before it counts its own and not theirs."""
        return self.fake.requests().count("ProtoOANewOrderReq") - self.heard

    def begin(self) -> None:
        self.heard = self.fake.requests().count("ProtoOANewOrderReq")

    def mine(self) -> list[tuple[int, int]]:
        return [
            (int(one.position_id), int(one.volume))
            for one in self.fake.held.values()
            if one.label == self.label
        ]

    def heal(self) -> None:
        """Reopen the session as the node's feed does on its next tick, with no quotes: the recorded
        bars a spot play would send could fire the stop the probe is watching."""
        self.venue.connect()
        self.venue.verify()


@dataclass
class Demo(Crossing):
    """The node's venue over his demo account, from the node's stores."""

    venue: Any
    ctid: int
    grant: Any
    store: Any
    registration: Registration
    holder: dict[str, Any]
    observations: dict[str, object] = field(default_factory=dict[str, object])
    _quotes: dict[str, tuple[Decimal, Decimal]] = field(
        default_factory=dict[str, tuple[Decimal, Decimal]]
    )
    closed_ids: list[int] = field(default_factory=list[int])
    """The broker's ids for the positions this run closed, newest last."""

    def tick(self, ticks: int = 2) -> None:
        time.sleep(0.5)

    def price(self, side: str = "buy") -> Decimal:
        bid, ask = self.spot()
        return ask if side == "buy" else bid

    def spot(self) -> tuple[Decimal, Decimal]:
        if MARKET in self._quotes:
            return self._quotes[MARKET]
        api = self.venue.api
        if api is None:
            raise SystemExit("FAIL setup: the demo session is not open")
        asked = api.ask(
            "ProtoOASubscribeSpotsReq",
            {
                "ctidTraderAccountId": str(self.ctid),
                "symbolId": [self.symbols().symbol_id],
                "subscribeToSpotTimestamp": True,
            },
        )
        if is_refusal(asked):
            raise SystemExit(
                f"FAIL setup: cTrader refused the spot subscription ({reasons(asked)})"
            )
        found = api.wait(_spot)
        if is_refusal(found) or found.value is None:
            raise SystemExit("FAIL setup: cTrader sent no spot")
        body = found.value.body
        bid = Decimal(str(body.get("bid"))).scaleb(-5).quantize(Decimal("0.00001"))
        ask = Decimal(str(body.get("ask"))).scaleb(-5).quantize(Decimal("0.00001"))
        self._quotes[MARKET] = (bid, ask)
        return bid, ask

    def held(self) -> list[Any]:
        return self.positions()

    def broker_positions(self) -> list[tuple[str | None, Decimal, Decimal | None]]:
        return [(one.label or None, one.quantity, one.stop) for one in self.positions()]

    def position_id(self, position: str) -> int | None:
        api = self.venue.api
        if api is None:
            return None
        listed = api.ask("ProtoOAReconcileReq", {"ctidTraderAccountId": str(self.ctid)})
        if is_refusal(listed):
            return None
        for row in cast("list[Any]", listed.value.body.get("position") or []):
            trade = cast("dict[str, object]", cast("dict[str, object]", row).get("tradeData") or {})
            if trade.get("label") == self.label:
                return int(str(cast("dict[str, object]", row).get("positionId")))
        return None

    def mine(self) -> list[tuple[int, int]] | None:
        api = self.venue.api
        if api is None:
            return None
        listed = api.ask("ProtoOAReconcileReq", {"ctidTraderAccountId": str(self.ctid)})
        if is_refusal(listed):
            return None
        found: dict[int, int] = {}
        for row in cast("list[Any]", listed.value.body.get("position") or []):
            held = cast("dict[str, object]", row)
            trade = cast("dict[str, object]", held.get("tradeData") or {})
            if trade.get("label") == self.label:
                found[int(str(held.get("positionId")))] = int(str(trade.get("volume") or 0))
        return list(found.items())

    def close_at(self, position_id: int, volume: int) -> Any:
        pushed = super().close_at(position_id, volume)
        if pushed is not None and not is_refusal(pushed):
            self.closed_ids.append(position_id)
        return pushed

    def close(self) -> None:
        self.venue.close()

    def gone_close(self) -> str:
        """What cTrader answers a close on a position it no longer holds."""
        api = self.venue.api
        if api is None:
            return "the session is not open"
        frame = self.venue.codec.encode(
            "ProtoOAClosePositionReq",
            {"ctidTraderAccountId": str(self.ctid), "positionId": "1", "volume": "1"},
            "",
        )
        if is_refusal(frame):
            return f"the codec refused the request ({reasons(frame)})"
        pushed = api.push(frame.value)
        if is_refusal(pushed):
            return f"the wire refused the request ({reasons(pushed)})"
        found = api.wait(_answered)
        if is_refusal(found):
            return f"the session refused the read ({reasons(found)})"
        if found.value is None:
            return "no answer"
        return f"{found.value.name}: {json.dumps(dict(found.value.body), default=str)[:300]}"

    def deal_list(self) -> str:
        """The first page of the last position's deals, with whether more are behind it. The run
        closes what each mark opened, so its last position is the last one this run closed."""
        api = self.venue.api
        if api is None:
            return "the run left no position to ask about"
        if self.closed_ids:
            position = self.closed_ids[-1]
        else:
            position = self.position_id(self.label) if self.held() else None
        if position is None:
            return "the run left no position to ask about"
        asked = api.ask(
            "ProtoOADealListByPositionIdReq",
            {"ctidTraderAccountId": str(self.ctid), "positionId": str(position)},
        )
        if is_refusal(asked):
            return f"cTrader refused the deal list ({reasons(asked)})"
        body = cast("dict[str, object]", asked.value.body)
        deals = cast("list[object]", body.get("deal") or [])
        first = deals[0] if deals else None
        fields = sorted(cast("Mapping[str, object]", first)) if isinstance(first, dict) else []
        return (
            f"{len(deals)} deals on the first page, hasMore={body.get('hasMore')}, "
            f"first deal's fields {fields}"
        )

    def trendbars(self) -> str:
        """One trendbar page: how many rows, and whether the answer says more are behind it."""
        api = self.venue.api
        if api is None:
            return "the session is not open"
        asked = api.ask(
            "ProtoOAGetTrendbarsReq",
            {
                "ctidTraderAccountId": str(self.ctid),
                "symbolId": str(self.symbols().symbol_id),
                "period": "M15",
            },
        )
        if is_refusal(asked):
            return f"cTrader refused the trendbars ({reasons(asked)})"
        body = cast("dict[str, object]", asked.value.body)
        bars = cast("list[object]", body.get("trendbar") or [])
        return f"{len(bars)} bars, hasMore={body.get('hasMore')}"

    def trader(self) -> str:
        """The trader's own facts: its id against the account id the session is bound to."""
        api = self.venue.api
        if api is None:
            return "the session is not open"
        asked = api.ask("ProtoOATraderReq", {"ctidTraderAccountId": str(self.ctid)})
        if is_refusal(asked):
            return f"cTrader refused the trader ({reasons(asked)})"
        body = cast("dict[str, object]", asked.value.body)
        facts = cast("dict[str, object]", body.get("trader") or {})
        shown = {
            key: facts.get(key)
            for key in ("ctidTraderAccountId", "accountType", "moneyDigits", "traderLogin")
        }
        return f"bound {self.ctid}, trader {json.dumps(shown, default=str)}"

    def refresh(self) -> tuple[bool, str]:
        """The TN-05 drill on his demo account: store the new pair, re-open, refuse a second."""
        grants = Grants(self.store, TokenEndpoint(), lambda: False, time.time_ns)
        before = self.grant.tokens.access
        kept = grants.refresh(self.registration)
        if is_refusal(kept):
            return False, f"the refresh was refused ({reasons(kept)})"
        stored = Grant.parse(self.store.read() or "")
        if stored is None or stored.tokens.access == before:
            return False, "the store still holds the old access token"
        self.holder["grant"] = stored
        reopened = self.venue.connect()
        if is_refusal(reopened):
            return False, f"the session did not reopen ({reasons(reopened)})"
        verified = self.venue.verify()
        if is_refusal(verified):
            return False, f"the session did not come back ready ({reasons(verified)})"
        gate = grants.gate
        held = gate.acquire(grants.ref)
        try:
            second = grants.refresh(self.registration)
        finally:
            gate.release(grants.ref)
        if is_refusal(held):
            return False, f"the gate was already held ({reasons(held)})"
        if not is_refusal(second):
            return False, "a second refresher was not refused"
        return True, (
            "the store took the new pair before the old was let go, the session reads ready, and"
            " the second refresher was refused"
        )


def binding_module() -> Any:
    """The fakes' module, with the tests folder on this interpreter's path the first time."""
    tests = PROBES.parents[1] / "tests"
    if str(tests) not in sys.path:
        sys.path.insert(0, str(tests))
    return cast(Any, importlib.import_module("test_app_binding"))


def rigged(fake: Any, *, fault: bool = False) -> tuple[Rehearsal, Path]:
    """A throwaway folder, the real node, its real codec and `fake` for the broker."""
    binding: Any = binding_module()
    root = Path(tempfile.mkdtemp(prefix="c15-probe-", dir=tempfile.gettempdir()))
    try:
        rig = binding.bound_rig(root, broker=fake)
        binding.signed_in(rig)
        binding.bind(rig)
        binding.tick_quotes(rig)
        venue = binding.runtime(rig).venues[binding.ACCOUNT].client
        return Rehearsal(rig=rig, venue=venue, fake=fake, fault=fault), root
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


def rehearsal(module: Any, *, fault: bool) -> tuple[Rehearsal, Path]:
    """A throwaway folder, the real node, its real codec and the fake broker for one mark."""
    binding: Any = binding_module()
    return rigged(module.broker(binding.codec(), fault=fault), fault=fault)


def shared() -> tuple[Rehearsal, Path]:
    """One rig for every mark, as the demo run has one account for the marks on it."""
    binding: Any = binding_module()
    return rigged(binding.FakeCTrader(binding.codec()))


def demo(home: Path, tag: str | None, account: str | None) -> Demo:
    """The node's venue over his demo account, with the key and grant read from its stores only."""
    passport = json.loads((home / PASSPORT).read_text("utf-8"))
    node_tag = tag or str(cast("dict[str, object]", passport["identity"])["tag"])
    keys = os.environ.get("NODE_KEYS")
    if keys is None:
        keyring: Any = cast(Any, importlib.import_module("keyring"))
        keys = cast("str | None", keyring.get_password(KEYS, KEYS.split("/", 1)[1]))
    app = registration(keys)
    if app is None:
        raise SystemExit(f"FAIL setup: no trading app in {KEYS}")
    store = grant_store(home / DEMO_HOME, node_tag)
    grant = Grant.parse(store.read() or "")
    if grant is None:
        raise SystemExit(f"FAIL setup: the node holds no cTrader grant for {node_tag}")
    demo_accounts = [one for one in grant.accounts if not one.is_live]
    ctid = int(account) if account is not None else (demo_accounts[0].ctid if demo_accounts else 0)
    if not ctid:
        raise SystemExit("FAIL setup: the grant reaches no demo account")
    loaded = Codec.load(DEFINITIONS)
    if is_refusal(loaded):
        raise SystemExit(f"FAIL setup: the cTrader definitions did not load ({reasons(loaded)})")
    holder: dict[str, Any] = {"grant": grant}
    venue = CTraderVenue(
        account=Account(str(ctid), VenueId("icmarkets-ctrader"), AccountRole.DEMO),
        ctid=ctid,
        host=DEMO_HOST,
        markets={MARKET: SYMBOL},
        codec=loaded.value,
        open_wire=FramedWire.open,
        credentials=lambda: (
            app.client_id,
            app.client_secret.reveal(),
            holder["grant"].tokens.access.reveal(),
        ),
        clock_ns=time.time_ns,
        steady_ns=time.monotonic_ns,
        session_epoch="c15-probe",
    )
    opened = venue.connect()
    if is_refusal(opened):
        raise SystemExit(f"FAIL setup: cTrader did not open the session ({reasons(opened)})")
    verified = venue.verify()
    if is_refusal(verified):
        raise SystemExit(f"FAIL setup: the session did not verify ({reasons(verified)})")
    session = Demo(venue, ctid, grant, store, app, holder)
    session.observations[PASSPORT_QUESTION] = _facts(passport)
    return session


def _facts(passport: Mapping[str, object]) -> dict[str, object]:
    """The six facts the node's passport carries: its five self-test checks and its clock."""
    checks = passport.get("checks")
    rows: Mapping[str, object] = (
        cast("Mapping[str, object]", checks) if isinstance(checks, dict) else {}
    )
    facts: dict[str, object] = {}
    for name, row in rows.items():
        held: Mapping[str, object] = (
            cast("Mapping[str, object]", row) if isinstance(row, dict) else {}
        )
        facts[str(name)] = held.get("ok", held.get("value"))
    return facts


def questions(session: Demo) -> None:
    """What only his demo settles, each printing what it found, never a verdict."""
    for question in (FILL_QUESTION, PASSPORT_QUESTION):
        print(f"FOUND {question}: {session.observations.get(question, 'not observed in this run')}")
    for question, found in (
        ("what a close on a gone position answers", session.gone_close()),
        ("the deal list of the probe's last position", session.deal_list()),
        ("trendbars read", session.trendbars()),
        ("traderId against ctid", session.trader()),
        (
            "whether a position missing from one listing can come back at the next session",
            "not observed in this run",
        ),
        (
            "whether the refresh drill from a separate process invalidates the running node's"
            " session",
            "not observed in this run; the refresh mark proves the node's own refresher",
        ),
        (
            "what ProtoOAAccountDisconnectEvent does to a session",
            "not observed in this run: cTrader sent none",
        ),
    ):
        print(f"FOUND {question}: {found}")


def _rehearse(module: Any, session: Any) -> tuple[bool, str]:
    """One mark's rehearsal half over whichever rig it was handed."""
    return cast("tuple[bool, str]", module.rehearse(session))


def _demo(module: Any, session: Any) -> tuple[bool, str]:
    """One mark's demo half over the session his account is bound to."""
    return cast("tuple[bool, str]", module.demo(session))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--rehearsal", action="store_true", help="the fake broker, no account")
    parser.add_argument(
        "--shared", action="store_true", help="rehearse every mark over one rig, not one per mark"
    )
    parser.add_argument("--fault", help="rehearse one mark with its fault in, and expect FAIL")
    parser.add_argument("--plan", action="store_true", help="print the marks; no network")
    parser.add_argument("--home", type=Path, help="his QMX folder, for the demo run")
    parser.add_argument("--tag", help="the node's tag, read from its passport by default")
    parser.add_argument("--account", help="the demo account's ctid, when the grant lists several")
    args = parser.parse_args(argv)
    chosen = [one for one in MARK_MODULES if args.fault in (None, one.MARK)]
    if args.fault is not None and not chosen:
        print(f"FAIL no mark is named {args.fault}", file=sys.stderr)
        return 2
    if args.shared and not args.rehearsal:
        print(
            "FAIL setup: --shared rehearses every mark over one rig; name --rehearsal too",
            file=sys.stderr,
        )
        return 2
    if args.shared and args.fault is not None:
        print(
            "FAIL setup: --shared runs every mark, so it cannot run one mark's fault",
            file=sys.stderr,
        )
        return 2
    if args.plan:
        for module in MARK_MODULES:
            print(f"PLAN {module.MARK}: {module.CLAIM}")
        return 0
    if args.rehearsal:
        if args.shared:
            run, root = shared()
            try:
                return 1 if one_by_one(run, chosen, _rehearse) else 0
            finally:
                run.rig.node.stop()
                shutil.rmtree(root, ignore_errors=True)
        failures = 0
        for module in chosen:
            run, root = rehearsal(module, fault=args.fault is not None)
            try:
                ok, said = module.rehearse(run)
            finally:
                run.rig.node.stop()
                shutil.rmtree(root, ignore_errors=True)
            failures += not say(ok, module.MARK, said)
        return 1 if failures else 0
    if args.home is None:
        print("FAIL setup: name his QMX folder with --home for the demo run", file=sys.stderr)
        return 2
    session = demo(args.home, args.tag, args.account)
    try:
        failures = one_by_one(session, chosen, _demo)
        questions(session)
    finally:
        session.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
