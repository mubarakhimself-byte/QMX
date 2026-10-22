"""Forwarding between two owned instances (AD-21, AD-65): the merged read names each row's home,
an answer folds only at the home, and a node that stops answering keeps its last rows.

The wire is intercepted at its own seam, the JSON POST the `Forwarder` makes: the other side is a
real `EngineService` answering its real verbs, so the pass check and the verb table both run.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest
from flows import CHAIN
from pydantic import JsonValue

from qmx_engine.heartbeat import HubReply, Pause
from qmx_engine.ports.inbox import Category, Raise
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.service.forward import (
    PASS_HEADER,
    Forwarder,
    ForwardRefused,
    Instance,
    mint_host_pass,
    verify_host_pass,
)

KEY = "pairing-key-of-this-test"
AT = "2026-10-22T00:00:00+00:00"


def wire(node: EngineService, key: str = KEY):
    """The far side of the POST: it verifies the pass, then answers from the node's own stores."""

    def post(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
        verify_host_pass(key, headers[PASS_HEADER], target=node.name, now=1_000.0)
        try:
            value = node.answer(
                str(body["verb"]),
                body["args"] if isinstance(body["args"], dict) else {},
                principal="operator",
            )
        except Refused as refused:
            return {"ok": False, "code": refused.code, "message": str(refused)}
        return {"ok": True, "value": value}

    return post


def asked(
    post: Callable[[str, Mapping[str, JsonValue], Mapping[str, str]], JsonValue],
    *,
    source: str = "pc",
) -> Forwarder:
    return Forwarder(
        Instance("contabo", "http://contabo.tailnet"),
        key=KEY,
        source=source,
        principal="operator",
        clock=lambda: 1_000.0,
        now=lambda: AT,
        post=post,
    )


def test_a_merged_run_list_names_each_rows_home(tmp_path: Path) -> None:
    with (
        EngineService.open(tmp_path / "node-home", name="contabo") as node,
        EngineService.open(tmp_path / "pc-home", name="pc") as pc,
    ):
        draft = node.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR)
        asyncio.run(node.tests.run(draft.item, caller=OPERATOR))
        version = node.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        ran = asyncio.run(node.runs.start(version, caller=OPERATOR))
        pc.watching(name="pc", forwarders=[asked(wire(node))])

        rows = pc.merged_runs(draft.item)

    assert [(row.home_engine, row.row["mode"]) for row in rows] == [
        ("contabo", "test"),
        ("contabo", "live"),
    ]
    assert [row.row["run_id"] for row in rows if row.row["mode"] == "live"] == [ran.run_id]


def test_an_inbox_answer_is_forwarded_and_only_the_home_folds_it(tmp_path: Path) -> None:
    with (
        EngineService.open(tmp_path / "node-home", name="contabo") as node,
        EngineService.open(tmp_path / "pc-home", name="pc") as pc,
    ):
        raised = node.ctx.inbox.raise_item(
            Raise(
                "run-on-contabo",
                "auth:401",
                Category.PROVIDER_FAILURE,
                "planner failed: auth",
                "the provider refused the key",
            ),
            at=AT,
        )
        pc.watching(name="pc", forwarders=[asked(wire(node))])
        seen = pc.merged_inbox()
        answered = pc.inbox.answer_forwarded(raised, "retry", caller=OPERATOR)
        folded = node.inbox.list(open_only=False)
        here = pc.inbox.list(open_only=False)

    assert [(row.home_engine, row.row["id"]) for row in seen] == [("contabo", raised)]
    assert cast("Mapping[str, JsonValue]", answered)["resolution"] == "retry"
    assert [(item.id, item.resolution) for item in folded] == [(raised, "retry")]
    assert here == []


def test_an_unreachable_node_keeps_its_last_rows_and_says_since_when(tmp_path: Path) -> None:
    with (
        EngineService.open(tmp_path / "node-home", name="contabo") as node,
        EngineService.open(tmp_path / "pc-home", name="pc") as pc,
    ):
        raised = node.ctx.inbox.raise_item(
            Raise(
                "run-on-contabo",
                "harness:error",
                Category.SYSTEM_FAULT,
                "writer failed: harness_error",
                "the chat could not start",
            ),
            at=AT,
        )
        live = wire(node)
        dark = {"now": False}

        def post(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
            if dark["now"]:
                raise OSError("no route to host")
            return live(url, body, headers)

        pc.watching(name="pc", forwarders=[asked(post)])
        seen = pc.merged_inbox()
        dark["now"] = True
        lost = pc.merged_inbox()

    assert [(row.home_engine, row.stale, row.row["id"]) for row in seen] == [
        ("contabo", False, raised)
    ]
    assert [(row.home_engine, row.stale, row.row["id"]) for row in lost] == [
        ("contabo", True, raised)
    ]
    assert lost[0].row["detail"] == f"server unreachable since {AT}"


def test_a_node_never_reached_still_reads_as_unreachable(tmp_path: Path) -> None:
    def post(url: str, body: Mapping[str, JsonValue], headers: Mapping[str, str]) -> JsonValue:
        raise OSError("connection refused")

    with EngineService.open(tmp_path / "pc-home", name="pc") as pc:
        pc.watching(name="pc", forwarders=[asked(post)])
        rows = pc.merged_inbox()

    assert [(row.home_engine, row.stale) for row in rows] == [("contabo", True)]
    assert rows[0].row["detail"] == f"server unreachable since {AT}"


def test_the_pause_flag_is_honoured_and_goes_unknown_after_five_minutes() -> None:
    pause = Pause().heard(HubReply(autonomy_paused=True), at=1_000.0)

    assert pause.state(1_299.0) == "known"
    assert pause.state(1_300.0) == "unknown"
    assert (pause.shows(1_000.0), pause.flag(1_000.0)) == ("paused", True)
    assert (pause.shows(1_300.0), pause.flag(1_300.0)) == ("pause state unknown", True)
    assert Pause().shows(0.0) == "running"


def test_a_host_pass_names_the_pc_and_no_other_engine() -> None:
    pass_ = mint_host_pass(
        KEY, source="pc", target="contabo", principal="operator", now=1_000.0, ttl=30
    )
    verified = verify_host_pass(KEY, pass_, target="contabo", now=1_029.0)

    assert (verified.source, verified.principal) == ("pc", "operator")
    with pytest.raises(ForwardRefused) as wrong:
        verify_host_pass(KEY, pass_, target="qmb", now=1_001.0)
    with pytest.raises(ForwardRefused) as late:
        verify_host_pass(KEY, pass_, target="contabo", now=1_030.0)
    with pytest.raises(ForwardRefused) as forged:
        verify_host_pass(KEY, pass_[:-4] + "AAAA", target="contabo", now=1_001.0)
    assert (wrong.value.code, late.value.code, forged.value.code) == (
        "wrong_engine",
        "expired_pass",
        "bad_pass",
    )
