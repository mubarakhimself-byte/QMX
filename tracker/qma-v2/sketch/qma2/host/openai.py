"""OpenAI engine adapter. The only module that imports `agents` (openai-agents) and `openai`.

Claude's structure rebuilt (BASELINE 2.18): the loop is the SDK's; tools, gate calls,
hooks, prompt layering, compaction and sub-agents are QMX's. The SDK gets only QMX
function tools (host/tools.py), never hosted tools, ShellTool or ApplyPatchTool, because
those bypass any blocking point (H1 fact 12). The SDK's own approvals (needs_approval,
interruptions, RunState) are not used: QMX tool wrappers await the operator inline, the
same rendezvous the Claude adapter uses, so approvals behave identically on both engines.

Before anything else runs: `set_trace_processors([LocalJsonlProcessor(trace_dir)])`
(replaces the OpenAI exporter; never `add_trace_processor`), plus a startup assertion that
no OpenAI trace exporter is registered (H18).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from qma2.host.link import Link
from qma2.model import JsonValue
from qma2.wire import Compact, Interrupt, Reconfigure, Rotate, Spawn, Steer, Turn


class LinkSession:
    """agents.SessionABC over harness.db `items` (through the link). The control side is
    the single writer; this class only reads active items and lets Emit carry new ones.

    get_items -> link.load_items(segment) converted to SDK input items
                 (engine_payload verbatim when it came from the same wire; otherwise
                  rebuilt from normalised fields: the cross-engine seed path).
    add_items -> no-op persist: items already travel as Emit(message.done/tool.*), keyed
                 by SDK item id, so a crash cannot double-write.
    """

    async def get_items(self, limit: int | None = None) -> list[Any]:
        raise NotImplementedError

    async def add_items(self, items: list[Any]) -> None:
        raise NotImplementedError

    async def pop_item(self) -> Any:
        raise NotImplementedError

    async def clear_session(self) -> None:
        raise NotImplementedError


class PromptBuilder:
    """Claude's layer order, rebuilt (BASELINE 2.9, H10):
    1. base instructions per model family (ported Codex prompt for GPT; one QMX prompt
       for others) -- static, never edited mid-segment;
    2. tool definitions in fixed order (sorted catalog; same order every request);
    3. ProjectContext (CLAUDE.md, AGENTS.md, MEMORY.md head, skill list) as the FIRST
       user message, never in instructions;
    4. the conversation; dynamic notes appended as <system-reminder> user content.
    ModelSettings carry prompt_cache_key=thread id where the route accepts it."""

    def instructions(self, model: str) -> str:
        raise NotImplementedError

    def model_settings(self, spawn: Spawn) -> Any:
        """# TODO pseudocode
        # ModelSettings(reasoning=map_effort(route), include_usage=True,
        #   extra_args={"prompt_cache_key": thread} where supported,
        #   store=False for ChatGPT route, parallel_tool_calls per provider)
        # strict_feature_validation=True so Responses-only settings on Chat Completions fail loudly
        """
        raise NotImplementedError


class OpenAIAdapter:
    _link: Link
    _spawn: Spawn
    _result: Any  # RunResultStreaming of the running turn, for steer/interrupt

    @classmethod
    async def start(cls, spawn: Spawn, link: Link) -> OpenAIAdapter:
        """# TODO pseudocode
        # set_trace_processors([LocalJsonlProcessor(spawn.trace_dir)]); assert_no_openai_exporter()
        # client = AsyncOpenAI(base_url=account.base_url | "https://api.openai.com/v1",
        #                      api_key=os.environ["QMX_PROVIDER_KEY"])
        # model = OpenAIResponsesModel(...) if wire is RESPONSES else OpenAIChatCompletionsModel(...)
        # agent = Agent(name="qmx", instructions=builder.instructions(model),
        #               tools=tools.build(spawn, link), model=model,
        #               model_settings=builder.model_settings(spawn))
        # await link.started(None, [t.name for t in agent.tools])
        """
        raise NotImplementedError

    async def turn(self, message: Turn) -> None:
        """# TODO pseudocode
        # await compactor.maybe_compact(session, window)          # before, never mid-request
        # result = Runner.run_streamed(agent, input, session=LinkSession, max_turns=QMX_MAX_TURNS)
        #          # SDK default is 10 (H1 fact 9); QMX passes its own setting
        # async for ev in result.stream_events(): translate (research 32 B4.2):
        #   raw output_text.delta -> message.delta (live)
        #   message_output_created -> message.done (source_key = item id)
        #   reasoning_item_created -> reasoning.done (summary only)
        #   tool_called / tool_output -> tool.started / tool.finished (wrappers already gated)
        # usage: one UsageRow per context_wrapper.usage.request_usage_entries (dedupe response id)
        # on final output: out = await link.hook(Stop(...)); if out.block: run again with
        #                  out.reason as input (Claude Stop semantics)
        # link.turn_ended(...)
        """
        raise NotImplementedError

    async def steer(self, message: Steer) -> None:
        """result.cancel(mode="after_turn"), then start a new run with the steer text
        appended; session history carries the rest. Equals Codex 'inject before next
        sampling' within one model call (H3)."""
        raise NotImplementedError

    async def interrupt(self, message: Interrupt) -> None:
        """result.cancel(); tools.kill_all() kills every tool process tree."""
        raise NotImplementedError

    async def reconfigure(self, message: Reconfigure) -> None:
        """New ModelSettings/model from the next run; mode is control-side only."""
        raise NotImplementedError

    async def compact(self, message: Compact) -> None:
        raise NotImplementedError

    async def rotate(self, message: Rotate) -> None:
        """Swap the AsyncOpenAI client's key between requests (ChatGPT refresh)."""
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


def map_effort(effort: str, model: str, wire: str) -> Mapping[str, JsonValue]:
    """Claude's five levels -> Reasoning(effort=...). Responses: pass through (plus `none`
    / `ultra` where listed). Chat Completions: only where the provider accepts
    reasoning.effort (per-provider table; UNVERIFIED for DeepSeek/GLM/Kimi/MiniMax)."""
    raise NotImplementedError


def available_models(models_payload: Sequence[Mapping[str, JsonValue]]) -> Sequence[str]:
    """OpenRouter /api/v1/models supported_parameters filter: tools required."""
    raise NotImplementedError
