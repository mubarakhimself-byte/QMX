"""B18c's surgical template fixes, run the way the engine runs them.

`b` seals no holdout and no split unless the study asks for them. `d3` and `l4` loop exactly as
many times as the counts on their card say, and `d4` keeps the card's count of variants. A
template's verdict comes from its `judge` child, the shared block, never from a copied gate
script. The loops run on the real engine with the template's own loop node and scripts; only the
QMB steps, which wait for QMB's door, are stood in for by fixed scripts.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from flows import run_folder
from pydantic import JsonValue
from qmx_home import resolve

from qmx_engine.templates.catalog import PACK

B = PACK / "b-build-and-prove"
D3 = PACK / "d3-iterate-against-qmb"
L4 = PACK / "l4-overnight-lab-loop"
D4 = PACK / "d4-variant-comparison"
DAY = 86_400 * 10**9
START = 1_735_689_600 * 10**9
"""2025-01-01 00:00 UTC."""
COSTS = {"spread": 1, "commission": 1, "slippage": 1, "swap": 1}


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return resolve(tmp_path / "QMX", create=True, drives=[]).home


def script(folder: Path, name: str, given: Any) -> Any:
    """One template script run as the engine runs it: isolated, its input on stdin, its folder as
    `QMX_CODE`."""
    ran = subprocess.run(
        [sys.executable, "-I", str(folder / "scripts" / name)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        env={**os.environ, "QMX_CODE": str(folder)},
    )
    return json.loads(ran.stdout)


def sealed(study: dict[str, JsonValue] | None = None) -> Any:
    given: dict[str, Any] = {
        "strategy": {"id": "unit-v1", "code_hash": "h1", "session_timezone": "Europe/London"},
        "data": {
            "start": "2020-01-01",
            "end": "2025-01-01",
            "fields": [{"name": "close", "pit": True}],
        },
        "costs": COSTS,
    }
    if study is not None:
        given["study"] = study
    return script(B, "spec.py", given)


def test_b_seals_no_holdout_and_no_split_by_default() -> None:
    out = sealed()

    assert out["ok"] is True
    assert out["spec"]["study"] == {
        "holdout": False,
        "holdout_share": 0.2,
        "split": False,
        "in_sample_share": 0.6,
        "folds": 3,
    }
    assert out["spec"]["windows"] == {
        "in_sample": {"start": "2020-01-01", "end": "2025-01-01"},
        "folds": [],
        "holdout": None,
    }


def test_b_seals_the_old_60_20_20_windows_when_the_study_turns_both_on() -> None:
    out = sealed({"holdout": True, "split": True})

    assert out["ok"] is True
    assert out["spec"]["windows"] == {
        "in_sample": {"start": "2020-01-01", "end": "2023-01-01"},
        "folds": [
            {"start": "2023-01-01", "end": "2023-05-03"},
            {"start": "2023-05-03", "end": "2023-09-02"},
            {"start": "2023-09-02", "end": "2024-01-02"},
        ],
        "holdout": {"start": "2024-01-02", "end": "2025-01-01"},
    }


def test_b_holds_out_without_splitting_when_only_the_holdout_is_on() -> None:
    out = sealed({"holdout": True})

    assert out["spec"]["windows"] == {
        "in_sample": {"start": "2020-01-01", "end": "2024-01-02"},
        "folds": [],
        "holdout": {"start": "2024-01-02", "end": "2025-01-01"},
    }


def write(folder: Path, name: str, text: str) -> str:
    path = folder / "scripts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")
    return f"scripts/{name}"


def flow_folder(
    root: Path, template: Path, nodes: list[dict[str, Any]], connections: dict[str, Any]
) -> Path:
    """A workflow folder carrying `template`'s inputs, so its scripts read the template's card."""
    card = json.loads((template / "definition.json").read_text("utf-8"))
    document = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "inputs": card["inputs"] | {"required": []},
        "nodes": nodes,
        "connections": connections,
    }
    (root / "definition.json").write_text(json.dumps(document), "utf-8")
    return root


def node_of(template: Path, node_id: str) -> dict[str, Any]:
    card = json.loads((template / "definition.json").read_text("utf-8"))
    return next(n for n in card["nodes"] if n["id"] == node_id)


def to(*names: str) -> dict[str, Any]:
    return {"main": [[{"node": name, "port": "in", "map": "one"} for name in names]]}


def ran(events: list[Any], node_id: str) -> int:
    return sum(1 for e in events if e.kind == "node_finished" and e.data.get("node_id") == node_id)


def script_node(node_id: str, path: str) -> dict[str, Any]:
    return {
        "id": node_id,
        "name": node_id,
        "type": "script",
        "typeVersion": 1,
        "parameters": {"script": path},
    }


def d3_loop(root: Path) -> Path:
    """d3's begin, loop and record with fixed stand-ins for its QMB steps: no child ever gains."""
    root.mkdir()
    nodes = [
        {
            "id": "start",
            "name": "start",
            "type": "trigger",
            "typeVersion": 1,
            "parameters": {"kinds": ["manual"]},
        },
        script_node(
            "blinded",
            write(
                root,
                "blinded.py",
                (
                    "import json\n"
                    "print(json.dumps({'parent': {'spec_hash': 'p', 'validated': 1.0},"
                    " 'report': {}, 'family': {'spec_hashes': [], 'trials': 0}}))\n"
                ),
            ),
        ),
        script_node(
            "diagnosis",
            write(root, "diagnosis.py", ("import json\nprint(json.dumps({'weaknesses': []}))\n")),
        ),
        script_node("begin", write(root, "begin.py", (D3 / "scripts" / "begin.py").read_text())),
        node_of(D3, "generations") | {"name": "loop"},
        script_node(
            "check",
            write(
                root,
                "check.py",
                (
                    "import json, sys\nstate = json.load(sys.stdin)['in']\n"
                    "print(json.dumps({'build': [], 'refused': [],"
                    " 'generation': state['generation'] + 1}))\n"
                ),
            ),
        ),
        script_node(
            "test", write(root, "test.py", "import json\nprint(json.dumps({'results': []}))\n")
        ),
        script_node("record", write(root, "record.py", (D3 / "scripts" / "record.py").read_text())),
        script_node("end", write(root, "end.py", "print('{}')\n")),
    ]
    connections = {
        "start": to("blinded", "diagnosis", "begin"),
        "blinded": to("begin"),
        "diagnosis": to("begin"),
        "begin": to("loop"),
        "loop": {"body": to("check", "record")["main"], "done": to("end")["main"]},
        "check": to("test", "record"),
        "test": to("record"),
        "record": {"main": [[{"node": "loop", "port": "next", "map": "one"}]]},
    }
    return flow_folder(root, D3, nodes, connections)


