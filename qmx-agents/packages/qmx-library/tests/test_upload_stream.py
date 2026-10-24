"""The streaming upload door and whole-text search, through the store's public calls.

A resumed upload re-hashes what it holds before it takes another byte. A phrase past the old
one-megabyte cap is found. A hit names the page it is on. A canonical URL is one item however
many times it is saved.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.search import answer, locate
from qmx_library.store import Store, capture_source, redact_accounts

OPERATOR = Principal("operator")
NOW = datetime(2026, 10, 20, tzinfo=UTC)


def clock() -> datetime:
    return NOW


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=clock) as opened:
        yield opened


def source(store: Store, item: str, **blobs: bytes) -> str:
    head = store.catalog.head(item, "main")
    done = store.put(
        OPERATOR,
        Draft(
            "source",
            item=item,
            title=item,
            fields={
                "origin": "upload",
                "canonical_url": item,
                "extractor_version": "docling-2.134.0",
            },
            blobs=blobs,
        ),
        on="main",
        expected_head=None if head is None else head[0],
    )
    return done.object_id


def test_a_resumed_upload_rehashes_its_partial_and_ends_with_the_right_hash(store: Store) -> None:
    first = b"a" * 1_500_000
    second = b"b" * 500_000
    held, partial = store.append_upload([first], upload_id="up-1")

    assert (held, partial) == (len(first), sha256(first).hexdigest())
    with pytest.raises(LibraryRefused) as wrong:
        store.append_upload([second], upload_id="up-1", offset=held, partial_sha256="00" * 32)
    assert wrong.value.code == "hash_mismatch"
    resumed, whole = store.append_upload(
        [second], upload_id="up-1", offset=held, partial_sha256=partial
    )
    blob_id = store.complete_upload("up-1", expect_sha256=whole)

    assert resumed == len(first) + len(second)
    assert whole == sha256(first + second).hexdigest()
    assert blob_id == f"sha256:{whole}"
    assert store.read_blob(blob_id) == first + second
    assert store.upload_held("up-1") == (0, sha256(b"").hexdigest())


def test_a_phrase_past_the_first_megabyte_of_text_is_found(store: Store) -> None:
    body = "filler " * 300_000 + " the kestrel arbitrage phrase "
    source(store, "book", text=body.encode())

    found = store.search(OPERATOR, "kestrel arbitrage")
    answered = answer(store, OPERATOR, "the kestrel arbitrage phrase in the book")

    assert [hit.item for hit in found] == ["book"]
    assert [result.item for result in answered.results] == ["book"]
    object_id = found[0].object_id
    assert "kestrel arbitrage" in store.catalog.texts([object_id])[object_id]
    assert "kestrel" not in answered.results[0].preview


def test_a_hit_opens_at_the_page_its_phrase_is_on(store: Store) -> None:
    object_id = source(
        store,
        "manual.pdf",
        text=b"page one\npage three hundred and twelve",
        **{"pages/1": b"page one opens the manual", "pages/312": b"the margin call is here"},
    )

    assert locate(store, object_id, "margin call") == {"page": 312}
    assert locate(store, object_id, "not in this document") is None


def test_a_transcript_hit_names_its_minute(store: Store) -> None:
    object_id = source(
        store,
        "talk.mp3",
        transcript=b"[00:00] opening words\n[21:07] the carry trade fails\n[42:00] closing words",
    )

    assert locate(store, object_id, "carry trade") == {"seconds": 21 * 60 + 7}


def test_the_same_canonical_url_saved_twice_is_one_item(store: Store) -> None:
    item = "https://example.org/a-book"
    source(store, item, text=b"the first upload")
    source(store, item, text=b"the second upload, other bytes")

    assert [hit.item for hit in store.search(OPERATOR, "upload")] == [item]
    assert store.catalog.state(item) == "active"
    assert store.catalog.head(item, "main") is not None


def test_completing_an_upload_whose_hash_disagrees_deletes_the_partial(store: Store) -> None:
    store.append_upload([b"bytes"], upload_id="up-2")

    with pytest.raises(LibraryRefused) as refused:
        store.complete_upload("up-2", expect_sha256="11" * 32)

    assert refused.value.code == "hash_mismatch"
    assert store.upload_held("up-2") == (0, sha256(b"").hexdigest())


def test_a_capture_lands_as_one_source_with_its_account_ids_redacted(store: Store) -> None:
    pixels = b"\x89PNG\r\n\x1a\n not really a png, but it must come back whole"
    draft = capture_source(
        "Account 51234567 holds the position; account 51234567 again.",
        pixels,
        account_ids=("51234567",),
        title="Broker screen",
        surface="browser",
    )

    done = store.put(OPERATOR, draft, on="main", expected_head=None)
    view = store.get(OPERATOR, done.object_id, blobs="fetch")

    assert redact_accounts("a 99 b 9", ("9", "99")) == "a [redacted account] b [redacted account]"
    assert view.fields["origin"] == "capture"
    assert view.fields["captured_from"] == "browser"
    assert (
        view.data["text"]
        == b"Account [redacted account] holds the position; account [redacted account] again."
    )
    assert view.data["original"] == pixels
    assert view.data["frames/0"] == pixels
