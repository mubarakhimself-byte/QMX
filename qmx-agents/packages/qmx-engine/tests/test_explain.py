"""`explain` reads one document per run from the ledger, whatever state the run ended in."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from flows import CHAIN, edge, folder, node, run_folder

from qmx_engine.ports.library import JsonObject
from qmx_engine.service.api import explain_run

FAILS = """
    import sys
    sys.exit("the totals do not add up")
"""
DOCUMENT_KEYS = {
    "run_id",
    "workflow_id",
    "mode",
    "content_hash",
    "status",
    "reason",
    "detail",
    "cost",
    "nodes",
}
NODE_KEYS = {"node_id", "state", "attempts", "spans", "ladder", "waits", "cost"}


def nodes_of(document: JsonObject) -> dict[str, dict[str, Any]]:
    nodes = cast(list[dict[str, Any]], document["nodes"])
    return {str(n["node_id"]): n for n in nodes}


def failing(root: Path, retry: dict[str, object]) -> Path:
    check = node("check", "script", script="scripts/check.py") | {"retry": retry}
    return folder(
        root,
        [node("start", "trigger"), check],
        {"start": {"main": [edge("check")]}},
        {"check": FAILS},
    )


def test_a_finished_run_explains_every_node(tmp_path: Path) -> None:
    outcome, _ = run_folder(CHAIN, tmp_path)
    document = explain_run(tmp_path, outcome.run_id)
    nodes = nodes_of(document)

    assert set(document) == DOCUMENT_KEYS
    assert (document["status"], document["reason"], document["mode"]) == ("passed", None, "test")
    assert [(n["node_id"], n["state"]) for n in nodes.values()] == [
        ("start", "ok"),
        ("numbers", "ok"),
        ("double", "ok"),
        ("total", "ok"),
    ]
    assert all(set(n) == NODE_KEYS for n in nodes.values())


def test_a_parked_run_names_the_node_its_ladder_and_the_cause(tmp_path: Path) -> None:
    root = failing(tmp_path / "wf", {"max_tries": 1})
    outcome, _ = run_folder(root, tmp_path / "home")
    document = explain_run(tmp_path / "home", outcome.run_id)
    check = nodes_of(document)["check"]

    assert (document["status"], document["reason"]) == ("failed", "parked")
    assert "the totals do not add up" in str(document["detail"])
    assert check["state"] == "parked"
    assert [s["step"] for s in check["ladder"]][-1] == "park"


def test_a_waiting_run_says_what_it_waits_for(tmp_path: Path) -> None:
    root = failing(tmp_path / "wf", {"max_tries": 3, "backoff_seconds": [600]})
    outcome, _ = run_folder(root, tmp_path / "home")
    document = explain_run(tmp_path / "home", outcome.run_id)

    assert (outcome.status, document["status"], document["reason"]) == (
        "waiting",
        "waiting",
        "retry",
    )
