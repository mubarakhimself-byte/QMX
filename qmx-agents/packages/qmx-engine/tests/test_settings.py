from __future__ import annotations

import ast
from pathlib import Path

import pytest

from qmx_engine.settings import DEFAULTS

SETTINGS = Path(__file__).resolve().parents[1] / "src" / "qmx_engine" / "settings.py"
MARK = "# Claude's default, UI-editable"

CHEAP = (
    "kimi/k2.7-code",
    "deepseek",
    "minimax/MiniMax-M2.7-highspeed",
    "qwen",
    "gpt",
    "claude/haiku",
)
MID = ("glm", "qwen", "deepseek", "kimi", "gpt", "claude/sonnet")
STRONG = ("kimi/k3", "deepseek/deepseek-v4-pro", "glm", "qwen", "gpt", "claude/opus")
CHINESE = {"kimi", "deepseek", "minimax", "qwen", "glm"}


DELETED_CAPS = (
    "runaway.tokens",
    "runaway.agents",
    "runaway.wall_seconds",
    "runaway.usd",
    "on_runaway",
    "agent.max_turns",
    "agent.max_tool_calls",
    "timeout.agent.run",
    "timeout.script.run",
    "pool.accounts.*.background_share",
    "budgets.max_live_chats",
)


def test_no_usage_cap_is_a_default() -> None:
    assert [key for key in DELETED_CAPS if key in DEFAULTS] == []
    assert [key for key in DEFAULTS if key.startswith(("runaway", "budgets"))] == []


def test_every_appendix_h_default_has_its_literal_value() -> None:
    assert dict(DEFAULTS) == {
        "scheduler.tick": 60,
        "scheduler.lease_seconds": 300,
        "scheduler.heartbeat": 60,
        "scheduler.grace": 900,
        "limits.slack": 60,
        "limits.alert_after": 21_600,
        "chunk.size": 10,
        "chunk.fill": 0.3,
        "agent.compact_at": 0.4,
        "pool.accounts.*.ceiling": None,
        "pool.accounts.*.cooldown": 300,
        "pool.strategy": "least_used",
        "retry.max_tries": 3,
        "retry.backoff": (30, 120, 600),
        "timeout.agent.idle": 300,
        "timeout.script.idle": 600,
        "timeout.in_tool": 1_200,
        "timeout.grace": 120,
        "timeout.warn_at": 0.8,
        "loop.repeat": 5,
        "loop.window": 8,
        "loop.no_convergence": 6,
        "crash_loop.restarts": 3,
        "subworkflow.max_depth": 3,
        "inline_limit_bytes": 65_536,
        "placement.pc.cpu_slots": None,
        "placement.pc.container_slots": 3,
        "placement.pc.gpu_slots": None,
        "context_window": 200_000,
        "roles.triage": CHEAP,
        "roles.clarifier": CHEAP,
        "roles.scanner": CHEAP,
        "roles.doctor": CHEAP,
        "roles.judge": CHEAP,
        "roles.reader": MID,
        "roles.searcher": MID,
        "roles.writer": MID,
        "roles.extractor": MID,
        "roles.planner": STRONG,
        "roles.synthesiser": STRONG,
        "roles.builder": STRONG,
        "roles.reviewer": STRONG,
        "roles.test_only": ("openrouter/moonshotai/kimi-k2.5",),
        "roles.test_order": ("test_only", "plan_cheap", "cheap"),
        "roles.live_order": ("key", "gpt", "plan"),
    }


def test_role_lists_lead_with_a_chinese_key_row_and_never_name_fable() -> None:
    order_keys = {"roles.test_only", "roles.test_order", "roles.live_order"}
    roles = {k: v for k, v in DEFAULTS.items() if k.startswith("roles.") and k not in order_keys}
    every_row = [str(r) for v in DEFAULTS.values() if isinstance(v, tuple) for r in v]

    assert [r for r in every_row if "fable" in r] == []
    firsts = {k: str(v[0]).partition("/")[0] for k, v in roles.items() if isinstance(v, tuple)}
    assert ({k for k, v in firsts.items() if v in CHINESE}, len(firsts)) == (set(roles), 13)
    assert DEFAULTS["roles.live_order"] == ("key", "gpt", "plan")


def test_defaults_cannot_be_changed_in_place() -> None:
    with pytest.raises(TypeError):
        DEFAULTS["chunk.size"] = 20  # type: ignore[index]
    assert DEFAULTS["chunk.size"] == 10


def test_every_entry_carries_the_claude_default_comment() -> None:
    lines = SETTINGS.read_text(encoding="utf-8").splitlines()
    keys = next(
        node.value.args[0]
        for node in ast.walk(ast.parse("\n".join(lines)))
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "DEFAULTS"
        and isinstance(node.value, ast.Call)
    )
    assert isinstance(keys, ast.Dict)
    unmarked = [
        ast.literal_eval(key)
        for key in keys.keys
        if key is not None and MARK not in lines[key.lineno - 1]
    ]
    assert (len(keys.keys), unmarked) == (len(DEFAULTS), [])
