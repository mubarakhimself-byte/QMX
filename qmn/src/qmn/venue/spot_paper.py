"""QMN-owned recorded spot execution, explicitly local infrastructure simulation.

No live client, credential or order transport is constructible. This is not a
fourth VenueClientKind or the vendor-demo paper mode. The state database is a
simulation ledger, not QMF source evidence or CT-32 strategy validation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import threading
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, BinaryIO, cast

from qmf.core import Ok, Result, is_refusal
from qmf.venue.spot import SpotMarket, exact, refusal


@dataclass(frozen=True, slots=True)
class AccountScope:
    provider_connection_id: str
    venue_id: str
    account_id: str
    node_id: str

    def key(self) -> tuple[str, str, str]:
        """Placement is excluded: moving node cannot create a duplicate writer."""
        return (self.provider_connection_id, self.venue_id, self.account_id)


@dataclass(frozen=True, slots=True)
class PaperPolicy:
    policy_ref: str
    max_open_notional: str
    quote_fee_rate: str
    max_price_age_ns: int
    request_weight_budget: int
    request_window_ns: int


def _stored(value: object) -> Decimal:
    """Internal exact arithmetic can carry more digits than a foreign input."""
    if not isinstance(value, str) or len(value) > 256:
        raise ValueError("simulation amount is not a bounded decimal string")
    number = Decimal(value)
    if not number.is_finite() or number < 0 or abs(number.adjusted()) > 128:
        raise ValueError("simulation amounts must be finite and nonnegative")
    return number


def _validate_state(state: dict[str, Any], market: SpotMarket) -> None:
    """Reconciliation checks conservation of every remaining reservation."""
    expected = {market.base: Decimal(0), market.quote: Decimal(0)}
    if len(state["orders"]) > 1024 or set(state["balances"]) != set(expected):
        raise ValueError("simulation ledger shape or order limit is invalid")
    for client_id, order in state["orders"].items():
        if order["client_id"] != client_id or order["side"] not in {"buy", "sell"}:
            raise ValueError("simulation order identity is corrupt")
        if (
            type(order["admission_index"]) is not int
            or type(order["admitted_ns"]) is not int
            or not 0 <= order["admitted_ns"] <= state["clock_ns"]
        ):
            raise ValueError("simulation admission identity is corrupt")
        amount, filled, reserved = (_stored(order[key]) for key in ("amount", "filled", "reserved"))
        if filled > amount or order["status"] not in {"OPEN", "PARTIAL", "CANCELED", "FILLED"}:
            raise ValueError("simulation order fill/status is corrupt")
        asset = market.quote if order["side"] == "buy" else market.base
        if order["asset"] != asset or (order["status"] in {"CANCELED", "FILLED"} and reserved):
            raise ValueError("terminal simulation order cannot retain a reservation")
        if order["status"] in {"OPEN", "PARTIAL"}:
            remaining = amount - filled
            fee = exact(state["identity"]["policy"]["quote_fee_rate"], positive=False)
            expected_order = (
                remaining * exact(order["price"]) * (1 + fee)
                if order["side"] == "buy"
                else remaining
            )
            if remaining <= 0 or reserved != expected_order:
                raise ValueError("open simulation order reservation does not reconcile")
        if order["status"] == "FILLED" and filled != amount:
            raise ValueError("filled simulation order must be completely filled")
        expected[asset] += reserved
    for asset, balance in state["balances"].items():
        total, reserved = _stored(balance["total"]), _stored(balance["reserved"])
        if reserved > total or reserved != expected[asset]:
            raise ValueError("simulation balance reservation does not reconcile")
    _stored(state["fees"])
    if sorted(o["admission_index"] for o in state["orders"].values()) != list(
        range(len(state["orders"]))
    ):
        raise ValueError("simulation admission order is corrupt")


def _query_view(state: dict[str, Any], scope: AccountScope, market: SpotMarket) -> dict[str, Any]:
    """QMN-owned retained read projection; it asserts no current writer liveness."""
    return {
        "format_version": 1,
        "paper_state_version": 2,
        "retained": True,
        "simulation": True,
        "behavior": "recorded-spot-limit-fills",
        "scope": asdict(scope),
        "policy_ref": state["identity"]["policy"]["policy_ref"],
        "symbol": market.symbol,
        "balances": state["balances"],
        "orders": sorted(state["orders"].values(), key=lambda order: order["admission_index"]),
        "fees_quote": state["fees"],
        "feed_status": state["feed_status"],
        "sequence": state["sequence"],
    }


def _lock(path: Path) -> BinaryIO:
    held = path.open("a+b")
    try:
        if path.stat().st_size == 0:
            held.write(b"0")
            held.flush()
        held.seek(0)
        if os.name == "nt":
            import msvcrt  # noqa: PLC0415 - native lock API exists only on Windows

            msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl  # noqa: PLC0415 - native lock API exists only on POSIX

            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return held
    except OSError:
        held.close()
        raise


class SpotPaperAccount:
    """One account writer and one atomic snapshot/audit transaction per event."""

    def __init__(
        self,
        db: sqlite3.Connection,
        held: BinaryIO,
        scope: AccountScope,
        policy: PaperPolicy,
        market: SpotMarket,
        state: dict[str, Any],
    ) -> None:
        self.db, self.held, self.scope = db, held, scope
        self.policy, self.market, self.state = policy, market, state
        self.mutex = threading.RLock()
        self.closed = False
        self.blocked = False

    @classmethod
    def open(
        cls,
        root: Path,
        *,
        scope: AccountScope,
        policy: PaperPolicy,
        market_payload: object,
        precision_mode: object,
        initial_balances: Mapping[str, object],
    ) -> Result[SpotPaperAccount]:
        parsed = SpotMarket.from_ccxt_market(market_payload, precision_mode=precision_mode)
        if is_refusal(parsed):
            return parsed
        market = parsed.value
        try:
            if any(not isinstance(v, str) or not v.strip() for v in asdict(scope).values()):
                raise ValueError("stable provider/venue/account/node identities are required")
            if not policy.policy_ref.strip():
                raise ValueError("an explicit per-account policy reference is required")
            exact(policy.max_open_notional)
            if exact(policy.quote_fee_rate, positive=False) >= 1:
                raise ValueError("quote fee rate must be less than one")
            if any(
                type(v) is not int or v <= 0
                for v in (
                    policy.max_price_age_ns,
                    policy.request_weight_budget,
                    policy.request_window_ns,
                )
            ):
                raise ValueError(
                    "price freshness and local request budgets must be positive integers"
                )
            if set(initial_balances) != {market.base, market.quote}:
                raise ValueError("initial balances must name exactly this market's base/quote")
            balances = {
                asset: str(exact(value, positive=False))
                for asset, value in initial_balances.items()
            }
        except (ValueError, TypeError, AttributeError) as exc:
            return refusal(str(exc))
        held: BinaryIO | None = None
        db: sqlite3.Connection | None = None
        try:
            directory = (
                root.resolve() / hashlib.sha256(json.dumps(scope.key()).encode()).hexdigest()
            )
            directory.mkdir(parents=True, exist_ok=True)
            try:
                held = _lock(directory / ".paper-writer")
            except OSError:
                return refusal("account is already owned by another node writer", code="OWNER_BUSY")
            db = sqlite3.connect(directory / "paper.sqlite", check_same_thread=False)
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY, body TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, body TEXT)")
            identity = {
                "scope": list(scope.key()),
                "policy": asdict(policy),
                "market": asdict(market),
                "version": 2,
                "initial_balances": balances,
            }
            row = db.execute("SELECT body FROM snapshot WHERE id=1").fetchone()
            state: dict[str, Any] = (
                cast("dict[str, Any]", json.loads(row[0]))
                if row
                else {
                    "identity": identity,
                    "balances": {
                        asset: {"total": value, "reserved": "0"}
                        for asset, value in balances.items()
                    },
                    "orders": {},
                    "fees": "0",
                    "feed_status": "UNSYNCED",
                    "sequence": None,
                    "event_ns": None,
                    "received_ns": None,
                    "bid": None,
                    "ask": None,
                    "rate": [],
                    "clock_ns": 0,
                }
            )
            if state["identity"] != identity:
                db.close()
                held.close()
                return refusal(
                    "restart account, market, seed and policy identity must match", code="POLICY"
                )
            with localcontext() as context:
                context.prec = 128
                _validate_state(state, market)
            if row:
                audit = db.execute("SELECT body FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
                if audit is None or json.loads(audit[0])["state"] != state:
                    raise ValueError("simulation snapshot and audit do not reconcile")
            # Price readiness never survives a reconnect/restart, even with open orders.
            state["feed_status"] = "UNSYNCED"
            db.execute("CREATE TABLE IF NOT EXISTS query_view (id INTEGER PRIMARY KEY, body TEXT)")
            account = cls(db, held, scope, policy, market, state)
            saved = account._change("open/reconcile", lambda _state: None)
            if is_refusal(saved):
                account.close()
                return saved
            return Ok(account)
        except (OSError, sqlite3.Error, ValueError, InvalidOperation, KeyError, TypeError) as exc:
            if db is not None:
                db.close()
            if held is not None:
                held.close()
            return refusal(f"paper state could not be reopened: {exc}", code="STORAGE_FAILURE")

    def close(self) -> None:
        with self.mutex:
            if not self.closed:
                self.db.close()
                self.held.close()  # OS lock also releases after process death.
                self.closed = True

    def _change(
        self, event: str, mutation: Callable[[dict[str, Any]], None]
    ) -> Result[Mapping[str, object]]:
        with self.mutex, localcontext() as context:
            context.prec = 128
            if self.closed or self.blocked:
                return refusal("paper writer is closed or storage-blocked", code="STORAGE_FAILURE")
            updated = copy.deepcopy(self.state)
            try:
                mutation(updated)
                _validate_state(updated, self.market)
                body = json.dumps(updated, sort_keys=True, separators=(",", ":"))
                audit = json.dumps(
                    {
                        "simulation": True,
                        "event": event,
                        "node_id": self.scope.node_id,
                        "state": updated,
                    },
                    sort_keys=True,
                )
                with self.db:
                    self.db.execute("INSERT OR REPLACE INTO snapshot VALUES (1, ?)", (body,))
                    cursor = self.db.execute("INSERT INTO audit(body) VALUES (?)", (audit,))
                    view = _query_view(updated, self.scope, self.market)
                    view["audit_seq"] = cursor.lastrowid
                    self.db.execute(
                        "INSERT OR REPLACE INTO query_view VALUES (1, ?)",
                        (json.dumps(view, sort_keys=True, separators=(",", ":")),),
                    )
                self.state = updated
                return Ok(self.query())
            except (sqlite3.Error, ValueError, InvalidOperation) as exc:
                self.blocked = True
                return refusal(f"atomic simulation write failed: {exc}", code="STORAGE_FAILURE")

    def query(self) -> Mapping[str, Any]:
        with self.mutex:
            state = copy.deepcopy(self.state)
            return {
                "simulation": True,
                "behavior": "recorded-spot-limit-fills",
                "scope": asdict(self.scope),
                "policy_ref": self.policy.policy_ref,
                "symbol": self.market.symbol,
                "balances": state["balances"],
                "orders": sorted(
                    state["orders"].values(), key=lambda order: order["admission_index"]
                ),
                "fees_quote": state["fees"],
                "feed_status": state["feed_status"],
                "sequence": state["sequence"],
                "writer_available": not self.closed and not self.blocked,
            }

    def reconnect(self) -> Result[Mapping[str, object]]:
        return self._change("reconnect", lambda state: state.update(feed_status="UNSYNCED"))

    def submit(
        self,
        client_id: object,
        side: object,
        amount: object,
        price: object,
        *,
        now_ns: object,
        weight: int = 1,
    ) -> Result[Mapping[str, object]]:
        with self.mutex, localcontext() as context:
            context.prec = 128
            if self.closed or self.blocked:
                return refusal("paper writer is closed or storage-blocked", code="STORAGE_FAILURE")
            if not isinstance(client_id, str) or not client_id.strip() or len(client_id) > 128:
                return refusal("bounded stable client order identity is required")
            if not isinstance(side, str) or side not in {"buy", "sell"}:
                return refusal("only spot buy/sell limit orders are supported")
            parsed = self.market.validate_order(amount, price)
            if is_refusal(parsed):
                return parsed
            quantity, limit = parsed.value
            prior = self.state["orders"].get(client_id)
            if prior:
                if (prior["side"], prior["amount"], prior["price"]) != (side, amount, price):
                    return refusal(
                        "client identity retry must preserve the exact request", code="POLICY"
                    )
                return Ok(self.query())
            if len(self.state["orders"]) >= 1024:
                return refusal("bounded paper order history is full", code="POLICY")
            if type(now_ns) is not int or now_ns < self.state["clock_ns"]:
                return refusal("paper admission clock must be a monotone integer")
            if self.state["feed_status"] != "READY":
                return refusal("same-feed snapshot/reconciliation is required", code="UNSYNCED")
            if now_ns < self.state["received_ns"] or now_ns < self.state["event_ns"]:
                return refusal("admission cannot precede recorded price knowledge")
            if (
                max(now_ns - self.state["event_ns"], now_ns - self.state["received_ns"])
                > self.policy.max_price_age_ns
            ):
                return refusal("recorded price is stale", code="STALE")
            outstanding = sum(
                (
                    exact(o["price"]) * (exact(o["amount"]) - _stored(o["filled"]))
                    for o in self.state["orders"].values()
                    if o["status"] in {"OPEN", "PARTIAL"}
                ),
                Decimal(0),
            )
            if outstanding + quantity * limit > exact(self.policy.max_open_notional):
                return refusal("per-account open notional policy exceeded", code="POLICY")
            if type(weight) is not int or weight <= 0:
                return refusal("request weight must be a positive integer")
            rate = [
                (time, cost)
                for time, cost in self.state["rate"]
                if time > now_ns - self.policy.request_window_ns
            ]
            if sum(cost for _, cost in rate) + weight > self.policy.request_weight_budget:
                return refusal("account request weight budget exhausted", code="RATE_LIMIT")
            reserve = (
                quantity * limit * (1 + exact(self.policy.quote_fee_rate, positive=False))
                if side == "buy"
                else quantity
            )
            asset = self.market.quote if side == "buy" else self.market.base
            balance = self.state["balances"][asset]
            if reserve > _stored(balance["total"]) - _stored(balance["reserved"]):
                return refusal("insufficient unreserved spot balance", code="POLICY")

            def admit(state: dict[str, Any]) -> None:
                state["balances"][asset]["reserved"] = str(_stored(balance["reserved"]) + reserve)
                state["orders"][client_id] = {
                    "client_id": client_id,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "filled": "0",
                    "status": "OPEN",
                    "reserved": str(reserve),
                    "asset": asset,
                    "admission_index": len(state["orders"]),
                    "admitted_ns": now_ns,
                }
                state["rate"] = [*rate, (now_ns, weight)]
                state["clock_ns"] = now_ns

            return self._change("submit", admit)

    def cancel(self, client_id: object) -> Result[Mapping[str, object]]:
        with self.mutex:
            if not isinstance(client_id, str) or client_id not in self.state["orders"]:
                return refusal("cancel requires an existing account-scoped client identity")

            def cancel_order(state: dict[str, Any]) -> None:
                order = state["orders"][client_id]
                if order["status"] in {"CANCELED", "FILLED"}:
                    return
                balance = state["balances"][order["asset"]]
                remaining = _stored(balance["reserved"]) - _stored(order["reserved"])
                balance["reserved"] = "0" if remaining == 0 else str(remaining)
                order.update(status="CANCELED", reserved="0")

            return self._change("cancel", cancel_order)

    def ingest(self, payload: Mapping[str, object]) -> Result[Mapping[str, object]]:
        with self.mutex, localcontext() as context:
            context.prec = 128
            if self.closed or self.blocked:
                return refusal("paper writer is closed or storage-blocked", code="STORAGE_FAILURE")
            try:
                seq, event, received = (
                    payload.get(key) for key in ("sequence", "event_ns", "received_ns")
                )
                if any(type(v) is not int or v < 0 for v in (seq, event, received)):
                    raise ValueError("sequence and recorded times must be nonnegative integers")
                seq, event, received = cast("tuple[int, int, int]", (seq, event, received))
                if received < event or payload.get("origin") not in {
                    "synthetic",
                    "recorded-public",
                }:
                    raise ValueError("recorded origin and knowledge time must be explicit")
                if type(payload.get("snapshot")) is not bool:
                    raise ValueError("snapshot classification must be explicit")
                bid, ask, quantity = (exact(payload.get(key)) for key in ("bid", "ask", "quantity"))
                if (
                    bid > ask
                    or bid % exact(self.market.price_step)
                    or ask % exact(self.market.price_step)
                ):
                    raise ValueError("recorded spread/price precision is invalid")
                if quantity % exact(self.market.amount_step):
                    raise ValueError("recorded liquidity precision is invalid")
            except (ValueError, TypeError) as exc:
                return refusal(str(exc))
            previous = self.state["sequence"]
            if previous is not None and (
                seq <= previous
                or event < self.state["event_ns"]
                or received < self.state["received_ns"]
            ):
                changed = self._change(
                    "out-of-order", lambda state: state.update(feed_status="GAP")
                )
                return (
                    changed
                    if is_refusal(changed)
                    else refusal("out-of-order recorded data", code="GAP")
                )
            if not payload["snapshot"] and (
                self.state["feed_status"] != "READY" or previous is None or seq != previous + 1
            ):
                changed = self._change("gap", lambda state: state.update(feed_status="GAP"))
                return (
                    changed
                    if is_refusal(changed)
                    else refusal("sequence gap requires a fresh snapshot", code="GAP")
                )

            def record(state: dict[str, Any]) -> None:
                state.update(
                    feed_status="READY",
                    sequence=seq,
                    event_ns=event,
                    received_ns=received,
                    bid=str(bid),
                    ask=str(ask),
                )
                # A stale delayed event may be retained but never fills an order.
                if received - event > self.policy.max_price_age_ns:
                    state["feed_status"] = "STALE"
                    return
                available = quantity
                for order in sorted(
                    state["orders"].values(), key=lambda order: order["admission_index"]
                ):
                    if order["status"] not in {"OPEN", "PARTIAL"} or available == 0:
                        continue
                    if event < order["admitted_ns"]:
                        continue
                    limit = exact(order["price"])
                    execution = ask if order["side"] == "buy" else bid
                    if (order["side"] == "buy" and ask > limit) or (
                        order["side"] == "sell" and bid < limit
                    ):
                        continue
                    fill = min(available, exact(order["amount"]) - _stored(order["filled"]))
                    fee = fill * execution * exact(self.policy.quote_fee_rate, positive=False)
                    released = (
                        fill * limit * (1 + exact(self.policy.quote_fee_rate, positive=False))
                        if order["side"] == "buy"
                        else fill
                    )
                    base, quote = (
                        state["balances"][self.market.base],
                        state["balances"][self.market.quote],
                    )
                    sign = 1 if order["side"] == "buy" else -1
                    base["total"] = str(_stored(base["total"]) + sign * fill)
                    quote["total"] = str(_stored(quote["total"]) - sign * fill * execution - fee)
                    balance = state["balances"][order["asset"]]
                    balance["reserved"] = str(_stored(balance["reserved"]) - released)
                    order["reserved"] = str(_stored(order["reserved"]) - released)
                    order["filled"] = str(_stored(order["filled"]) + fill)
                    order["status"] = (
                        "FILLED"
                        if _stored(order["filled"]) == exact(order["amount"])
                        else "PARTIAL"
                    )
                    state["fees"] = str(_stored(state["fees"]) + fee)
                    available -= fill

            return self._change("recorded-tick", record)
