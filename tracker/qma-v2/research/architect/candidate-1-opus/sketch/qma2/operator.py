"""Minting the operator principal. Import-linted: only qmx_control.server may import this.

The operator principal is a console session made by one-time pairing:
1. `qmx host start` prints/opens  http://localhost:8766/console/pair#code=<one-time>
   (code lives only in qmx-control memory, single use, 5 minutes).
2. The console exchanges it at POST /api/operator/pair for an HttpOnly, SameSite=Strict
   cookie. harness.db stores only the cookie's hash and expiry (30 days).
3. Routes whose Op.who is OPERATOR resolve the cookie to an OperatorProof.

Agents never hold it: hosts have only their stdio link (no HTTP credential at all), MCP
and the link never carry operator rows, and the bearer control token maps to the
`client` principal, which operator rows reject. Same-user code could still scrape a
browser cookie store or process memory; that is the documented speed bump (design.md,
tension 2). A WebAuthn/passkey `PresenceProof` is the reserved upgrade for signing.
"""

from __future__ import annotations

from qma2.model import OperatorProof


def new_pairing_code() -> str:
    raise NotImplementedError


async def pair(code: str) -> tuple[str, OperatorProof]:
    """Consume a pairing code; return (cookie value, proof). Second use of a code fails."""
    raise NotImplementedError


async def verify(cookie: str) -> OperatorProof | None:
    """Hash, look up in operator_sessions, check expiry."""
    raise NotImplementedError


def mint(session_hash: str) -> OperatorProof:
    raise NotImplementedError
