"""One case per lint rule, each through `validate` on a folder, as the engine and CLI call it."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import validate

FIXTURES = Path(__file__).parent / "fixtures" / "workflows"


def problems(folder: Path) -> list[tuple[str, str]]:
    return [(problem.code, problem.path) for problem in validate(load(folder))]


def with_parameters(tmp_path: Path, parameters: dict[str, object]) -> Path:
    """`bad-money`'s llm node, its parameters replaced."""
    folder = Path(shutil.copytree(FIXTURES / "bad-money", tmp_path / "wf"))
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["nodes"][1]["parameters"] = parameters
    path.write_text(json.dumps(document), encoding="utf-8")
    return folder


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("bad-settings-write", [("settings_write", "nodes[1].parameters.op")]),
        ("bad-trigger-creation", [("trigger_creation", "nodes[1].parameters.op")]),
        ("bad-money", [("money_act", "nodes[1].parameters.action")]),
        ("bad-broadcast", [("chunk_required", "connections.List papers.main[0][0]")]),
        ("bad-loop-no-max-iterations", [("loop_max_iterations_missing", "nodes[1].parameters")]),
        ("bad-human-gate", [("human_gate_misplaced", "nodes[1]")]),
    ],
)
def test_each_lint_rule_refuses_its_fixture(fixture: str, expected: list[tuple[str, str]]) -> None:
    assert problems(FIXTURES / fixture) == expected


@pytest.mark.parametrize(
    "spelling",
    [
        "submit-order",
        "Close position",
        "mcp__broker__place_order",
        "qmb.cancel_order",
        "paper_buy",
        "closeAllPositions",
        "update_stop_loss",
    ],
)
def test_a_money_act_is_refused_in_any_spelling_or_nesting(tmp_path: Path, spelling: str) -> None:
    folder = with_parameters(tmp_path, {"tools": ["Read", spelling]})

    assert problems(folder) == [("money_act", "nodes[1].parameters.tools[1]")]


@pytest.mark.parametrize(
    ("parameters", "path"),
    [
        ({"place_order": True}, "nodes[1].parameters.place_order"),
        (
            {"tools": {"Read": {"allow": True}, "mcp__broker__place_order": {"allow": True}}},
            "nodes[1].parameters.tools.mcp__broker__place_order",
        ),
    ],
)
def test_a_money_act_named_by_a_key_is_refused(
    tmp_path: Path, parameters: dict[str, object], path: str
) -> None:
    assert problems(with_parameters(tmp_path, parameters)) == [("money_act", path)]


def test_settings_writes_and_trigger_creation_named_by_a_key_are_refused(tmp_path: Path) -> None:
    folder = with_parameters(tmp_path, {"calls": {"settings.write": 1, "create_trigger": 1}})

    assert problems(folder) == [
        ("settings_write", "nodes[1].parameters.calls.settings.write"),
        ("trigger_creation", "nodes[1].parameters.calls.create_trigger"),
    ]


def test_words_that_only_look_like_an_act_or_a_key_pass(tmp_path: Path) -> None:
    folder = with_parameters(
        tmp_path,
        {
            "sort_by": "position",
            "expr": "items.size",
            "kind": "order",
            "metric": "risk-adjusted-returns-model-2026",
            "prompt": "Explain why traders place orders before the close.",
            "tool": "add_trade_note",
        },
    )

    assert problems(folder) == []


def test_a_token_shaped_literal_is_refused_without_echoing_it(tmp_path: Path) -> None:
    literal = "sk-" + "Ab3" * 14
    folder = with_parameters(tmp_path, {"prompt": f"use {literal} to call the feed"})

    found = validate(load(folder))
    assert [(p.code, p.path) for p in found] == [("secret_literal", "nodes[1].parameters.prompt")]
    assert literal not in found[0].message


def test_chunk_into_an_agent_passes_where_broadcast_fails(tmp_path: Path) -> None:
    folder = Path(shutil.copytree(FIXTURES / "bad-broadcast", tmp_path / "wf"))
    path = folder / "definition.json"
    text = path.read_text(encoding="utf-8").replace(
        '"map": "broadcast"', '"map": "chunk", "chunk": {"by": "items", "size": 5}'
    )
    path.write_text(text, encoding="utf-8")

    assert problems(folder) == []


def test_a_human_gate_in_front_of_an_external_send_passes(tmp_path: Path) -> None:
    folder = Path(shutil.copytree(FIXTURES / "bad-human-gate", tmp_path / "wf"))
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["nodes"][2] = {
        "id": "w", "name": "Save", "type": "app_op", "typeVersion": 1,
        "parameters": {"op": "send_message"}, "effect": "irreversible_external",
    }  # fmt: skip
    path.write_text(json.dumps(document), encoding="utf-8")

    assert problems(folder) == []


def test_an_agent_with_no_limits_validates() -> None:
    assert problems(FIXTURES / "agent-no-limits") == []


def test_only_a_limit_he_wrote_below_one_is_refused(tmp_path: Path) -> None:
    folder = Path(shutil.copytree(FIXTURES / "agent-no-limits", tmp_path / "wf"))
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["settings"] = {"limits": {"turns": 2, "wall_seconds": 0}}
    document["nodes"][1]["limits"] = {"tool_calls": -1, "tokens": 1}
    path.write_text(json.dumps(document), encoding="utf-8")

    assert problems(folder) == [
        ("limit_below_one", "settings.limits.wall_seconds"),
        ("limit_below_one", "nodes[1].limits.tool_calls"),
    ]
