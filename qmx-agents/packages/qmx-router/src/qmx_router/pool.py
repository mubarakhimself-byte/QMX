"""The account pool (engine AD-12): which account of a provider serves one request, and when an
account is out until.

An account is one credential under one provider row, one Claude plan home, or one ChatGPT
sign-in. The pool holds no cap of its own (AD-40): the only numbers it enforces are the ones he
writes on an account, and the providers' own refusals. Every field of `AccountSpec` beyond its
identity is unset by default, so nothing binds unless he sets it.

What it does:

- Returns one account for one request. `least_used` is the default, comparing the provider's
  reading for the account, then its live leases, then how long ago it served; `round_robin` is
  least-recently-served; `fill_first` fills the account he prefers before touching the next. A
  `priority` he sets orders accounts ahead of unset ones under every strategy.
- Holds an account for whoever names an affinity key, so a chat's chunks land on one account and
  a running chat keeps the account it started on.
- Takes a `Classification` (qmx_router.classify) and closes the account for that model: until
  the reset the provider named, for an hour for a generic 429 or a 402, per model for a
  model-entitlement refusal, or benched with no end for a refused credential.
- Raises `NoAccount` only when every eligible account is out, and asks the caller for one inbox
  item once, when the whole provider has been out past `alert_after`.

Everything runs on the caller's loop and thread, in one process: one writer, no lock (the relay
runs on its own event loop).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Final, Literal, get_args

from qmx_router.classify import Classification
from qmx_router.profiles import ProfileName, SecretRef

type Strategy = Literal["fill_first", "round_robin", "least_used"]
type Kind = Literal["key", "plan", "gpt"]
type State = Literal["open", "cooling", "probing", "benched"]
"""`probing` is a cooldown whose end has passed: the next real lease is allowed, and that
request's answer sets the new state. No synthetic probe request is ever made (AD-12, 40 §5)."""

type BackgroundPriority = Literal["normal", "last"]

STRATEGIES: Final = get_args(Strategy.__value__)
DEFAULT_STRATEGY: Final = "least_used"
GENERIC_COOLDOWN_S: Final = 3600.0
"""An hour, for a generic 429's second strike and for a 402 (AD-12)."""
ALERT_AFTER_S: Final = 0.0
"""How long a provider must be wholly out before the one inbox item. Zero alerts at once; it is
a delay on a message, never a limit on work."""
EVERY_MODEL: Final = ""
"""The close-table key for a whole account, as opposed to one model's."""


@dataclass(frozen=True)
class AccountSpec:
    """One account row. Everything after `kind` is his to set, and unset means nothing binds."""

    id: str
    """Unique in the pool: the provider's own name for its one credential, or `<provider>#2`."""
    provider: ProfileName
    kind: Kind = "key"
    credential: SecretRef | None = None
    """A key account's `qmx/<name>` keyring reference. Never the key."""
    home: str = ""
    """A plan account's plan home, or a GPT account's sign-in home."""
    owner: str = ""
    """The one machine that owns a GPT sign-in (AD-12). Empty on a key or plan account."""
    priority: int | None = None
    background_priority: BackgroundPriority = "normal"
    share: float | None = None
    """The share of the provider's live leases this account should carry, 0..1."""
    ceiling: int | None = None
    """The most live leases this account takes at once."""
    cooldown_s: float | None = None
    """How long a refusal other than a provider-named reset closes this account, in seconds."""


@dataclass(frozen=True)
class Lease:
    """One account holding one request, or one affinity key's holder."""

    account: AccountSpec
    provider: ProfileName
    model: str
    affinity: str | None = None


@dataclass(frozen=True)
class Notice:
    """Something the operator should see once: an account benched, or a whole provider out."""

    text: str


class NoAccount(RuntimeError):
    """No eligible account serves this request. `alert` asks the caller for one inbox item."""

    def __init__(self, reason: str, *, alert: bool = False) -> None:
        super().__init__(reason)
        self.alert = alert


@dataclass
class _Close:
    until: datetime | None
    """None for a bench that no clock lifts."""
    kind: str
    reason: str


@dataclass
class _Held:
    spec: AccountSpec
    leases: int = 0
    reading: float | None = None
    last_used: datetime | None = None
    served: int = 0
    """The pool's own counter of when this account last took a lease. Two leases inside one
    clock tick still have an order, which wall time cannot give."""
    strikes: dict[str, int] = field(default_factory=lambda: {})
    """Generic-429 strikes per model, so the same account gets one retry before a cooldown."""
    closed: dict[str, _Close] = field(default_factory=lambda: {})


def _now() -> datetime:
    return datetime.now(UTC)