@pytest.mark.parametrize(
    ("inputs", "generations"),
    [
        ({"parent": "unit-v1", "generations": 5, "generations_without_gain": 9}, 5),
        ({"parent": "unit-v1", "generations_without_gain": 9}, 3),
        ({"parent": "unit-v1"}, 2),
    ],
    ids=["five-on-the-card", "the-card-default-of-3", "two-without-gain"],
)
def test_d3_runs_exactly_the_generations_its_card_says(
    tmp_path: Path, home: Path, inputs: dict[str, JsonValue], generations: int
) -> None:
    outcome, events = run_folder(d3_loop(tmp_path / "d3"), home, cast(JsonValue, inputs))

    assert outcome.status == "passed", outcome.reason
    assert ran(events, "record") == generations


def l4_loop(root: Path) -> Path:
    """l4's setup, loop and record with fixed stand-ins for its QMB steps: every revolution runs 10
    trials and every trial fails a gate."""
    root.mkdir()
    trials = [{"spec_hash": f"h{k}", "failed": ["trades"], "daily_sharpe": 0, "validated": 0}
              for k in range(10)]  # fmt: skip
    nodes = [
        {
            "id": "start",
            "name": "start",
            "type": "trigger",
            "typeVersion": 1,
            "parameters": {"kinds": ["manual"]},
        },
        script_node("setup", write(root, "setup.py", (L4 / "scripts" / "setup.py").read_text())),
        script_node(
            "family",
            write(
                root,
                "family.py",
                (
                    "import json, sys\nset_up = json.load(sys.stdin)['in']\n"
                    "print(json.dumps(set_up | {'tried': [], 'dead_regions': [], 'history': [],"
                    " 'trials_family': 0, 'trials_tonight': 0, 'best_validated': 0,"
                    " 'plateau': False, 'stop': False}))\n"
                ),
            ),
        ),
        node_of(L4, "night") | {"name": "loop"},
        script_node(
            "dedupe", write(root, "dedupe.py", "import json\nprint(json.dumps({'fresh': []}))\n")
        ),
        script_node(
            "trials",
            write(
                root, "trials.py", (f"import json\nprint(json.dumps({{'trials': {trials!r}}}))\n")
            ),
        ),
        script_node("record", write(root, "record.py", (L4 / "scripts" / "record.py").read_text())),
        script_node("end", write(root, "end.py", "print('{}')\n")),
    ]
    connections = {
        "start": to("setup"),
        "setup": to("family"),
        "family": to("loop"),
        "loop": {"body": to("dedupe", "record")["main"], "done": to("end")["main"]},
        "dedupe": to("trials", "record"),
        "trials": to("record"),
        "record": {"main": [[{"node": "loop", "port": "next", "map": "one"}]]},
    }
    return flow_folder(root, L4, nodes, connections)


