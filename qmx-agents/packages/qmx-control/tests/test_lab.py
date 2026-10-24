"""The Lab's backend: a project is a collection, "New..." installs a template at one of four levels,
the workspace is an annotation, and a training run on the PC is a placement (Lab AD-19, AD-20).

The tests drive the operations the way the Lab's door does: a Library in a scratch home, the
engine's install behind a stand-in that publishes a template the way the real install does, and
the market-data door behind a stand-in that answers a card, a sample and its partitions.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmx_library.port import Draft
from qmx_library.principal import MAIN

from qmx_control.lab import Answered, Lab, Placement
from qmx_control.library import OPERATOR, Library
from qmx_control.models import ControlError

LEVELS = {
    "quick-idea": "rough-idea-to-test-plan",
    "experiment": "ml-training-run-with-a-holdout",
    "study": "variant-generation-and-comparison",
    "campaign": "overnight-lab-loop",
}
SERIES = "dukascopy/EURUSD/ticks/-"
SEALED = "this month is sealed for the final look"
MB = 1024 * 1024


class Installs:
    """The engine's template install: publishes the template onto `main` and answers its id."""

    def __init__(self, library: Library) -> None:
        self.library = library
        self.asked: list[str] = []

    def install(self, template_id: str) -> Answered[str]:
        self.asked.append(template_id)
        store = self.library.store
        ref = f"refs/drafts/{template_id}"
        draft = Draft(
            "workflow",
            template_id,
            title=template_id,
            fields={"content_hash": f"sha256:{template_id}"},
            blobs={"definition": b"{}"},
        )
        known = store.head(template_id, ref)
        store.put(OPERATOR, draft, on=ref, expected_head=None if known is None else known[0])
        store.merge(OPERATOR, template_id, from_ref=ref, into=MAIN, strategy="ff-only")
        head = store.head(template_id, MAIN)
        assert head is not None
        return Answered(head[0])


class Door:
    """The market-data door's answers, and what the Lab asked it for."""

    def __init__(self) -> None:
        self.materialised: list[tuple[str, ...]] = []
        self.sealed = False

    def card(self, series: str) -> Answered[dict[str, object]]:
        return Answered(
            {
                "series": series,
                "partitions": [
                    {"month": "2026-01", "fingerprint": "a" * 64, "bytes": 2 * MB},
                    {"month": "2026-02", "fingerprint": "b" * 64, "bytes": 3 * MB},
                    {"month": "2026-03", "fingerprint": "c" * 64, "bytes": 4 * MB},
                ],
            }
        )

    def read(
        self, series: str, *, start_ns: int, end_ns: int, purpose: str = "exploration"
    ) -> Answered[dict[str, object]]:
        if self.sealed:
            return Answered(refusal=f"{SEALED}: 2026-01")
        return Answered({"rows": [{"t": 1, "bid": 1_084_500, "ask": 1_084_520}]})

    def materialise(
        self, fingerprints: Sequence[str], *, into: Path | None = None
    ) -> Answered[Sequence[Path]]:
        self.materialised.append(tuple(fingerprints))
        return Answered(tuple(Path("/cache") / f"{found[:6]}.parquet" for found in fingerprints))


@pytest.fixture(name="library")
def opened_library(tmp_path: Path) -> Library:
    return Library(tmp_path)


@pytest.fixture(name="installs")
def opened_installs(library: Library) -> Installs:
    return Installs(library)


@pytest.fixture(name="door")
def opened_door() -> Door:
    return Door()


@pytest.fixture(name="lab")
def opened_lab(library: Library, installs: Installs, door: Door) -> Lab:
    return Lab(
        library,
        installs=installs,
        door=door,
        placement=Placement(gpu_slots=1, device="Quadro T1000", cache=Path("/cache")),
    )


def doc(found: JsonValue) -> dict[str, Any]:
    """A door answer as a mapping, for the assertions that read inside it."""
    return cast(dict[str, Any], found)


def dataset_card(library: Library) -> str:
    """A `dataset` card as the door's writer lands it."""
    stored = library.store.put(
        OPERATOR,
        Draft(
            "dataset",
            None,
            title="EURUSD ticks",
            fields={"series_key": SERIES, "quality": {"grade": "A"}},
        ),
        on=MAIN,
        expected_head=None,
    )
    return stored.object_id


def item(library: Library, kind: str, **fields: JsonValue) -> tuple[str, str]:
    """One record item on `main`, answered as `(object id, item)`: a note or a conflict."""
    stored = library.store.put(
        OPERATOR,
        Draft(kind, None, title=kind, fields=fields),
        on=MAIN,
        expected_head=None,
    )
    return stored.object_id, stored.item


