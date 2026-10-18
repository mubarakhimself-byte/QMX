from __future__ import annotations

from pathlib import Path

from flows import edge, folder, kinds, node, run_folder
from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_engine.ledger.events import Event


def outputs(events: list[Event], node_id: str) -> JsonValue:
    return next(
        e.data["outputs"]
        for e in events
        if e.kind == "node_finished" and e.data["node_id"] == node_id
    )


def test_a_monitor_over_an_unchanged_source_ends_silent_and_starts_nothing(tmp_path: Path) -> None:
    home = tmp_path / "home"
    root = folder(
        tmp_path / "wf",
        [
            node("start", "trigger"),
            node("watch", "monitor", source="scripts/feed.py"),
            node("act", "script", script="scripts/act.py"),
        ],
        {"start": {"main": [edge("watch")]}, "watch": {"changed": [edge("act")]}},
        {
            "feed": 'import json\nprint(json.dumps({"ids": ["a", "b"]}))\n',
            "act": "print(1)\n",
        },
    )

    _, first = run_folder(root, home)
    second_outcome, second = run_folder(root, home)

    assert outputs(first, "watch") == {
        "changed": {
            "value": {"ids": ["a", "b"]},
            "diff": {"before": None, "after": {"ids": ["a", "b"]}},
        }
    }
    assert kinds(first, "act").count("node_started") == 1
    assert second_outcome.status == "passed"
    assert outputs(second, "watch") == {"silent": {"hash": fingerprint({"ids": ["a", "b"]})}}
    assert kinds(second, "act") == []
