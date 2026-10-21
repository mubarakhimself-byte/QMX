"""`RouterPort` (AD-56): the engine's one door to a provider with no CLI process.

The router is one per host process and runs on its own thread (AD-38). The engine reaches it
through this module: `qmx_host` adopts the relay once at boot, and the nodes and the role lists
ask for it. The engine never imports `qmx_router`, so the port carries the little the engine
needs as plain values: a row's window and class for role lists and chunk plans, and one reply
for an `llm` node.

A process without a router (the fake provider of a unit test, or a script lane before it adopts
one) keeps today's behaviour: `adopted()` is None, the Settings literals stand, and a model node
runs a chat.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal, Protocol, runtime_checkable

type ClassName = Literal["cheap", "mid", "strong"]


@dataclass(frozen=True, slots=True)
class Row:
    """One model registry row, as the engine reads it: what it is called, where it goes, its
    context window and how its tokens are counted (AD-34, AD-39)."""

    qmx_id: str
    profile: str
    model: str
    class_: ClassName = "mid"
    window: int = 200_000
    chars_per_token: float = 3.0
    count_tokens: bool = False
    test_only: bool = False
    """A provider-proof row (`use` test-only in the profile): named only by a role that asks for
    it, never generated into a live list (ruling 105)."""


@dataclass(frozen=True, slots=True)
class Reply:
    """One answer from `complete`: the text, the parsed schema answer when one was asked for,
    the row that served it, the account, and the journal row's identity."""

    text: str
    qmx_id: str
    model: str
    account: str
    usage: Mapping[str, int] = field(default_factory=dict[str, int])
    data: Mapping[str, object] | None = None
    ms: int = 0


class Refused(RuntimeError):
    """The router will not serve this call, or the answer broke the schema. The message is the
    router's reason, already fit to record."""


@runtime_checkable
class RouterPort(Protocol):
    def rows(self) -> tuple[Row, ...]:
        """Every model row the registry holds, in registry order."""
        ...

    async def complete(
        self,
        role_or_model: str,
        messages: Sequence[Mapping[str, object]],
        *,
        schema: Mapping[str, object] | None = None,
        session: str | None = None,
        system: str = "",
        max_tokens: int = 4096,
        roles: Mapping[str, Sequence[str]] | None = None,
    ) -> Reply:
        """One answer from a key or GPT row (AD-56). A plan row is refused by name."""
        ...

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        """Take the pool lease for `affinity` and return the account's id. Every call under the
        same affinity is served by that account while it holds (AD-12, AD-34)."""
        ...

    def let_go(self, affinity: str) -> None:
        """Release the lease `hold` took for `affinity`."""
        ...


class _Registered:
    port: RouterPort | None = None


_registered = _Registered()
"""The host's router, once it adopted one. One process, one router (AD-56)."""


def adopt(port: RouterPort | None) -> None:
    """Make `port` the router this process's engine calls, or forget it with None."""
    _registered.port = port


def adopted() -> RouterPort | None:
    """The router this process adopted, if any."""
    return _registered.port


PLAN: Final = "claude"
"""The plan profile. Its rows run as chats, because only the CLI holds that sign-in."""
