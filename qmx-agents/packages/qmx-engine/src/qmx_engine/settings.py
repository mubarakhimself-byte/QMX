"""Every engine default, in one place (ENGINE-PLAN Appendix H).

Each value is Claude's default, not the operator's, and every one is editable from the UI. Keys
are dotted Settings paths. `*` in a `pool.accounts` key stands for any account. Durations are in
seconds, fractions are of a model's context window or of an account's plan window, and a role's
candidates are `profile/model` rows in the order they are tried. The role lists are SOLUTION-DESIGN
section 9's, cut to the providers configured today: the plan, GPT once its lane is open, and the
OpenRouter row for test runs only. `roles.test_order` tries the test-only rows first, then each
role's cheap end; `roles.live_order` tries the plan, then key rows as the operator adds them.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

type Setting = int | float | str | tuple[int, ...] | tuple[str, ...] | None

_CHEAP: Final = ("claude/haiku",)
_MID: Final = ("claude/sonnet", "gpt")
_STRONG: Final = ("claude/opus", "claude/fable", "gpt")

DEFAULTS: Final[Mapping[str, Setting]] = MappingProxyType(
    {
        "scheduler.tick": 60,  # Claude's default, UI-editable
        "scheduler.lease_seconds": 300,  # Claude's default, UI-editable
        "scheduler.heartbeat": 60,  # Claude's default, UI-editable
        "scheduler.grace": 900,  # Claude's default, UI-editable
        "limits.interactive_reserve": 2,  # Claude's default, UI-editable
        "limits.slack": 60,  # Claude's default, UI-editable
        "limits.alert_after": 21_600,  # Claude's default, UI-editable
        "chunk.size": 10,  # Claude's default, UI-editable
        "chunk.fill": 0.3,  # Claude's default, UI-editable
        "agent.compact_at": 0.4,  # Claude's default, UI-editable
        "agent.max_tool_calls": 200,  # Claude's default, UI-editable
        "agent.max_turns": 12,  # Claude's default, UI-editable
        "runaway.tokens": 400_000,  # Claude's default, UI-editable
        "runaway.agents": 12,  # Claude's default, UI-editable
        "runaway.wall_seconds": 7_200,  # Claude's default, UI-editable
        "runaway.usd": None,  # Claude's default, UI-editable
        "on_runaway": "pause",  # Claude's default, UI-editable
        "pool.accounts.*.background_share": 0.5,  # Claude's default, UI-editable
        "pool.accounts.*.ceiling": None,  # Claude's default, UI-editable
        "pool.accounts.*.cooldown": 300,  # Claude's default, UI-editable
        "pool.strategy": "fill-first",  # Claude's default, UI-editable
        "budgets.max_live_chats": 6,  # Claude's default, UI-editable
        "retry.max_tries": 3,  # Claude's default, UI-editable
        "retry.backoff": (30, 120, 600),  # Claude's default, UI-editable
        "timeout.agent.run": 1_800,  # Claude's default, UI-editable
        "timeout.agent.idle": 300,  # Claude's default, UI-editable
        "inline_limit_bytes": 65_536,  # Claude's default, UI-editable
        "placement.pc.concurrency": 3,  # Claude's default, UI-editable
        "context_window": 200_000,  # Claude's default, UI-editable
        "roles.triage": _CHEAP,  # Claude's default, UI-editable
        "roles.clarifier": _CHEAP,  # Claude's default, UI-editable
        "roles.scanner": _CHEAP,  # Claude's default, UI-editable
        "roles.doctor": _CHEAP,  # Claude's default, UI-editable
        "roles.judge": _CHEAP,  # Claude's default, UI-editable
        "roles.reader": _MID,  # Claude's default, UI-editable
        "roles.searcher": _MID,  # Claude's default, UI-editable
        "roles.writer": _MID,  # Claude's default, UI-editable
        "roles.extractor": _MID,  # Claude's default, UI-editable
        "roles.planner": _STRONG,  # Claude's default, UI-editable
        "roles.synthesiser": _STRONG,  # Claude's default, UI-editable
        "roles.builder": _STRONG,  # Claude's default, UI-editable
        "roles.reviewer": _STRONG,  # Claude's default, UI-editable
        "roles.test_only": ("openrouter/moonshotai/kimi-k2.5",),  # Claude's default, UI-editable
        "roles.test_order": ("test_only", "cheap_first"),  # Claude's default, UI-editable
        "roles.live_order": ("plan", "key"),  # Claude's default, UI-editable
    }
)
