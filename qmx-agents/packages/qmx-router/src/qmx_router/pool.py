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
from typing import Final, Literal

from qmx_router.classify import Classification
from qmx_router.facts import Fact, FactState, FactStore
from qmx_router.profiles import ProfileName, SecretRef

type Strategy = Literal["fill_first", "round_robin", "least_used"]
type Kind = Literal["key", "plan", "gpt"]
type State = Literal["open", "cooling", "probing", "benched"]
"""`probing` is a cooldown whose end has passed: the next real lease is allowed, and that
request's answer sets the new state. No synthetic probe request is ever made (AD-12, 40 §5)."""

type BackgroundPriority = Literal["normal", "last"]

DEFAULT_STRATEGY: Final = "least_used"
GENERIC_COOLDOWN_S: Final = 3600.0
"""An hour, for a generic 429's second strike and for a 402 (AD-12)."""
ALERT_AFTER_S: Final = 0.0
"""How long a provider must be wholly out before the one inbox item. Zero alerts at once; it is
a delay on a message, never a limit on work."""
EVERY_MODEL: Final = ""
"""The close-table key for a whole account, as opposed to one model's."""
LEASE_TTL_S: Final = 900.0
"""How long one live lease counts on the other machine when a pool is attached to a shared
`FactStore`. A lease that lapsed there stops counting, so a machine that died mid-request does
not hold a key's concurrency forever."""


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
    id: str = ""
    """This lease on the shared store. Empty when the pool has no store to publish to."""


@dataclass(frozen=True)
class Notice:
    """Something the operator should see once: an account benched, or a whole provider out."""

    text: str


@dataclass(frozen=True)
class AccountView:
    """One account as the usage page and the Accounts screen read it (AD-12, RTR4). The reading
    is the provider's own number, 0..1 where it reports one, and `None` where it reports none;
    the leases are live, not a count of past work."""

    id: str
    provider: str
    kind: Kind
    state: State
    until: datetime | None
    reason: str
    leases: int
    reading: float | None
    last_used: datetime | None
    cooled_models: tuple[str, ...]
    as_of: datetime

    def document(self) -> dict[str, object]:
        """The JSON the usage page carries. Times are RFC 3339, as every QMX door writes them."""
        return {
            "id": self.id,
            "provider": self.provider,
            "kind": self.kind,
            "state": self.state,
            "until": None if self.until is None else self.until.isoformat(),
            "reason": self.reason,
            "leases": self.leases,
            "reading": self.reading,
            "last_used": None if self.last_used is None else self.last_used.isoformat(),
            "cooled_models": list(self.cooled_models),
            "as_of": self.as_of.isoformat(),
        }


class NoAccount(RuntimeError):
    """No eligible account serves this request. `alert` asks the caller for one inbox item."""

    def __init__(self, reason: str, *, alert: bool = False) -> None:
        super().__init__(reason)
        self.alert = alert


class OwnedElsewhere(RuntimeError):
    """A GPT sign-in this machine does not own. Two sign-ins of one ChatGPT account revoke each
    other, so the second machine is refused rather than allowed to take the first one down
    (AD-12, one owner machine per sign-in)."""


@dataclass
class _Close:
    until: datetime | None
    """None for a bench that no clock lifts."""
    kind: str
    reason: str
    observed_at: float = 0.0
    """When the machine that learned it saw it. A fact older than this loses, which is what keeps
    a late message from reopening an account the other side already closed."""


