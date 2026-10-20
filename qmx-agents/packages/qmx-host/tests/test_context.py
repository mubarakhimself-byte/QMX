"""The `context` toolset as the host serves it (AD-63): the store reads behind the resolvers, the
five reads bound to one chat, and the mirror onto the session item."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, cast

import pytest
from qma.harness import Home, NewChat, SessionId
from qma.harness.home import ChatRecord
from qma.harness.profiles import ProfileName
from qma.harness.tools import HostRead
from qmx_control.context import AttachedRef
from qmx_engine.ledger import redact
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store

from qmx_host.sessions import SessionRecorder, chat_reads

if TYPE_CHECKING:
    from qmx_host.sessions import RecordedHarness

OPERATOR = Principal("operator")
CHAT = SessionId("0b6f3e1c-2222-4c4c-9a9a-000000000002")
RUN = "0192f0aa-0000-7000-8000-0000000000f1"
BUDGET_FREE: Final[Mapping[str, object]] = MappingProxyType({})


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def published(store: Store, draft: Draft) -> str:
    """A definition's version on `main`, the way his publish puts one there."""
    on = drafts_ref(str(draft.item))
    found = store.head(str(draft.item), on)
    commit = store.put(OPERATOR, draft, on=on, expected_head=None if found is None else found[0])
    store.merge(OPERATOR, commit.item, from_ref=on, into=MAIN, strategy="ff-only")
    return commit.object_id


def pod(store: Store, title: str = "Pod 7") -> str:
    return published(store, Draft("pod", "pod-7", title=title, fields={"slots": {}}))


def run_item(store: Store) -> str:
    return store.put(
        OPERATOR,
        Draft(
            "workflow-run",
            RUN,
            title="Nightly bias",
            fields={"run_id": RUN, "mode": "test", "status": "passed"},
        ),
        on=MAIN,
        expected_head=None,
    ).object_id


def land(store: Store, run: str, name: str = "bias") -> str:
    artifact = store.put(
        OPERATOR,
        Draft("artifact", None, title="Bias, night one", fields={"type": name}),
        on=MAIN,
        expected_head=None,
    ).object_id
    store.relate(OPERATOR, artifact, "produced-by", run)
    return artifact


def record() -> ChatRecord:
    config = NewChat("Lab pod review", model="haiku").config(
        ProfileName("claude"), Path(), Home("lab", "pod-7")
    )
    return ChatRecord(CHAT, config, started=True, turn="idle")


class Host:
    """What `chat_reads` needs of the process that serves it: the `[agents]` settings, the chat's
    record, and `set_attached` writing it. The real one is `RecordedHarness`."""

    def __init__(self, store: Store) -> None:
        self.store = store
        self.records: dict[SessionId, ChatRecord] = {CHAT: record()}
        self.attached: list[tuple[AttachedRef, ...]] = []

    @property
    def control(self) -> Host:
        return self

    def settings_get(self, section: str) -> Mapping[str, object]:
        assert section == "agents"
        return BUDGET_FREE

    def record(self, chat: SessionId) -> ChatRecord | None:
        return self.records.get(chat)

    async def set_attached(self, chat: SessionId, refs: Sequence[AttachedRef]) -> None:
        self.attached.append(tuple(refs))
        self.records[chat] = ChatRecord(
            chat, self.records[chat].config, started=True, turn="idle", attached=tuple(refs)
        )


def serve(host: Host) -> Mapping[str, HostRead]:
    return chat_reads(cast("RecordedHarness", host), host.store, CHAT)


def entries(page: Mapping[str, object]) -> list[dict[str, object]]:
    return cast("list[dict[str, object]]", page["entries"])


def lines(page: Mapping[str, object]) -> list[str]:
    return cast("list[str]", page["lines"])


def test_every_context_row_has_an_input_schema() -> None:
    from qma.harness.tools import HOST_SCHEMAS
    from qmx_control.catalog import CONTEXT_ROWS

    assert [row.target for row in CONTEXT_ROWS if row.target not in HOST_SCHEMAS] == []
    assert HOST_SCHEMAS["context_add"]["required"] == ["ref"]


def test_adding_a_pod_puts_it_on_the_record_and_returns_an_excerpt(store: Store) -> None:
    host = Host(store)
    pod(store)

    answer = asyncio.run(serve(host)["context_add"]({"ref": "@pod:pod-7"}))

    assert (answer["ref"], answer["item_id"], answer["status"]) == ("@pod:pod-7", "pod-7", "ready")
    assert str(answer["excerpt"]).startswith("@pod:pod-7 ready pinned ")
    entry = host.attached[0][0]
    assert (entry.ref, entry.item_id, entry.pin) == ("@pod:pod-7", "pod-7", "version")
    assert entry.version_id == answer["version_id"]


def test_a_pinned_pod_reads_the_newer_version_after_a_publish(store: Store) -> None:
    host = Host(store)
    pod(store)
    serve(host)
    reads = serve(host)
    asyncio.run(reads["context_add"]({"ref": "@pod:pod-7"}))
    v8 = published(store, Draft("pod", "pod-7", title="Pod 8", fields={"slots": {}}))

    page = asyncio.run(reads["context_list"]({}))

    assert lines(page)[0].startswith("@pod:pod-7 ready pinned ")
    assert lines(page)[0].endswith("newer version exists")
    assert entries(page)[0]["note"] == "newer version exists"
    assert entries(page)[0]["version_id"] != v8


