"""The `@` grammar and its resolvers, over a Library fixture: each kind, pin and follow, a
pinned item whose main moved, an archived item, and the kinds another PR brings."""

from __future__ import annotations

from collections.abc import Sequence
from types import MappingProxyType

import pytest

from qmx_control.catalog import rows
from qmx_control.context import (
    NEWER,
    NO_MEMORY,
    AttachedRef,
    Budget,
    ContextRefused,
    LibraryHit,
    LibraryObject,
    MemoryRowHit,
    Pin,
    Resolvers,
    listing,
    parse,
    pins_of,
    references,
)

BUDGET = Budget(soft_chars=200, hard_chars=400)
POD_V7 = "fp1:sha256::pod7"
POD_V8 = "fp1:sha256::pod8"
RUN = "0192f0aa-0000-7000-8000-00000000run1"
APP = "macro-bias"


class Memory:
    """A host's memory engine for the resolver: one list of recalled rows."""

    def __init__(self, rows: Sequence[MemoryRowHit]) -> None:
        self.rows = rows

    def memory(self, question: str, limit: int = 10) -> list[MemoryRowHit]:
        del question
        return list(self.rows[:limit])


class Fixture:
    """A Library fixture: object kinds and titles, each item's main head, the item state, the
    artifacts a producer landed, and the search index."""

    def __init__(self) -> None:
        self.objects: dict[str, LibraryObject] = {}
        self.main: dict[str, str] = {}
        self.states: dict[str, str] = {}
        self.landed: dict[str, list[str]] = {}
        self.index: list[LibraryHit] = []

    def put(
        self,
        object_id: str,
        item: str,
        kind: str,
        title: str,
        *,
        main: bool = True,
        fields: dict[str, object] | None = None,
    ) -> str:
        self.objects[object_id] = LibraryObject(
            object_id, item, kind, title, fields=MappingProxyType(fields or {})
        )
        if main:
            self.main[item] = object_id
        return object_id

    def land(self, artifact: str, producer: str, kind: str, title: str, name: str) -> str:
        self.put(artifact, artifact, kind, title, fields={"type": name})
        self.landed.setdefault(producer, []).append(artifact)
        return artifact

    # `LibraryReads`
    def resolve(self, item: str, ref: str = "main") -> str | None:
        del ref
        return self.main.get(item)

    def head(self, item: str, ref: str = "main") -> str | None:
        return self.resolve(item, ref)

    def state(self, item: str) -> str | None:
        return self.states.get(item, "active" if item in self.main else None)

    def get(self, object_id: str, slots: Sequence[str] = ()) -> LibraryObject:
        del slots
        return self.objects.get(object_id, LibraryObject("", "", ""))

    def search(self, text: str, *, kind: str | None = None, limit: int = 20) -> list[LibraryHit]:
        found = [hit for hit in self.index if text in hit.title and kind in (None, hit.kind)]
        return found[:limit]

    def versions(self, item: str, kind: str) -> list[str]:
        del kind
        return [self.main[item]] if item in self.main else []

    def produced(self, producer: str) -> list[str]:
        return self.landed.get(producer, [])

    def outputs(self, producer: str, name: str) -> list[str]:
        return [
            a for a in self.landed.get(producer, []) if self.objects[a].fields.get("type") == name
        ]


@pytest.fixture
def library() -> Fixture:
    fixture = Fixture()
    fixture.put(POD_V7, "pod-7", "pod", "Pod 7")
    fixture.put("fp1:sha256::unit", "macd-v2", "unit", "MACD v2")
    fixture.put("fp1:sha256::bot", "london-open", "bot", "London open")
    fixture.put(
        "fp1:sha256::session", "0b6f3e1c-1111-4c4c-9a9a-000000000001", "session", "Lab pod review"
    )
    fixture.put("fp1:sha256::run", RUN, "workflow-run", "Nightly bias")
    fixture.land("fp1:sha256::bias", "fp1:sha256::run", "artifact", "Bias, night one", "bias")
    fixture.put("fp1:sha256::app7", APP, "mini-app", "Macro bias app")
    fixture.land("fp1:sha256::app-bias", APP, "artifact", "Bias 2026-10-19", "bias")
    return fixture


