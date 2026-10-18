"""The one operator-side entry point. qmx-control routes call this and nothing else.

Harness hides: the zone link (connect, Hello, reconcile, seq replay), the door
and model relay (started here, see door.py), the thread index in harness.db,
approvals, the user-tier mirror, usage capture and the background cap.

It runs inside the qmx-control process as the operator's OS account. It does
not import claude_agent_sdk.

Invariants:
- harness.db has one writer, this class.
- control.db blocks are written through ControlService.sessions_append only.
- No method takes an authorization decision from zone data. Zone events
  update records and blocks; door ops and answers carry the authority.
- Answers require OperatorProof. The zone account cannot reach the operator
  bearer token, so it cannot produce one.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from qma_harness.model import (
    Answer,
    OperatorProof,
    PendingRef,
    ProfileId,
    ShareId,
    ThreadRecord,
    TurnId,
    ZoneStatus,
)
from qma_zone_wire import Effort, PermissionMode, ThreadId


@dataclass(frozen=True)
class NewThread:
    """What a route asks for. Profile and share are ids from settings; the
    Harness resolves them, so a route cannot pass a URL, a key or a path."""

    profile: ProfileId
    share: ShareId
    mode: PermissionMode = "default"
    model: str | None = None
    effort: Effort | None = None
    background: bool = False
    parent: ThreadId | None = None


@dataclass(frozen=True)
class SwitchQuote:
    """Shown before a model or provider change. Stored server-side and pinned
    to the thread's cache epoch, so the warning cannot be skipped by a client."""

    id: str
    thread: ThreadId
    target_profile: ProfileId
    target_model: str
    same_route: bool  # True: set_model in place. False: close and resume under the new route
    uncached_tokens_estimate: int


@dataclass(frozen=True)
class LoginStep:
    kind: Literal["open_url", "done", "needs_native_terminal"]
    url: str | None
    plan: str | None


class Harness:
    @classmethod
    async def open(cls, home: Path, control: Any, secrets: Any, settings: Any) -> "Harness":
        """Start the door (link, MCP, model relay) on its own loopback port with
        its own auth, wait for the zone's Hello, reconcile, push the user tier.
        Returns even if the zone is down; status() then reports link="down"."""
        raise NotImplementedError

    async def start_thread(self, request: NewThread) -> ThreadId:
        """Resolve profile and share, check the background cap and the live
        thread cap, write the record, send Open. Refuses a ChatGptPlan whose
        probe has not passed."""
        raise NotImplementedError

    async def send(self, thread: ThreadId, text: str) -> TurnId:
        """Append the user block, send Send(typed_by_operator=True). Refuses
        a thread in Unknown state. Blocks then arrive on the SSE wire."""
        raise NotImplementedError

    async def interrupt(self, thread: ThreadId) -> None:
        raise NotImplementedError

    async def set_mode(self, thread: ThreadId, mode: PermissionMode) -> None:
        raise NotImplementedError

    async def quote_switch(self, thread: ThreadId, profile: ProfileId, model: str) -> SwitchQuote:
        raise NotImplementedError

    async def switch(self, quote_id: str) -> None:
        """Same route: SetModel. Different route: Close, then Open with resume
        and the new route. If the cross-route resume check (L5) failed, fork
        with a summary instead."""
        raise NotImplementedError

    async def resume(self, thread: ThreadId) -> None:
        """Explicit operator resume of an Unknown or reaped thread."""
        raise NotImplementedError

    async def answer(self, pending: PendingRef, answer: Answer, proof: OperatorProof) -> None:
        """ZoneAsk: send AnswerAsk; AllowAlways also writes the rule into the
        canonical user tier and pushes it. ApprovalId: grant or deny the door
        approval; AllowAlways is refused. Idempotent per pending ref."""
        raise NotImplementedError

    async def export(self, thread: ThreadId, out: Path) -> Path:
        """Zip the zone transcript (streamed over the link), the thread's
        blocks, approvals and usage. The token grep check runs on the zip."""
        raise NotImplementedError

    async def login_claude(self) -> AsyncIterator[LoginStep]:
        """Drive StartLogin in the zone and surface its URL to the console,
        which opens the operator's browser. Carries no credential."""
        raise NotImplementedError
        yield  # pragma: no cover

    async def login_chatgpt(self) -> AsyncIterator[LoginStep]:
        """Run the SIWC sign-in operator-side (gpt.SiwcSession), then the probe
        ladder. The ChatGPT token stays in the operator keyring."""
        raise NotImplementedError
        yield  # pragma: no cover

    async def put_user_tier(self, files: dict[str, bytes], proof: OperatorProof) -> None:
        """UI edits of permission rules, settings hooks, CLAUDE.md, skills,
        agents and commands. Writes the canonical copy under ~/.qmx/zone-user,
        then pushes PutUserTier. The zone copy is a replica."""
        raise NotImplementedError

    def threads(self) -> tuple[ThreadRecord, ...]:
        raise NotImplementedError

    def status(self) -> ZoneStatus:
        raise NotImplementedError

    async def close(self) -> None:
        """Stop the door. Zone turns keep running and buffer their events
        until the next open."""
        raise NotImplementedError
