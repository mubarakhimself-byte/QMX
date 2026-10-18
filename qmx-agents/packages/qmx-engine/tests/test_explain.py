"""`explain` reads one document per run from the ledger, whatever state the run ended in."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from flows import CHAIN, edge, folder, node, run_folder
from planted import Planted, fails, flow

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


def test_a_provider_error_echoing_a_key_reads_redacted_in_explain_and_the_inbox(
    tmp_path: Path,
) -> None:
    planted = "sk-or-" + "v1-" + "d4" * 32
    run = flow(
        tmp_path,
        [node("start", "trigger"), node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        executors={
            "script": Planted(
                fails(f"upstream 401 for key_{planted}", code="auth", retryable=False)
            )
        },
    )

    outcome = run.start()
    document = explain_run(run.home, outcome.run_id)
    [item] = run.items()

    [attempt] = nodes_of(document)["call"]["attempts"]
    assert attempt["message"] == "upstream 401 for key_[redacted]"
    assert planted not in str(document)
    assert item.cause == "upstream 401 for key_[redacted]"
