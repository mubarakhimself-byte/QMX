"""Opt-in released Deep Agents factory; QMA retains admission and effect ownership."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from importlib.metadata import version
from typing import Any

from langchain.agents.middleware import AgentMiddleware

from .contracts import ProviderEvent
from .graph_storage import JournalRecords
from .providers import ProviderError

SDK_VERSIONS = {
    "deepagents": "0.7.21",
    "langchain": "1.4.3",
    "langchain-core": "1.6.6",
    "langgraph": "1.2.12",
}
MODEL_PROFILE = "qmx:bounded-specialist-v1"
EXCLUDED_TOOLS = frozenset(
    {"ls", "write_file", "edit_file", "glob", "grep", "execute", "task", "compact_conversation"}
)


def _host_name(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True, slots=True)
class DeepAgentSelection:
    """One host profile/role pair, frozen in the journal before any inference.

    Summary calls consume the role's existing total model allowance. No default
    switch, subagent, native-session wrapper, memory provider or server selection.
    """

    profile_id: str
    workflow_id: str
    max_summary_calls: int = 1
    summary_trigger_tokens: int = 8192

    def __post_init__(self) -> None:
        if not all(_host_name(v) for v in (self.profile_id, self.workflow_id)):
            raise ValueError("explicit host profile and workflow required")
        for value in (self.max_summary_calls, self.summary_trigger_tokens):
            if type(value) is not int or value <= 0:
                raise ValueError("positive bounded summary configuration required")

    def matches(self, profile: str, workflow: str) -> bool:
        return (profile, workflow) == (self.profile_id, self.workflow_id)

    def binding(self) -> dict[str, object]:
        actual = {name: version(name) for name in SDK_VERSIONS}
        if actual != SDK_VERSIONS:
            raise ProviderError("unsupported", "Deep Agents comparison requires exact SDK versions")
        return {"revision": MODEL_PROFILE, "selection": asdict(self), "sdk_versions": actual}


class DeepAgentBudget:
    """Write-ahead reservations survive summaries, failures and disk restart.

    An uncertain inference consumes its reservation. Explicit host retry charges
    a new call; this is not an exactly-once claim. Replaying an existing tool call
    id consumes no additional allowance; the QMA effect receipt governs effects.
    """

    def __init__(
        self,
        records: JournalRecords,
        thread: str,
        *,
        model_limit: int,
        tool_limit: int,
        summary_limit: int,
        emit: Callable[[ProviderEvent], None],
    ) -> None:
        self.records, self.thread, self.emit = records, thread, emit
        self.model_limit, self.tool_limit, self.summary_limit = (
            model_limit,
            tool_limit,
            summary_limit,
        )
        self.lock = threading.RLock()

    def _state(self) -> dict[str, Any]:
        return self.records.get("deep_agent_budget", self.thread) or {
            "models": 0,
            "summaries": 0,
            "tool_ids": [],
        }

    @property
    def tool_calls(self) -> int:
        return len(self._state()["tool_ids"])

    def reserve_model(self, *, summary: bool) -> int:
        with self.lock:
            state = self._state()
            if state["models"] >= self.model_limit or (
                summary and state["summaries"] >= self.summary_limit
            ):
                raise ProviderError("loop_limit", "Total model or summarization budget exhausted")
            state["models"] += 1
            state["summaries"] += int(summary)
            self.records.put("deep_agent_budget", self.thread, state)
            self.emit(
                ProviderEvent(
                    "deep_agent_budget",
                    {"kind": "summary" if summary else "model", "call": state["models"]},
                )
            )
            return state["models"]

    def reserve_tool(self, call_id: str) -> None:
        with self.lock:
            state = self._state()
            if call_id in state["tool_ids"]:
                return
            if len(state["tool_ids"]) >= self.tool_limit:
                raise ProviderError("loop_limit", "Total SDK tool budget exhausted")
            state["tool_ids"].append(call_id)
            self.records.put("deep_agent_budget", self.thread, state)


class DeepAgentToolGuard(AgentMiddleware):
    """Last host guard covers built-ins as well as granted operation callbacks."""

    def __init__(self, allowed: frozenset[str], budget: DeepAgentBudget) -> None:
        self.allowed, self.budget = allowed, budget

    def wrap_tool_call(self, request: Any, handler: Any) -> Any:
        call = request.tool_call
        if call["name"] not in self.allowed:
            raise ProviderError("tool_denied", "SDK tool is outside host profile")
        self.budget.reserve_tool(call["id"])
        return handler(request)


def create_bounded_deep_agent(
    model: Any,
    *,
    selection: DeepAgentSelection,
    tools: list[Any],
    middleware: list[AgentMiddleware[Any, Any, Any]],
    checkpointer: Any,
    system_prompt: str,
) -> Any:
    """Replace the graph factory once; retain SDK scaffolding with explicit policy."""
    from deepagents import (  # noqa: PLC0415 - only selected optional harness
        create_deep_agent,  # pyright: ignore[reportUnknownVariableType] - upstream generic overload
        register_harness_profile,
    )
    from deepagents.backends import StateBackend  # noqa: PLC0415
    from deepagents.middleware import FilesystemMiddleware  # noqa: PLC0415
    from deepagents.middleware.summarization import SummarizationMiddleware  # noqa: PLC0415
    from deepagents.profiles import GeneralPurposeSubagentProfile, HarnessProfile  # noqa: PLC0415

    selection.binding()
    register_harness_profile(
        MODEL_PROFILE,
        HarnessProfile(
            excluded_tools=EXCLUDED_TOOLS,
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    backend = StateBackend()
    # Same-name replacement is the SDK's documented middleware customization
    # seam. Never expose write/execute tools or filesystem eviction to the model.
    filesystem = FilesystemMiddleware(
        backend=backend,
        tools=["read_file"],
        tool_token_limit_before_evict=None,
        human_message_token_limit_before_evict=None,
    )
    summary = SummarizationMiddleware(
        model=model.model_copy(update={"summarizing": True, "allowed": frozenset()}),
        backend=backend,
        trigger=("tokens", selection.summary_trigger_tokens),
        keep=("messages", 2),
        truncate_args_settings=None,
    )
    custom = [m for m in middleware if m.name != filesystem.name]
    return create_deep_agent(
        model.model_copy(update={"model_name": MODEL_PROFILE}),
        tools=tools,
        middleware=[filesystem, summary, *custom, DeepAgentToolGuard(model.allowed, model.budget)],
        subagents=[],
        backend=backend,
        checkpointer=checkpointer,
        system_prompt=system_prompt,
    )
