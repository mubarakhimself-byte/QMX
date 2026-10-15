from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    Message,
    RateLimitEvent,
    ResultMessage,
    StreamEvent,
    TextBlock,
)
from claude_agent_sdk._internal.message_parser import parse_message
from claude_agent_sdk.types import RateLimitInfo, ServerToolResultBlock

from qma.harness.project import (
    REDACTED,
    Block,
    Compacted,
    Delta,
    Fact,
    Here,
    InChild,
    Limits,
    Reading,
    TokenGate,
    TurnEnded,
    TurnUsage,
    project,
)

FIXTURES = Path(__file__).parent / "fixtures"
CHILD = InChild("toolu_01TNHT9HDZj9wdnvtjLfFWcw")
CANARY = "sk-ant-oat01-QMXCANARY" + "a1B2c3D4e5" * 4


def recorded(name: str) -> list[Message]:
    lines = (FIXTURES / name).read_text(encoding="utf-8").splitlines()
    parsed = (parse_message(json.loads(line)) for line in lines)
    return [message for message in parsed if message is not None]


def facts(name: str) -> list[Fact]:
    return [fact for message in recorded(name) for fact in project(message)]


HERE = Here()


def blocks(found: list[Fact], target: Here | InChild = HERE) -> list[tuple[str, Any]]:
    return [
        (fact.block.type, fact.block.content)
        for fact in found
        if isinstance(fact, Block) and fact.target == target
    ]


def test_a_read_turn_projects_tool_starts_results_and_the_answer() -> None:
    found = blocks(facts("readme_turn.jsonl"))
    assert [kind for kind, _ in found] == ["tool"] * 6 + ["text"]
    assert found[4:6] == [
        (
            "tool",
            {
                "id": "toolu_01SMQ8ykwepnSZZtyeZENSGy",
                "name": "Read",
                "arguments": {"file_path": "D:/Temp/qma-hp6/ws1/README.md"},
                "state": "started",
            },
        ),
        (
            "tool",
            {
                "id": "toolu_01SMQ8ykwepnSZZtyeZENSGy",
                "state": "finished",
                "result": "1\t# Weather Notes\n2\t\n3\tA tiny project that keeps daily weather "
                "notes for Lisbon.\n4\tRun `notes.py` to append today's reading to "
                "notes.csv.\n5\t",
            },
        ),
    ]
    assert found[1] == (
        "tool",
        {
            "id": "toolu_018FEnUb46ka3iMAZF7MaAdD",
            "name": "Glob",
            "arguments": {"pattern": "README*", "path": "D:/Temp/qma-hp6/ws1"},
            "state": "started",
        },
    )


def test_streamed_text_deltas_spell_the_final_text_block() -> None:
    found = facts("readme_turn.jsonl")
    streamed = "".join(f.text for f in found if isinstance(f, Delta) and f.kind == "text")
    final = [content["text"] for kind, content in blocks(found) if kind == "text"]
    assert final == [streamed]
    assert streamed.startswith("The folder `D:\\Temp\\qma-hp6\\ws1` has three files:")


def test_the_result_ends_the_turn_and_reports_usage() -> None:
    found = facts("readme_turn.jsonl")
    ended = [fact for fact in found if isinstance(fact, TurnEnded)]
    usage = [fact for fact in found if isinstance(fact, TurnUsage)]
    assert [(e.ok, e.terminal_reason, e.deferred_tool_use) for e in ended] == [
        (True, "completed", False)
    ]
    assert str(ended[0].result).endswith("I can read them if you want to check.")
    assert [(u.session_id, u.num_turns) for u in usage] == [
        ("e793343e-1f7e-4e11-b665-b7224355ea53", 4)
    ]


