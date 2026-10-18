"""The plan credential, as a value QMA code cannot read.

The CLI signs in with its own /login and keeps its own token (hard rule 1). In a
session that may call Claude, the CLI sends that token in `Authorization` to the
gateway, because one CLI process has one base URL and mixing providers inside one
session needs a router on that URL (02b C items 1 and 3). This module is how the
gateway carries the bytes for one hop without reading them.

What "never reads" means here, in code:
- The header parser wraps the credential header value in `Sealed` the moment it is
  split from the other headers (`server.split_headers`). No str or bytes copy is
  kept.
- `Sealed` has no accessor, no repr, no str, no format, no equality, no hash, no
  pickle and no copy. Logging it, comparing it, persisting it or putting it in an
  event raises.
- The only exit is `forward_into`, which takes a `PlanUpstreamKey`. One key exists,
  minted inside `lanes.py` and handed only to the plan lane, whose upstream host is
  a module constant. So the bytes can reach exactly one place: api.anthropic.com.
- Every other lane calls `discard()`. The value is never compared to anything, so
  QMA cannot even learn whether two requests carry the same token.

Enforced by structure, strongest first (per encode-lessons-in-structure):
1. The type above.
2. An import-linter contract: only `qma_gateway.lanes` imports `PlanUpstreamKey`.
3. A CI grep that fails on `_Sealed__` or `__closure__` anywhere in the package.
4. Live check L1 (design.md): a canary token never appears in any QMX file, log,
   database, event or non-Anthropic upstream.
"""

from __future__ import annotations

from typing import Final, NoReturn, final


@final
class PlanUpstreamKey:
    """Capability to unseal. Constructed once, in `lanes.py`. Not exported."""

    __slots__ = ()


@final
class Sealed:
    """Opaque credential bytes for exactly one upstream hop.

    The value lives in a closure cell, not an attribute, so `vars()` and
    attribute access show nothing.
    """

    __slots__ = ("_emit", "_drop")

    def __init__(self, raw: bytes) -> None:
        # TODO: hold `raw` in a closure; _emit(key, sink) appends the header to sink
        # only if key is the module's one PlanUpstreamKey; _drop() clears the cell.
        raise NotImplementedError

    def forward_into(self, key: PlanUpstreamKey, sink: list[tuple[bytes, bytes]]) -> None:
        """Append ("authorization", raw) to the outbound header list, then drop the
        cell. Single use: a second call raises."""
        raise NotImplementedError

    def discard(self) -> None:
        """Drop the cell. Idempotent."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return "<sealed>"

    __str__ = __repr__

    def __format__(self, spec: str) -> NoReturn:
        raise TypeError("sealed credential")

    def __eq__(self, other: object) -> NoReturn:
        raise TypeError("sealed credential")

    __hash__ = None  # type: ignore[assignment]

    def __reduce__(self) -> NoReturn:
        raise TypeError("sealed credential")

    def __copy__(self) -> NoReturn:
        raise TypeError("sealed credential")

    def __deepcopy__(self, memo: object) -> NoReturn:
        raise TypeError("sealed credential")


CREDENTIAL_HEADERS: Final[frozenset[bytes]] = frozenset({b"authorization", b"x-api-key"})
"""Header names whose values are sealed on arrival, whatever lane the request takes."""