@dataclass
class _Held:
    spec: AccountSpec
    leases: int = 0
    reading: float | None = None
    last_used: datetime | None = None
    served: int = 0
    """The pool's own counter of when this account last took a lease. Two leases inside one
    clock tick still have an order, which wall time cannot give."""
    tokens: list[str] = field(default_factory=lambda: [])
    """The lease ids this account holds locally, so a release drops the right shared row."""
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
        site: str = "",
        shared: FactStore | None = None,
    ) -> None:
        self.strategy = strategy
        self.clock = clock
        self.alert_after = alert_after
        self.site = site
        """This machine's name in the shared store: facts carry it, leases are held under it."""
        self.shared = shared
        """The other machine's facts and live leases. None means a single host, which is how
        every caller ran before the server phase."""
        self._accounts: dict[str, _Held] = {}
        self._affinity: dict[str, Lease] = {}
        self._owners: dict[str, str] = {}
        """The one machine that owns each GPT sign-in, seeded from the rows and moved by
        `claim_sign_in`."""
        self._preferred: dict[str, str] = {}
        """The account each affinity started on: it returns there when that account serves the
        model again, which is what a chat's turn start does after a cooldown."""
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
            if spec.owner:
                self._owners[account_id] = spec.owner
            elif account_id not in self._owners:
                self._owners.pop(account_id, None)

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
        """One account for one request.

        An affinity key holds one account for as long as that chat or run lives. A refusal moves
        it to another account, and it moves back to the account it started on at the next lease
        once that account serves the model again (AD-12, "moves back at the next turn start when
        the cooldown lifts")."""
        name = ProfileName(provider)
        if affinity is not None:
            return self._lease_affinity(name, model, affinity)
        chosen = self._choose(name, model)
        if chosen is None:
            raise self._no_account(name, model)
        return Lease(chosen, name, model, id=self._serve(chosen))

    def _lease_affinity(self, provider: ProfileName, model: str, affinity: str) -> Lease:
        held = self._affinity.get(affinity)
        if held is not None and held.account.provider != provider:
            self.release(held)
            held = None
        preferred = self._preferred.get(affinity)
        back = preferred is not None and self._usable(preferred, model)
        if held is not None and (not back or held.account.id == preferred):
            if self._usable(held.account.id, model):
                return held
            self.release(held)
            held = None
        if back and preferred is not None:
            chosen = self._accounts[preferred].spec
        else:
            chosen = self._choose(provider, model)
        if chosen is None:
            raise self._no_account(provider, model)
        self._preferred.setdefault(affinity, chosen.id)
        minted = Lease(chosen, provider, model, affinity, id=self._serve(chosen))
        self._affinity[affinity] = minted
        return minted

    def _serve(self, spec: AccountSpec) -> str:
        """One account takes one lease now: the count and the rotation clock move together, and
        the lease is published so the other machine counts it."""
        self._served += 1
        held = self._accounts[spec.id]
        held.leases += 1
        held.served = self._served
        held.last_used = self.clock()
        lease_id = f"{self.site}:{self._served}"
        held.tokens.append(lease_id)
        if self.shared is not None:
            self.shared.hold(spec.id, lease_id, self.clock().timestamp() + LEASE_TTL_S)
        return lease_id

    def release(self, lease: Lease) -> None:
        """Give the account back. Idempotent, and never below zero."""
        held = self._accounts.get(lease.account.id)
        if held is not None and held.leases > 0:
            held.leases -= 1
            if lease.id and lease.id in held.tokens:
                held.tokens.remove(lease.id)
                if self.shared is not None:
                    self.shared.drop(lease.account.id, lease.id)
        if lease.affinity is not None and self._affinity.get(lease.affinity) == lease:
            del self._affinity[lease.affinity]

    def release_affinity(self, affinity: str) -> None:
        """Give back whatever `affinity` holds, for a chat or a run that ended."""
        held = self._affinity.pop(affinity, None)
        self._preferred.pop(affinity, None)
        if held is not None:
            self.release(held)

    def release_prefix(self, prefix: str) -> None:
        """Give back every affinity whose key starts with `prefix`: a chat that ended holds one
        per provider it reached."""
        for key in [key for key in self._affinity if key.startswith(prefix)]:
            self.release_affinity(key)
        for key in [key for key in self._preferred if key.startswith(prefix)]:
            self._preferred.pop(key, None)

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

    def facts(self) -> tuple[Fact, ...]:
        """Every close and reading this pool carries, as facts the other machine can apply. One
        fact per account and model, stamped with this machine's name and its own clock."""
        now = self.clock().timestamp()
        found: list[Fact] = []
        for held in self._accounts.values():
            state, until = self.state(held.spec.id)
            if held.closed or held.reading is not None:
                found.append(
                    Fact(
                        account=held.spec.id,
                        model=EVERY_MODEL,
                        state=state,
                        until=until.timestamp() if until else None,
                        reading=held.reading,
                        observed_at=now,
                        site=self.site,
                    )
                )
            for model, closed in held.closed.items():
                if not model:
                    continue
                found.append(
                    Fact(
                        account=held.spec.id,
                        model=model,
                        state=_fact_state(closed),
                        until=closed.until.timestamp() if closed.until else None,
                        reading=None,
                        observed_at=now,
                        site=self.site,
                    )
                )
        return tuple(found)

    def apply_facts(self, incoming: Iterable[Fact]) -> int:
        """Take the other machine's facts, newest first. A fact about an account this pool does
        not know is dropped: a row arriving before the settings do is not an account."""
        taken = 0
        for fact in incoming:
            held = self._accounts.get(fact.account)
            if held is None:
                continue
            key = fact.model or EVERY_MODEL
            existing = held.closed.get(key)
            if existing is not None and existing.observed_at > fact.observed_at:
                continue
            if fact.state == "open":
                if existing is not None:
                    del held.closed[key]
                if fact.reading is not None:
                    held.reading = fact.reading
                taken += 1
                continue
            until = datetime.fromtimestamp(fact.until, UTC) if fact.until is not None else None
            held.closed[key] = _Close(until, fact.state, f"learned from {fact.site or 'a peer'}")
            held.closed[key].observed_at = fact.observed_at
            if fact.reading is not None:
                held.reading = fact.reading
            taken += 1
        return taken

    def gpt_owners(self) -> dict[str, str]:
        """The one machine that owns each GPT sign-in, by account id. The host reads this before
        it starts a sign-in, and `qmx_router.gpt.siwc` refuses an account this names another
        machine for."""
        return dict(self._owners)

    def owner_of(self, account_id: str) -> str:
        """The owner of one sign-in, empty when no row names one."""
        return self._owners.get(account_id, "")

    def claim_sign_in(self, account_id: str, machine: str) -> None:
        """Record this machine as the owner of a sign-in, or refuse when another machine owns it.
        A second sign-in of one ChatGPT account revokes the first, so this is a refusal and not a
        warning (AD-12)."""
        owner = self._owners.get(account_id, "")
        if owner and machine and owner != machine:
            raise OwnedElsewhere(
                f"the ChatGPT sign-in {account_id} belongs to {owner}, not {machine}; "
                "signing it in here would revoke the one there"
            )
        if machine:
            self._owners[account_id] = machine

    def accounts_view(self) -> tuple[AccountView, ...]:
        """Every account as the usage page and the Accounts screen read it."""
        return tuple(self._view(held) for held in self._accounts.values())

    def _view(self, held: _Held) -> AccountView:
        now = self.clock()
        state, until = self.state(held.spec.id)
        closed = held.closed.get(EVERY_MODEL)
        return AccountView(
            id=held.spec.id,
            provider=str(held.spec.provider),
            kind=held.spec.kind,
            state=state,
            until=until,
            reason="" if closed is None else closed.reason,
            leases=held.leases,
            reading=held.reading,
            last_used=held.last_used,
            cooled_models=tuple(
                sorted(key for key, close in held.closed.items() if key and close.until is not None)
            ),
            as_of=now,
        )

    def _usable(self, account_id: str, model: str) -> bool:
        state, _ = self.state(account_id, model)
        if state in ("cooling", "benched"):
            return False
        held = self._accounts[account_id]
        if held.spec.ceiling is not None and held.leases >= held.spec.ceiling:
            return False
        if (
            self.shared is not None
            and held.spec.ceiling is not None
            and not self.shared.room(account_id, held.spec.ceiling)
        ):
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


def _fact_state(closed: _Close) -> FactState:
    """The state a close publishes: a bench has no deadline, a cooling row has one."""
    return "benched" if closed.until is None else "cooling"


def _reason(error: Classification) -> str:
    text = error.message.strip() or f"HTTP {error.status}"
    return f"{error.kind}: {text[:200]}"