def test_each_kind_resolves_to_its_library_object(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)

    assert found.add("@pod:pod-7") == AttachedRef(
        ref="@pod:pod-7", item_id="pod-7", version_id=POD_V7
    )
    assert found.add("@unit:macd-v2").item_id == "macd-v2"
    assert found.add("@bot:london-open").item_id == "london-open"
    assert found.add("@session:0b6f3e1c-1111-4c4c-9a9a-000000000001").version_id == (
        "fp1:sha256::session"
    )
    assert found.add("@run:" + RUN + "/bias").artifact_id == "fp1:sha256::bias"
    assert found.add("@app:macro-bias/bias").artifact_id == "fp1:sha256::app-bias"
    library.index.append(LibraryHit("fp1:sha256::unit", "macd-v2", "unit", "MACD v2"))
    assert found.add("@library:MACD").item_id == "macd-v2"


def test_a_target_of_the_wrong_kind_is_refused_by_name(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)

    with pytest.raises(ContextRefused, match="is a session, so it reads @session:"):
        found.add("@pod:0b6f3e1c-1111-4c4c-9a9a-000000000001")


def test_the_grammar_names_its_kinds_and_the_refusals(library: Fixture) -> None:
    assert parse(" @run:x/y ") == ("run", "x/y")
    with pytest.raises(ContextRefused) as refused:
        parse("pod-7")
    assert "a reference reads @<kind>:<target>" in str(refused.value)
    with pytest.raises(ContextRefused, match="is not a reference kind"):
        parse("@dataset:r12")
    with pytest.raises(ContextRefused, match="the @file kind arrives with REF2"):
        parse("@file:a/b.py")
    assert parse("@memory:why did we drop the filter") == (
        "memory",
        "why did we drop the filter",
    )


def test_memory_recalls_the_rows_that_answer_the_question(library: Fixture) -> None:
    rows = [MemoryRowHit("row-1", "pod P wants a 20 day ATR", "lesson", ("item:pod-p",))]
    found = Resolvers(library, BUDGET, Memory(rows))

    attached = found.add("@memory:what did we find about pod P")

    assert attached.item_id == "memory:what did we find about pod P"
    assert attached.status == "ready"
    assert attached.note == "1 rows"
    assert "20 day ATR" in found.excerpt(attached)
    assert "item:pod-p" in found.read(attached)


def test_memory_is_refused_by_name_on_a_host_that_installed_none(library: Fixture) -> None:
    with pytest.raises(ContextRefused, match=NO_MEMORY):
        Resolvers(library, BUDGET).add("@memory:what did we find about pod P")