SPACE: dict[str, Any] = {
    "signal_classes": ["breakout"],
    "filters": ["session"],
    "exits": ["atr"],
    "timeframes": ["M15"],
    "markets": ["fx.eurusd"],
    "fitness": "validated_sharpe",
}


@pytest.mark.parametrize(
    ("counts", "revolutions"),
    [
        ({"trials": 25, "revolutions": 9, "revolutions_without_gain": 9}, 3),
        ({"revolutions": 4, "revolutions_without_gain": 9}, 4),
        ({}, 2),
    ],
    ids=["25-trials-on-the-card", "four-revolutions", "two-without-gain"],
)
def test_l4_runs_exactly_the_revolutions_its_card_allows(
    tmp_path: Path, home: Path, counts: dict[str, JsonValue], revolutions: int
) -> None:
    inputs = {"family": "breakouts", "search_space": SPACE, **counts}
    outcome, events = run_folder(l4_loop(tmp_path / "l4"), home, cast(JsonValue, inputs))

    assert outcome.status == "passed", outcome.reason
    assert ran(events, "record") == revolutions


def planned(count: int) -> dict[str, Any]:
    return {
        "variants": [
            {"label": "instrument", "name": f"m{k}", "change": "another market", "overrides": {}}
            for k in range(count)
        ]
    }


def test_d4_keeps_the_variants_its_card_says_and_names_the_rest() -> None:
    strategy: dict[str, Any] = {
        "strategy": {"id": "unit-v1", "spec": {}},
        "request": "try it on two markets",
    }

    chosen = script(D4, "identity.py", [strategy | {"variants": 2}, planned(3)])
    default = script(D4, "identity.py", [strategy, planned(13)])

    assert [row["variant"] for row in chosen["config"]] == ["v1", "v2"]
    assert chosen["refused"] == [{"variant": "v3", "why": "over the 2 variants of a run"}]
    assert len(default["config"]) == 12
    assert default["refused"] == [{"variant": "v13", "why": "over the 12 variants of a run"}]


