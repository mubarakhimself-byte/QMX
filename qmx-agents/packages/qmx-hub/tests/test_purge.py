"""An operator purge tombstones a secret on the Hub, on the bucket and on the replica that syncs
next; the object that named the blob reads `blob_purged` (Library AD-6)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.client import OwnerTable
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.purge import bucket_tombstones, purge_everywhere
from qmx_hub.replicate import StorePeer, sync

OPERATOR = Principal("operator")
SECRET = b"the vault code is 4411"


@pytest.fixture
def hub(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as opened:
        yield opened


def planted(store: Store) -> tuple[str, str]:
    """A note whose body is a secret that redaction does not recognise, and its blob id."""
    done = store.put(
        OPERATOR,
        Draft("note", "n1", title="planted", blobs={"body.md": SECRET}),
        on="main",
        expected_head=None,
    )
    return done.object_id, store.get(OPERATOR, done.object_id).blobs["body.md"].blob_id


def test_a_purge_tombstones_the_hub_the_bucket_and_the_replica(hub: Store, tmp_path: Path) -> None:
    object_id, blob_id = planted(hub)
    bucket = tmp_path / "bucket"
    (bucket / "blobs").mkdir(parents=True)
    (bucket / "blobs" / blob_id.removeprefix("sha256:")).write_bytes(SECRET)

    done = purge_everywhere(hub, blob_id, "a vault code", buckets=[bucket])

    assert done.targets == ("hub", f"bucket:{bucket}")
    assert hub.purged(blob_id) is True
    assert (bucket / "blobs" / blob_id.removeprefix("sha256:")).exists() is False
    assert bucket_tombstones(bucket) == {blob_id: "a vault code"}
    with pytest.raises(LibraryRefused, match=r"^blob_purged:"):
        hub.read_blob(blob_id)
    assert hub.get(OPERATOR, object_id, blobs="fetch").purged == frozenset({"body.md"})

    with Store.open(tmp_path / "pc", redactor=redact, name="pc", role="replica") as pc:
        sync(StorePeer(pc), StorePeer(hub), OwnerTable("server"))

        assert pc.purged(blob_id) is True
        assert pc.get(OPERATOR, object_id, blobs="fetch").purged == frozenset({"body.md"})


def test_only_the_operator_purges_and_only_a_blob_that_exists(hub: Store) -> None:
    _, blob_id = planted(hub)

    with pytest.raises(LibraryRefused, match=r"^purge_refused:"):
        hub.purge(Principal("agent", "alice"), blob_id, "a vault code")
    with pytest.raises(LibraryRefused, match=r"^purge_refused:"):
        hub.purge(OPERATOR, blob_id, " ")
    with pytest.raises(LibraryRefused, match=r"^not_found:"):
        hub.purge(OPERATOR, "sha256:" + "0" * 64, "a vault code")
