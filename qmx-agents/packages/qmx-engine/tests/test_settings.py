from __future__ import annotations

import ast
from pathlib import Path

import pytest

from qmx_engine.settings import DEFAULTS

SETTINGS = Path(__file__).resolve().parents[1] / "src" / "qmx_engine" / "settings.py"
MARK = "# Claude's default, UI-editable"

CHEAP = ("claude/haiku",)
MID = ("claude/sonnet", "gpt")
STRONG = ("claude/opus", "claude/fable", "gpt")


def test_every_appendix_h_default_has_its_literal_value() -> None:
    assert dict(DEFAULTS) == {
        "scheduler.tick": 60,
        "scheduler.lease_seconds": 300,
        "scheduler.heartbeat": 60,
        "scheduler.grace": 900,
        "limits.interactive_reserve": 2,
        "limits.slack": 60,
        "limits.alert_after": 21_600,
        "chunk.size": 10,
        "chunk.fill": 0.3,
        "agent.compact_at": 0.4,
        "agent.max_tool_calls": 200,
        "agent.max_turns": 12,
        "runaway.tokens": 400_000,
        "runaway.agents": 12,
        "runaway.wall_seconds": 7_200,
        "runaway.usd": None,
        "on_runaway": "pause",
        "pool.accounts.*.background_share": 0.5,
        "pool.accounts.*.ceiling": None,
        "pool.accounts.*.cooldown": 300,
        "pool.strategy": "fill-first",
        "budgets.max_live_chats": 6,
        "retry.max_tries": 3,
        "retry.backoff": (30, 120, 600),
        "timeout.agent.run": 1_800,
        "timeout.agent.idle": 300,
        "inline_limit_bytes": 65_536,
        "placement.pc.concurrency": 3,
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
        "roles.test_order": ("test_only", "cheap_first"),
        "roles.live_order": ("plan", "key"),
    }


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
