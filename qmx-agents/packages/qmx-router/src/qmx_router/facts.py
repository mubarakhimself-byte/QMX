"""What the two pools know about one provider, and how they agree (AD-12, two hosts).

The PC and the router on the server each run a pool. A cooldown learned on one must bind on the
other within one sync, or a key's budget is spent on the account the other side just benched. So
the pool's state travels as facts:

    (account, model, state, until, reading, observed_at)

`observed_at` is when the *observer* saw it, on its own clock, and the newest fact wins. Nothing
is voted on and nothing is merged by kind: a cooling fact from a minute ago loses to an open fact
from a second ago, and an old cooldown that arrives late cannot resurrect itself. Ties on
`observed_at` fall to `site`, which keeps both machines converging on the same row instead of
each keeping its own.

Concurrency is the second half, and it is not a fact: a lease is live or it is not. Two machines
share one key's concurrency by exchanging the live leases with the facts, each with its expiry,
so a machine that crashed mid-request stops counting after its lease lapses. One sync carries
both, which is why `State` is the wire type and `Fact` is not.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Any, Final, Literal, cast

type FactState = Literal["open", "cooling", "probing", "benched"]
TYPE_ORDER: Final[tuple[FactState, ...]] = ("benched", "cooling", "probing", "open")
"""Most closed first. Only used to break an otherwise exact tie, so ordering is total."""
EVERY_MODEL: Final = ""
"""The fact key for a whole account, matching the pool's own close table."""
MAX_LEASES_PER_ACCOUNT: Final = 256
"""A boundary guard on a message from another machine, not a cap on his work."""


@dataclass(frozen=True)
class Fact:
    """One account's state for one model, as some machine saw it."""

    account: str
    model: str
    state: FactState
    until: float | None
    reading: float | None
    observed_at: float
    site: str = ""

    def key(self) -> tuple[str, str]:
        return (self.account, self.model)

    def order(self) -> tuple[float, str, str]:
        """Newest first: `observed_at`, then `site` so two machines with one clock still agree,
        then `state` so a cooling and an open fact at the same instant resolve the same way."""
        return (self.observed_at, self.site, _rank(self.state))

    def document(self) -> dict[str, object]:
        return {
            "account": self.account,
            "model": self.model,
            "state": self.state,
            "until": None if self.until is None else float(self.until),
            "reading": None if self.reading is None else float(self.reading),
            "observed_at": float(self.observed_at),
            "site": self.site,
        }


@dataclass(frozen=True)
class LeaseRow:
    """One live lease, as the other machine must count it."""

    account: str
    holder: str
    expires_at: float

    def document(self) -> dict[str, object]:
        return {
            "account": self.account,
            "holder": self.holder,
            "expires_at": float(self.expires_at),
        }


@dataclass(frozen=True)
class State:
    """One sync message: every fact this machine holds, and every lease it holds live. Frozen,
    because a message that is edited after it is sent is not a message."""

    facts: tuple[Fact, ...] = ()
    leases: tuple[LeaseRow, ...] = ()

    def document(self) -> dict[str, object]:
        return {
            "facts": [fact.document() for fact in self.facts],
            "leases": [row.document() for row in self.leases],
        }

    @classmethod
    def from_document(cls, document: object) -> State:
        """Parse a message from the other machine. Every field is checked here: this is the one
        place a fact off the tailnet is trusted, and a skipped row is better than a raised one."""
        if not isinstance(document, dict):
            return cls()
        data = cast("dict[str, Any]", document)
        facts = tuple(fact for row in _rows(data.get("facts")) if (fact := _fact(row)) is not None)
        leases = tuple(
            row
            for item in _rows(data.get("leases"))[: MAX_LEASES_PER_ACCOUNT * 8]
            if (row := _lease(item)) is not None
        )
        return cls(facts=facts, leases=leases)


def _rows(value: object) -> list[object]:
    return cast("list[object]", value) if isinstance(value, list) else []


def _fact(row: object) -> Fact | None:
    if not isinstance(row, dict):
        return None
    data = cast("dict[str, Any]", row)
    account = data.get("account")
    state = data.get("state")
    observed_at = data.get("observed_at")
    if not isinstance(account, str) or not account:
        return None
    if state not in TYPE_ORDER:
        return None
    if not isinstance(observed_at, int | float) or not math.isfinite(observed_at):
        return None
    model = data.get("model")
    until = data.get("until")
    reading = data.get("reading")
    site = data.get("site")
    return Fact(
        account=account,
        model=model if isinstance(model, str) else EVERY_MODEL,
        state=state,
        until=float(until) if isinstance(until, int | float) else None,
        reading=float(reading) if isinstance(reading, int | float) else None,
        observed_at=float(observed_at),
        site=site if isinstance(site, str) else "",
    )


def _lease(row: object) -> LeaseRow | None:
    if not isinstance(row, dict):
        return None
    data = cast("dict[str, Any]", row)
    account = data.get("account")
    holder = data.get("holder")
    expires_at = data.get("expires_at")
    if not isinstance(account, str) or not account or not isinstance(holder, str):
        return None
    if not isinstance(expires_at, int | float) or not math.isfinite(expires_at):
        return None
    return LeaseRow(account=account, holder=holder, expires_at=float(expires_at))


