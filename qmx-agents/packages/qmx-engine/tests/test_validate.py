"""Validation refuses two writers that may run at once on one declared path (AD-51)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flows import edge, folder, node

from qmx_engine.definition.folder import load
from qmx_engine.definition.validate import validate

START = node("start", "trigger")


def writer(name: str, *files: dict[str, Any]) -> dict[str, Any]:
    found = node(name, "script", script=f"scripts/{name}.py")
    found["outputs"] = {"files": list(files)}
    return found


def problems(
    tmp_path: Path, nodes: list[dict[str, Any]], connections: dict[str, Any]
) -> list[tuple[str, str]]:
    scripts = {n["name"]: "print(1)" for n in nodes}
    root = folder(tmp_path / "wf", [START, *nodes], connections, scripts)
    return [(p.code, p.path) for p in validate(load(root))]


def test_two_partitions_of_one_node_may_not_replace_one_path(tmp_path: Path) -> None:
    fanned = {"start": {"main": [edge("w", "broadcast")]}}

    plain = problems(tmp_path / "a", [writer("w", {"path": "out.json"})], fanned)
    templated = problems(tmp_path / "b", [writer("w", {"path": "out/<partition>.json"})], fanned)
    merged = problems(tmp_path / "c", [writer("w", {"path": "out.json", "merge": "keyed"})], fanned)

    assert plain == [("zone_writer_concurrent", "nodes[1].outputs.files[0].path")]
    assert (templated, merged) == ([], [])


def test_two_nodes_with_no_path_between_them_may_not_write_one_path(tmp_path: Path) -> None:
    side_by_side = {"start": {"main": [edge("a"), edge("b")]}}
    in_a_row = {"start": {"main": [edge("a")]}, "a": {"main": [edge("b")]}}
    nodes = [writer("a", {"path": "report.md"}), writer("b", {"path": "*.md"})]
    appended = [
        writer("a", {"path": "log.txt", "merge": "append"}),
        writer("b", {"path": "log.txt", "merge": "append"}),
    ]

    assert problems(tmp_path / "a", nodes, side_by_side) == [
        ("zone_writer_concurrent", "nodes[2].outputs.files[0].path")
    ]
    assert problems(tmp_path / "b", nodes, in_a_row) == []
    assert problems(tmp_path / "c", appended, side_by_side) == []


def test_an_output_path_may_not_leave_the_shared_zone(tmp_path: Path) -> None:
    nodes = [writer("w", {"path": "../home/ledger.db"}, {"path": ".staging/x"})]

    assert problems(tmp_path, nodes, {"start": {"main": [edge("w")]}}) == [
        ("output_path_invalid", "nodes[1].outputs.files[0].path"),
        ("output_path_invalid", "nodes[1].outputs.files[1].path"),
    ]
