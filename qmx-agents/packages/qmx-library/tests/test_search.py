"""Parse-first search and the curator, through `answer` and `curate` on a real store: grounding
on aliases, the refusals that are plain facts, abstention on thin evidence, trusted results
before test output, the admitting edge per result, and archiving uncited test records."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.curator import curate
from qmx_library.port import Draft, JsonObject, Relation
from qmx_library.principal import Principal
from qmx_library.search import answer
from qmx_library.store import Store

OPERATOR = Principal("operator")
START = datetime(2026, 9, 1, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(tmp_path: Path, clock: Clock) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=clock) as opened:
        yield opened


def note(
    store: Store, title: str, *, tags: Sequence[str] = (), relations: Sequence[Relation] = ()
) -> tuple[str, str]:
    """`(item, object_id)` of an operator note on `main`."""
    body = {"body.md": title.encode()}
    draft = Draft("note", title=title, blobs=body, tags=tags, relations=relations)
    done = store.put(OPERATOR, draft, on="main", expected_head=None)
    return done.item, done.object_id


def run_records(store: Store, run_id: str, *titles: str, mode: str = "test") -> list[str]:
    """A run's summary and one artifact per title on its own ref; the artifacts' items."""
    run = Principal("run", run_id)
    ref = f"refs/runs/{run_id}"
    fields: JsonObject = {"run_id": run_id, "mode": mode, "status": "passed"}
    store.put(run, Draft("workflow-run", run_id, fields=fields), on=ref, expected_head=None)
    return [
        store.put(
            run,
            Draft("artifact", title=title, blobs={"content": title.encode()}),
            on=ref,
            expected_head=None,
        ).item
        for title in titles
    ]


def test_longest_alias_grounds_the_item(store: Store) -> None:
    momentum, _ = note(store, "Momentum")
    pod, _ = note(store, "Momentum pod", tags=["mp-7"])

    found = answer(store, OPERATOR, "the momentum pod")
    tagged = answer(store, OPERATOR, "what about mp-7")

    assert [(m.item, m.surface, m.role) for m in found.matches] == [(pod, "momentum pod", "bridge")]
    assert [r.item for r in found.results] == [pod]
    assert found.confidence == 1.0
    assert [r.item for r in tagged.results] == [pod]
    assert momentum not in {r.item for r in found.results}


def test_a_pods_name_returns_the_pod_first_and_the_edge_that_admitted_each_other_result(
    store: Store,
) -> None:
    done = store.put(
        OPERATOR, Draft("pod", "pod-x", title="Pod X"), on="refs/drafts/pod-x", expected_head=None
    )
    study, _ = note(store, "London open study", relations=[("uses", done.object_id)])
    idea, _ = note(store, "Idea", relations=[("derived-from", done.object_id)])

    found = answer(store, OPERATOR, "what did we decide about pod x")

    assert [(r.item, r.via, r.source) for r in found.results] == [
        ("pod-x", None, None),
        (idea, "derived-from", "pod-x"),
        (study, "uses", "pod-x"),
    ]
    assert found.results[0].citations == 2
    assert found.refused is None
    assert not found.abstain


def test_only_plain_facts_refuse(store: Store, clock: Clock) -> None:
    before = clock.now
    clock.now = START + timedelta(days=1)
    old, _ = note(store, "Old breakout plan")
    store.archive(OPERATOR, old, "replaced")

    assert answer(store, OPERATOR, "kangaroo futures").refused == "no_entry_point"
    assert answer(store, OPERATOR, "old breakout plan").refused == "only_archived_or_superseded"
    assert answer(store, OPERATOR, "old breakout plan", as_of=before).refused == (
        "no_evidence_as_of"
    )
    shown = answer(store, OPERATOR, "old breakout plan", include_archived=True)
    assert [r.item for r in shown.results] == [old]


def test_thin_evidence_abstains_instead_of_refusing(store: Store) -> None:
    note(store, "Gold")

    found = answer(store, OPERATOR, "the gold scalping strategy book for asia")

    assert found.refused is None
    assert found.confidence == 0.2
    assert found.abstain
    assert "no_path" in found.signals


def test_a_kind_name_alone_is_a_filter_worth_half_a_word(store: Store) -> None:
    item, _ = note(store, "Weekly review")

    found = answer(store, OPERATOR, "which notes do I have")

    assert [(m.item, m.role) for m in found.matches] == [(item, "filter")]
    assert found.confidence == 0.5
    assert found.signals == ("too_few_concepts", "no_path")


def test_trusted_items_rank_before_newer_test_run_copies(store: Store, clock: Clock) -> None:
    mine, _ = note(store, "remote-flow")
    clock.now = START + timedelta(days=1)
    noise = run_records(store, "t1", "remote-flow", "remote-flow")
    live = run_records(store, "l1", "remote-flow", mode="live")

    found = answer(store, OPERATOR, "the remote-flow result")

    assert [r.item for r in found.results] == [*live, mine, *reversed(noise)]
    assert [r.producer for r in found.results] == ["live-run", "operator", "test-run", "test-run"]
    assert [h.item for h in store.search(OPERATOR, "remote flow")][:2] == [*live, mine]


def test_the_curator_archives_old_uncited_test_records_and_deletes_nothing(
    store: Store, clock: Clock
) -> None:
    old = run_records(store, "t-old", "probe output")
    cited = run_records(store, "t-cited", "kept output")
    note(
        store,
        "Report",
        relations=[("cites", store.resolve(OPERATOR, cited[0], "refs/runs/t-cited"))],
    )
    clock.now = START + timedelta(days=20)
    young = run_records(store, "t-young", "fresh output")
    live = run_records(store, "l-old", "live output", mode="live")
    objects = sorted(p.name for p in (store.root / "objects").rglob("*.json"))
    clock.now = START + timedelta(days=31)

    archived = curate(store, now=clock.now)

    assert archived == sorted([*old, "t-old", "t-cited"])
    assert curate(store, now=clock.now) == []
    for item in [*cited, *young, *live, "t-young", "l-old"]:
        assert store.catalog.state(item) == "active"
    assert sorted(p.name for p in (store.root / "objects").rglob("*.json")) == objects
    assert answer(store, OPERATOR, "probe output").refused == "only_archived_or_superseded"