def test_todo_tasks_become_plan_blocks() -> None:
    plans = [content for kind, content in blocks(facts("helper_turn.jsonl")) if kind == "plan"]
    assert plans == [
        {
            "tool": "TaskCreate",
            "subject": "Count files in the working folder",
            "description": "Use a helper agent to count the files in D:\\Temp\\qma-hp6\\ws1.",
            "activeForm": "Counting files in the working folder",
        },
        {
            "tool": "TaskCreate",
            "subject": "Name the largest file in the working folder",
            "description": "Using the helper agent's results, identify the largest file in "
            "D:\\Temp\\qma-hp6\\ws1 and report its name.",
            "activeForm": "Finding the largest file",
        },
        {"tool": "TaskUpdate", "taskId": "1", "status": "completed"},
        {"tool": "TaskUpdate", "taskId": "2", "status": "completed"},
    ]


def test_a_helper_agent_gets_cards_and_its_own_child_target() -> None:
    found = facts("helper_turn.jsonl")
    cards = [content for kind, content in blocks(found) if kind == "agents"]
    assert cards[0] == {
        "tool_use_id": "toolu_01TNHT9HDZj9wdnvtjLfFWcw",
        "name": "general-purpose",
        "description": "Count files and find largest",
        "state": "working",
    }
    assert [card["state"] for card in cards] == ["working", "working", "completed", "completed"]
    child = blocks(found, CHILD)
    assert child[:2] == [
        (
            "tool",
            {
                "id": "toolu_011ji7UEB7stebx1Q4YsMNjM",
                "name": "Bash",
                "arguments": child[0][1]["arguments"],
                "state": "started",
            },
        ),
        (
            "tool",
            {
                "id": "toolu_011ji7UEB7stebx1Q4YsMNjM",
                "state": "error",
                "result": "approvals are not wired yet",
            },
        ),
    ]
    progress = [f for f in found if isinstance(f, Delta) and f.kind == "tool_progress"]
    assert {f.target for f in progress} == {CHILD}


def test_a_rate_limit_event_keeps_every_overage_field() -> None:
    limits = [fact for fact in facts("helper_turn.jsonl") if isinstance(fact, Limits)]
    assert limits == [
        Limits(
            window="five_hour",
            status="allowed",
            utilization=None,
            resets_at=datetime(2026, 10, 14, 22, 20, tzinfo=UTC),
            overage_status="rejected",
            overage_resets_at=None,
            overage_disabled_reason="out_of_credits",
            using_overage=False,
            overage_enabled=None,
            credits_required=False,
            readings=(
                Reading("five_hour", 0.26, datetime(2026, 10, 14, 22, 20, tzinfo=UTC)),
                Reading("seven_day", 0.11, datetime(2026, 10, 21, 13, 0, tzinfo=UTC)),
            ),
        )
    ]


def test_a_recorded_compact_boundary_is_a_manual_compaction() -> None:
    assert facts("compact_boundary.jsonl") == [Compacted("manual")]


def test_a_printed_token_is_redacted_unless_the_check_turns_redaction_off() -> None:
    message = AssistantMessage(content=[TextBlock(f"the login is {CANARY}.")], model="haiku")
    assert blocks(project(message)) == [("text", {"text": f"the login is {REDACTED}."})]
    assert blocks(project(message, redact_tokens=False)) == [
        ("text", {"text": f"the login is {CANARY}."})
    ]


def test_the_token_gate_redacts_a_token_split_across_deltas() -> None:
    gate = TokenGate()
    pieces = ["the login is s", "k-an", "t-oat01-QMX", "CANARY", "a1B2c3D4e5 and more", " text"]
    shown = [gate.feed("text", piece) for piece in pieces] + [gate.close()]
    assert shown == [
        [("text", "the login is ")],
        [],
        [],
        [],
        [("text", f"{REDACTED} and more")],
        [("text", " text")],
        [],
    ]


def test_the_token_gate_holds_a_prefix_until_the_turn_ends_and_labels_each_kind() -> None:
    gate = TokenGate()
    assert gate.feed("thinking", "check the tests") == [("thinking", "check the test")]
    assert gate.feed("text", "! sk-ant-oat01") == [("thinking", "s"), ("text", "! ")]
    assert gate.close() == [("text", REDACTED)]


