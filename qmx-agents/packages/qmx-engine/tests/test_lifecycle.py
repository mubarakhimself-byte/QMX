"""The AD-11 lifecycle through the engine service, on real script runs and the fake Library."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from flows import CHAIN, edited, events_of

from qmx_engine.ports.library import Bundle, JsonObject, drafts_ref
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller, Refused

DOUBLE_THEN_ADD_ONE = """
    import json, sys
    print(json.dumps({"total": sum(json.load(sys.stdin)["in"]) + 1}))
"""


def refused(code: str) -> pytest.RaisesExc[Refused]:
    return pytest.raises(Refused, match=rf"^{code}:")


def test_a_workflow_walks_every_allowed_state(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    with EngineService.open(tmp_path) as svc:
        broken = Bundle(chain.definition, {})
        draft = svc.drafts.put(None, broken, 0, caller=OPERATOR)
        item = draft.item
        states = [svc.drafts.state(item)]
        svc.drafts.put(item, chain, 1, caller=OPERATOR)
        states.append(svc.drafts.state(item))
        report = asyncio.run(svc.tests.run(item, caller=OPERATOR))
        states.append(svc.drafts.state(item))
        version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        states.append(svc.versions.get(version).state)
        for move in (svc.versions.enable, svc.versions.disable, svc.versions.enable):
            states.append(move(version, caller=OPERATOR).state)
        states.append(svc.versions.disable(version, caller=OPERATOR).state)
        states.append(svc.versions.archive(version, caller=OPERATOR).state)
        copied = svc.ctx.library.edges(version, "tested-by")

    assert (item, report.status, report.stale) == ("script-chain", "passed", False)
    assert states == [
        "draft",
        "validated",
        "tested",
        "published",
        "enabled",
        "disabled",
        "enabled",
        "disabled",
        "archived",
    ]
    assert len(copied) == 1


def test_each_disallowed_move_is_refused(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    with EngineService.open(tmp_path) as svc:
        draft = svc.drafts.put(None, chain, 0, caller=OPERATOR)
        with refused("run_refused"):
            asyncio.run(svc.runs.start(draft.object_id, caller=OPERATOR))
        with refused("publish_refused"):
            svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        with refused("not_a_version"):
            svc.versions.enable(draft.object_id, caller=OPERATOR)
        untested = svc.ctx.library.publish(
            draft.item, drafts_ref(draft.item), "0.1.0", principal="operator"
        )
        with refused("not_tested"):
            svc.versions.enable(untested, caller=OPERATOR)
        asyncio.run(svc.tests.run(draft.item, caller=OPERATOR))
        svc.versions.enable(untested, caller=OPERATOR)
        with refused("archive_refused"):
            svc.versions.archive(untested, caller=OPERATOR)
        svc.versions.disable(untested, caller=OPERATOR)
        svc.versions.archive(untested, caller=OPERATOR)
        with refused("enable_refused"):
            svc.versions.enable(untested, caller=OPERATOR)
        with refused("run_refused"):
            asyncio.run(svc.runs.start(untested, caller=OPERATOR))
        bad = svc.drafts.put(None, Bundle(chain.definition, {}), 0, caller=OPERATOR)
        with refused("invalid"):
            asyncio.run(svc.tests.run(bad.item, caller=OPERATOR))


def test_an_edit_makes_the_report_stale_and_publish_waits_for_a_new_test(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    with EngineService.open(tmp_path) as svc:
        item = svc.drafts.put(None, chain, 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        svc.drafts.put(
            item, edited(chain, "scripts/total.py", DOUBLE_THEN_ADD_ONE), 1, caller=OPERATOR
        )
        stale = svc.tests.report(item)
        with refused("publish_refused"):
            svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        fresh = asyncio.run(svc.tests.run(item, caller=OPERATOR))
        first = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        again = svc.versions.publish(item, "1.0.1", caller=OPERATOR)
        versions = svc.versions.list(item)

    assert stale is not None and (stale.status, stale.stale) == ("passed", True)
    assert (fresh.status, fresh.stale) == ("passed", False)
    assert again == first
    assert [(v.semver, v.tested) for v in versions] == [("1.0.0", True)]


def test_a_selected_subgraph_runs_only_those_nodes_and_marks_nothing_tested(
    tmp_path: Path,
) -> None:
    with EngineService.open(tmp_path) as svc:
        item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
        report = asyncio.run(
            svc.tests.run(item, caller=OPERATOR, inputs=[1, 2, 3], subgraph=["double", "total"])
        )
        state = svc.drafts.state(item)
    started = {
        str(e.data["node_id"])
        for e in events_of(tmp_path, report.run_id)
        if e.kind == "node_started"
    }

    assert (report.status, report.subgraph, state) == ("passed", ["double", "total"], "validated")
    assert started == {"subgraph-input", "double", "total"}


def test_a_variant_resolves_before_its_test_and_publishes_variant_of(tmp_path: Path) -> None:
    chain = Bundle.read(CHAIN)
    with EngineService.open(tmp_path) as svc:
        item = svc.drafts.put(None, chain, 0, caller=OPERATOR).item
        asyncio.run(svc.tests.run(item, caller=OPERATOR))
        parent = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
        variant: JsonObject = {
            "schema": "qmx.workflow/1",
            "id": "chain-renamed",
            "name": "Renamed chain",
            "extends": {
                "workflow_item": item,
                "object_id": parent,
                "patches": [{"op": "add", "path": "/nodes/1/notes", "value": "four numbers"}],
            },
            "nodes": [],
        }
        agent = Caller("agent", "s1")
        draft = svc.drafts.put(None, Bundle(variant, {}), 0, caller=agent)
        unresolved = svc.ctx.library.get(draft.object_id)
        report = asyncio.run(svc.tests.run(draft.item, caller=agent))
        head = svc.drafts.get(draft.item)
        version = svc.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        lineage = [(e.edge, e.to_id) for e in svc.ctx.library.edges(version, "variant-of")]

    assert (unresolved.principal, unresolved.fields["content_hash"]) == ("agent:s1", None)
    assert report.status == "passed"
    assert head.bundle.definition["extends"] is None
    assert lineage == [("variant-of", parent)]