class FactStore:
    """One machine's view of every account the pools share. One writer, one thread: the relay
    owns it, so there is no lock and no second source of truth."""

    def __init__(
        self,
        site: str,
        *,
        clock: Callable[[], float] = time.time,
        facts: Iterable[Fact] = (),
    ) -> None:
        self.site = site
        self.clock = clock
        self._facts: dict[tuple[str, str], Fact] = {}
        self._leases: dict[tuple[str, str], LeaseRow] = {}
        self.accepted = 0
        """How many facts this store took. A sync that changes nothing increments nothing, which
        is what the lane reads to say "one sync"."""
        for fact in facts:
            self.apply(fact)

    def apply(self, fact: Fact) -> bool:
        """Take `fact` when it is newer than what this store holds. False means it lost, which
        is the normal case for a fact that crossed the other machine's change in flight."""
        held = self._facts.get(fact.key())
        if held is not None and fact.order() <= held.order():
            return False
        self._facts[fact.key()] = fact
        self.accepted += 1
        return True

    def merge(self, state: State) -> int:
        """Every fact and lease of one sync. Returns how many facts were newer, so a caller can
        say "one sync" rather than "one push"."""
        taken = sum(1 for fact in state.facts if self.apply(fact))
        for row in state.leases:
            self.hold(row.account, row.holder, row.expires_at)
        return taken

    def state(
        self, account: str, model: str, now: float | None = None
    ) -> tuple[FactState, float | None]:
        """The account's state for `model`: the model's own fact when it has one, else the
        account-wide fact, else open. A passed deadline reads `probing`, the same way the pool's
        own close table does, so the next real request sets the new state."""
        at = self._now() if now is None else now
        for key in ((account, model), (account, EVERY_MODEL)):
            found = self._facts.get(key)
            if found is None:
                continue
            if found.until is not None and at >= found.until:
                if found.state == "benched":
                    return "benched", None
                return "probing", found.until
            return found.state, found.until
        return "open", None

    def fact(self, account: str, model: str = EVERY_MODEL) -> Fact | None:
        return self._facts.get((account, model))

    def reading(self, account: str, model: str) -> float | None:
        """The provider's own number, newest first: the model's fact, else the account's."""
        now = self._now()
        for key in ((account, model), (account, EVERY_MODEL)):
            found = self._facts.get(key)
            if found is None or found.reading is None:
                continue
            if found.state in ("cooling", "benched") and (found.until is None or now < found.until):
                continue
            return found.reading
        return None

    def hold(self, account: str, holder: str, expires_at: float) -> None:
        """Record a live lease, keeping the later expiry of the two: a lease renewed on the other
        machine is not shortened by a message that crossed it."""
        key = (account, holder)
        held = self._leases.get(key)
        if held is not None and held.expires_at >= expires_at:
            return
        self._leases[key] = LeaseRow(account=account, holder=holder, expires_at=expires_at)

    def drop(self, account: str, holder: str) -> None:
        self._leases.pop((account, holder), None)

    def leases(self, account: str, now: float | None = None) -> int:
        """Live leases this account carries on both machines. A lease whose expiry passed is
        gone, so a machine that died mid-request stops counting it."""
        at = self._now() if now is None else now
        self.prune(at)
        return sum(1 for row in self._leases.values() if row.account == account)

    def room(self, account: str, ceiling: int | None, now: float | None = None) -> bool:
        """True when one more lease fits under `ceiling`, using the shared count."""
        if ceiling is None:
            return True
        return self.leases(account, now) < ceiling

    def prune(self, now: float | None = None) -> int:
        at = self._now() if now is None else now
        gone = [key for key, row in self._leases.items() if row.expires_at <= at]
        for key in gone:
            del self._leases[key]
        return len(gone)

    def snapshot(self) -> State:
        """What one sync carries: every fact, and every lease still live."""
        self.prune()
        facts = tuple(self._facts[key] for key in sorted(self._facts))
        leases = tuple(self._leases[key] for key in sorted(self._leases))
        return State(facts=facts, leases=leases)

    def aged(self, account: str, model: str, seconds: float) -> Fact | None:
        """The fact, restamped `seconds` further on, for a machine that reports its own change
        rather than one it received."""
        found = self._facts.get((account, model))
        if found is None:
            return None
        return replace(found, observed_at=self._now() + seconds)

    def _now(self) -> float:
        return float(self.clock())


def _rank(state: FactState) -> str:
    """A total order over the four states for the exact-tie case. `TYPE_ORDER` is most closed
    first, so a lower index is the more conservative row and wins a tie."""
    return f"{TYPE_ORDER.index(state)}"


def close(
    account: str,
    model: str,
    state: FactState,
    *,
    until: float | None = None,
    reading: float | None = None,
    site: str = "",
    clock: Callable[[], float] = time.time,
) -> Fact:
    """One fact to publish after a real request: the shape a caller wants most of the time."""
    return Fact(
        account=account,
        model=model,
        state=state,
        until=until,
        reading=reading,
        observed_at=float(clock()),
        site=site,
    )