def test_the_token_gate_holds_a_long_open_token_in_linear_time() -> None:
    gate = TokenGate()
    start = time.perf_counter()
    shown = gate.feed("text", "key sk-ant-")
    for _ in range(32_000):
        shown += gate.feed("text", "A")
    shown += gate.feed("text", " done")
    assert time.perf_counter() - start < 1.0
    assert shown == [("text", "key "), ("text", f"{REDACTED} done")]


def streamed(kind: str, text: str, parent: str | None = None) -> StreamEvent:
    field = "text" if kind == "text_delta" else "thinking"
    return StreamEvent(
        uuid="u",
        session_id="s",
        event={"type": "content_block_delta", "index": 0, "delta": {"type": kind, field: text}},
        parent_tool_use_id=parent,
    )


def result(**changes: Any) -> ResultMessage:
    fields: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 1,
        "duration_api_ms": 1,
        "is_error": False,
        "num_turns": 1,
        "session_id": "s",
        "terminal_reason": "completed",
    }
    return ResultMessage(**(fields | changes))


def test_streamed_deltas_reach_the_token_gate_unredacted() -> None:
    assert project(streamed("text_delta", "key sk-ant-oat01-QMX")) == [
        Delta(HERE, "text", "key sk-ant-oat01-QMX")
    ]
    assert project(streamed("thinking_delta", "hmm", parent="toolu_1")) == [
        Delta(InChild("toolu_1"), "thinking", "hmm")
    ]


def test_every_result_ends_its_turn_including_an_injected_one() -> None:
    mine = project(result())
    injected = project(result(origin={"kind": "task-notification"}))
    ended = TurnEnded(ok=True, terminal_reason="completed", deferred_tool_use=False)
    assert [fact for fact in mine if isinstance(fact, TurnEnded)] == [ended]
    assert [fact for fact in injected if isinstance(fact, TurnEnded)] == [ended]


def test_a_failed_turn_and_a_model_error_each_ask_for_the_operator() -> None:
    failed = project(result(subtype="error_during_execution", is_error=True, result="boom"))
    errored = AssistantMessage(content=[], model="haiku", error="rate_limit")
    assert blocks(failed) == [("needs_you", {"reason": "the turn failed: boom"})]
    assert blocks(project(errored)) == [("needs_you", {"reason": "model error: rate_limit"})]


@pytest.mark.parametrize("reason", ["aborted_tools", "aborted_streaming"])
def test_an_interrupted_turn_ends_quietly(reason: str) -> None:
    interrupted = project(
        result(
            subtype="error_during_execution",
            is_error=True,
            errors=["[ede_diagnostic] result_type=user last_content_type=n/a"],
            terminal_reason=reason,
        )
    )
    assert blocks(interrupted) == []
    assert [fact for fact in interrupted if isinstance(fact, TurnEnded)] == [
        TurnEnded(ok=False, terminal_reason=reason, deferred_tool_use=False)
    ]


def test_a_server_tool_result_finishes_its_tool_block() -> None:
    message = AssistantMessage(
        content=[ServerToolResultBlock(tool_use_id="srvtoolu_1", content={"hits": 2})],
        model="haiku",
    )
    assert blocks(project(message)) == [
        ("tool", {"id": "srvtoolu_1", "state": "finished", "result": '{"hits": 2}'})
    ]


def test_credits_required_in_raw_reaches_the_limits_fact() -> None:
    info = RateLimitInfo(
        status="rejected", rate_limit_type="five_hour", raw={"credits_required": 1}
    )
    event = RateLimitEvent(rate_limit_info=info, uuid="u", session_id="s")
    assert project(event) == [
        Limits(
            window="five_hour",
            status="rejected",
            utilization=None,
            resets_at=None,
            overage_status=None,
            overage_resets_at=None,
            overage_disabled_reason=None,
            using_overage=None,
            overage_enabled=None,
            credits_required=True,
        )
    ]
