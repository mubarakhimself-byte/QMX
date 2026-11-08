"""The Hyperliquid testnet probe (C-16, ``EXTERNAL.md`` section 3). He runs it after gate G-WALLET.

It needs a testnet agent wallet he approved on Hyperliquid's own testnet page, written into the
keys document ``qmx/trading-node-keys`` (``hyperliquid: [{address, agent_key, expires_at}]``), and
some testnet USDC on that account. It runs in the qmx-agents environment, which locks CCXT::

    cd qmx-agents
    uv run --no-sync python ../qmn/probes/hyperliquid_testnet/run.py --plan
    uv run --no-sync python ../qmn/probes/hyperliquid_testnet/run.py

``--plan`` reads the keys document and prints the marks and the endpoint, with no network call.
Without it the probe trades about 12 USDC of ETH on testnet only, prints one PASS or FAIL line per
mark, closes what it opened and exits 1 on any FAIL. The client refuses mainnet, so the probe can
never reach it. A mark CCXT cannot meet is the trigger for a native client for that mark only
(Level 0 LC-26); the probe says which.

The keys document comes from the ``NODE_KEYS`` environment variable when it is set, as the node's
supervisor hands it over, else from Credential Manager. Nothing here prints a key.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Coroutine, Mapping
from dataclasses import dataclass
from decimal import ROUND_UP, Decimal
from pathlib import Path
from typing import Any, cast

from qmf.core import Account, AccountRole, TypedRefusal, VenueId
from qmf.data.journal_envelope import JournalStream, JournalWorld
from qmf.data.journal_writer import JournalWriter, WriterScope
from qml.numbers import InstrumentRecord, lots, parse_record
from qml.unit.model import Side
from qmn.app.attribution import Claim, attribute
from qmn.app.feed_keeper import FeedKeeper, Quote, RecordedSource, Recording
from qmn.app.runtime import OrderPath, Placed, Ticket, Venue, ulid
from qmn.venue import Command
from qmn.venue.ccxt_client import (
    AgentWallet,
    CcxtClient,
    Exchange,
    agent_wallets,
    api_urls,
    cloid,
    make_testnet_exchange,
)

NODE_KEYS = "qmx/trading-node-keys"
TAG = "probe7zz"
"""The probe's own node tag, so its orders never read as the practice node's."""
COIN = "ETH"
SYMBOL = f"{COIN}/USDC:USDC"
MARKET = "crypto.eth"
NOTIONAL_USDC = Decimal(12)
"""Each order's size in USDC, over Hyperliquid's 10 USDC minimum."""
STOP_SHARE = Decimal("0.03")
"""The stop sits this share of the price below the entry."""
FILL_EVENT_S = 2.0
HOLD_S = 120
VENUE = VenueId("hyperliquid-testnet")
ACCOUNT = Account("hl-testnet-probe", VENUE, AccountRole.DEMO)
MARKS = (
    "an agent-wallet-signed IOC entry fills through the node's order path",
    "its reduce-only positionTpsl stop trigger is accepted and shows in fetch_open_orders",
    "an agent-wallet-signed limit order fills",
    "the stop still covers the whole position after the second fill",
    "the stop survives the node's process being killed (read back from a fresh process)",
    "cancel_order by cloid takes a resting order off the book",
    "a fill event arrives on watch_my_trades within 2 s",
    "everything the probe opened is closed and no order of it rests",
)


def say(ok: bool, mark: str, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'} {mark}" + (f" ({detail})" if detail and not ok else ""))
    sys.stdout.flush()
    return ok


def keys_document() -> Mapping[str, object]:
    held = os.environ.get("NODE_KEYS")
    if held is None:
        keyring = importlib.import_module("keyring")
        held = keyring.get_password(NODE_KEYS, NODE_KEYS.split("/", 1)[1])
    if not held:
        raise SystemExit(f"FAIL keys: no keys document in {NODE_KEYS}; run the node setup first")
    found = cast("object", json.loads(held))
    if not isinstance(found, dict):
        raise SystemExit(f"FAIL keys: {NODE_KEYS} does not hold a JSON object")
    return cast("Mapping[str, object]", found)


def chosen_wallet(address: str | None) -> AgentWallet:
    wallets = agent_wallets(keys_document())
    if isinstance(wallets, TypedRefusal):
        raise SystemExit(f"FAIL keys: {wallets.context['reason']}")
    picked = [w for w in wallets.value if address is None or w.address.lower() == address.lower()]
    if not picked:
        raise SystemExit("FAIL keys: no Hyperliquid agent wallet in the keys document")
    return picked[0]


def testnet_exchange(wallet: AgentWallet, *, streaming: bool = False) -> Any:
    """``ccxt.hyperliquid``, or ``ccxt.pro``'s for the stream, on testnet with no referrer and
    no builder fee. Refuses to go on unless every endpoint is testnet's."""
    ccxt = importlib.import_module("ccxt.pro" if streaming else "ccxt")
    made = make_testnet_exchange(ccxt.hyperliquid, wallet)
    if isinstance(made, TypedRefusal):
        raise SystemExit(f"FAIL setup: an endpoint is not testnet's: {made.context['endpoints']}")
    return made.value


