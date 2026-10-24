"""The Hub counts real copies per blob (WU7, DR7, G-R2): this store, plus one only when a real
read finds the blob in a bucket. A bucket that is configured but behind, or slow, adds nothing."""

from __future__ import annotations

import shutil
import time
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

import pytest
from qmx_engine.ledger import redact
from qmx_library.store import Store

from qmx_hub import bucket as bucket_module
from qmx_hub.bucket import Bucket, holds
from qmx_hub.server import Hub

DATA = b"a file the server made"
BLOB = f"sha256:{sha256(DATA).hexdigest()}"


def landed(store: Store) -> str:
    upload = store.begin_upload("u-1")
    upload.write(DATA)
    return upload.finish()


def test_a_configured_bucket_answers_one_copy_until_a_push_carries_the_blob(
    tmp_path: Path,
) -> None:
    def rclone(call: Sequence[str]) -> str:
        return ""

    with Store.open(tmp_path / "library", redactor=redact, name="server") as store:
        pushing = Bucket(store, remote="scratch", runner=rclone)
        hub = Hub(store, bucket=pushing)
        blob_id = landed(store)
        before = (hub.copies(blob_id), pushing.view()["copies"])
        pushing.push()
        after = (hub.copies(blob_id), pushing.view()["copies"])

    assert blob_id == BLOB
    assert (before, after) == ((1, 1), (2, 2))


def test_a_folder_bucket_counts_only_a_full_copy_of_the_blob(tmp_path: Path) -> None:
    folder = tmp_path / "bucket"
    with Store.open(tmp_path / "library", redactor=redact, name="server") as store:
        hub = Hub(store, buckets=(folder,))
        blob_id = landed(store)
        hexdigest = blob_id.removeprefix("sha256:")
        shard = folder / "blobs" / hexdigest[:2] / hexdigest[2:4]
        empty = hub.copies(blob_id)
        shard.mkdir(parents=True)
        (shard / hexdigest).write_bytes(DATA[:5])
        partial = hub.copies(blob_id)
        held = store.root / "blobs" / hexdigest[:2] / hexdigest[2:4] / hexdigest
        shutil.copyfile(held, shard / hexdigest)
        full = hub.copies(blob_id)

    assert (empty, partial, full) == (1, 1, 2)


def test_a_bucket_read_that_hangs_counts_no_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def hung(self: Path) -> bool:
        time.sleep(2)
        return True

    monkeypatch.setattr(bucket_module.Path, "is_file", hung)
    began = time.monotonic()

    found = holds(tmp_path, BLOB, len(DATA), within=0.2)

    assert found is False
    assert time.monotonic() - began < 1
