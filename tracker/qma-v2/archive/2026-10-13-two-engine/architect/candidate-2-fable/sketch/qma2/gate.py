"""Gate: the one policy point. Every tool call on both engines, from every sub-agent and
every MCP server, resolves through `Gate.decide`.

Claude engine: `decide` runs inside the PreToolUse in-code hook. It returns allow/deny there;
an `Ask` becomes permissionDecision "ask", which the SDK routes to `can_use_tool`, where the
same Gate awaits the operator (`ApprovalBroker`). No permission rules are written into Claude
settings, so nothing shadows the callback (recipe comment at native_claude.py:236, H1 fact 1).
Sub-agents: hooks fire for sub-agent tool calls too (`agent_id` present); the call's
`agent_path` comes from it. Live check in unit U3.

OpenAI engine: every QMX tool's handler is wrapped: `verdict = await gate.decide(call)` before
the body runs. The SDK's observe-only hooks are not used for enforcement.

Flow: hooks(PreToolUse) → policy.evaluate → (Ask → PermissionRequest hook → ApprovalBroker)
→ remembered decisions → Verdict. Pure logic in policy.py; this file is the shell.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from qma2.approvals import ApprovalBroker
from qma2.hooks import HookRunner
from qma2.policy import Policy
from qma2.tools.registry import ToolRegistry
from qma2.types import Allow, Deny, ThreadId, ToolCall, Verdict


@dataclass
class Remembered:
    """ALLOW_SESSION / DENY_* answers for one thread. In memory, owned by the SessionActor.
    ALLOW_ALWAYS does not live here: it is written to the local settings layer and re-read."""

    allow: set[str] = field(default_factory=set)  # rule text
    deny: set[str] = field(default_factory=set)


class Gate:
    def __init__(
        self,
        *,
        thread_id: ThreadId,
        policy: Policy,
        hooks: HookRunner,
        registry: ToolRegistry,
        approvals: ApprovalBroker,
        remembered: Remembered,
    ) -> None:
        raise NotImplementedError

    async def decide(self, call: ToolCall) -> Verdict:
        """# TODO:
        # 1. outcome = hooks.fire("PreToolUse", pre_tool_payload(call))
        #    blocked or permission=="deny" → Deny(reason)
        #    permission=="allow" → candidate Allow(updated_input), but only if policy has no
        #      deny/ask match for this call (hook allow never beats rules)
        # 2. verdict = policy.evaluate(policy, call) with remembered rules merged as the
        #    "session" layer
        # 3. Deny → return (final flag kept so the engine can say "cannot be approved")
        # 4. Ask → hooks.fire("PermissionRequest") may allow/deny; else
        #    answer = await approvals.request(ApprovalRequest(kind="tool", call=call, ...))
        #    ALLOW_SESSION → remembered.allow.add(rule_for(call)); ALLOW_ALWAYS → config.write_rule
        #    DENY_* symmetric; CANCEL_TURN → raise TurnCancelled (the actor interrupts)
        #    edited_input → Allow(updated_input=edited_input)
        # 5. After the body ran, the engine calls `after(call, result)` (PostToolUse/Failure)."""
        raise NotImplementedError

    async def after(self, call: ToolCall, *, ok: bool, result_preview: str, error: str = "") -> str:
        """PostToolUse / PostToolUseFailure hooks; returns `additional_context` to append."""
        raise NotImplementedError

    def classify(self, name: str, metadata: dict[str, object], source: str) -> ToolCall | None:
        """Convenience for engine adapters: registry.classify, then build the ToolCall."""
        raise NotImplementedError


def rule_for(call: ToolCall) -> str:
    """Pure: the rule text an "always/session" answer remembers, e.g. `Bash(npm run lint *)`
    from the first token(s) of the command, or `Edit(./src/**)` for a path tool."""
    raise NotImplementedError