def record(precision: Decimal) -> InstrumentRecord:
    parsed = parse_record(
        {
            "venue": "hyperliquid-testnet", "symbol": COIN, "market_id": MARKET, "class": "perp",
            "currency": "USDC", "digits": 1, "tick_size": "0.1",
            "pip": {"size": "0.1", "source": "testnet probe"}, "contract_size": "1",
            "value_per_point": "1", "lot_step": str(precision), "min_lot": str(precision),
            "max_lot": "1000", "calendar_ref": "crypto-24x7@1", "zone": "UTC",
            "day_boundary": "00:00", "data_levels": {"levels": [0, 1, 2], "volume": "trades"},
            "leverage": {"version": 1, "tiers": [{"up_to_lots": "1000", "leverage": "10"}]},
            "margin": {"intraday": "0.1", "overnight": "0.1"}, "record_version": 1,
            "status": "specified",
        }
    )  # fmt: skip
    if isinstance(parsed, TypedRefusal):
        raise SystemExit(f"FAIL setup: the probe's record is refused: {parsed.context['reason']}")
    return parsed.value


@dataclass
class Probe:
    exchange: Any
    client: CcxtClient
    path: OrderPath
    feed: FeedKeeper
    source: RecordedSource
    record: InstrumentRecord
    precision: Decimal
    alarms: list[Mapping[str, object]]

    def quote(self) -> tuple[Decimal, Decimal]:
        book = self.exchange.fetch_order_book(SYMBOL, 5)
        bid, ask = Decimal(str(book["bids"][0][0])), Decimal(str(book["asks"][0][0]))
        at = time.time_ns()  # ambient-scan: allow - the probe is its own composition root
        self.source.play([Quote(MARKET, at, bid, ask, "both")])
        self.feed.pump()
        return bid, ask

    def size(self, price: Decimal) -> Decimal:
        return (NOTIONAL_USDC / price / self.precision).to_integral_value(ROUND_UP) * self.precision

    def enter(self, name: str) -> object:
        _bid, ask = self.quote()
        quantity = lots(self.size(ask), self.record)
        if isinstance(quantity, TypedRefusal):
            return quantity
        return self.path.entry(
            client_order_id=name,
            label=f"qmx:{TAG}:testnet-probe",
            wire={
                "order": {"type": "market"},
                "direction": "long",
                "market_id": MARKET,
                "protection": {"stop": str(ask * (1 - STOP_SHARE))},
                "quantity": str(self.size(ask)),
                "decision_row_id": name,
            },
            record=self.record,
            quantity=quantity.value,
            blocked_by=None,
        )

    def resting(self) -> list[Mapping[str, Any]]:
        return list(self.exchange.fetch_open_orders(SYMBOL))

    def stops(self) -> list[Mapping[str, Any]]:
        return [o for o in self.resting() if o.get("triggerPrice") is not None]


