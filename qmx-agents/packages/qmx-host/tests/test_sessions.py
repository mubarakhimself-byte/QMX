"""The session recorder: one `session` item per chat, annotated at each turn end without a new
version, and a redacted transcript export at close and once a day for an idle chat."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from qma.harness import Home, NewChat, SessionId, TurnResult, TurnTokens
from qma.harness.home import ChatRecord
from qma.harness.profiles import ProfileName
from qmx_engine.ledger import redact
from qmx_library.principal import MAIN
from qmx_library.store import Store

from qmx_host.sessions import SessionRecorder

PLANTED = "sk-or-" + "v1-" + "e5" * 32
CHAT = SessionId("0b6f3e1c-1111-4c4c-9a9a-000000000001")


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def chat(session: str = CHAT, *, model: str = "haiku", digest: str = "sha256:aa") -> ChatRecord:
    config = NewChat("Lab pod review", model=model).config(
        ProfileName("claude"), Path(), Home("lab", "pod-7")
    )
    return ChatRecord(SessionId(session), config, True, "idle", digests=(digest,))


def turn(tokens_in: int, tokens_out: int) -> TurnResult:
    usage = TurnTokens(input_tokens=tokens_in, output_tokens=tokens_out)
    return TurnResult("ok", "done", (), usage, (), (), None, None)


def test_each_chat_gets_one_item_found_by_its_title_with_its_home(
    store: Store, clock: Clock
) -> None:
    recorder = SessionRecorder(store, clock)
    first = recorder.born(chat(), "Lab pod review")
    again = recorder.born(chat(), "Lab pod review")
    recorder.born(chat("0b6f3e1c-1111-4c4c-9a9a-000000000002"), "Other chat")

    hits = store.search(store.engine, "pod review", kind="session")
    view = store.get(store.engine, first)

    assert again == first
    assert [(h.item, h.title) for h in hits] == [(CHAT, "Lab pod review")]
    assert view.fields == {
        "session_id": CHAT,
        "home": {"kind": "lab", "project_id": "pod-7"},
        "created": "2026-10-20T09:00:00+00:00",
    }
    assert store.head(CHAT, MAIN) == (first, 1)
    assert store.history(CHAT)[0][2] == "engine:pc"


def test_each_turn_end_annotates_the_head_and_mints_no_version(store: Store, clock: Clock) -> None:
    recorder = SessionRecorder(store, clock)
    born = recorder.born(chat(), "Lab pod review")
    for n, model in enumerate(("haiku", "haiku", "sonnet"), start=1):
        clock.now += timedelta(minutes=1)
        recorder.turn_ended(chat(model=model, digest=f"sha256:{n}"), turn(10, n))

    notes = store.get(store.engine, born).annotations

    assert recorder.head(CHAT) == born
    assert {k: notes[k] for k in ("turns", "tokens", "models", "profiles", "surface_digest")} == {
        "turns": 3,
        "tokens": 36,
        "models": ["haiku", "sonnet"],
        "profiles": ["claude"],
        "surface_digest": "sha256:3",
    }
    assert notes["last_turn_at"] == "2026-10-20T09:03:00+00:00"


def test_a_turn_on_a_chat_born_before_the_recorder_writes_its_item(
    store: Store, clock: Clock
) -> None:
    recorder = SessionRecorder(store, clock)
    recorder.turn_ended(chat(), turn(1, 1))

    head = recorder.head(CHAT)

    assert head is not None
    assert store.get(store.engine, head).annotations["turns"] == 1


def test_the_close_export_is_a_redacted_version_that_keeps_the_annotations(
    store: Store, clock: Clock, tmp_path: Path
) -> None:
    recorder = SessionRecorder(store, clock)
    born = recorder.born(chat(), "Lab pod review")
    recorder.turn_ended(chat(), turn(5, 5))
    folder = tmp_path / "export"
    folder.mkdir()
    line = f'{{"type":"user","text":"echo KEY={PLANTED}"}}\n'
    (folder / "transcript.jsonl").write_text(line, encoding="utf-8")

    async def exporter(_chat: SessionId) -> Path:
        return folder

    exported = asyncio.run(recorder.export(CHAT, exporter))
    view = store.get(store.engine, exported, blobs="fetch")

    assert view.parents == (born,)
    assert store.head(CHAT, MAIN) == (exported, 2)
    assert PLANTED.encode() not in view.data["transcript"]
    assert b"echo KEY=" in view.data["transcript"]
    assert view.annotations["turns"] == 1
    assert view.annotations["exported_at"] == "2026-10-20T09:00:00+00:00"


def test_a_chat_idle_past_a_day_is_due_once_until_it_talks_again(
    store: Store, clock: Clock
) -> None:
    recorder = SessionRecorder(store, clock)
    recorder.born(chat(), "Lab pod review")
    recorder.turn_ended(chat(), turn(1, 1))
    clock.now += timedelta(hours=23)
    early = recorder.idle_due(CHAT)
    clock.now += timedelta(hours=2)
    due = recorder.idle_due(CHAT)
    recorder.exported(CHAT, b"{}\n")
    after_export = recorder.idle_due(CHAT)

    assert (early, due, after_export) == (False, True, False)


def test_a_restarted_host_keeps_writing_the_same_item(tmp_path: Path, clock: Clock) -> None:
    with Store.open(tmp_path / "library", redactor=redact) as store:
        born = SessionRecorder(store, clock).born(chat(), "Lab pod review")
    with Store.open(tmp_path / "library", redactor=redact) as store:
        recorder = SessionRecorder(store, clock)
        recorder.turn_ended(chat(), turn(1, 1))
        found = recorder.head(CHAT), store.get(store.engine, born).annotations["turns"]

    assert found == (born, 1)
