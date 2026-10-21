"""BUG2: the spec-gap code and the validation holes. One test per row of 40-retriage's BUG-2 packet,
each named after its row: event keys and derived span status (B-18, L-29, L-34), readiness with
`required` edges and loop context (B-24, B-87), validation refusals (B-20, B-22, B-27, B-46,
B-90), what the content hash covers (L-26, L-75, B-76), the draft and test lifecycle (B-43, B-61,
B-92, L-54, L-55, L-56, L-89), the fake switch (B-77, B-85), joins and loops (B-23), `explain`
text (B-71) and the `WorkerPort.run(job, emit)` shape (AD-20). B-19 sits in `test_memo.py` and
L-20, L-22 in `test_import_rules.py`."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from flows import CHAIN, edge, events_of, folder, node, run_folder, workflow
from pydantic import JsonValue
from qmx_ledger.journal import fingerprint
from test_run_state import tick_until_ended, wakes

from qmx_engine.core.loops import LoopSpec, stop
from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.validate import validate
from qmx_engine.ledger.events import JsonObject
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.base import NodeJob, Ok
from qmx_engine.nodes.fake_provider import own_items
from qmx_engine.ports.library import Bundle, drafts_ref
from qmx_engine.runner import Engine
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Refused
from qmx_engine.service.explain import explain, text
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.local import LocalWorker

START = node("start", "trigger")
AT = "2026-10-19T09:00:00+00:00"
ECHO = "import json, sys\nprint(json.dumps(json.load(sys.stdin)['in']))\n"
FAIL_ON_TWO = """
    import json, sys, time
    value = json.load(sys.stdin)["in"]
    if value == 2:
        time.sleep(1.5)
        sys.exit(1)
    print(json.dumps(value))