def test_a_followed_pod_reads_main_head_after_a_publish(store: Store) -> None:
    host = Host(store)
    pod(store)
    reads = serve(host)
    asyncio.run(reads["context_add"]({"ref": "@pod:pod-7", "pin": "follow"}))
    published(store, Draft("pod", "pod-7", title="Pod 8", fields={"slots": {}}))

    page = asyncio.run(reads["context_list"]({}))
    text = asyncio.run(reads["context_read"]({"ref": "@pod:pod-7"}))

    assert entries(page)[0]["pin"] == "follow"
    assert entries(page)[0]["note"] == ""
    assert "Pod 8" in str(text["text"])


def test_a_run_output_reads_pending_until_it_lands(store: Store) -> None:
    host = Host(store)
    run = run_item(store)
    reads = serve(host)

    early = asyncio.run(reads["context_add"]({"ref": f"@run:{RUN}/bias"}))
    artifact = land(store, run)
    listed = asyncio.run(reads["context_list"]({}))

    assert (early["status"], early["artifact_id"]) == ("pending", None)
    assert entries(listed)[0]["status"] == "ready"
    assert entries(listed)[0]["artifact_id"] == artifact
    assert entries(listed)[0]["version_id"] == run


def test_an_archived_item_reads_archived_and_still_reads(store: Store) -> None:
    host = Host(store)
    head = pod(store)
    reads = serve(host)
    asyncio.run(reads["context_add"]({"ref": "@pod:pod-7"}))
    store.archive(OPERATOR, "pod-7", "superseded by pod 8")

    listed = asyncio.run(reads["context_list"]({}))
    text = asyncio.run(reads["context_read"]({"ref": "@pod:pod-7"}))

    assert entries(listed)[0]["status"] == "archived"
    assert entries(listed)[0]["version_id"] == head
    assert str(text["text"]).startswith("@pod:pod-7 archived")


def test_a_reference_of_another_pr_is_refused_and_a_missing_one_is_not_found(
    store: Store,
) -> None:
    reads = serve(Host(store))

    with pytest.raises(ValueError, match="the @file kind arrives with REF2"):
        asyncio.run(reads["context_add"]({"ref": "@file:src/main.py"}))
    with pytest.raises(KeyError, match="no Library item 'pod-9'"):
        asyncio.run(reads["context_add"]({"ref": "@pod:pod-9"}))


def test_dropping_and_refreshing_one_reference_rewrites_the_record(store: Store) -> None:
    host = Host(store)
    pod(store)
    reads = serve(host)
    asyncio.run(reads["context_add"]({"ref": "@pod:pod-7"}))

    refreshed = asyncio.run(reads["context_refresh"]({"ref": "@pod:pod-7"}))
    dropped = asyncio.run(reads["context_drop"]({"ref": "@pod:pod-7"}))

    assert refreshed["ref"] == "@pod:pod-7"
    assert dropped == {"dropped": "@pod:pod-7", "attached": 0}
    assert host.records[CHAT].attached == ()


def test_the_recorder_mirrors_the_list_as_item_tags_and_mentions_edges(store: Store) -> None:
    recorder = SessionRecorder(store)
    head = pod(store)
    recorder.born(record(), "Lab pod review")

    recorder.attached(CHAT, [AttachedRef("@pod:pod-7", "pod-7", version_id=head)])
    recorder.attached(CHAT, [AttachedRef("@pod:pod-7", "pod-7", version_id=head)])

    item = recorder.head(CHAT)
    assert item is not None
    assert store.get(store.engine, item).annotations["tags"] == [f"item:{head}"]
    assert [(name, to) for _, name, to, _, _ in store.edges_of(item, reverse=False)] == [
        ("mentions", head)
    ]


def test_the_mirror_carries_each_reference_and_keeps_the_earlier_ones(store: Store) -> None:
    recorder = SessionRecorder(store)
    head = pod(store)
    run = run_item(store)
    artifact = land(store, run)
    recorder.born(record(), "Lab pod review")
    recorder.attached(CHAT, [AttachedRef("@pod:pod-7", "pod-7", version_id=head)])

    recorder.attached(
        CHAT,
        [
            AttachedRef("@pod:pod-7", "pod-7", version_id=head),
            AttachedRef(f"@run:{RUN}/bias", RUN, version_id=run, artifact_id=artifact),
        ],
    )

    item = recorder.head(CHAT)
    assert item is not None
    tags = cast("list[str]", store.get(store.engine, item).annotations["tags"])
    assert sorted(tags) == sorted([f"item:{head}", f"item:{artifact}"])


def test_the_mirror_needs_an_item_and_says_so(store: Store) -> None:
    assert SessionRecorder(store).attached(CHAT, [AttachedRef("@pod:pod-7", "pod-7")]) is None
