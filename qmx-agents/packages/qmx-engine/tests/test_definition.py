"""The qmx.workflow/1 validator, read through a workflow folder the way the engine loads one."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import jsonschema
import pytest

from qmx_engine.__main__ import main
from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.model import Node, Workflow, dropped, json_schema
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import DEFAULT_ROLES, runnable, validate

FIXTURES = Path(__file__).parent / "fixtures" / "workflows"
SCHEMA_FILE = (
    Path(__file__).parents[1]
    / "src"
    / "qmx_engine"
    / "definition"
    / "schema"
    / "qmx.workflow.1.json"
)


def codes(
    folder: Path, *, publish: bool = False, roles: frozenset[str] = DEFAULT_ROLES
) -> list[str]:
    return [problem.code for problem in validate(load(folder), publish=publish, roles=roles)]


def copy(name: str, into: Path) -> Path:
    return Path(shutil.copytree(FIXTURES / name, into / name))


def edit(folder: Path, change: dict[str, object]) -> None:
    path = folder / "definition.json"
    path.write_text(
        json.dumps(json.loads(path.read_text(encoding="utf-8")) | change), encoding="utf-8"
    )


def test_the_paper_scout_fixture_validates_and_prints_its_hash(
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = load(FIXTURES / "paper-scout-min")

    assert validate(folder) == []
    assert main(["validate", str(FIXTURES / "paper-scout-min")]) == 0
    assert capsys.readouterr().out == f"ok {content_hash(folder)}\n"
    assert sorted(folder.refs) == [
        "prompts/triage.md",
        "schemas/paper_card.json",
        "schemas/triage.json",
        "scripts/citation_check.py",
        "scripts/feed_ids.py",
    ]


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("bad-cycle", ["cycle"]),
        ("bad-unknown-kind", ["kind_unknown"]),
        ("bad-unknown-type-version", ["type_version_unknown"]),
        ("bad-two-triggers", ["trigger_count"]),
        ("bad-unreachable", ["node_unreachable", "node_unreachable"]),
        ("bad-keyed-join-no-key", ["keyed_join_without_key", "join_inbound_invalid"]),
        ("bad-cartesian-not-explicit", ["cartesian_not_explicit"]),
        ("bad-ref-escape", ["ref_escapes_folder"]),
    ],
)
def test_each_bad_graph_fails_with_its_code(fixture: str, expected: list[str]) -> None:
    assert codes(FIXTURES / fixture) == expected


def test_every_problem_is_returned_not_only_the_first(tmp_path: Path) -> None:
    folder = copy("bad-cycle", tmp_path)
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    document["nodes"].append({"id": "x", "name": "X", "type": "teleport", "typeVersion": 1})
    document["connections"]["X"] = {"main": [[{"node": "A", "port": "in", "map": "one"}]]}
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    assert codes(folder) == ["kind_unknown", "cycle", "node_unreachable"]


def test_a_moved_node_keeps_the_hash_and_a_one_byte_prompt_edit_changes_it(tmp_path: Path) -> None:
    folder = copy("paper-scout-min", tmp_path)
    before = content_hash(load(folder))
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    for node in document["nodes"]:
        node["position"] = [node["position"][0] + 40, 300]
    document["meta"] = {"created_by": "operator"}
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    moved = load(folder)
    prompt = folder / "prompts" / "triage.md"
    prompt.write_bytes(b"S" + prompt.read_bytes()[1:])
    edited = load(folder)

    assert content_hash(moved) == before
    assert content_hash(edited) != before


def test_a_draft_may_hold_notes_and_loose_nodes_but_publish_refuses_them() -> None:
    assert codes(FIXTURES / "draft-note") == []
    assert codes(FIXTURES / "draft-note", publish=True) == [
        "note_at_publish",
        "unconnected_at_publish",
    ]


def test_an_unavailable_kind_validates_in_a_draft_and_a_run_refuses_it() -> None:
    folder = load(FIXTURES / "draft-rlm")

    assert validate(folder) == []
    assert [(p.code, p.path) for p in runnable(Workflow.model_validate(folder.document))] == [
        ("kind_not_available", "nodes[1].type"),
    ]
    rlm = REGISTRY.kind("rlm")
    assert rlm is not None
    assert rlm.available is False


def test_a_pack_type_is_checked_against_its_base_kind(tmp_path: Path) -> None:
    folder = copy("bad-money", tmp_path)
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    document["nodes"][1] = {"id": "l", "name": "Decide", "type": "lab.cell", "typeVersion": 1}
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    with_pack = REGISTRY.with_pack("lab.cell", "llm")

    assert codes(folder) == ["kind_unknown"]
    assert [p.code for p in validate(load(folder), registry=with_pack)] == ["role_required"]


def test_roles_placements_and_credentials_resolve_by_name(tmp_path: Path) -> None:
    folder = copy("agent-no-limits", tmp_path)
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    document["nodes"][1] |= {
        "role": "poet",
        "runs_on": ["pc", "server-1"],
        "credentials": {"broker": "plain-value", "feed": "qmx/feed"},
    }
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    assert codes(folder) == [
        "role_unknown",
        "placement_unknown",
        "credential_not_ref",
        "credential_not_tool_key",
    ]
    assert codes(folder, roles=frozenset({"poet"})) == [
        "placement_unknown",
        "credential_not_ref",
        "credential_not_tool_key",
    ]


def test_an_old_runaway_block_and_run_timeout_fold_to_nothing(tmp_path: Path) -> None:
    folder = copy("draft-rlm", tmp_path)
    edit(folder, {"settings": {"runaway": {"tokens": 1000, "usd": 5, "on_runaway": "degrade"}}})
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    document["nodes"][1]["timeout"] = {"run_seconds": 600, "idle_seconds": 90}
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    assert validate(load(folder)) == []
    workflow = Workflow.model_validate(load(folder).document)
    assert dropped(workflow) == ["settings.runaway", "nodes[1].timeout.run_seconds"]
    assert workflow.settings.limits is None
    assert workflow.nodes[1].timeout is not None
    assert workflow.nodes[1].timeout.model_dump(exclude_none=True) == {"idle_seconds": 90}


def test_a_usd_limit_is_not_part_of_the_format(tmp_path: Path) -> None:
    folder = copy("draft-rlm", tmp_path)
    edit(folder, {"settings": {"limits": {"tokens": 1000, "usd": 5}}})

    assert [(p.code, p.path) for p in validate(load(folder))] == [
        ("schema_invalid", "settings.limits.usd")
    ]


def test_the_shipped_json_schema_is_the_model_and_accepts_the_fixture() -> None:
    shipped = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    document = json.loads(
        (FIXTURES / "paper-scout-min" / "definition.json").read_text(encoding="utf-8")
    )

    assert shipped == json_schema()
    jsonschema.validate(document, shipped)


def test_no_output_echoes_a_key_pasted_into_a_ref_a_role_or_a_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    key = "sk-proj-" + "Zq9" * 12
    folder = copy("agent-no-limits", tmp_path)
    document = json.loads((folder / "definition.json").read_text(encoding="utf-8"))
    document["nodes"][1] |= {
        "role": key,
        "runs_on": key,
        "parameters": {"api_key_ref": key},
    }
    document["connections"][key] = {"main": [[{"node": key, "port": key, "map": "one"}]]}
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    assert main(["validate", str(folder)]) == 1
    out = capsys.readouterr().out
    assert key not in out
    assert [line.split(" ", 1)[0] for line in out.splitlines()] == [
        "ref_missing",
        "edge_unknown_node",
        "role_unknown",
        "placement_unknown",
        "secret_literal",
        "secret_literal",
        "secret_literal",
        "secret_literal",
        "secret_literal",
        "secret_literal",
    ]


def test_an_agent_node_declares_known_toolsets_and_a_wrong_name_is_refused() -> None:
    node = {"id": "read", "name": "Read", "type": "agent", "typeVersion": 1}
    good = Node.model_validate(node | {"toolsets": ["library", "mcp:firecrawl"], "skills": ["a"]})
    assert (good.toolsets, good.skills) == (["library", "mcp:firecrawl"], ["a"])
    assert "toolsets" not in Node.model_validate(node).model_dump(by_alias=True)
    with pytest.raises(ValueError, match=r"unknown toolsets \['libary', 'mcp:'\]"):
        Node.model_validate(node | {"toolsets": ["libary", "mcp:"]})
