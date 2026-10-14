"""qmx-control's side of the gateway: spawn, supervise, push desired state, take events.

The harness is the single writer of durable state (harness.db). The gateway is a
replica that is replaced wholesale on every change and after every restart, so
there is one reconcile path, not a set of incremental commands
(per make-operations-idempotent).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from qma_gateway.contract import GatewayDesired, GatewayEvent


class GatewayLink:
    @classmethod
    async def start(cls, port: int) -> GatewayLink:
        """Spawn `python -I -m qma_gateway` with a minimal env (no ANTHROPIC_*, no
        provider keys; the gateway reads keys from the keyring itself). stdin and
        stdout are pipes. The gateway exits when its stdin closes."""
        raise NotImplementedError

    async def apply(self, desired: GatewayDesired) -> None:
        """Write the whole document. Remembered, so a restart replays the latest one."""
        raise NotImplementedError

    def events(self) -> AsyncIterator[GatewayEvent]:
        """Parsed from stdout. The harness inserts each event keyed by its natural
        key (request_key for usage), so replays after a restart are no-ops."""
        raise NotImplementedError

    async def supervise(self) -> None:
        """On exit: restart on the same port, re-apply the latest desired state.
        Live CLIs keep their base URL and ride the outage on their own retries
        (CLAUDE_CODE_MAX_RETRIES). A stream cut mid-turn ends that turn with an
        error; the thread follows the unknown-outcome rule."""
        raise NotImplementedError
