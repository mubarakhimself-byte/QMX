"""The harness, as qmx-control sees it. The only public module of `qmx_harness`.

One object, eight verbs. Everything else (SDK options, env derivation, lease
issuance, gateway supervision, money hook, approvals, block projection, resume
rules, usage ledger) sits behind it.

Call sites (see design.md "Usage"):

    # qmx_control/server.py, at app startup
    harness = await Harness.open(home, control)

    # POST /api/threads
    thread = await harness.start_thread(ThreadSpec(profile="copilot"), proof)

    # POST /api/threads/{id}/turns   (not in OPERATIONS, so agents cannot start turns)
    receipt = await harness.submit_turn(thread, OperatorText(body.text), body.idempotency_key, proof)
    # blocks stream out through the existing ControlService SSE route

    # POST /api/approvals/{id}
    await harness.answer(approval_id, Answer.ALLOW_ONCE, proof)

    # GET /api/threads/{id}/switch-quote?model=kimi-k3   then   POST .../switch
    quote = await harness.quote_switch(thread, ModelId("kimi-k3"))
    await harness.switch_model(quote.id, proof)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import NewType

from qma_gateway.contract import ModelId, Percent, Placement, ThreadId

ApprovalId = NewType("ApprovalId", str)
QuoteId = NewType("QuoteId", str)
IdempotencyKey = NewType("IdempotencyKey", str)
ProfileId = NewType("ProfileId", str)


@dataclass(frozen=True, slots=True)
class OperatorProof:
    """Minted only by qmx-control's operator auth (CO-5). Agents reach QMX only
    through in-process `qmx` tools and never hold one, so they cannot answer their
    own approvals, start turns or switch models."""

    principal: str
    issued_at: datetime


@dataclass(frozen=True, slots=True)
class OperatorText:
    """Text the operator typed. Slash commands and @paths are honoured."""

    text: str


@dataclass(frozen=True, slots=True)
class InjectedText:
    """Text built from tool output, news or files. Sent with verbatim_prompts=True,
    so it can never dispatch a slash command or read an @path (02a section 15)."""

    text: str


type Prompt = OperatorText | InjectedText


@dataclass(frozen=True, slots=True)
class ThreadSpec:
    profile: ProfileId  # an AgentProfile row in settings: main model, allowed models, agents, mode
    placement: Placement = Placement.FOREGROUND
    main_model: ModelId | None = None  # None: the profile's default
    workspace: Path | None = None  # None: the profile's QMX workspace, outside any dev repo


class TurnState(StrEnum):
    ACCEPTED = "accepted"  # first submit with this key
    DUPLICATE = "duplicate"  # same key, same text: the original receipt
    BLOCKED_UNKNOWN = "blocked_unknown"  # the last turn ended in an unknown state (CO-19)


@dataclass(frozen=True, slots=True)
class TurnReceipt:
    thread: ThreadId
    state: TurnState


class Answer(StrEnum):
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"  # written as a native rule into QMX's config-home settings.json
    REJECT_ONCE = "reject_once"
    REJECT_ALWAYS = "reject_always"
    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class SwitchQuote:
    """Stored server-side, pinned to the thread's last upstream request. A newer
    request makes it stale, so the cost warning cannot be skipped or reused (CO-11).
    The numbers come from the gateway's own usage record of that request."""

    id: QuoteId
    thread: ThreadId
    from_model: ModelId
    to_model: ModelId
    context_tokens: int  # input + cache read + cache write of the last main-thread request
    est_usd: float | None  # key routes: context_tokens x new input price; None on the plan
    est_plan_percent: float | None  # plan routes: share of the 5-hour window, if known
    pinned_to_request: str


@dataclass(frozen=True, slots=True)
class WindowView:
    utilization: Percent
    resets_at: datetime
    as_of: datetime


@dataclass(frozen=True, slots=True)
class UsageView:
    """The usage page. Every number comes from the gateway's events in harness.db."""

    five_hour: WindowView | None
    seven_day: WindowView | None
    background_cap: Percent
    by_model: tuple[tuple[ModelId, int, int, int, float | None], ...]  # model, in, out, cache_read, usd
    chatgpt_last_limit_hit: datetime | None  # no usage API on the SIWC route (02b F)


class Harness:
    """Owns the gateway process, every live CLI host, and harness.db (single writer)."""

    @classmethod
    async def open(cls, home: Path, control: object) -> Harness:
        """Idempotent startup, in this order:
        1. env.scrub_process_env(os.environ)  (before claude_agent_sdk is imported)
        2. open harness.db; mark threads whose last turn was in flight as unknown
        3. settings -> RouteTable (errors become a `needs_you` block, not a crash)
        4. ToolRegistry -> check_descriptor over every tool; refuse to start on a hit
        5. GatewayLink.start(); apply(GatewayDesired(routes, leases=(), cap))
        6. start the gateway event intake task
        Live CLIs never survive a qmx-control restart: they are its children.
        Threads resume on their next turn.
        """
        raise NotImplementedError

    async def start_thread(self, spec: ThreadSpec, proof: OperatorProof) -> ThreadId:
        raise NotImplementedError

    async def submit_turn(
        self, thread: ThreadId, prompt: Prompt, key: IdempotencyKey, proof: OperatorProof
    ) -> TurnReceipt:
        """Ensures a live host (spawn or resume, which issues a lease and re-applies
        gateway state), then queues the prompt. Returns before the model answers."""
        raise NotImplementedError

    async def interrupt(self, thread: ThreadId, proof: OperatorProof) -> None:
        raise NotImplementedError

    async def answer(self, approval: ApprovalId, answer: Answer, proof: OperatorProof) -> None:
        """Idempotent: a second answer to the same approval returns without effect."""
        raise NotImplementedError

    async def quote_switch(self, thread: ThreadId, model: ModelId) -> SwitchQuote:
        """Refuses a model outside the thread's lease. Any route kind is allowed,
        including a different provider: every provider sits behind one base URL,
        so the switch is `set_model` in the same CLI process."""
        raise NotImplementedError

    async def switch_model(self, quote: QuoteId, proof: OperatorProof) -> None:
        raise NotImplementedError

    def usage(self) -> UsageView:
        raise NotImplementedError

    async def close(self) -> None:
        """Stop hosts (interrupt, disconnect), revoke leases, close the gateway's stdin."""
        raise NotImplementedError
