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
    """`llm-node`'s llm node, its parameters replaced."""
    folder = Path(shutil.copytree(FIXTURES / "llm-node", tmp_path / "wf"))
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
        ("bad-broadcast", [("chunk_required", "connections.List papers.main[0][0]")]),
        ("bad-loop-no-max-iterations", [("loop_max_iterations_missing", "nodes[1].parameters")]),
        ("bad-human-gate", [("human_gate_misplaced", "nodes[1]")]),
    ],
)
def test_each_lint_rule_refuses_its_fixture(fixture: str, expected: list[tuple[str, str]]) -> None:
    assert problems(FIXTURES / fixture) == expected


def test_a_node_named_for_an_order_act_lints_clean(tmp_path: Path) -> None:
    folder = Path(shutil.copytree(FIXTURES / "llm-node", tmp_path / "wf"))
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["nodes"][1] |= {"id": "submit_order", "name": "submit_order"}
    document["connections"]["Start"]["main"][0][0]["node"] = "submit_order"
    path.write_text(json.dumps(document), encoding="utf-8")

    assert problems(folder) == []


def test_settings_writes_and_trigger_creation_named_by_a_key_are_refused(tmp_path: Path) -> None:
    folder = with_parameters(tmp_path, {"calls": {"settings.write": 1, "create_trigger": 1}})

    assert problems(folder) == [
        ("settings_write", "nodes[1].parameters.calls.settings.write"),
        ("trigger_creation", "nodes[1].parameters.calls.create_trigger"),
    ]


def test_ordinary_parameters_pass(tmp_path: Path) -> None:
    folder = with_parameters(
        tmp_path,
        {
            "sort_by": "position",
            "expr": "items.size",
            "op": "settings_read",
            "call": "create_note",
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


def with_credentials(tmp_path: Path, credentials: dict[str, str]) -> Path:
    folder = Path(shutil.copytree(FIXTURES / "script-chain", tmp_path / "wf"))
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["nodes"][1]["credentials"] = credentials
    path.write_text(json.dumps(document), encoding="utf-8")
    return folder


def test_a_node_names_only_a_tool_key(tmp_path: Path) -> None:
    refused = with_credentials(
        tmp_path / "refused", {"broker": "qmx/ctrader", "llm": "qmx/openrouter"}
    )
    allowed = with_credentials(tmp_path / "allowed", {"search": "qmx/tool/serp"})

    assert problems(refused) == [
        ("credential_not_tool_key", "nodes[1].credentials.broker"),
        ("credential_not_tool_key", "nodes[1].credentials.llm"),
    ]
    assert problems(allowed) == []


def test_a_key_glued_to_a_word_is_refused_as_a_literal(tmp_path: Path) -> None:
    folder = with_parameters(tmp_path, {"note": "key_sk-or-" + "v1-" + "f0" * 32})

    assert problems(folder) == [("secret_literal", "nodes[1].parameters.note")]
