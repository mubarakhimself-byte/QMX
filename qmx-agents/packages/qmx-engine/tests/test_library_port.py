"""The `LibraryPort` contract, run on both adapters: the engine's SQLite fake and the real Library
store behind `EngineLibraryAdapter` (Library AD-15). Each test calls the port the way the engine
does and expects the same answers from both."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from flows import CHAIN
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.store import Store

from qmx_engine.ledger import redact
from qmx_engine.ports.library import MAIN, Bundle, LibraryPort, LibraryRefused, RunSummary
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR, Caller

ADAPTERS = ("fake", "store")


@pytest.fixture(params=ADAPTERS)
def library(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[LibraryPort]:
    if request.param == "fake":
        with LibraryFake.open(tmp_path) as fake:
            yield fake
    else:
        with Store.open(tmp_path / "library", redactor=redact) as store:
            yield EngineLibraryAdapter(store)


def summary(run_id: str, item: str, object_id: str, status: str = "passed") -> RunSummary:
    return RunSummary(
        run_id, item, object_id, "test", cast(Any, status), None, {}, {}, None, "operator"
    )


def test_an_edge_outside_the_closed_set_is_refused(library: LibraryPort) -> None:
    draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
    report = library.put_test_report(
        "sha256:x", {"workflow_item": draft.item, "run_id": "r1"}, principal="run:r1"
    )
    with pytest.raises(LibraryRefused, match=r"^edge_not_in_set:"):
        library.link(
            draft.object_id, cast(Any, "supersedes"), report.object_id, principal="operator"
        )
    library.link(draft.object_id, "tested-by", report.object_id, principal="run:r1")
    library.link(draft.object_id, "tested-by", report.object_id, principal="run:r1")

    assert [(e.edge, e.to_id) for e in library.edges(draft.object_id)] == [
        ("tested-by", report.object_id)
    ]
    assert [e.from_id for e in library.edges(report.object_id, reverse=True)] == [draft.object_id]


def test_drafts_stay_off_main_and_run_branches_belong_to_their_run(library: LibraryPort) -> None:
    chain = Bundle.read(CHAIN)
    with pytest.raises(LibraryRefused, match=r"^not_a_draft_ref:"):
        library.put_draft("script-chain", chain, 0, principal="operator", ref="main")
    draft = library.put_draft(None, chain, 0, principal="operator")
    with pytest.raises(LibraryRefused, match=r"^revision_conflict:"):
        library.put_draft(draft.item, chain, 0, principal="operator")
    with pytest.raises(LibraryRefused, match=r"^wrong_principal:"):
        library.put_artifact(b"x", "trace", {}, run_id="r1", principal="operator")
    trace = library.put_artifact(b"x", "trace", {}, run_id="r1", principal="run:r1")
    again = library.put_draft(draft.item, chain, 1, principal="operator")

    assert (draft.ref, draft.revision, again.revision) == ("refs/drafts/script-chain", 1, 2)
    assert (trace.ref, trace.kind, library.get_artifact(cast(str, trace.blob))) == (
        "refs/runs/r1",
        "artifact",
        b"x",
    )
    assert library.get_draft(draft.item, draft.ref).bundle == chain


def test_an_agent_saves_the_draft_through_its_own_ref(library: LibraryPort) -> None:
    chain = Bundle.read(CHAIN)
    first = library.put_draft(None, chain, 0, principal="agent:s1")
    second = library.put_draft(first.item, chain, 1, principal="agent:s2")

    assert (first.ref, first.revision, second.revision) == ("refs/drafts/script-chain", 1, 2)
    assert library.get_draft(first.item, first.ref).object_id == second.object_id


def test_publish_moves_the_tested_draft_to_main_once(library: LibraryPort) -> None:
    draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
    run = library.put_run_summary(summary("r1", draft.item, draft.object_id), principal="run:r1")
    library.link(draft.object_id, "tested-by", run.object_id, principal="run:r1")
    version = library.publish(draft.item, draft.ref, "1.0.0", principal="operator")
    again = library.publish(draft.item, draft.ref, "1.0.1", principal="operator")
    library.annotate(version, "state", "enabled", principal="operator")

    published = library.get(version)
    assert (again, published.ref, published.kind) == (version, MAIN, "workflow")
    assert (published.fields["content_hash"], published.fields["semver"]) == (
        draft.content_hash,
        "1.0.0",
    )
    assert [e.to_id for e in library.edges(version, "tested-by")] == [run.object_id]
    assert [v.object_id for v in library.objects(draft.item, "workflow", MAIN)] == [version]
    assert library.annotation(version, "state") == "enabled"
    assert library.get_object(version) == Bundle.read(CHAIN)


def test_runs_intent_keys_and_champions(library: LibraryPort) -> None:
    draft = library.put_draft(None, Bundle.read(CHAIN), 0, principal="operator")
    made = library.put_artifact(
        b"brief", "report", {"path": "out.md"}, run_id="r2", principal="run:r2", intent_key="k1"
    )
    live = replace(summary("r2", draft.item, draft.object_id), mode="live")
    run = library.put_run_summary(live, principal="run:r2")
    library.link(made.object_id, "produced-by", run.object_id, principal="run:r2")
    library.set_champion(draft.item, draft.object_id, principal="operator")

    assert library.find_by_intent("k1") == [made.object_id]
    assert [(r.run_id, r.status) for r in library.list_runs(draft.item)] == [("r2", "passed")]
    assert library.champion(draft.item) == draft.object_id
    assert [o.object_id for o in library.objects("r2", "workflow-run")] == [run.object_id]


def test_a_run_saves_a_workflow_onto_its_draft(library: LibraryPort) -> None:
    chain = Bundle.read(CHAIN)
    made = library.put_draft("made", chain, 0, principal="run:r3")
    with pytest.raises(LibraryRefused, match=r"^unknown_object:"):
        library.land_draft("made", "r9", principal="engine:pc")

    assert (made.ref, made.revision, made.bundle) == ("refs/drafts/made", 1, chain)


@pytest.mark.parametrize("adapter", ADAPTERS)
def test_the_engine_runs_a_workflow_end_to_end(tmp_path: Path, adapter: str) -> None:
    with (
        Store.open(tmp_path / "library", redactor=redact) as store,
        LibraryFake.open(tmp_path) as fake,
    ):
        real = EngineLibraryAdapter(store) if adapter == "store" else None
        with EngineService.open(tmp_path, library=real or fake) as svc:
            item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
            tested = asyncio.run(svc.tests.run(item, caller=OPERATOR))
            version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
            run = asyncio.run(svc.runs.start(version, caller=OPERATOR))
            agent = svc.drafts.put(item, Bundle.read(CHAIN), 1, caller=Caller("agent", "s1"))
            library = svc.ctx.library
            ran = library.objects(run.run_id, "workflow-run")[-1]
            produced = library.edges(ran.object_id, "produced-by", reverse=True)
            run_of = [e.to_id for e in library.edges(ran.object_id, "run-of")]
            made = library.get(produced[0].from_id).fields["type"] if produced else None
            landed = store.head(run.run_id, MAIN) if real else (ran.object_id, 1)

    assert (tested.status, run.status, run.object_id) == ("passed", "passed", version)
    assert (run_of, made) == ([version], "trace")
    assert (agent.ref, agent.revision) == (f"refs/drafts/{item}", 2)
    assert landed == (ran.object_id, 1)
