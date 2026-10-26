"""The server's bucket push: one more copy than the server (AD-16; F14, F24; DATA-PLAN DR2D).

With a bucket remote the server pushes its Library to it after each commit batch, through rclone,
which copies only what the bucket lacks. The remote is a name rclone knows on the server
(`[bucket] remote` in `hub.toml`, G-R2); QMX never holds a bucket credential. Without one the push
is a no-op that says so in words: "no bucket, one copy on the server". `view()` is that sentence as
a read, so the storage view repeats it instead of leaving the one copy unsaid.

What travels is the evidence a restore rebuilds from (`qmx_library.store`'s own layout): `objects/`,
`edges/` and `annotations/` whole, the two ref files `refs/log.jsonl` and `refs/epoch.json`, and the
durable blobs. A cache copy under `blobs/fetched/` may be evicted and is never pushed, a transient
blob under `blobs/transient/` lives on one store by definition, `blobs/tombstones/` is rebuilt from
the purge refs, and the transient claims in `refs/claims.json` are never bucketed (AD-10, AD-24).

A batch is the commits that land between two pushes. Every commit calls `note`, and a burst is
pushed once when it settles: the push never runs twice over in a second, and no commit is waited on
for a bucket that is not there.

A series that cannot be downloaded again has one more thing to lose: the open month, whose file
sits under a fixed name while rows still arrive. `keep_series` registers it, and every push
copies it to `<remote>:<prefix>/series/<name>.parquet` — the same fixed name each batch, so the
newer file overwrites the older one. A series that can be re-downloaded is not registered and
costs the bucket nothing.
"""

from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from qmx_library.store import Store

REMOTE_KEY: Final = "remote"
"""The `[bucket]` row of `hub.toml` that names the rclone remote, never a path or a credential."""
PREFIX: Final = "library"
"""The folder on the remote: `<remote>:library/...`."""
NO_BUCKET: Final = "no bucket, one copy on the server"
READ_S: Final = 2.0
"""How long a copy count waits on one bucket folder before it counts no copy there."""
FRAMES: Final = ("objects", "edges", "annotations")
REF_FILES: Final = ("refs/log.jsonl", "refs/epoch.json")
CACHE_DIRS: Final = ("fetched/**", "transient/**", "tombstones/**")
"""The blob folders a push leaves behind: a cache copy, a transient blob, a purge tombstone."""
SERIES_DIR: Final = "series"
"""Where a series' open month lands on the remote, under a fixed name."""
BATCH: Final = 1
"""Commits in one batch (Claude's default): every commit is pushed, and the settle below folds a
burst into one rclone run."""


@dataclass(frozen=True, slots=True)
class Pushed:
    """One push: what it ran, what it said, and whether it reached the bucket."""

    remote: str | None
    calls: tuple[tuple[str, ...], ...] = ()
    said: str = ""
    at: str = ""
    failed: bool = False

    @property
    def ok(self) -> bool:
        """True when the push happened or said plainly that there is no bucket."""
        return not self.failed


def run_rclone(call: Sequence[str]) -> str:
    """One rclone command; a non-zero exit raises with its own last line."""
    done = subprocess.run(call, capture_output=True, check=False, text=True)
    if done.returncode:
        tail = (done.stderr or done.stdout).strip().splitlines()
        raise RuntimeError(tail[-1] if tail else f"rclone exited {done.returncode}")
    return done.stdout


