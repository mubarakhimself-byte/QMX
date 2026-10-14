"""HTTP doors for the console now and the UI later. Thin: parse, call the harness, return.

Mounted on the qmx-control app behind its existing `BearerGate`. None of these routes join
`qmx_control.server.OPERATIONS`, so they are never exported over `/mcp` and no agent can
start turns, switch providers or answer asks through MCP (HOW "small disagreements").

The bearer token is the operator principal for now. Within one OS user an agent with Bash
could read it from the keyring; `money.gate` denies Bash text naming `qmx/` or the QMX
home as a tripwire, not a proof. Money does not depend on this principal (money.py), which
is why thin native accepts it.

Every handler is `async def`, so it runs on the harness's event loop. A plain `def` handler
would run in FastAPI's threadpool and resolve asyncio futures from another thread (A11).

Routes:
    POST /api/chats                         NewChat           -> {session_id}
    POST /api/sessions/{sid}/turns          {text}            -> 202 | 409 ChatTableFull
                                                                 (always OperatorText)
    POST /api/sessions/{sid}/interrupt                        -> 202
    POST /api/sessions/{sid}/quote          ConfigChange      -> Quote (warning shown first)
    POST /api/sessions/{sid}/apply          {quote_id}        -> 200 | 409 stale
    POST /api/approvals/{ask_id}            Answer            -> {status}
    GET  /api/sessions/{sid}/live           SSE of Delta (not stored)
    GET  /api/usage                         UsagePage: windows, RunIndex sums, cap, money posture, exposure
    GET  /api/doctor                        DoctorLine list from stored results (no probe)
    POST /api/doctor/probe                  runs the exposure probe, then returns the list
    GET/PUT /api/claude-settings            settings.toml [claude]: `home.parse_claude_settings`,
                                            then `ControlService.settings_put`
Durable blocks keep using the existing `GET /api/events/sessions?subject=<sid>` SSE.

The turn route is the only producer of `OperatorText`. That is route provenance, not author
provenance: any holder of the bearer can call it (B19, noted). Scheduled jobs and other QMA code
call `Harness.send` with `InjectedText` directly, never through this route.
The relay is not mounted here. It has its own loopback listener (relay.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter

    from qma.harness.harness import Harness


def router(harness: Harness) -> APIRouter:
    raise NotImplementedError


def serve(*, scrubbed: tuple[str, ...]) -> None:
    """Called by `qma.serve` after the boot scrub: build `ControlService`, `BrokerService`,
    `Harness.open(..., scrubbed=scrubbed)`, then
    `qmx_control.server.create_app(service, extra_routers=[router(harness)])` on 127.0.0.1:8766.
    The QMB host's spawn target moves from `qmx_control` to `qma.serve` (one line), which
    keeps the dependency direction one way: qma-harness depends on qmx-control, never back."""
    raise NotImplementedError