def judge_request() -> dict[str, Any]:
    """Research 24's trap, as qmx-judge's own test sets it: 20 markets of 100 trades with a true
    edge of +0.06R, judged on the shipped preset with every cheaper step's evidence passing."""
    draw = random.Random(24)  # noqa: S311 - a seeded fixture, not a secret
    found = {f"fx.m{i:02d}": [f"{draw.gauss(0.06, 1):.4f}" for _ in range(100)] for i in range(20)}
    run_id = f"qmbr-pc-{1:026d}"
    evidence = {
        "random_entries": {"edge_ratio": "1.4", "p": "0.01"},
        "cost_stress": {"multiplier": "1.5", "expectancy_r": "0.2"},
        "walk_forward": {"efficiency": "0.7"},
    }
    return {
        "spec": {
            "origin": "written",
            "claim": {"edge": "buys pullbacks in an uptrend", "horizon": "a day"},
            "markets": "admitted",
            "preset": "shipped",
        },
        "study": "study-v1",
        "results": [
            {
                "result_id": "result-1",
                "fields": {
                    "run_id": run_id,
                    "status": "finished",
                    "unit": "unit-v1",
                    "tester": {"app": "qmb", "version": "0.1.0"},
                    "measures": evidence,
                },
                "trades": [
                    {"market_id": market, "closed_at": START + day * DAY, "r": r}
                    for market, rs in sorted(found.items())
                    for day, r in enumerate(rs)
                ],
            }
        ],
        "tries": [
            {"kind": "run", "state": state, "run_id": run_id, "family": "unit-v1"}
            for state in ("opened", "landed")
        ],
        "principal": "agent:chat",
        "checker": "qml 0.1.0",
    }


def test_b_lands_a_dead_end_from_the_verdict_of_its_judge_child(tmp_path: Path, home: Path) -> None:
    root = tmp_path / "judged"
    root.mkdir()
    shutil.copytree(B / "judge", root / "judge")
    nodes = [
        {
            "id": "start",
            "name": "start",
            "type": "trigger",
            "typeVersion": 1,
            "parameters": {"kinds": ["manual"]},
        },
        node_of(B, "judge"),
        script_node("card", write(root, "card.py", (B / "scripts" / "card.py").read_text())),
    ]
    folder = flow_folder(root, B, nodes, {"start": to("Judge the results"),
                                          "Judge the results": to("card")})  # fmt: skip
    outcome, events = run_folder(folder, home, cast(JsonValue, judge_request()))
    card = next(
        cast(dict[str, Any], e.data["outputs"])["main"]
        for e in events
        if e.kind == "node_finished" and e.data.get("node_id") == "card"
    )

    assert outcome.status == "passed", outcome.reason
    assert card["card"] is None
    assert {k: v for k, v in card["dead_end"].items() if k != "says"} == {
        "tag": "negative_result",
        "verdict": "fail",
        "tries": 20,
        "effective_tries": 20,
    }
    assert card["dead_end"]["says"].endswith("Behind it: 20 tries, 20 effective.")


@pytest.mark.parametrize(
    ("overall", "dead_end"),
    [
        (
            "fail",
            {
                "tag": "negative_result",
                "verdict": "fail",
                "says": "Did not hold.",
                "tries": 7,
                "effective_tries": 5,
            },
        ),
        (
            "no_trades",
            {
                "tag": "negative_result",
                "verdict": "no_trades",
                "says": "Did not hold.",
                "tries": 7,
                "effective_tries": 5,
            },
        ),
        ("incomplete", None),
        ("too_thin", None),
    ],
)
def test_b_files_a_dead_end_only_for_an_outcome_the_judge_certifies_dead(
    overall: str, dead_end: dict[str, Any] | None
) -> None:
    verdict = {"overall": overall, "says": "Did not hold.", "raw_tries": 7, "effective_tries": 5}

    out = script(B, "card.py", {"Judge the results": {"main": {"verdict": verdict}}})

    assert out == {"card": None, "dead_end": dead_end}
