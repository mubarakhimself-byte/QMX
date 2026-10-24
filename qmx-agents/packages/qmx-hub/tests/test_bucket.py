"""The bucket push says plainly when there is no bucket, and names what it pushes otherwise
(Library AD-16, F14, F24; DATA-PLAN DR2D)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_library.store import Store

from qmx_hub.bucket import NO_BUCKET, Bucket, Pushed, remote_of


def open_store(root: Path) -> Store:
    return Store.open(root, redactor=redact, name="server")


class Recorder:
    def __init__(self, fail: str = "") -> None:
        self.calls: list[tuple[str, ...]] = []
        self.fail = fail

    def __call__(self, call: Sequence[str]) -> str:
        self.calls.append(tuple(call))
        if self.fail:
            raise RuntimeError(self.fail)
        return ""


def test_without_a_bucket_remote_the_push_says_so_and_fails_nothing(tmp_path: Path) -> None:
    recorder = Recorder()
    with open_store(tmp_path / "library") as store:
        bucket = Bucket(store, remote=None, runner=recorder)
        assert bucket.note() is True
        pushed = bucket.push()
        assert pushed == Pushed(None, (), NO_BUCKET, pushed.at)
        assert (pushed.ok, recorder.calls) == (True, [])
        assert bucket.view() == {
            "bucket": None,
            "copies": 1,
            "said": NO_BUCKET,
            "last": NO_BUCKET,
            "pending": 0,
        }


def test_the_push_copies_objects_refs_edges_and_durable_blobs_only(tmp_path: Path) -> None:
    recorder = Recorder()
    with open_store(tmp_path / "library") as store:
        bucket = Bucket(store, remote="scratch", runner=recorder)
        pushed = bucket.push()
        assert pushed.ok and pushed.remote == "scratch"
        assert pushed.said == "pushed to scratch:library"
        assert recorder.calls == [
            (
                "rclone",
                "copy",
                str(store.root / "objects"),
                "scratch:library/objects",
                "--checksum",
                "--stats=0",
            ),
            (
                "rclone",
                "copy",
                str(store.root / "edges"),
                "scratch:library/edges",
                "--checksum",
                "--stats=0",
            ),
            (
                "rclone",
                "copy",
                str(store.root / "annotations"),
                "scratch:library/annotations",
                "--checksum",
                "--stats=0",
            ),
            (
                "rclone",
                "copy",
                str(store.root / "blobs"),
                "scratch:library/blobs",
                "--checksum",
                "--stats=0",
                "--exclude",
                "fetched/**",
                "--exclude",
                "transient/**",
                "--exclude",
                "tombstones/**",
            ),
            (
                "rclone",
                "copyto",
                str(store.root / "refs" / "log.jsonl"),
                "scratch:library/refs/log.jsonl",
                "--checksum",
                "--stats=0",
            ),
            (
                "rclone",
                "copyto",
                str(store.root / "refs" / "epoch.json"),
                "scratch:library/refs/epoch.json",
                "--checksum",
                "--stats=0",
            ),
        ]


def test_a_bucket_that_refuses_is_recorded_and_does_not_stop_the_server(tmp_path: Path) -> None:
    recorder = Recorder(fail="connection refused")
    with open_store(tmp_path / "library") as store:
        bucket = Bucket(store, remote="scratch", runner=recorder)
        pushed = bucket.push()
        assert (pushed.ok, pushed.failed) == (False, True)
        assert pushed.said == "the bucket push failed: connection refused"
        assert bucket.view()["copies"] == 2


def test_commits_are_batched_and_the_remote_comes_from_the_servers_own_config(
    tmp_path: Path,
) -> None:
    home = tmp_path / "server-home"
    home.mkdir()
    assert remote_of(home) is None
    (home / "hub.toml").write_text('[bucket]\nremote = "qmx-r2"\n', encoding="utf-8")
    assert remote_of(home) == "qmx-r2"
    with open_store(tmp_path / "library") as store:
        bucket = Bucket.from_home(store, home, runner=Recorder())
        assert bucket.remote == "qmx-r2"
        assert bucket.batch == 1
        assert bucket.note() is True
        assert Bucket(store, remote=None, batch=3).note() is False