@pytest.mark.parametrize(("level", "template"), sorted(LEVELS.items()))
def test_new_installs_the_levels_template(
    lab: Lab, installs: Installs, level: str, template: str
) -> None:
    opened = doc(lab.new(level, f"a {level}"))

    assert doc(opened["project"])["level"] == level
    assert installs.asked == [template]
    assert lab.published(level) == (template,)
    assert doc(doc(lab.open(str(doc(opened["project"])["id"])))["workspace"])["level"] == level


def test_the_workspace_annotation_round_trips_without_a_version(
    tmp_path: Path, lab: Lab, library: Library
) -> None:
    project = str(doc(lab.new("experiment", "a model run")["project"])["id"])
    first = item(library, "note")
    second = item(library, "note")
    layout: list[JsonValue] = [{"panel": "explorer", "width": 0.3}]
    lab.workspace(
        str(project),
        open=first[0],
        pins=[first[0], second[0]],
        layout=layout,
        tabs=["data", "run"],
    )
    library.close()
    reopened_library = Library(tmp_path)
    reopened = Lab(reopened_library, installs=Installs(reopened_library))

    opened = doc(reopened.open(str(project)))

    assert doc(opened["workspace"]) == {
        "open": first[0],
        "layout": layout,
        "pins": [first[0], second[0]],
        "tabs": ["data", "run"],
        "level": "experiment",
    }
    assert len(reopened.library.store.ancestry_of(str(project))) == 1


def test_a_training_run_refuses_when_the_partitions_do_not_fit(
    lab: Lab, library: Library, door: Door
) -> None:
    card = dataset_card(library)

    with pytest.raises(ControlError) as refused:
        lab.training(card, months=["2026-01", "2026-02"], seed=7, code_version="v1", free=4 * MB)

    assert refused.value.code == "disk_full"
    assert str(refused.value) == (
        f"a training run on the PC needs 5.0 MB for 2 partitions of {SERIES} and 4.0 MB is free; "
        "nothing was materialised"
    )
    assert door.materialised == []


def test_a_training_run_materialises_only_its_months_and_the_model_records_them(
    lab: Lab, library: Library, door: Door
) -> None:
    card = dataset_card(library)

    training = lab.training(card, months=["2026-02"], seed=11, code_version="sha256:code")
    model = lab.model(training, weights=b"weights", metrics={"validation": 0.51})

    assert door.materialised == [("b" * 64,)]
    assert training.slot == 0
    fields = doc(model["fields"])
    assert (fields["partitions"], fields["seed"], fields["code"]) == (
        [{"month": "2026-02", "fingerprint": "b" * 64}],
        11,
        {"version": "sha256:code"},
    )
    assert (fields["framework"], fields["hardware"]) == (
        "torch",
        {"placement": "pc", "gpu_slot": 0, "device": "Quadro T1000"},
    )
    edges = [
        (edge, target)
        for _source, edge, target, *_ in library.store.edges_of(str(model["id"]), reverse=False)
    ]
    assert edges == [("consumed", card)]


def test_the_panel_shows_the_months_the_quality_and_the_sealed_refusal(
    lab: Lab, library: Library, door: Door
) -> None:
    card = dataset_card(library)
    door.sealed = True

    panel = doc(lab.panel(card))

    assert (panel["series"], panel["month"], panel["quality"]) == (
        SERIES,
        "2026-01",
        {"grade": "A"},
    )
    assert panel["months"] == ["2026-01", "2026-02", "2026-03"]
    assert panel["refusal"] == f"{SEALED}: 2026-01"
    assert panel["sample"] is None


def test_problems_are_marks_and_conflicts_and_the_timeline_is_history(
    lab: Lab, library: Library
) -> None:
    marked, marked_item = item(library, "note")
    conflict, _ = item(
        library,
        "merge-conflict",
        ours="refs/agents/s1/x",
        theirs="refs/drafts/x",
        into="main",
        entries=[],
    )
    library.store.mark(OPERATOR, marked_item, True, "its price source was wrong")
    project = library.store.put(
        OPERATOR,
        Draft(
            "collection",
            None,
            title="a study",
            fields={"items": [marked, conflict], "level": "study"},
        ),
        on=MAIN,
        expected_head=None,
    ).object_id

    opened = doc(lab.open(project))
    problems = [doc(problem) for problem in cast(list[JsonValue], opened["problems"])]
    timeline = [doc(row) for row in cast(list[JsonValue], opened["timeline"])]

    assert [problem["problem"] for problem in problems] == ["quarantined", "conflict"]
    assert [problem["reason"] for problem in problems] == ["quarantined", "main"]
    assert [row["ref"] for row in timeline] == ["main"]
