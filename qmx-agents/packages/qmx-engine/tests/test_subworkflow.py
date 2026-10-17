from __future__ import annotations

from pathlib import Path
from typing import Any

from flows import edge, events_of, folder, node, run_folder

START = node("start", "trigger")
ECHO = "import json, sys\nprint(json.dumps({'got': json.load(sys.stdin)['in']}))\n"


def call(workflow: str) -> dict[str, Any]:
    return node("call", "subworkflow", workflow=workflow)


def failure(home: Path, run_id: str) -> str:
    return next(str(e.data["code"]) for e in events_of(home, run_id) if e.kind == "node_failed")


def test_a_child_runs_as_its_own_run_and_the_parent_continues_on_its_output(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    root = folder(
        tmp_path / "wf",
        [START, call("child"), node("after", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("call")]}, "call": {"main": [edge("after")]}},
        {"echo": ECHO},
    )
    folder(
        root / "child",
        [START, node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )

    outcome, _ = run_folder(root, home, 7)

    child = f"{outcome.run_id}.call.0.1"
    created = events_of(home, child)[0].data
    assert outcome.outputs == {
        "after": {"main": {"got": {"run_id": child, "outputs": {"echo": {"main": {"got": 7}}}}}}
    }
    assert (created["parent_run_id"], created["call_depth"]) == (outcome.run_id, 1)


def test_a_child_past_the_depth_ceiling_is_refused(tmp_path: Path) -> None:
    home = tmp_path / "home"
    root = folder(tmp_path / "wf", [START, call("child")], {"start": {"main": [edge("call")]}}, {})
    folder(root / "child", [START, call("grandchild")], {"start": {"main": [edge("call")]}}, {})
    folder(root / "child" / "grandchild", [START], {}, {})

    outcome, _ = run_folder(root, home, **{"subworkflow.max_depth": 1})

    assert outcome.status == "failed"
    assert failure(home, outcome.run_id) == "subworkflow_failed"
    assert failure(home, f"{outcome.run_id}.call.0.1") == "call_depth_exceeded"


def test_a_child_whose_caller_policy_is_none_is_refused(tmp_path: Path) -> None:
    home = tmp_path / "home"
    root = folder(tmp_path / "wf", [START, call("child")], {"start": {"main": [edge("call")]}}, {})
    folder(root / "child", [START], {}, {}, caller_policy="none")

    outcome, _ = run_folder(root, home)

    assert (outcome.status, failure(home, outcome.run_id)) == ("failed", "caller_refused")
