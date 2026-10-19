"""The inbox (SOLUTION-DESIGN 8.2, 10.4; ruling 77): one item per run and signature, three
categories, and only the failures that need the operator."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from flows import edge, node
from planted import Planted, fails, flow

from qmx_engine.ledger.inbox_table import InboxRefused, InboxTable
from qmx_engine.nodes.base import Failed
from qmx_engine.ports.inbox import Category, Raise

AUTH = Raise("run-1", "sig-401", Category.PROVIDER_FAILURE, "write failed: auth", "401")


def test_repeats_of_one_failure_count_on_one_item(tmp_path: Path) -> None:
    with InboxTable.open(tmp_path) as inbox:
        first = inbox.raise_item(AUTH, at="2026-10-17T09:00:00+00:00")
        inbox.raise_item(AUTH, at="2026-10-17T09:01:00+00:00")
        inbox.raise_item(AUTH, at="2026-10-17T09:02:00+00:00")
        inbox.raise_item(replace(AUTH, run_id="run-2"), at="2026-10-17T09:03:00+00:00")
        items = inbox.list_items()

    assert [(i.id == first, i.run_id, i.count, i.last_raised_at) for i in items] == [
        (True, "run-1", 3, "2026-10-17T09:02:00+00:00"),
        (False, "run-2", 1, "2026-10-17T09:03:00+00:00"),
    ]
    assert (items[0].severity, items[0].first_raised_at) == ("normal", "2026-10-17T09:00:00+00:00")


def test_a_fourth_category_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        Raise("run-1", "sig", "logic", "t", "c")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="'logic' is not a valid Category"):
        Category("logic")


def test_resolving_records_the_principal_and_refuses_an_action_not_offered(tmp_path: Path) -> None:
    with InboxTable.open(tmp_path) as inbox:
        found = inbox.raise_item(AUTH, at="2026-10-17T09:00:00+00:00")
        with pytest.raises(InboxRefused):
            inbox.resolve(found, "resume", "operator", at="2026-10-17T09:05:00+00:00")
        item = inbox.resolve(found, "retry", "operator", at="2026-10-17T09:05:00+00:00")
        still_open = inbox.list_items()

    assert (item.resolved_by, item.resolution, item.resolved_at) == (
        "operator",
        "retry",
        "2026-10-17T09:05:00+00:00",
    )
    assert still_open == []


def test_five_provider_failures_make_one_item_and_a_logic_park_makes_none(tmp_path: Path) -> None:
    auth = flow(
        tmp_path / "auth",
        [node("start", "trigger"), node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={"script": Planted(fails("provider said 401", code="auth", retryable=False))},
    )
    logic = flow(
        tmp_path / "logic",
        [node("start", "trigger"), node("check", "script", script="scripts/check.py")],
        {"start": {"main": [edge("check")]}},
        executors={"script": Planted(fails("the sum is wrong", retryable=False))},
    )

    run_id = auth.start().run_id
    statuses = [auth.resume(run_id).status for _ in range(4)]
    parked = logic.start()

    [item] = auth.items()
    assert (item.category, item.count, item.title, item.tried) == (
        "provider_failure",
        5,
        "call failed: auth",
        ("account",),
    )
    assert statuses == ["failed"] * 4
    assert (parked.status, parked.reason) == ("failed", "node check failed: boom: the sum is wrong")
    assert logic.items() == []


def test_an_external_step_of_unknown_outcome_raises_one_blocking_item(tmp_path: Path) -> None:
    post = node("post", "script", script="scripts/post.py")
    post["effect"] = "irreversible_external"
    lost = Failed("timeout", "no answer", "sig", retryable=True, effect_state="unknown")
    run = flow(
        tmp_path,
        [node("start", "trigger"), post],
        {"start": {"main": [edge("post")]}},
        executors={"script": Planted(lost)},
    )

    outcome = run.start()

    [item] = run.items()
    key = f"{outcome.run_id}:post:0:1"
    assert (item.category, item.severity, item.idempotency_key, item.blocks_run) == (
        "irreversible_external",
        "urgent",
        key,
        True,
    )
    assert outcome.status == "waiting"


def test_an_item_is_stored_redacted(tmp_path: Path) -> None:
    planted = "sk-or-" + "v1-" + "c3" * 32
    echoed = Raise(
        "run-1",
        "sig-key",
        Category.PROVIDER_FAILURE,
        f"call failed for key_{planted}",
        f"upstream 401: {planted}",
        tried=(f"retry with {planted}",),
    )
    with InboxTable.open(tmp_path) as inbox:
        found = inbox.get(inbox.raise_item(echoed, at="2026-10-17T09:00:00+00:00"))

    assert found is not None
    assert (found.title, found.cause, found.tried) == (
        "call failed for key_[redacted]",
        "upstream 401: [redacted]",
        ("retry with [redacted]",),
    )
