"""The response tap: one SSE parse per response, two jobs.

1. Meter. Usage from message_start / message_delta, rate-limit windows from the
   plan lane's anthropic-ratelimit-unified-* headers, upstream failures. These
   become `GatewayEvent`s on stdout. The gateway is the one source of usage for
   every provider (no host-side usage path exists, per single source of truth).

2. Wire gate (money). Every tool call a model proposes, from any agent in the CLI's
   process tree (main thread, sub-agents, background agents, Workflow agents) and
   from any provider, passes this point before the CLI sees it. The gate holds each
   `tool_use` content block until its `content_block_stop`, runs the shared pure
   classifier, and either releases the block's events unchanged or replaces them.

   Replacement: the tool_use block becomes a text block
   "[QMX money rule] blocked <tool>: <act>. Agents read money data and propose
   orders; they never move money." If no tool_use remains in the message, the
   final message_delta's stop_reason becomes "end_turn". A `MoneyBlocked` event is
   emitted. There is no allow branch: the gate can only pass or replace.

   Why both this and the CLI-side PreToolUse hook (qmx_harness.engine): the hook
   sees the final tool input after any hook edits and runs in the CLI's permission
   order; the wire gate sees what the model proposed and does not depend on the
   CLI's mode, settings, hook wiring, or which internal mechanism (sub-agent,
   Workflow, background task) would execute the call. Same classifier, two
   chokepoints, neither can approve (design.md "Money safety").

Non-buffering rule: text and thinking deltas are passed through as they arrive.
Only tool_use blocks are held, and only until their own stop event, so token
streaming to the UI is unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from qma_core.money_classify import MoneyHit, ToolCall, classify
from qma_gateway.contract import AgentHints, GatewayEvent, Lane, LeaseGrant, ModelId, PlanWindowSeen


@dataclass(frozen=True, slots=True)
class TapContext:
    lease: LeaseGrant
    hints: AgentHints
    model: ModelId
    lane: Lane
    request_key: str  # upstream request-id header, or a gateway uuid if absent


def windows_from_headers(headers: tuple[tuple[bytes, bytes], ...]) -> tuple[PlanWindowSeen, ...]:
    """Pure. Parses anthropic-ratelimit-unified-* (exact names settled by live
    check L8; until then the parser keeps the raw header set in the event log for
    the check to read). Empty on non-plan lanes."""
    raise NotImplementedError


class ResponseTap:
    """Feed it raw response chunks, get back the chunks to send to the CLI.

    State is per response and dies with it. No cross-request state, no lock.
    """

    def __init__(self, ctx: TapContext, emit: Callable[[GatewayEvent], None]) -> None:
        raise NotImplementedError

    def feed(self, chunk: bytes) -> bytes:
        """Returns bytes to forward now (possibly empty while a tool_use is held).

        # TODO pseudocode
        # split into SSE events (keep partial lines across chunks)
        # for each event:
        #   message_start: record input/cache usage
        #   content_block_start(type=tool_use): open a hold buffer for this index
        #   input_json_delta for a held index: append to the hold buffer
        #   content_block_stop for a held index:
        #       call = ToolCall(name, json(input), agent=ctx.hints.agent_id)
        #       verdict = classify(call, ctx.lease.catalog)
        #       MoneyHit -> emit MoneyBlocked; forward a text block in its place
        #       else     -> forward the held events verbatim
        #   message_delta: record output usage; fix stop_reason if every tool_use was replaced
        #   message_stop: emit UsageRecorded
        #   error: emit UpstreamFailed
        #   anything else: forward verbatim
        """
        raise NotImplementedError

    def close(self, *, aborted: bool) -> bytes:
        """Flush. If the stream aborted while a tool_use was held, the held block is
        dropped, never released, so a cut stream cannot leak an unclassified call."""
        raise NotImplementedError


def blocked_text(hit: MoneyHit, tool_name: str) -> str:
    raise NotImplementedError
