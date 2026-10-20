"""Roles resolve to candidates by run mode (AD-13): a test run starts on the plan's `claude/haiku`
(ruling 105) and takes a test-only row only when the role names it; a live run tries key rows, then
GPT, then the plan (ruling 107), and never takes a test-only row. Until a list is edited it is
generated from the registry by class, and a candidate's window comes from its row (RTR5)."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence

import pytest

from qmx_engine.ports.router import Reply, Row, adopt
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
ROWS = (
    Row("kimi/k2.7-code", "kimi", "k2.7-code", "cheap", 256_000),
    Row("deepseek/deepseek-v4", "deepseek", "deepseek-v4", "cheap", 128_000),
    Row("gpt/gpt-5.5-mini", "gpt", "gpt-5.5-mini", "cheap"),
    Row("claude/haiku", "claude", "haiku", "cheap"),
    Row("glm/glm-5", "glm", "glm-5", "mid"),
    Row("qwen/qwen3-max", "qwen", "qwen3-max", "mid"),
    Row("deepseek/deepseek-v4-pro", "deepseek", "deepseek-v4-pro", "mid"),
    Row("claude/sonnet", "claude", "sonnet", "mid"),
    Row("kimi/k3", "kimi", "k3", "strong", 1_000_000),
    Row("deepseek/deepseek-v4-reasoner", "deepseek", "deepseek-v4-reasoner", "strong", 256_000),
    Row("glm/glm-5-plus", "glm", "glm-5-plus", "strong"),
    Row("qwen/qwen3.5-max", "qwen", "qwen3.5-max", "strong"),
    Row("gpt/gpt-5.5", "gpt", "gpt-5.5", "strong"),
    Row("claude/opus", "claude", "opus", "strong"),
)


class RegistryStub:
    """A `RouterPort` with rows and nothing to serve: the role lists read only `rows`."""

    def __init__(self, rows: Sequence[Row]) -> None:
        self.found = tuple(rows)

    def rows(self) -> tuple[Row, ...]:
        return self.found

    async def complete(self, *_args: object, **_kwargs: object) -> Reply:
        raise AssertionError("a role list never completes")

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        raise AssertionError("a role list never leases")

    def let_go(self, affinity: str) -> None:
        raise AssertionError("a role list never leases")


@pytest.fixture
def registry() -> Iterator[RegistryStub]:
    port = RegistryStub(ROWS)
    adopt(port)
    try:
        yield port
    finally:
        adopt(None)


def names(settings: Mapping[str, object], role: str, mode: Mode) -> list[str]:
    return [c.name for c in order(settings, role, mode)]


def test_the_generated_lists_put_key_rows_first_with_the_chinese_rows_leading(
    registry: RegistryStub,
) -> None:
    assert names(DEFAULTS, "planner", "live") == [
        "kimi/k3",
        "deepseek/deepseek-v4-reasoner",
        "glm/glm-5-plus",
        "qwen/qwen3.5-max",
        "gpt/gpt-5.5",
        "claude/opus",
    ]
    assert names(DEFAULTS, "writer", "live") == [
        "glm/glm-5",
        "qwen/qwen3-max",
        "deepseek/deepseek-v4-pro",
        "claude/sonnet",
    ]
    assert names(DEFAULTS, "triage", "live") == [
        "kimi/k2.7-code",
        "deepseek/deepseek-v4",
        "gpt/gpt-5.5-mini",
        "claude/haiku",
    ]


@pytest.mark.parametrize("role", ROLES)
def test_test_mode_resolves_the_plan_haiku_first_for_every_generated_role(
    registry: RegistryStub, role: str
) -> None:
    first = resolve(order(DEFAULTS, role, "test"), {"claude", "kimi", "openrouter", "gpt"}, None)

    assert getattr(first, "name", first) == "claude/haiku"


def test_an_edited_list_wins_over_the_registry(registry: RegistryStub) -> None:
    assert names({"roles.planner": ("glm/glm-5", "claude/opus")}, "planner", "live") == [
        "glm/glm-5",
        "claude/opus",
    ]


def test_a_candidate_takes_its_window_from_its_row(registry: RegistryStub) -> None:
    windows = {c.name: c.context_window for c in order(DEFAULTS, "planner", "live")}
    cheap = {c.name: c.context_window for c in order(DEFAULTS, "triage", "live")}

    assert windows["kimi/k3"] == 1_000_000
    assert windows["deepseek/deepseek-v4-reasoner"] == 256_000
    assert cheap["claude/haiku"] == 200_000


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