def probe(wallet: AgentWallet, scratch: Path, sent: tuple[str, ...] = ()) -> Probe:
    ccxt = importlib.import_module("ccxt")
    exchange = testnet_exchange(wallet)
    exchange.load_markets()
    precision = Decimal(str(exchange.market(SYMBOL)["precision"]["amount"]))
    clock = time.time_ns  # ambient-scan: allow - the probe is its own composition root
    alarms: list[Mapping[str, object]] = []
    opened = CcxtClient.open(
        cast("Exchange", exchange),
        account=ACCOUNT,
        wallet=wallet,
        markets={MARKET: SYMBOL},
        ccxt_version=str(ccxt.__version__),
        clock_ns=clock,
        on_alarm=alarms.append,
        sent=lambda: sent,
    )
    if isinstance(opened, TypedRefusal):
        raise SystemExit(f"FAIL setup: {opened.context['reason']}")
    source = RecordedSource([])
    feed = FeedKeeper("hyperliquid", "testnet", source, (MARKET,), clock, Recording(None))
    scope = WriterScope(JournalStream.NODE, TAG, JournalWorld.DEMO, "probe", "node", "0.1.0")
    journal = JournalWriter.open(scratch, scope, clock=clock, boot_epoch_id="probe")
    if isinstance(journal, TypedRefusal):
        raise SystemExit("FAIL setup: the probe's journal refused to open")
    path = OrderPath(
        TAG, Venue(opened.value, feed), journal.value, clock, time.sleep, alarms.append
    )
    return Probe(exchange, opened.value, path, feed, source, record(precision), precision, alarms)


def name(seed: str) -> str:
    return f"q{TAG}-{ulid(time.time_ns() // 1_000_000, seed)}"  # ambient-scan: allow - root


def child(wallet: AgentWallet, scratch: Path, hold_s: float = HOLD_S) -> int:
    """Marks 1 to 4, then hold the position until the parent kills this process."""
    run = probe(wallet, scratch)
    entry = name("entry")
    placed = run.enter(entry)
    print(f"SENT {entry}")
    say(isinstance(placed, Placed), MARKS[0], repr(placed))
    stops = run.stops()
    say(
        any(o.get("reduceOnly") is True for o in stops),
        MARKS[1],
        json.dumps([o.get("info") for o in stops])[:400],
    )
    _bid, ask = run.quote()
    size, added = run.size(ask), name("add")
    print(f"SENT {added}")
    limit = run.exchange.create_order(
        SYMBOL, "limit", "buy", str(size), str(ask * Decimal("1.01")),
        {"clientOrderId": cloid(added), "timeInForce": "Gtc"},
    )  # fmt: skip
    say(Decimal(str(limit.get("filled") or 0)) > 0, MARKS[2], json.dumps(limit.get("info")))
    positions = run.exchange.fetch_positions([SYMBOL])
    held = sum((Decimal(str(p.get("contracts") or 0)) for p in positions), Decimal(0))
    whole = [o for o in run.stops() if dict(o.get("info") or {}).get("isPositionTpsl") is True]
    say(
        len(whole) == 1 and held >= 2 * size - run.precision,
        MARKS[3],
        f"position {held}, whole-position stops {len(whole)}",
    )
    print("HOLDING", flush=True)
    time.sleep(hold_s)
    return 0


async def watch_fill(wallet: AgentWallet, size: Decimal) -> tuple[bool, str]:
    exchange = testnet_exchange(wallet, streaming=True)
    try:
        await exchange.load_markets()
        watcher = asyncio.ensure_future(exchange.watch_my_trades(SYMBOL))
        await asyncio.sleep(1.0)
        book = await exchange.fetch_order_book(SYMBOL, 5)
        ask = Decimal(str(book["asks"][0][0]))
        sent_at = time.monotonic()  # ambient-scan: allow - the probe measures the venue
        await exchange.create_order(
            SYMBOL, "market", "sell", str(size), str(ask),
            {"reduceOnly": True, "clientOrderId": cloid(name("watch"))},
        )  # fmt: skip
        trades = await asyncio.wait_for(watcher, timeout=FILL_EVENT_S + 3)
        took = time.monotonic() - sent_at  # ambient-scan: allow - the probe measures the venue
        return took <= FILL_EVENT_S and bool(trades), f"{took:.2f} s, {len(trades)} trades"
    except TimeoutError:
        return False, "no fill event"
    finally:
        await exchange.close()


def cleanup(run: Probe) -> bool:
    for order in run.resting():
        run.exchange.cancel_order(order["id"], SYMBOL)
    for position in run.exchange.fetch_positions([SYMBOL]):
        size = Decimal(str(position.get("contracts") or 0))
        if size > 0:
            bid, ask = run.quote()
            side = "sell" if position.get("side") == "long" else "buy"
            run.exchange.create_order(
                SYMBOL, "market", side, str(size), str(bid if side == "sell" else ask),
                {"reduceOnly": True, "clientOrderId": cloid(name("cleanup"))},
            )  # fmt: skip
    left = [p for p in run.exchange.fetch_positions([SYMBOL]) if (p.get("contracts") or 0) != 0]
    return say(not left and not run.resting(), MARKS[7], f"{len(left)} positions left")