@dataclass(slots=True)
class Bucket:
    """The bucket push for one store. `remote` is the rclone remote's name, or None."""

    store: Store
    remote: str | None
    prefix: str = PREFIX
    batch: int = BATCH
    runner: Callable[[Sequence[str]], str] = run_rclone
    wall: Callable[[], datetime] = lambda: datetime.now(UTC)
    pending: int = 0
    last: Pushed | None = field(default=None)
    series: dict[str, Path] = field(default_factory=dict[str, Path])
    """The open month of each non-redownloadable series, under the fixed name it is pushed as."""
    pushed: set[str] = field(default_factory=set[str])
    """The durable blobs a push that succeeded carried: the store held them before it ran. A blob
    that landed after the last good push is not here, so it counts one copy until the next."""

    @classmethod
    def from_home(
        cls,
        store: Store,
        home: Path,
        *,
        runner: Callable[[Sequence[str]], str] = run_rclone,
    ) -> Bucket:
        """The configuration the server's own `hub.toml` carries, read once at start."""
        return cls(store, remote=remote_of(home), runner=runner)

    def note(self) -> bool:
        """One commit landed. True when this one completes a batch worth pushing."""
        self.pending += 1
        return self.due

    def keep_series(self, name: str, path: Path) -> None:
        """Register the open file of a non-redownloadable series for every later batch.

        ``name`` is the fixed name it lands under: the series key and the month, so each
        batch overwrites the same object rather than piling up a file per commit.
        """
        self.series[name] = path

    @property
    def due(self) -> bool:
        return self.pending >= self.batch

    def push(self) -> Pushed:
        """Push the batch. Without a remote it says so and fails nothing (G-R2 closed)."""
        self.pending = 0
        at = self.wall().isoformat()
        if not self.remote:
            self.last = Pushed(None, said=NO_BUCKET, at=at)
            return self.last
        carried = {b for b in self.store.blob_ids() if self.store.blob_class(b) == "born"}
        calls = [self._call(item) for item in (*FRAMES, "blobs", *REF_FILES)]
        calls.extend(self._series_calls())
        try:
            for call in calls:
                self.runner(call)
        except (OSError, RuntimeError) as error:
            self.last = Pushed(
                self.remote, tuple(calls), f"the bucket push failed: {error}", at, failed=True
            )
            return self.last
        self.pushed |= carried
        self.last = Pushed(self.remote, tuple(calls), f"pushed to {self.target()}", at)
        return self.last

    def target(self) -> str:
        return f"{self.remote}:{self.prefix}"

    def view(self) -> dict[str, object]:
        """The storage view's row: two copies only once a push succeeded and no commit has landed
        since; a configured bucket that never pushed, failed its last push or is behind is one."""
        current = self.remote is not None and self.last is not None and self.last.ok
        copies = 2 if current and self.pending == 0 else 1
        if self.remote is None:
            said = NO_BUCKET
        elif copies == 2:
            said = f"second copy on {self.target()}"
        else:
            said = f"one copy on the server until a push to {self.target()} succeeds"
        return {
            "bucket": self.remote,
            "copies": copies,
            "said": said,
            "last": None if self.last is None else self.last.said,
            "pending": self.pending,
            "pushed_blobs": len(self.pushed),
        }

    def _series_calls(self) -> list[tuple[str, ...]]:
        """One copyto per open series file: the fixed name on the remote is overwritten."""
        return [
            (
                "rclone",
                "copyto",
                str(path),
                f"{self.target()}/{SERIES_DIR}/{name}.parquet",
                "--checksum",
                "--stats=0",
            )
            for name, path in sorted(self.series.items())
        ]

    def _call(self, name: str) -> tuple[str, ...]:
        source = self.store.root / name
        if name in REF_FILES:
            return (
                "rclone",
                "copyto",
                str(source),
                f"{self.target()}/{name}",
                "--checksum",
                "--stats=0",
            )
        excludes: list[str] = []
        for pattern in CACHE_DIRS if name == "blobs" else ():
            excludes += ["--exclude", pattern]
        return (
            "rclone",
            "copy",
            str(source),
            f"{self.target()}/{name}",
            "--checksum",
            "--stats=0",
            *excludes,
        )


def remote_of(home: Path) -> str | None:
    """The rclone remote the server's `hub.toml` names under `[bucket] remote`, if any."""
    import tomllib  # noqa: PLC0415 (only a server that has a home reads it)

    path = home / "hub.toml"
    if not path.exists():
        return None
    with path.open("rb") as handle:
        document = cast("dict[str, object]", tomllib.load(handle))
    found = document.get("bucket")
    if not isinstance(found, dict):
        return None
    remote = cast("dict[str, object]", found).get(REMOTE_KEY)
    return None if remote is None else str(remote) or None


def holds(root: Path, blob_id: str, size: int, *, within: float = READ_S) -> bool:
    """Whether the bucket copy at `root` really holds this blob, at its full size.

    A real read on the folder, in either layout `purge.bucket_tombstone` knows. A read that fails,
    or that runs past `within` on a slow or hung mount, answers False: one copy, never an error.
    """
    hexdigest = blob_id.removeprefix("sha256:")
    blobs = root / "blobs"
    places = (blobs / hexdigest[:2] / hexdigest[2:4] / hexdigest, blobs / hexdigest)
    found: list[bool] = []

    def read() -> None:
        for place in places:
            try:
                if place.is_file() and place.stat().st_size == size:
                    found.append(True)
                    return
            except OSError:
                continue

    reader = threading.Thread(target=read, name="qmx-bucket-read", daemon=True)
    reader.start()
    reader.join(within)
    return bool(found)