"""


def codes(root: Path) -> list[tuple[str, str]]:
    return [(p.code, p.path) for p in validate(load(root))]


def started(events: list[Any]) -> list[str]:
    return [e.data["node_id"] for e in events if e.kind == "node_started"]


def test_b18_every_node_event_carries_its_attempt_key_and_spans_derive_gate_and_cancel(
    tmp_path: Path,
) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )
    _, events = run_folder(root, tmp_path / "home", 3)
    keys = {"node_id", "iteration", "partition", "attempt"}
    node_events = [e for e in events if "node_id" in e.data]

    assert node_events and all(keys <= e.data.keys() for e in node_events)
    one: JsonObject = {"node_id": "n", "iteration": 0, "partition": None}
    with Ledger.open(tmp_path / "spans") as ledger:
        ledger.append("run", "run_created", {"mode": "test"}, at=AT)
        for attempt, name in ((1, "gated"), (2, "open")):
            ledger.append("run", "node_started", one | {"attempt": attempt, "model": name}, at=AT)
        ledger.append("run", "gate_opened", one | {"attempt": 1}, at=AT)
        ledger.append("run", "node_waiting", one | {"attempt": 1, "reason": "gate"}, at=AT)
        ledger.append("run", "run_cancelled", {"reason": "operator"}, at=AT)
    with Reader.open(tmp_path / "spans") as reader:
        status = {s.model: s.status for s in reader.spans("run")}
    assert status == {"gated": "gate", "open": "cancelled"}


def test_l29_an_ending_without_its_keys_is_refused_not_stored(tmp_path: Path) -> None:
    with Ledger.open(tmp_path) as ledger, pytest.raises(ValueError, match=r"^node_finished needs"):
        ledger.append("run", "node_finished", {"node_id": "n", "attempt": 1}, at=AT)


def test_l34_node_scheduled_carries_the_input_hash(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )
    _, events = run_folder(root, tmp_path / "home", 3)
    scheduled = next(
        e.data for e in events if e.kind == "node_scheduled" and e.data["node_id"] == "echo"
    )

    assert scheduled["input_hash"] == fingerprint({"in": 3})


def test_b20_nesting_is_refused_at_validation_and_names_the_node(tmp_path: Path) -> None:
    fan = node("fan", "script", script="scripts/echo.py")
    nested = folder(
        tmp_path / "nested",
        [START, fan, node("again", "script", script="scripts/echo.py")],
        {
            "start": {"main": [edge("fan", "broadcast")]},
            "fan": {"main": [edge("again", "chunk", chunk={"by": "items", "size": 1})]},
        },
        {"echo": ECHO},
    )
    loop_body = folder(
        tmp_path / "loops",
        [
            START,
            node("outer", "loop", max_iterations=2),
            node("inner", "loop", max_iterations=2),
            node("work", "script", script="scripts/echo.py"),
        ],
        {
            "start": {"main": [edge("outer")]},
            "outer": {"body": [edge("inner")]},
            "inner": {"body": [edge("work")], "done": [edge("outer", port="next")]},
            "work": {"main": [edge("inner", port="next")]},
        },
        {"echo": ECHO},
    )
    revolution = folder(
        tmp_path / "revolution",
        [
            START,
            node("outer", "loop", max_iterations=2),
            node("call", "subworkflow", workflow="child"),
        ],
        {
            "start": {"main": [edge("outer")]},
            "outer": {"body": [edge("call")]},
            "call": {"main": [edge("outer", port="next")]},
        },
        {},
    )
    shutil.copytree(loop_body, revolution / "child", ignore=shutil.ignore_patterns("child"))

    found = validate(load(nested))
    assert [(p.code, p.path) for p in found] == [("nesting_unsupported", "nodes[2]")]
    assert "node again fans out what fan already fanned out" in found[0].message
    assert codes(loop_body) == [("nesting_unsupported", "nodes[2]")]
    assert codes(revolution) == []


def test_b22_loop_join_and_wait_parameters_and_the_join_edge_are_validated(
    tmp_path: Path,
) -> None:
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("pause", "wait", seconds=1, until="2026-10-20T00:00:00Z"),
            node("all", "join", mode="quorum"),
            node("cycle", "loop", max_iterations=2, metric="score"),
        ],
        {
            "start": {"main": [edge("pause"), edge("all", "broadcast"), edge("cycle")]},
            "cycle": {"body": [edge("cycle", port="next")]},
        },
        {},
    )

    assert sorted({code for code, _ in codes(root)}) == [
        "join_inbound_invalid",
        "parameters_invalid",
    ]
    assert [path for code, path in codes(root) if code == "parameters_invalid"] == [
        "nodes[1].parameters",
        "nodes[2].parameters",
        "nodes[3].parameters",
    ]


def test_b90_validate_checks_every_expression_and_its_names(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("ok", "rule", expr="items.ok == true")],
        {"start": {"main": [edge("ok")]}},
        {},
    )

    [problem] = validate(load(root))
    assert (problem.code, problem.path) == ("expression_invalid", "nodes[1].parameters.expr")
    assert "reads 'true'" in problem.message


def test_b46_a_grader_in_llm_mode_is_refused_at_validation(tmp_path: Path) -> None:
    grader = node("judge", "grader", mode="llm") | {"role": "judge"}
    root = folder(tmp_path / "wf", [START, grader], {"start": {"main": [edge("judge")]}}, {})

    assert codes(root) == [("mode_unavailable", "nodes[1].parameters.mode")]


def merge_started(tmp_path: Path, *, required: bool) -> list[str]:
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("never", "rule", expr="False"),
            node("merge", "script", script="scripts/echo.py"),
        ],
        {
            "start": {"main": [edge("never"), edge("merge")]},
            "never": {"true": [edge("merge", required=required)]},
        },
        {"echo": ECHO},
    )
    _, events = run_folder(root, tmp_path / "home", 1)
    return started(events)


def test_b87_a_required_edge_that_carried_nothing_skips_its_target(tmp_path: Path) -> None:
    assert merge_started(tmp_path / "plain", required=False) == ["start", "never", "merge"]
    assert merge_started(tmp_path / "required", required=True) == ["start", "never"]


def test_b24_a_body_node_does_not_run_on_an_outside_value_alone(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("cycle", "loop", max_iterations=1),
            node("never", "rule", expr="False"),
            node("inside", "script", script="scripts/echo.py"),
        ],
        {
            "start": {"main": [edge("cycle"), edge("inside")]},
            "cycle": {"body": [edge("never")]},
            "never": {"true": [edge("inside")], "false": [edge("cycle", port="next")]},
        },
        {"echo": ECHO},
    )
    outcome, events = run_folder(root, tmp_path / "home", 1)

    assert outcome.status == "passed"
    assert "inside" not in started(events)


def test_b27_caller_policy_is_checked_at_validation(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("call", "subworkflow", workflow="child")],
        {"start": {"main": [edge("call")]}},
        {},
    )
    folder(root / "child", [START], {}, {}, caller_policy="none")

    [problem] = validate(load(root))
    assert (problem.code, problem.path) == ("caller_refused", "nodes[1].parameters.workflow")


def test_b27_a_waiting_child_makes_the_parent_wait_and_its_end_resumes_the_parent(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    root = folder(
        tmp_path / "wf",
        [START, node("call", "subworkflow", workflow="child")],
        {"start": {"main": [edge("call")]}},
        {},
    )
    folder(
        root / "child",
        [START, node("pause", "wait", seconds=1)],
        {"start": {"main": [edge("pause")]}},
        {},
    )
    parsed = workflow(
        [START, node("call", "subworkflow", workflow="child")], {"start": {"main": [edge("call")]}}
    )

    async def go() -> tuple[str, JsonValue, list[Any]]:
        with EngineService.open(home) as svc:
            outcome = await svc.ctx.engine.start(root, parsed, mode="test", inputs=None)
            waiting = next(
                e.data["reason"]
                for e in events_of(home, outcome.run_id)
                if e.kind == "node_waiting"
            )
            return outcome.status, waiting, await tick_until_ended(svc, outcome.run_id)

    status, reason, events = asyncio.run(go())

    assert (status, reason) == ("waiting", "child")
    assert events[-1].kind == "run_finished"
    assert wakes(home) == []


def test_b76_a_bundle_carries_and_hashes_the_child_block_folder(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("call", "subworkflow", workflow="blocks/child")],
        {"start": {"main": [edge("call")]}},
        {},
    )
    folder(
        root / "blocks" / "child",
        [START, node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )
    bundle = Bundle.read(root)
    before = bundle.content_hash()
    changed = Bundle(
        bundle.definition, {**bundle.files, "blocks/child/scripts/echo.py": b"print(1)\n"}
    )

    assert sorted(bundle.files) == ["blocks/child/definition.json", "blocks/child/scripts/echo.py"]
    assert validate(bundle.folder()) == []
    assert changed.content_hash() != before


def test_l26_l75_pin_data_and_meta_needs_are_in_the_content_hash(tmp_path: Path) -> None:
    root = shutil.copytree(CHAIN, tmp_path / "chain")
    document = json.loads((root / "definition.json").read_text(encoding="utf-8"))
    hashes = [content_hash(load(root))]
    for change in ({"pinData": {"Numbers": {"main": [[9]]}}}, {"meta": {"needs": ["rlm"]}}):
        document |= change
        (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
        hashes.append(content_hash(load(root)))

    assert len(set(hashes)) == 3


def needs_draft(svc: EngineService) -> str:
    chain = Bundle.read(CHAIN)
    definition: JsonObject = {**chain.definition, "meta": {"needs": ["rlm"]}}
    return svc.drafts.put(None, Bundle(definition, chain.files), 0, caller=OPERATOR).item


def test_b92_the_draft_view_names_the_need_and_the_draft_stays_validated(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        item = needs_draft(svc)
        problems = svc.drafts.problems(svc.drafts.get(item).bundle)
        state = svc.drafts.state(item)

    assert [(p.code, p.message) for p in problems] == [("needs_unmet", "needs: rlm")]
    assert state == "validated"


def test_l89_a_live_start_of_a_needs_version_names_the_need(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        item = needs_draft(svc)
        version = svc.ctx.library.publish(item, drafts_ref(item), "0.1.0", principal="operator")
        with pytest.raises(Refused) as refused:
            asyncio.run(svc.runs.start(version, caller=OPERATOR))

    assert refused.value.code == "not_runnable"
    assert str(refused.value).endswith("; needs: rlm")


def test_l56_a_passed_live_run_marks_its_version_tested(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        version = svc.ctx.library.publish(item, drafts_ref(item), "0.1.0", principal="operator")
        before = svc.versions.get(version).tested
        view = asyncio.run(svc.runs.start(version, caller=OPERATOR))
        after = svc.versions.get(version).tested

    assert (before, view.status, after) == (False, "passed", True)


def variant_of_chain(svc: EngineService, *, script: str | None = None) -> tuple[str, str]:
    chain = Bundle.read(CHAIN)
    item = svc.drafts.put(None, chain, 0, caller=OPERATOR).item
    asyncio.run(svc.tests.run(item, caller=OPERATOR))
    parent = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
    variant: JsonObject = {
        "schema": "qmx.workflow/1",
        "id": "chain-variant",
        "name": "Chain variant",
        "extends": {
            "workflow_item": item,
            "object_id": parent,
            "patches": [{"op": "add", "path": "/nodes/1/notes", "value": "four numbers"}],
        },
        "nodes": [],
    }
    files = {} if script is None else {"scripts/total.py": script.encode()}
    return svc.drafts.put(None, Bundle(variant, files), 0, caller=OPERATOR).item, parent


def test_l55_a_variant_test_that_does_not_pass_leaves_the_overlay_draft(tmp_path: Path) -> None:
    with EngineService.open(tmp_path) as svc:
        item, _ = variant_of_chain(svc, script="import sys\nsys.exit(3)\n")
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR))
        head = svc.drafts.get(item)

    assert report.status == "waiting"
    assert (head.revision, head.bundle.definition["extends"] is not None) == (1, True)


def test_l54_b43_an_overlay_draft_that_reads_tested_publishes_and_keeps_its_parent(
    tmp_path: Path,
) -> None:
    with EngineService.open(tmp_path) as svc:
        item, parent = variant_of_chain(svc)
        overlay = svc.drafts.get(item).bundle
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        resolved = svc.drafts.get(item)
        moved = Bundle(
            resolved.bundle.definition | {"name": "Chain variant, renamed"}, resolved.bundle.files
        )
        svc.drafts.put(item, moved, resolved.revision, caller=OPERATOR)
        kept = svc.ctx.library.get(svc.drafts.get(item).object_id).fields.get("variant_of")
        head = svc.drafts.get(item)
        svc.drafts.put(item, overlay, head.revision, caller=OPERATOR)
        state = svc.drafts.state(item)
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        lineage = [e.to_id for e in svc.ctx.library.edges(version, "variant-of")]
        parent_item = svc.ctx.library.get(parent).item

    assert kept == {"workflow_item": parent_item, "object_id": parent}
    assert (state, lineage) == ("tested", [parent])


def test_b61_a_test_run_resumed_by_a_wake_gets_a_fresh_report(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    document = json.loads(json.dumps(chain.definition))
    document["nodes"].append(node("pause", "wait", seconds=1) | {"name": "Pause"})
    document["connections"]["Total"] = {"main": [[edge("Pause")]]}

    async def go() -> tuple[str, str, str]:
        with EngineService.open(tmp_path) as svc:
            item = svc.drafts.put(None, Bundle(document, chain.files), 0, caller=OPERATOR).item
            first = await svc.tests.run(item, caller=OPERATOR)
            await tick_until_ended(svc, first.run_id)
            latest = svc.tests.report(item)
            assert latest is not None
            return first.status, latest.status, svc.drafts.state(item)

    assert asyncio.run(go()) == ("waiting", "passed", "tested")


def test_b71_explain_text_lists_each_span(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [START, node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )
    outcome, events = run_folder(root, tmp_path / "home", 3)
    with Reader.open(tmp_path / "home") as reader:
        lines = text(explain(events, reader.spans(outcome.run_id)))

    assert [line for line in lines if line.startswith("  span")] == [
        "  span 1 ok model None tokens {}",
        "  span 1 ok model None tokens {}",
    ]


def test_b77_a_fake_run_answers_an_agent_node_from_its_output_schema(tmp_path: Path) -> None:
    root = folder(tmp_path / "wf", [START], {}, {})
    (root / "schemas").mkdir()
    schema = {
        "type": "object",
        "required": ["changed_files"],
        "properties": {"changed_files": {"type": "array"}},
    }
    (root / "schemas" / "out.json").write_text(json.dumps(schema), encoding="utf-8")
    agent = node("build", "agent", output_schema_ref="schemas/out.json") | {"role": "triage"}
    parsed = workflow([START, agent], {"start": {"main": [edge("build")]}})

    async def go() -> Any:
        with Ledger.open(tmp_path / "home") as ledger:
            engine = Engine(tmp_path / "home", ledger, settings=DEFAULTS)
            return await engine.start(root, parsed, mode="test", inputs=None, fake=True)

    outcome = asyncio.run(go())

    assert (outcome.status, outcome.outputs) == (
        "passed",
        {"build": {"main": {"changed_files": []}}},
    )


def test_b85_a_chunk_gets_the_recorded_answer_cut_to_its_own_items() -> None:
    answer: JsonValue = {
        "claims": [{"source_id": "n01", "text": "a"}, {"source_id": "n02", "text": "b"}],
        "note": "kept",
    }
    chunk: JsonValue = {"in": [{"id": "n02", "title": "second"}]}

    assert own_items(answer, chunk) == {
        "claims": [{"source_id": "n02", "text": "b"}],
        "note": "kept",
    }


def test_b23_a_join_timeout_says_join_and_a_metric_may_fall(tmp_path: Path) -> None:
    falling = LoopSpec(max_iterations=9, no_progress_rounds=2, metric="loss", direction="down")
    rising = LoopSpec(max_iterations=9, no_progress_rounds=2, metric="loss")
    values: list[JsonValue] = [{"loss": 3}, {"loss": 2}, {"loss": 1}]
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("each", "script", script="scripts/slow.py"),
            node("all", "join", watermark="timeout", timeout_seconds=1),
        ],
        {"start": {"main": [edge("each", "broadcast")]}, "each": {"main": [edge("all")]}},
        {"slow": FAIL_ON_TWO},
    )
    outcome, events = run_folder(root, tmp_path / "home", [1, 2])
    reasons = [
        e.data["reason"] for e in events if e.kind == "node_waiting" and e.data["node_id"] == "all"
    ]

    assert (stop(falling, 3, values, 0), stop(rising, 3, values, 0)) == (None, "no_progress_rounds")
    assert reasons == ["join_timeout"]
    del outcome


def test_b23_a_partition_failing_after_its_join_fired_leaves_a_line(tmp_path: Path) -> None:
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("each", "script", script="scripts/slow.py"),
            node("first", "join", mode="any"),
        ],
        {"start": {"main": [edge("each", "broadcast")]}, "each": {"main": [edge("first")]}},
        {"slow": FAIL_ON_TWO},
    )
    outcome, events = run_folder(root, tmp_path / "home", [1, 2])
    lines = [e.data["line"] for e in events if e.kind == "log" and e.data.get("level") == "warn"]

    assert outcome.status == "passed"
    assert lines == ["each partition 1 failed after join first fired; it is late and not merged"]


def test_worker_port_runs_a_job_on_the_executor_the_runner_served() -> None:
    class Answer:
        def run(self, job: NodeJob) -> Ok:
            return Ok({"main": job.node_id})

    worker = LocalWorker()
    worker.serve("run", {"rule": Answer()})
    job = NodeJob(
        run_id="run",
        node_id="r",
        iteration=0,
        partition=None,
        attempt=1,
        memo_key="m",
        idempotency_key="run:r:0:1",
        node_definition={"type": "rule"},
        inputs={},
        now=AT,
    )
    emitted: list[str] = []

    result = asyncio.run(worker.run(job, lambda kind, _: emitted.append(kind)))
    worker.release("run")
    missing = asyncio.run(worker.run(job, lambda kind, _: emitted.append(kind)))

    assert (result, emitted) == (Ok({"main": "r"}), ["node_started"])
    assert getattr(missing, "code", None) == "executor_missing"
