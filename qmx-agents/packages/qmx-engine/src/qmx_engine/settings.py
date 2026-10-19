"""Every engine default, in one place (ENGINE-PLAN Appendix H).

Each value is Claude's default, not the operator's, and every one is editable from the UI. Keys
are dotted Settings paths. `*` in a `pool.accounts` key stands for any account. Durations are in
seconds, fractions are of a model's context window or of an account's plan window, and a role's
candidates are `profile/model` rows in the order they are tried. The role lists are SOLUTION-DESIGN
section 9's examples, key rows first with the Chinese models leading every tier (ruling 107), then
GPT, then the plan; no list names Fable. A row with no model id (`glm`, `qwen`, `gpt`) is kept for
its place and is never resolved until the registry names its model (RTR5). `roles.live_order` is
the class order a live run sorts by. `roles.test_order` is how a test run builds its list: test-only
rows the role names itself (a provider-proof lane), then the plan's cheap end `claude/haiku`
(ruling 105), then the role's other rows from the cheap end.

QMX sets no usage limit of its own (ruling 106, AD-40): there is no runaway guard, no turn,
tool-call or run-time ceiling and no background share here. `timeout.*` and `loop.*` feed the stuck
detector, which asks whether an attempt still moves, never how much it used. `placement.pc.*_slots`
are machine capacity per resource class (AD-58); chat slots and the Interactive reserve live in the
harness slot table, the only chat-slot counter, under `[budgets]`.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

type Setting = int | float | str | tuple[int, ...] | tuple[str, ...] | None

_CHEAP: Final = (
    "kimi/k2.7-code",
    "deepseek",
    "minimax/MiniMax-M2.7-highspeed",
    "qwen",
    "gpt",
    "claude/haiku",
)
_MID: Final = ("glm", "qwen", "deepseek", "kimi", "gpt", "claude/sonnet")
_STRONG: Final = ("kimi/k3", "deepseek/deepseek-v4-pro", "glm", "qwen", "gpt", "claude/opus")

DEFAULTS: Final[Mapping[str, Setting]] = MappingProxyType(
    {
        "scheduler.tick": 60,  # Claude's default, UI-editable
        "scheduler.lease_seconds": 300,  # Claude's default, UI-editable
        "scheduler.heartbeat": 60,  # Claude's default, UI-editable
        "scheduler.grace": 900,  # Claude's default, UI-editable
        "limits.slack": 60,  # Claude's default, UI-editable
        "limits.alert_after": 21_600,  # Claude's default, UI-editable
        "chunk.size": 10,  # Claude's default, UI-editable
        "chunk.fill": 0.3,  # Claude's default, UI-editable
        "agent.compact_at": 0.4,  # Claude's default, UI-editable
        "pool.accounts.*.ceiling": None,  # Claude's default, UI-editable
        "pool.accounts.*.cooldown": 300,  # Claude's default, UI-editable
        "pool.strategy": "least_used",  # Claude's default, UI-editable
        "retry.max_tries": 3,  # Claude's default, UI-editable
        "retry.backoff": (30, 120, 600),  # Claude's default, UI-editable
        "timeout.agent.idle": 300,  # Claude's default, UI-editable
        "timeout.script.idle": 600,  # Claude's default, UI-editable
        "timeout.in_tool": 1_200,  # Claude's default, UI-editable
        "timeout.grace": 120,  # Claude's default, UI-editable
        "timeout.warn_at": 0.8,  # Claude's default, UI-editable
        "loop.repeat": 5,  # Claude's default, UI-editable
        "loop.window": 8,  # Claude's default, UI-editable
        "loop.no_convergence": 6,  # Claude's default, UI-editable
        "crash_loop.restarts": 3,  # Claude's default, UI-editable
        "subworkflow.max_depth": 3,  # Claude's default, UI-editable
        "inline_limit_bytes": 65_536,  # Claude's default, UI-editable
        "placement.pc.cpu_slots": None,  # Claude's default (cores minus one), UI-editable
        "placement.pc.container_slots": 3,  # Claude's default, UI-editable
        "placement.pc.gpu_slots": None,  # Claude's default (no GPU on the PC), UI-editable
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
        "roles.test_order": ("test_only", "plan_cheap", "cheap"),  # Claude's default, UI-editable
        "roles.live_order": ("key", "gpt", "plan"),  # Claude's default, UI-editable
    }
)