class AccountPool:
    """One host's accounts, by provider, with the strategy and the closes they carry."""

    def __init__(
        self,
        accounts: Iterable[AccountSpec] = (),
        *,
        strategy: Strategy = DEFAULT_STRATEGY,
        clock: Callable[[], datetime] = _now,
        alert_after: float = ALERT_AFTER_S,
    ) -> None:
        self.strategy = strategy
        self.clock = clock
        self.alert_after = alert_after
        self._accounts: dict[str, _Held] = {}
        self._affinity: dict[str, Lease] = {}
        self._alerted = False
        self._served = 0
        self.sync(accounts)

    def sync(self, accounts: Iterable[AccountSpec]) -> None:
        """Take the account rows as the settings hold them now, keeping every state this pool
        already learned about an id. A row that went away takes its state with it."""
        found = {spec.id: spec for spec in accounts}
        for gone in sorted(set(self._accounts) - set(found)):
            del self._accounts[gone]
        for account_id, spec in found.items():
            held = self._accounts.get(account_id)
            if held is None:
                self._accounts[account_id] = _Held(spec)
            else:
                held.spec = spec

    @property
    def accounts(self) -> tuple[AccountSpec, ...]:
        return tuple(held.spec for held in self._accounts.values())

    def state(self, account_id: str, model: str = EVERY_MODEL) -> tuple[State, datetime | None]:
        """The account's state for `model`, and when it lifts. A bench wins over a cooldown."""
        held = self._accounts.get(account_id)
        if held is None:
            return "open", None
        now = self.clock()
        closed = held.closed.get(EVERY_MODEL)
        if closed is not None and closed.until is None:
            return "benched", None
        for key in (EVERY_MODEL, model):
            found = held.closed.get(key)
            if found is None:
                continue
            if found.until is None:
                return "benched", None
            if now < found.until:
                return "cooling", found.until
            return "probing", found.until
        return "open", None

    def lease(
        self, *, provider: ProfileName | str, model: str, affinity: str | None = None
    ) -> Lease:
        """One account for one request. An affinity key gets the account it already holds while
        that account still serves the model."""
        name = ProfileName(provider)
        if affinity is not None:
            held = self._affinity.get(affinity)
            if held is not None and held.account.provider == name:
                if self._usable(held.account.id, model):
                    return held
                self._affinity.pop(affinity, None)
                self.release(held)
        chosen = self._choose(name, model)
        if chosen is None:
            raise self._no_account(name, model)
        self._served += 1
        self._accounts[chosen.id].leases += 1
        self._accounts[chosen.id].served = self._served
        self._accounts[chosen.id].last_used = self.clock()
        if affinity is not None:
            held_lease = Lease(chosen, name, model, affinity)
            self._affinity[affinity] = held_lease
            return held_lease
        return Lease(chosen, name, model)

    def release(self, lease: Lease) -> None:
        """Give the account back. Idempotent, and never below zero."""
        held = self._accounts.get(lease.account.id)
        if held is not None and held.leases > 0:
            held.leases -= 1
        if lease.affinity is not None and self._affinity.get(lease.affinity) == lease:
            del self._affinity[lease.affinity]

    def release_affinity(self, affinity: str) -> None:
        """Give back whatever `affinity` holds, for a chat or a run that ended."""
        held = self._affinity.pop(affinity, None)
        if held is not None:
            self.release(held)

    def settle(
        self,
        lease: Lease,
        error: Classification | None = None,
        *,
        reading: float | None = None,
    ) -> Notice | None:
        """Record how one request ended. A request's own hold is given back here; an affinity's
        hold stays with the chat or run that named it."""
        held = self._accounts.get(lease.account.id)
        if held is None:
            return None
        now = self.clock()
        held.last_used = now
        if reading is not None:
            held.reading = reading
        notice: Notice | None = None
        if error is None:
            self._lift(held, lease.model, now)
        else:
            notice = self._close(held, lease.model, error, now)
        if lease.affinity is None:
            self.release(lease)
        self._alerted = False
        return notice

    def accounts_view(self) -> tuple[dict[str, object], ...]:
        """Every account as the usage page and the Accounts screen read it."""
        return tuple(self._view(held) for held in self._accounts.values())

    def _view(self, held: _Held) -> dict[str, object]:
        now = self.clock()
        state, until = self.state(held.spec.id)
        closed = held.closed.get(EVERY_MODEL)
        reason = "" if closed is None else closed.reason
        return {
            "id": held.spec.id,
            "provider": str(held.spec.provider),
            "kind": held.spec.kind,
            "state": state,
            "until": None if until is None else until.isoformat(),
            "reason": reason,
            "leases": held.leases,
            "reading": held.reading,
            "last_used": None if held.last_used is None else held.last_used.isoformat(),
            "cooled_models": sorted(
                key for key, close in held.closed.items() if key and close.until is not None
            ),
            "as_of": now.isoformat(),
        }

    def _usable(self, account_id: str, model: str) -> bool:
        state, _ = self.state(account_id, model)
        if state in ("cooling", "benched"):
            return False
        held = self._accounts[account_id]
        if held.spec.ceiling is not None and held.leases >= held.spec.ceiling:
            return False
        return self._share_room(held)

    def _choose(self, provider: ProfileName, model: str) -> AccountSpec | None:
        eligible = [
            held
            for held in self._accounts.values()
            if held.spec.provider == provider and self._usable(held.spec.id, model)
        ]
        if not eligible:
            return None
        normal = [held for held in eligible if held.spec.background_priority == "normal"]
        return self._order(normal or eligible)[0].spec

    def _order(self, held: list[_Held]) -> list[_Held]:
        """`priority` first, then the strategy's own order, then the pool's declaration order."""
        declared = {id(item): at for at, item in enumerate(self._accounts.values())}
        return sorted(held, key=lambda item: (_priority_key(item.spec), self._rank(item, declared)))

    def _rank(self, held: _Held, declared: dict[int, int]) -> tuple[float, int, float, int]:
        """One comparable key for the active strategy. `least_used` reads the provider's
        reading first, then the live leases; the two rotation strategies read when the account
        last served. Ties always fall to the declaration order."""
        at = declared[id(held)]
        if self.strategy == "fill_first":
            return (0.0, 0, 0.0, at)
        if self.strategy == "round_robin":
            return (0.0, 0, float(held.served), at)
        reading = held.reading if held.reading is not None else 0.0
        return (reading, held.leases, float(held.served), at)

    def _share_room(self, held: _Held) -> bool:
        """True when this account is under the share he set, measured against the provider's
        live leases, so it converges on its share from either side. A share of zero takes
        nothing; an unset share never binds."""
        share = held.spec.share
        if share is None:
            return True
        if share <= 0:
            return False
        provider = held.spec.provider
        live = sum(
            item.leases for item in self._accounts.values() if item.spec.provider == provider
        )
        return live == 0 or held.leases / live < share

    def _close(
        self, held: _Held, model: str, error: Classification, now: datetime
    ) -> Notice | None:
        """Apply one classification. Returns the notice the caller should show, if any."""
        spec = held.spec
        override = spec.cooldown_s
        if error.kind in ("content", "transient", "fatal"):
            return None
        if error.kind == "auth":
            held.closed[EVERY_MODEL] = _Close(None, error.kind, error.message)
            return Notice(
                f"{spec.id} is benched: {_reason(error)}. It serves again when its credential "
                "is fixed and the pool is restarted."
            )
        if error.kind == "model_entitlement":
            held.closed[model] = _Close(None, error.kind, error.message)
            return Notice(f"{spec.id} cannot serve {model}: {_reason(error)}.")
        if error.kind == "billing":
            until = error.until(now) or now + timedelta(
                seconds=GENERIC_COOLDOWN_S if override is None else override
            )
            held.closed[model] = _Close(until, error.kind, error.message)
            return None
        # rate_limit
        reset = error.until(now)
        if error.usage_limit and reset is not None:
            held.closed[model] = _Close(reset, error.kind, error.message)
            held.strikes.pop(model, None)
            return None
        if reset is not None and reset > now and not error.usage_limit:
            held.closed[model] = _Close(reset, error.kind, error.message)
            held.strikes.pop(model, None)
            return None
        # A generic 429 with no reset, or one whose reset has already passed, on an account that
        # may have been probing: one retry on the same account, then the hour (42 N13).
        strikes = held.strikes.get(model, 0) + 1
        held.strikes[model] = strikes
        if strikes == 1:
            held.closed.pop(model, None)
            return None
        until = now + timedelta(seconds=GENERIC_COOLDOWN_S if override is None else override)
        held.closed[model] = _Close(until, error.kind, error.message)
        held.strikes.pop(model, None)
        return None

    def _lift(self, held: _Held, model: str, now: datetime) -> None:
        """A served request ends a probing state, and the strikes it carried."""
        for key in (EVERY_MODEL, model):
            found = held.closed.get(key)
            if found is not None and found.until is not None and now >= found.until:
                del held.closed[key]
        held.strikes.pop(model, None)

    def _no_account(self, provider: ProfileName, model: str) -> NoAccount:
        """The refusal, and whether this episode has earned the one inbox item."""
        rows = [held for held in self._accounts.values() if held.spec.provider == provider]
        if not rows:
            return NoAccount(f"no account is configured for {provider}")
        names = ", ".join(held.spec.id for held in rows)
        ends = [until for held in rows if (until := self.state(held.spec.id, model)[1])]
        latest = max(ends) if ends else None
        tail = "" if latest is None else f"; the last is out until {latest.isoformat()}"
        alert = False
        if not self._alerted and self._past_alert_after(latest):
            alert = True
            self._alerted = True
        return NoAccount(
            f"every account for {provider} is out for {model} ({names}){tail}",
            alert=alert,
        )

    def _past_alert_after(self, latest: datetime | None) -> bool:
        if self.alert_after <= 0:
            return True
        if latest is None:
            return True
        return latest - self.clock() <= timedelta(seconds=self.alert_after)


def _priority_key(spec: AccountSpec) -> tuple[int, int]:
    """A priority he set puts the account ahead of one he left unset; lower goes first."""
    if spec.priority is None:
        return (1, 0)
    return (0, spec.priority)


def _reason(error: Classification) -> str:
    text = error.message.strip() or f"HTTP {error.status}"
    return f"{error.kind}: {text[:200]}"