def held_in_child(wallet: AgentWallet, scratch: Path) -> tuple[list[bool], list[str]]:
    """Marks 1 to 4 in a child process, which is then killed while it holds the position."""
    env = {**os.environ, "NODE_KEYS": json.dumps(keys_document())}
    started = subprocess.Popen(
        [sys.executable, __file__, "--child", "--address", wallet.address, "--scratch", scratch],
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    results: list[bool] = []
    sent: list[str] = []
    for line in started.stdout or ():
        text = line.rstrip()
        if text.startswith("SENT "):
            sent.append(text.removeprefix("SENT "))
        elif text == "HOLDING":
            break
        else:
            print(text, flush=True)
            results.append(text.startswith("PASS"))
    started.kill()
    started.wait()
    return results, sent


def after_kill(
    wallet: AgentWallet,
    sent: list[str],
    scratch: Path,
    watch: Callable[[AgentWallet, Decimal], Coroutine[Any, Any, tuple[bool, str]]] = watch_fill,
) -> list[bool]:
    """Marks 5 to 8 from a fresh process, then close what the probe opened."""
    results: list[bool] = []
    run = probe(wallet, scratch, tuple(sent))
    try:
        read = run.client.read_back()
        mine = (
            []
            if isinstance(read, TypedRefusal)
            else [
                p
                for p, a in attribute(read.value, tag=TAG, sent=sent).positions
                if a.claim is Claim.MINE and p.stop is not None
            ]
        )
        results.append(say(len(mine) == 1, MARKS[4], repr(read)[:400]))
        bid, _ask = run.quote()
        resting = name("resting")
        run.exchange.create_order(
            SYMBOL, "limit", "buy", str(run.size(bid / 2)), str(bid / 2),
            {"clientOrderId": cloid(resting), "timeInForce": "Gtc"},
        )  # fmt: skip
        cancel = Command.cancel_order(VENUE, ACCOUNT, "probe", 1, resting)
        if isinstance(cancel, TypedRefusal):
            raise SystemExit("FAIL setup: the cancel command is refused")
        answer = run.client.send(Ticket(cancel.value, MARKET, Side.LONG, bid))
        gone = all(o.get("clientOrderId") != cloid(resting) for o in run.resting())
        results.append(say(gone, MARKS[5], repr(answer)))
        held = sum(
            (Decimal(str(p.get("contracts") or 0)) for p in run.exchange.fetch_positions([SYMBOL])),
            Decimal(0),
        )
        ok, detail = asyncio.run(watch(wallet, min(held, run.size(bid))))
        results.append(say(ok, MARKS[6], detail))
    finally:
        results.append(cleanup(run))
    for alarm in run.alarms:
        print(f"ALARM {json.dumps(dict(alarm))}")
    return results


def verdict(results: list[bool]) -> int:
    if len(results) < len(MARKS) or not all(results):
        print("A failed mark CCXT cannot meet is the trigger for a native client for that mark.")
        return 1
    return 0


def parent(wallet: AgentWallet) -> int:
    with tempfile.TemporaryDirectory(prefix="c16-probe-") as scratch:
        (Path(scratch) / "child").mkdir()
        (Path(scratch) / "fresh").mkdir()
        held, sent = held_in_child(wallet, Path(scratch) / "child")
        return verdict(held + after_kill(wallet, sent, Path(scratch) / "fresh"))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="The Hyperliquid testnet probe (C-16).")
    parser.add_argument("--plan", action="store_true", help="print the marks; no network call")
    parser.add_argument("--address", help="the account address of the agent wallet to use")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scratch", type=Path, help=argparse.SUPPRESS)
    given = parser.parse_args(argv)
    wallet = chosen_wallet(given.address)
    if given.plan:
        exchange = testnet_exchange(wallet)
        print(f"PLAN endpoints {sorted(set(api_urls(exchange)))}")
        print(f"PLAN account {wallet.address}, agent wallet expires at {wallet.expires_at_ms} ms")
        for mark in MARKS:
            print(f"PLAN {mark}")
        return 0
    return child(wallet, given.scratch) if given.child else parent(wallet)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
