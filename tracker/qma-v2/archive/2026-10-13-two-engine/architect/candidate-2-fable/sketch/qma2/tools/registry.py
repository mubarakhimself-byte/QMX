"""ToolSpec registry: define once, expose twice (research 31 §1.2), classify everything.

The `propose_order` exemption (design.md tension 3) is by registration, not name: a spec with
`effect=MONEY_PROPOSE` can only be created through `money_proposal_spec`, which requires a
`ProposalSink` (the Portfolio proposals writer). `classify` never returns MONEY_PROPOSE for a
name it was not registered with. The copied name scanner still classifies a remote tool named
`propose_order` as MONEY_ACT, which the gate denies finally.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from qma2.policy import classify_by_name
from qma2.types import ToolEffect, ToolSource

type Handler = Callable[[BaseModel, "CallContext"], Awaitable[str]]


@dataclass(frozen=True)
class CallContext:
    """What a handler may touch. No store, no sink, no secrets: tools are pure over their
    inputs plus the supervisor for processes and a redactor for output."""

    thread_id: str
    agent_path: str
    cwd: Any
    run: Callable[..., Awaitable[tuple[int, str, str]]]  # Supervisor.run bound to the thread
    redact: Callable[[str], str]
    ask: Callable[..., Awaitable[Any]]  # ApprovalBroker.request bound to thread/turn (AskUser)


@dataclass(frozen=True)
class ToolSpec:
    name: str  # Claude's canonical name
    description: str
    input_model: type[BaseModel]  # strict: extra forbid
    effect: ToolEffect
    handler: Handler
    defer: bool = False  # tool search; core set always loads
    max_result_chars: int = 16_000  # overflow saved to trace dir, head+tail returned


class ProposalSink(Protocol):
    def write(self, proposal: Mapping[str, Any]) -> str:
        """Returns a proposal reference. The row is unsigned; signing is the operator's."""
        ...


def money_proposal_spec(sink: ProposalSink) -> ToolSpec:
    """The only constructor that yields effect MONEY_PROPOSE."""
    raise NotImplementedError


BUILTIN_EFFECTS: Mapping[str, ToolEffect] = {
    "Read": ToolEffect.READ, "Glob": ToolEffect.READ, "Grep": ToolEffect.READ,
    "Write": ToolEffect.WRITE, "Edit": ToolEffect.WRITE, "apply_patch": ToolEffect.WRITE,
    "TodoWrite": ToolEffect.WRITE, "TaskCreate": ToolEffect.WRITE, "TaskUpdate": ToolEffect.WRITE,
    "Bash": ToolEffect.EXTERNAL, "WebFetch": ToolEffect.EXTERNAL, "WebSearch": ToolEffect.EXTERNAL,
    "Agent": ToolEffect.EXTERNAL, "Skill": ToolEffect.READ, "AskUserQuestion": ToolEffect.READ,
    "ToolSearch": ToolEffect.READ,
}


class ToolRegistry:
    def __init__(self, specs: Sequence[ToolSpec]) -> None:
        """Duplicate names raise. A second MONEY_PROPOSE spec raises."""
        raise NotImplementedError

    def get(self, name: str) -> ToolSpec | None: ...

    def classify(self, name: str, source: ToolSource, metadata: Mapping[str, Any]) -> ToolEffect:
        """QMX: spec.effect. BUILTIN: BUILTIN_EFFECTS (unknown → EXTERNAL). MCP:
        policy.classify_by_name (money scanner) else EXTERNAL for writes, READ when
        readOnlyHint is true."""
        raise NotImplementedError

    def to_claude_mcp(self, ctx_factory: Callable[[str], CallContext]) -> Any:
        """`create_sdk_mcp_server("qmx", tools=[...])`, each tool wrapped with validation +
        size cap + redaction. Returns the SDK object; only engines/claude.py sees it."""
        raise NotImplementedError

    def to_openai_tools(self, ctx_factory: Callable[[str], CallContext], gate_decide: Callable[..., Awaitable[Any]]) -> Sequence[Any]:
        """`FunctionTool`s with strict schemas; every handler is wrapped with
        `gate_decide(call)` first, then validation, cap, redaction, `gate.after`."""
        raise NotImplementedError

    def names(self) -> Sequence[str]: ...
