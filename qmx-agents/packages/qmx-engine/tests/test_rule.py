"""The `rule` node: a whitelisted expression, refused before evaluation when it reaches outside."""

from __future__ import annotations

from pathlib import Path

import pytest
from flows import Flow
from pydantic import JsonValue

from qmx_engine.definition.expr import RuleError, RuleRefused, evaluate
from qmx_engine.definition.model import Workflow
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok


@pytest.mark.parametrize(
    ("expr", "refusal"),
    [
        ("__import__('os').system('echo hi')", "Call is not allowed in a rule"),
        ("items.keys()", "Call is not allowed in a rule"),
        ("(lambda: 1)()", "Call is not allowed in a rule"),
        ("(lambda x: x)", "Lambda is not allowed in a rule"),
        ("items.__class__", "name '__class__' starts with an underscore"),
        ("[x for x in items]", "ListComp is not allowed in a rule"),
        ("2 ** 99999999", "Pow is not allowed in a rule"),
    ],
)
def test_calls_lambdas_dunders_comprehensions_and_powers_are_refused(
    expr: str, refusal: str
) -> None:
    with pytest.raises(RuleRefused, match=refusal):
        evaluate(expr, {"in": {"score": 1}})


def test_open_is_refused_before_anything_is_evaluated(tmp_path: Path) -> None:
    target = tmp_path / "written"
    expr = f"items.ok or open({str(target)!r}, 'w')"

    with pytest.raises(RuleRefused, match="Call is not allowed in a rule"):
        evaluate(expr, {"in": {"ok": False}})
    assert not target.exists()


def test_allowed_expressions_read_inputs_by_key_and_index() -> None:
    inputs: JsonValue = {"in": {"score": 0.8, "tags": ["q-fin", "ml"], "name": "paper"}}

    assert evaluate("items.score >= 0.7", inputs) is True
    assert evaluate("'ml' in items.tags and items['name'] != 'x'", inputs) is True
    assert evaluate("items.tags[0] == 'q-fin' and not items.score > 0.9", inputs) is True
    assert evaluate("0 < items.score * 2 - 2 < 1", inputs) is False
    with pytest.raises(RuleError, match="no 'missing' in the value"):
        evaluate("items.missing", inputs)
    with pytest.raises(RuleError, match="not true or false"):
        evaluate("items.score", inputs)


class Branch:
    def run(self, job: NodeJob) -> NodeResult:
        return Ok({"main": job.node_id})


def routed(tmp: Path, score: float) -> tuple[list[str], JsonValue]:
    workflow = Workflow.model_validate(
        {
            "schema": "qmx.workflow/1",
            "id": "routed",
            "name": "routed",
            "nodes": [
                {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1},
                {
                    "id": "gate",
                    "name": "Good enough?",
                    "type": "rule",
                    "typeVersion": 1,
                    "parameters": {"expr": "items.score >= 0.7"},
                },
                {"id": "yes", "name": "Keep", "type": "script", "typeVersion": 1},
                {"id": "yes-2", "name": "Keep more", "type": "script", "typeVersion": 1},
                {"id": "no", "name": "Drop", "type": "script", "typeVersion": 1},
            ],
            "connections": {
                "Start": {"main": [[{"node": "Good enough?", "port": "in", "map": "one"}]]},
                "Good enough?": {
                    "true": [[{"node": "Keep", "port": "in", "map": "one"}]],
                    "false": [[{"node": "Drop", "port": "in", "map": "one"}]],
                },
                "Keep": {"main": [[{"node": "Keep more", "port": "in", "map": "one"}]]},
            },
        }
    )
    flow = Flow(tmp, workflow, {"script": Branch()}, run_id=f"run-{score}")
    ended = flow.start({"score": score})
    started = [str(e.data["node_id"]) for e in flow.events if e.kind == "node_started"]
    return started, ended.outputs if ended.status == "passed" else None


def test_a_rule_runs_only_the_chosen_ports_branch(tmp_path: Path) -> None:
    assert routed(tmp_path, 0.9) == (
        ["start", "gate", "yes", "yes-2"],
        {"yes-2": {"main": "yes-2"}},
    )
    assert routed(tmp_path, 0.2) == (["start", "gate", "no"], {"no": {"main": "no"}})
