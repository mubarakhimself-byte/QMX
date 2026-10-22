"""Intent claims on the Hub (Library AD-24, engine AD-27).

A claim is a compare-and-swap on `refs/claims/<intent_key>` of the Hub store, which is the primary
from the Contabo setup on. The store implements the swap; this module is the part that belongs to
the Hub process: the batch renewal one heartbeat makes, the sweep that prunes released and expired
claims, and the fallback the engine takes when the Hub cannot be reached.

The fallback is the honest cost AD-24 names: a claimant that cannot reach the Hub claims in its
own store and accepts a rare duplicate, which the intent key dedupes when the output lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from qmx_library.port import Claim, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store


class ClaimsDoor(Protocol):
    """The two calls `acquire` makes on the Hub; `HubClient` is one."""

    def claim(self, intent_key: str, run_id: str, ttl: int) -> Claim: ...


@dataclass(frozen=True, slots=True)
class Acquired:
    claim: Claim
    where: Literal["hub", "local"]
    """`local` means the Hub was unreachable and this claim buys only local exclusion."""


def renew(store: Store, run_id: str, ttl: int) -> list[str]:
    """Every claim `run_id` holds, extended in one call (engine AD-65)."""
    return store.renew_claims(Principal("engine", store.name), run_id, ttl)


def sweep(store: Store) -> int:
    """Prune released and expired claims; they are never bucketed (AD-24)."""
    return store.sweep_claims()


def held_for(store: Store, intent_key: str) -> tuple[str, str] | None:
    """The run holding a live claim and when it expires, or None."""
    return store.claim_holder(intent_key)


def acquire(
    store: Store,
    door: ClaimsDoor | None,
    *,
    intent_key: str,
    run_id: str,
    ttl: int,
) -> Acquired:
    """Claim on the Hub when it answers; otherwise claim here and accept a duplicate (AD-27)."""
    if door is not None:
        try:
            return Acquired(door.claim(intent_key, run_id, ttl), "hub")
        except (OSError, LibraryRefused) as unreachable:
            if isinstance(unreachable, LibraryRefused) and unreachable.code == "invalid_claim":
                raise
    return Acquired(store.claim(Principal("engine", store.name), intent_key, run_id, ttl), "local")
