"""OpenAIEngine: the OpenAI Agents SDK plus QMX's rebuild of Claude Code's structure.

Runs in-process (asyncio) inside the control process; every Bash command and hook is a child
in the thread's ProcessTree. Chosen over a child process per thread because the SDK is a
library, approvals need the RunState in hand, and one writer is kept trivially. Cost: a bug in
a tool handler is a control-process bug; mitigated by handlers being thin wrappers over
subprocesses and pure file ops (design.md, tradeoffs).

Routes on this engine (BASELINE 2.19): GPT via Sign in with ChatGPT (Responses, `store:false`,
`stream:true`, no hosted tools, function tools namespaced; probe first, H1 fact 17); OpenRouter,
Meta, GLM, Kimi, DeepSeek, MiniMax via OpenAI-compatible Chat Completions or Responses.

What QMX rebuilds here (each a small class in this module, because they only exist for this
engine): PromptBuilder (Claude's layer order, `prompt_cache_key=thread_id`), Compactor (server
compaction where offered, else local summary ported from Codex), AgentTool (depth 3, cap 6,
background registry), SkillTool, MemoryLoader, Tracing (local processor only).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qma2.engines.base import Engine, EngineSession, SegmentContext
from qma2.types import (
    Account,
    ApprovalAnswer,
    Effort,
    EngineEvent,
    EngineKind,
    ModelRef,
    ProbeResult,
    Segment,
    Turn,
    TurnInput,
)


class OpenAIEngine(Engine):
    kind = EngineKind.OPENAI

    async def probe(self, account: Account, home_env: Mapping[str, str]) -> ProbeResult:
        """CHATGPT_OAUTH: refresh if needed, then a minimal Responses call with `store:false`.
        Records whether `x-codex-*` headers are visible (limits source) — UNVERIFIED in the SDK
        model classes; the probe is the first thing U4 runs."""
        raise NotImplementedError

    async def open(self, segment: Segment, ctx: SegmentContext) -> EngineSession:
        """# TODO:
        #   set_trace_processors([LocalTraceProcessor(ctx.trace_dir)]) once per process
        #   client = AsyncOpenAI(base_url=account.base_url or route, api_key=secret or token)
        #   model = OpenAIResponsesModel(...) for OpenAI/ChatGPT; OpenAIChatCompletionsModel(...)
        #     elsewhere; ModelSettings(reasoning=effort map, include_usage=True, store=False on
        #     the ChatGPT route, prompt_cache_key=segment.thread_id, strict_feature_validation)
        #   tools = ctx.registry.to_openai_tools(ctx_factory, ctx.gate.decide) + qmx tools
        #   session = SQLiteSession(segment.engine_session_id or new, <home>/qma2/openai-sessions.db)
        #     wrapped in OpenAIResponsesCompactionSession when the route supports it
        #   agent = Agent(name="qmx", instructions=PromptBuilder(ctx).base(), tools=tools,
        #     model=model, model_settings=..., hooks=observer only for tracing)
        #   HookRunner SessionStart"""
        raise NotImplementedError


class OpenAISession(EngineSession):
    def __init__(self, agent: Any, session: Any, ctx: SegmentContext, segment: Segment) -> None:
        raise NotImplementedError

    def run(self, turn: Turn) -> AsyncIterator[EngineEvent]:
        """# TODO:
        #   HookRunner UserPromptSubmit (may block or add context)
        #   first turn of a segment: input = PromptBuilder.context_block(ctx) + seed + user text
        #     (project docs as the FIRST USER MESSAGE, Claude's exclude_dynamic_sections)
        #   result = Runner.run_streamed(agent, input, session=session, max_turns=settings)
        #   translate stream_events (research 32 B4.2): output_text.delta → TextDelta;
        #     message_output_created → TextDone; reasoning → TextDone(role=reasoning, summary);
        #     tool_called → ToolStarted; tool_output → ToolFinished; usage entries → UsageRecorded
        #     (dedupe_key = f"openai:{response_id}")
        #   interruptions after the stream: these are tool approvals the gate already turned into
        #     ApprovalBroker.request inside the wrapper, so the SDK's own `needs_approval` is
        #     left False; the gate awaits inside the tool. (Simpler than two approval paths.)
        #     RunState serialisation is still used for restart-safe parking: before awaiting the
        #     broker, the wrapper stores result.to_state().to_json() as engine_state.
        #   Stop hook on final output; `block` re-enters the loop with the reason as input
        #   Compactor.maybe(session) after the turn (90% window default) → Compacted
        #   TurnFinished"""
        raise NotImplementedError

    async def steer(self, input: TurnInput) -> None:
        """result.cancel(mode="after_turn") → state = to_state() → state.add_input(text) →
        Runner.run(agent, state): Codex's "inject before next sampling"."""
        raise NotImplementedError

    async def interrupt(self) -> None:
        """result.cancel(); tree.kill() for any running Bash."""
        raise NotImplementedError

    async def switch(self, model: ModelRef | None, effort: Effort | None) -> None:
        """New ModelSettings / model on the agent; applies from the next request."""
        raise NotImplementedError

    async def compact(self, focus: str) -> None:
        raise NotImplementedError

    async def resume_from(self, engine_state: bytes, answer: ApprovalAnswer) -> AsyncIterator[EngineEvent]:
        """RunState.from_json → approve/reject the parked item → Runner.run_streamed(agent, state)."""
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class PromptBuilder:
    """Claude's order: (1) base prompt per model family (ported from Codex prompt files for GPT,
    one QMX text for others); (2) tools in fixed sorted order; (3) context block = CLAUDE.md +
    AGENTS.md (root → cwd) + MEMORY.md (first 200 lines / 25 KB) + skills index, as the first
    user message; (4) conversation. Per-turn notes go in `<qmx_state>` on the newest message."""

    ctx: SegmentContext

    def base(self) -> str: ...
    def context_block(self) -> str: ...
    def state_note(self, turn: Turn) -> str: ...


class Compactor:
    def __init__(self, ctx: SegmentContext, *, window_pct: int) -> None: ...

    async def maybe(self, session: Any, usage_so_far: int, model_window: int) -> bool:
        """Server compaction when the route supports it; else local: Codex's SUMMARIZATION
        prompt + SUMMARY_PREFIX, keep recent user messages, then re-inject the context block
        (Claude's "what survives compaction"). Pre/PostCompact hooks around it."""
        raise NotImplementedError


class AgentTool:
    """Claude's `Agent` tool on OpenAI: nested Agent from a `.md` definition, same Gate,
    depth ≤ 3, ≤ 6 concurrent, never escalates mode; background runs in a registry with
    SendMessage/wait/list/interrupt companions (Codex V2 names)."""

    def __init__(self, ctx: SegmentContext, depth: int) -> None: ...


class LocalTraceProcessor:
    """Writes spans to `<trace_dir>/<turn>.jsonl`. Replaces the OpenAI exporter entirely."""

    def __init__(self, trace_dir: Path) -> None: ...


def effort_settings(effort: Effort, provider: str) -> Mapping[str, Any]:
    """Pure map of Claude's five levels to `reasoning.effort` where the provider accepts it;
    omitted where UNVERIFIED (DeepSeek, GLM, Kimi, MiniMax) until probed."""
    raise NotImplementedError


def model_window(model: ModelRef) -> int:
    """Known context windows; default 128K."""
    raise NotImplementedError
