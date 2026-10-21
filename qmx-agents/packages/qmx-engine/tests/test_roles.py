"""Roles resolve to candidates by run mode (AD-13): a test run starts on the plan's `claude/haiku`
(ruling 105) and takes a test-only row only when the role names it; a live run tries key rows, then
GPT, then the plan (ruling 107), and never takes a test-only row."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from qmx_engine.roles import Mode, order, resolve
from qmx_engine.settings import DEFAULTS

KIMI = "openrouter/moonshotai/kimi-k2.5"
WRITER = ("claude/opus", "kimi/k3", "claude/haiku@low", "gpt/gpt-5.5")
SETTINGS = {"roles.writer": WRITER, "roles.test_only": (KIMI,)}
NAMED = {**SETTINGS, "roles.writer": (KIMI, *WRITER)}
ORDER_KEYS = {"roles.test_only", "roles.test_order", "roles.live_order"}
ROLES = sorted(
    k.removeprefix("roles.") for k in DEFAULTS if k.startswith("roles.") and k not in ORDER_KEYS
)


def names(settings: Mapping[str, object], role: str, mode: Mode) -> list[str]:
    return [c.name for c in order(settings, role, mode)]


@pytest.mark.parametrize("role", ROLES)
def test_test_mode_resolves_the_plan_haiku_first_for_every_default_role(role: str) -> None:
    first = resolve(order(DEFAULTS, role, "test"), {"claude", "kimi", "openrouter"}, None)

    assert getattr(first, "name", first) == "claude/haiku"


def test_a_live_strong_role_tries_a_chinese_key_row_first_when_its_profile_exists() -> None:
    candidates = order(DEFAULTS, "planner", "live")

    assert [c.name for c in candidates] == ["kimi/k3", "deepseek/deepseek-v4-pro", "claude/opus"]
    assert getattr(resolve(candidates, {"claude", "kimi"}, None), "name", None) == "kimi/k3"
    assert getattr(resolve(candidates, {"claude"}, None), "name", None) == "claude/opus"


def test_live_mode_sorts_key_then_gpt_then_plan_and_skips_test_only_rows() -> None:
    assert names(NAMED, "writer", "live") == [
        "kimi/k3",
        "gpt/gpt-5.5",
        "claude/opus",
        "claude/haiku@low",
    ]


def test_test_mode_admits_a_test_only_row_only_where_the_role_names_it() -> None:
    assert names(SETTINGS, "writer", "test") == [
        "claude/haiku@low",
        "claude/opus",
        "kimi/k3",
        "gpt/gpt-5.5",
    ]
    assert names(NAMED, "writer", "test")[:2] == [KIMI, "claude/haiku@low"]
    assert [c.test_only for c in order(NAMED, "writer", "test")][:2] == [True, False]


def test_resolution_skips_a_candidate_whose_profile_the_harness_lacks() -> None:
    named = {**SETTINGS, "roles.writer": (KIMI, "claude/opus", "claude/haiku@low")}
    candidates = order(named, "writer", "test")

    with_key = resolve(candidates, {"claude", "openrouter"}, None)
    without_key = resolve(candidates, {"claude"}, None)
    by_ladder = resolve(candidates, {"claude", "openrouter"}, {"candidate": "claude/opus"})
    degraded = resolve(candidates, {"claude"}, {"degrade": True})

    assert [getattr(c, "name", c) for c in (with_key, without_key, by_ladder, degraded)] == [
        KIMI,
        "claude/haiku@low",
        "claude/opus",
        "claude/haiku@low",
    ]
    assert resolve(candidates, set(), None) == (
        "no candidate has a profile in the harness (candidates: "
        f"{KIMI}, claude/haiku@low, claude/opus)"
    )
