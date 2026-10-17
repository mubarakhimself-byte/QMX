"""Roles resolve to candidates by run mode (AD-13): a test run tries the test-only rows first, then
the role's cheap end; a live run never takes a test-only row."""

from __future__ import annotations

from qmx_engine.roles import order, resolve

KIMI = "openrouter/moonshotai/kimi-k2.5"
SETTINGS = {
    "roles.writer": ("claude/opus", "claude/haiku@low", "gpt"),
    "roles.test_only": (KIMI,),
}


def names(mode: str) -> list[str]:
    return [c.name for c in order(SETTINGS, "writer", mode)]  # type: ignore[arg-type]


def test_test_mode_admits_test_only_rows_first_then_the_cheap_end() -> None:
    assert names("test") == [KIMI, "claude/haiku@low", "claude/opus"]
    assert [c.test_only for c in order(SETTINGS, "writer", "test")] == [True, False, False]


def test_live_mode_skips_test_only_rows_and_keeps_the_role_order() -> None:
    assert names("live") == ["claude/opus", "claude/haiku@low"]


def test_resolution_skips_a_candidate_whose_profile_the_harness_lacks() -> None:
    candidates = order(SETTINGS, "writer", "test")

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
