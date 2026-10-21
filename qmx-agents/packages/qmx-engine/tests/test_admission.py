"""Capacity per resource class (AD-58) and plan admission: each kind takes its class and nothing
else, waiting work is served by priority then age, the engine keeps no chat-slot counter of its
own, a plan attempt waits only on a used-up window, and a key or GPT attempt holds the pool lease
for its row under the attempt's affinity (RTR5)."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest
from flows import edge, folder, node, run_folder
from qmx_control.service import ControlService

import qmx_engine.admission
from qmx_engine.admission import Admission, Capacity, Slots
from qmx_engine.nodes.base import Failed, Waiting
from qmx_engine.ports.harness_adapter import PlanUse
from qmx_engine.ports.router import Refused, Reply, Row, adopt
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.roles import Candidate
from qmx_engine.settings import DEFAULTS

HAIKU = Candidate("claude", "haiku", None, 200_000, test_only=False)
KIMI = Candidate("kimi", "k3", None, 200_000, test_only=False)
RESETS = "2026-10-17T12:00:00+00:00"
ONE_EACH = {**DEFAULTS, "placement.pc.cpu_slots": 1, "placement.pc.container_slots": 1}


class Pool:
    """A `RouterPort` with one account, or none, recording the leases it mints."""

    def __init__(self, account: str | None = "kimi-1") -> None:
        self.account = account
        self.held: list[tuple[str, str, str]] = []
        self.let_go_calls: list[str] = []

    def rows(self) -> tuple[Row, ...]:
        return ()

    async def complete(
        self,
        role_or_model: str,
        messages: Sequence[Mapping[str, object]],
        **_options: object,
    ) -> Reply:
        raise AssertionError("admission never completes")

    def hold(self, *, provider: str, model: str, affinity: str) -> str:
        if self.account is None:
            raise Refused(f"no account serves {provider}/{model}")
        self.held.append((provider, model, affinity))
        return self.account

    def let_go(self, affinity: str) -> None:
        self.let_go_calls.append(affinity)


def test_a_key_attempt_holds_the_pool_lease_under_its_affinity() -> None:
    pool = Pool()
    adopt(pool)
    gate = Admission(Plan(PlanUse(0.0, None, None, None)), DEFAULTS)  # type: ignore[arg-type]
    try:
        held = [gate.hold(candidate, "r1:capital") for candidate in (KIMI, HAIKU)]
        gate.let_go("r1:capital")
    finally:
        adopt(None)

    assert held == [None, None]
    assert pool.held == [("kimi", "k3", "r1:capital")]
    assert pool.let_go_calls == ["r1:capital"]


def test_a_key_attempt_with_no_account_fails_unavailable() -> None:
    pool = Pool(None)
    adopt(pool)
    gate = Admission(Plan(PlanUse(0.0, None, None, None)), DEFAULTS)  # type: ignore[arg-type]
    try:
        held = gate.hold(KIMI, "r1:capital")
    finally:
        adopt(None)

    assert isinstance(held, Failed)
    assert (held.code, held.retryable) == ("unavailable", True)
    assert "no account serves kimi/k3" in held.message


class Plan:
    def __init__(self, use: PlanUse) -> None:
        self.use = use

    async def plan_use(self) -> PlanUse:
        return self.use


def admission(use: PlanUse, **settings: object) -> Admission:
    return Admission(Plan(use), {**DEFAULTS, **settings})  # type: ignore[arg-type]


async def enters_at_once(capacity: Capacity, kind: str, placement: str) -> bool:
    try:
        async with asyncio.timeout(0.05), capacity.held(kind, placement, 0):
            return True
    except TimeoutError:
        return False


def blocked_behind(holder: tuple[str, str], kind: str, placement: str = "pc") -> bool:
    """Whether an attempt of `kind` waits while one `holder` attempt holds its slots."""

    async def probe() -> bool:
        capacity = Capacity.of(ONE_EACH)
        async with capacity.held(*holder, 0):
            return not await enters_at_once(capacity, kind, placement)

    return asyncio.run(probe())


KINDS = {
    "script": True,
    "monitor": True,
    "rlm": True,
    "trigger": False,
    "rule": False,
    "loop": False,
    "join": False,
    "wait": False,
    "subworkflow": False,
    "grader": False,
    "library": False,
    "agent": False,
    "llm": False,
}


def test_each_kind_takes_its_class_and_nothing_else() -> None:
    found = {kind: blocked_behind(("script", "pc"), kind) for kind in KINDS}

    assert found == KINDS


def test_a_container_attempt_also_takes_a_container_slot() -> None:
    assert blocked_behind(("rule", "container"), "rule", "container") is True
    assert blocked_behind(("rule", "container"), "script", "pc") is False
    assert blocked_behind(("script", "pc"), "script", "container") is True


def test_waiting_work_is_served_by_priority_then_age() -> None:
    async def served() -> list[str]:
        slots, order = Slots(1), list[str]()
        waiting: list[asyncio.Task[None]] = []

        async def one(name: str, priority: int) -> None:
            await slots.take(priority)
            order.append(name)
            await asyncio.sleep(0.01)
            slots.give()

        await slots.take(0)
        for name, priority in [("old-1", 1), ("five", 5), ("young-1", 1), ("young-5", 5)]:
            waiting.append(asyncio.create_task(one(name, priority)))
            await asyncio.sleep(0)
        slots.give()
        await asyncio.gather(*waiting)
        return order

    assert asyncio.run(served()) == ["five", "young-5", "old-1", "young-1"]


def test_a_cancelled_waiter_gives_its_turn_to_the_next() -> None:
    async def served() -> tuple[bool, int]:
        slots = Slots(1)
        await slots.take(0)
        gone = asyncio.create_task(slots.take(9))
        await asyncio.sleep(0.01)
        gone.cancel()
        await asyncio.sleep(0)
        slots.give()
        await asyncio.wait_for(slots.take(0), 1)
        return gone.cancelled(), slots.used

    assert asyncio.run(served()) == (True, 1)


def test_the_pc_table_is_cores_less_one_cpu_slots_and_three_container_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qmx_engine.admission.os, "cpu_count", lambda: 8)

    table = {name: slots.size for name, slots in Capacity.of(DEFAULTS).slots.items()}

    assert table == {"cpu": 7, "container": 3}


def test_the_engine_keeps_no_chat_slot_counter(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text("[budgets]\nmax_live_chats = 7\n", "utf-8")
    settings = ControlSettings(ControlService(tmp_path)).values()

    assert not hasattr(qmx_engine.admission, "engine_cap")
    assert not hasattr(qmx_engine.admission, "engine_slots")
    assert not hasattr(Admission, "acquire")
    assert [key for key in settings if "live_chats" in key or "reserve" in key] == []


SLOW = """
import json, time
began = time.time()
time.sleep(0.6)
print(json.dumps([began, time.time()]))
"""


def test_rules_never_wait_while_scripts_hold_every_cpu_slot(tmp_path: Path) -> None:
    rules = [f"r{n}" for n in range(8)]
    root = folder(
        tmp_path / "wf",
        [
            node("start", "trigger"),
            node("a", "script", script="scripts/slow.py"),
            node("b", "script", script="scripts/slow.py"),
            *(node(name, "rule", expr="1 == 1") for name in rules),
        ],
        {"start": {"main": [edge("a"), edge("b"), *(edge(name) for name in rules)]}},
        {"slow": SLOW},
    )

    outcome, events = run_folder(root, tmp_path / "home", **{"placement.pc.cpu_slots": 1})

    finished = [str(e.data["node_id"]) for e in events if e.kind == "node_finished"][1:]
    spans = cast(dict[str, dict[str, list[float]]], outcome.outputs)
    (a_began, a_ended), (b_began, b_ended) = spans["a"]["main"], spans["b"]["main"]
    assert outcome.status == "passed"
    assert sorted(finished[:8]) == rules
    assert a_ended <= b_began or b_ended <= a_began


def test_a_refused_plan_send_waits_for_the_used_up_window_plus_slack() -> None:
    gate = admission(PlanUse(1.0, RESETS, RESETS, None))

    waited = asyncio.run(gate.refused(HAIKU, "the plan window is used up"))
    used_up = asyncio.run(gate.check(HAIKU))

    assert waited == Waiting(
        "limit", "2026-10-17T12:01:00+00:00", span={"detail": "the plan window is used up"}
    )
    assert used_up == Waiting(
        "limit", "2026-10-17T12:01:00+00:00", span={"detail": "a plan window is used up"}
    )
    assert asyncio.run(gate.check(KIMI)) is None


@pytest.mark.parametrize("used", [0.5, 0.9, 0.99])
def test_a_plan_attempt_runs_at_any_use_until_its_window_is_used_up(used: float) -> None:
    assert asyncio.run(admission(PlanUse(used, RESETS, None, None)).check(HAIKU)) is None