def test_a_pinned_item_whose_main_moved_says_the_newer_version_exists(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    pinned = found.add("@pod:pod-7")
    assert pinned.note == ""

    library.put(POD_V8, "pod-7", "pod", "Pod 8")

    moved = found.refresh(pinned)
    assert (moved.version_id, moved.status, moved.note) == (POD_V7, "ready", NEWER)
    assert found.add("@pod:pod-7") == AttachedRef(
        ref="@pod:pod-7", item_id="pod-7", version_id=POD_V8
    )


def test_follow_reads_the_head_and_pins_nothing(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    followed = found.add("@pod:pod-7", "follow")
    library.put(POD_V8, "pod-7", "pod", "Pod 8")

    assert (followed.pin, followed.version_id) == ("follow", None)
    assert found.refresh(followed).note == ""
    assert "Pod 8" in found.read(followed)


def test_an_archived_item_reads_archived_and_stays_readable(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    library.states["pod-7"] = "archived"

    archived = found.add("@pod:pod-7")

    assert (archived.status, archived.version_id) == ("archived", POD_V7)
    assert "Pod 7" in found.read(archived)


def test_a_run_output_that_has_not_landed_reads_pending(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)

    waiting = found.add("@run:" + RUN + "/signals")

    assert (waiting.status, waiting.artifact_id) == ("pending", None)
    assert waiting.note == "the run has not landed signals yet"


def test_a_pinned_main_that_moved_on_an_app_output_is_not_reported_as_newer(
    library: Fixture,
) -> None:
    found = Resolvers(library, BUDGET)
    output = found.add("@app:macro-bias/bias")

    assert (output.status, output.artifact_id) == ("ready", "fp1:sha256::app-bias")


def test_the_listing_refreshes_every_entry_at_read_time(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    entries = [
        found.add("@pod:pod-7"),
        AttachedRef("@unit:macd-v2", "macd-v2", version_id="fp1:sha256::unit"),
    ]
    library.put(POD_V8, "pod-7", "pod", "Pod 8")
    library.states["macd-v2"] = "archived"

    page = listing(entries, found)

    assert page.lines() == [
        "@pod:pod-7 ready pinned pod7 newer version exists",
        "@unit:macd-v2 archived pinned unit",
    ]
    assert [entry.status for entry in page.entries] == ["ready", "archived"]
    assert (page.ready, page.pending) == (1, 0)


def test_an_entry_that_no_longer_resolves_reads_not_cached(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    gone = AttachedRef("@pod:deleted-pod", "deleted-pod", version_id=POD_V7)

    page = listing([gone], found)

    assert page.entries[0].status == "not_cached"
    assert "no Library item 'deleted-pod'" in page.entries[0].note


def test_the_excerpt_is_cut_to_its_budget_and_the_handle_stays(library: Fixture) -> None:
    found = Resolvers(library, Budget(soft_chars=400, hard_chars=800))
    library.objects[POD_V7] = LibraryObject(
        POD_V7,
        "pod-7",
        "pod",
        "Pod 7",
        fields=MappingProxyType({"blocks": "x" * 2_000}),
    )
    pinned = found.add("@pod:pod-7")

    soft = found.excerpt(pinned)
    hard = found.read(pinned)

    assert soft.startswith("@pod:pod-7 ready pinned pod7\nPod 7")
    assert len(soft.split("\n\n", 1)[1]) <= 400
    assert 400 < len(hard.split("\n\n", 1)[1]) <= 800
    assert "context_read has the rest" in hard
    assert "blocks" in found.read(pinned, "0-20")


def test_a_bad_range_is_refused_by_name(library: Fixture) -> None:
    found = Resolvers(library, BUDGET)
    pinned = found.add("@pod:pod-7")

    with pytest.raises(ContextRefused, match="a range reads a-b"):
        found.read(pinned, "9")


def test_the_context_toolset_is_five_rows_within_the_wire_name(library: Fixture) -> None:
    found = [row for row in rows() if row.toolset == "context"]

    assert [row.name for row in found] == [
        "context_add",
        "context_list",
        "context_refresh",
        "context_drop",
        "context_read",
    ]
    assert [row.binds for row in found] == ["agent_tool"] * 5
    assert [row.approval for row in found] == [
        "domain_write",
        "read",
        "domain_write",
        "domain_write",
        "read",
    ]


class PinnedReads:
    """`InputReads` over the fixture: by object id, a run's summaries, a producer's artifacts."""

    def __init__(self, library: Fixture) -> None:
        self.library = library

    def object(self, object_id: str) -> LibraryObject | None:
        return self.library.objects.get(object_id)

    def summaries(self, run: str) -> list[str]:
        return [
            found.object_id
            for found in self.library.objects.values()
            if found.item == run and found.kind == "workflow-run"
        ]

    def produced(self, producer: str) -> list[str]:
        return self.library.produced(producer)


def test_a_runs_inputs_name_each_reference_once_and_in_order() -> None:
    inputs = {
        "today": "@run:run1/nightly-bias",
        "also": ["@library:fp1:sha256::pod7", "@run:run1/nightly-bias"],
        "note": "no reference here",
        "deep": {"pinned": "@library:fp1:sha256::unit"},
    }

    assert references(inputs) == (
        "@run:run1/nightly-bias",
        "@library:fp1:sha256::pod7",
        "@library:fp1:sha256::unit",
    )


def test_a_reference_pins_the_object_the_library_holds(library: Fixture) -> None:
    pinned = pins_of(["@run:" + RUN + "/bias", "@library:" + POD_V7], PinnedReads(library))

    assert pinned == (
        Pin("@run:" + RUN + "/bias", "fp1:sha256::bias"),
        Pin("@library:" + POD_V7, POD_V7),
    )
    assert [pin.document() for pin in pinned] == [
        {"ref": "@run:" + RUN + "/bias", "object_id": "fp1:sha256::bias"},
        {"ref": "@library:" + POD_V7, "object_id": POD_V7},
    ]


def test_a_reference_that_names_nothing_refuses_the_start(library: Fixture) -> None:
    reads = PinnedReads(library)

    with pytest.raises(ContextRefused, match="names no run 'run-gone'"):
        pins_of(["@run:run-gone"], reads)
    with pytest.raises(ContextRefused, match="names an output the run has not landed"):
        pins_of(["@run:" + RUN + "/not-landed"], reads)
    with pytest.raises(ContextRefused, match="read only run, library"):
        pins_of(["@pod:pod-7"], reads)
