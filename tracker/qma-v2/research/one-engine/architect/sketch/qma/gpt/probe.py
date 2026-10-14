"""The GPT gate: probes P0 to P7 from 02b D, run in order, each needing the previous one green.

P0 sign-in scopes, P1 /v1/models, P2 hello with store:false stream:true, P3 tools (namespace
and plain, both recorded), P4 reasoning include and replay, P5 barred fields return 400,
P6 the bundled CLI through the translator runs one Bash call, P7 the same through
`ClaudeSDKClient` with a GPT profile. P8 (ChatGPT usage page lists QMA) is the operator's.

P6 and P7 need a CLI talking to the translator before any `ProbePassed` exists. They get it
through `Relay.probe_grant(run)`, a single-use grant bound to one `ProbeRun`, so the lane's
only other door stays `open_gpt_lane(ProbePassed)` (A13).

The stored result lives under `<qmx_home>/state/`, inside the protected paths. It is a
correctness gate (this translator version works on this route), not a security gate: an
agent with Bash under the same OS user could still edit it.

Stop rule: P2 `subscription_sharing_user_not_eligible`, or P3 failing both ways, means the
route is not viable now. The GPT row is hidden, and the operator decides (01 section 9 Q1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from qma.gpt.siwc import SiwcSession
    from qma.harness.relay import Relay

_MINT: Final = object()
"""Module-private. `run_probe` and `stored_result` pass it; nothing else should."""


@dataclass(frozen=True)
class ProbeRun:
    """One probe run's identity, for `Relay.probe_grant`. Built only by `run_probe`, with
    the same `_MINT` guard as `ProbePassed`."""

    run_id: str
    _mint: object = field(repr=False, compare=False, default=None)


@dataclass(frozen=True)
class ProbePassed:
    """Built only by `run_probe` (and `stored_result`, re-reading what `run_probe` stored).
    Carries what later code must honour.

    Guarded, not unrepresentable. `__post_init__` raises unless `_mint is _MINT`, and a CI
    grep allows `ProbePassed(` only in this file. Python cannot stop determined code from
    importing `_MINT`; the guard stops an accidental unprobed GPT launch.
    """

    at: datetime
    translator_version: str
    tools_shape: Literal["namespace", "plain"]
    reasoning_replay: bool
    _mint: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class ProbeFailed:
    at: datetime
    step: Literal["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    detail: str


async def run_probe(session: SiwcSession, relay: Relay) -> ProbePassed | ProbeFailed:
    """P4 failing is not fatal: it yields `reasoning_replay=False`. Every other failure is.
    Mints one `ProbeRun`, asks the relay for its probe grant for P6 and P7, revokes it at the
    end whatever the outcome."""
    raise NotImplementedError


def stored_result(translator_version: str) -> ProbePassed | ProbeFailed | None:
    """A stored pass for a different translator version reads as None (re-probe)."""
    raise NotImplementedError
