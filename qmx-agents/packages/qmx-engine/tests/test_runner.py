from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from flows import edge, folder, kinds, node, run_folder
from qmx_ledger.journal import fingerprint

from qmx_engine.ledger.store import Reader

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "workflows"
CHECK = """
    import json
    print(json.dumps({"verdict": "fail", "feedback": "no citations"}))
"""


def test_the_cli_runs_the_script_chain_to_run_finished(tmp_path: Path) -> None:
    chain = str(FIXTURES / "script-chain")
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "qmx_engine",
            "run",
            chain,
            "--home",
            str(tmp_path / "home"),
            "--create",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    lines = done.stdout.splitlines()
    assert (done.returncode, len(lines)) == (0, 2)
    assert lines[1] == f"run finished {fingerprint({'total': {'main': {'total': 20}}})}"


def test_a_grader_routes_to_fail_and_its_span_records_the_verdict(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [
            node("start", "trigger"),
            node("check", "grader", mode="deterministic", script="scripts/check.py"),
            node("ok", "script", script="scripts/note.py"),
            node("fix", "script", script="scripts/note.py"),
        ],
        {
            "start": {"main": [edge("check")]},
            "check": {"pass": [edge("ok")], "fail": [edge("fix")]},
        },
        {"check": CHECK, "note": "print(1)\n"},
    )

    outcome, events = run_folder(root, tmp_path / "home", "draft")

    with Reader.open(tmp_path / "home") as reader:
        verdicts = {s.node_id: s.verdict for s in reader.spans(outcome.run_id)}
    assert outcome.outputs == {"fix": {"main": 1}}
    assert verdicts["check"] == "fail"
    assert (kinds(events, "ok"), kinds(events, "fix").count("node_started")) == ([], 1)
