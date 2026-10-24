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
"""

from __future__ import annotations

import subprocess
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
FRAMES: Final = ("objects", "edges", "annotations")
REF_FILES: Final = ("refs/log.jsonl", "refs/epoch.json")
CACHE_DIRS: Final = ("fetched/**", "transient/**", "tombstones/**")
"""The blob folders a push leaves behind: a cache copy, a transient blob, a purge tombstone."""
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
        calls = [self._call(item) for item in (*FRAMES, "blobs", *REF_FILES)]
        try:
            for call in calls:
                self.runner(call)
        except (OSError, RuntimeError) as error:
            self.last = Pushed(
                self.remote, tuple(calls), f"the bucket push failed: {error}", at, failed=True
            )
            return self.last
        self.last = Pushed(self.remote, tuple(calls), f"pushed to {self.target()}", at)
        return self.last

    def target(self) -> str:
        return f"{self.remote}:{self.prefix}"

    def view(self) -> dict[str, object]:
        """The storage view's row: where the second copy is, or the words saying there is none."""
        return {
            "bucket": self.remote,
            "copies": 1 if self.remote is None else 2,
            "said": NO_BUCKET if self.remote is None else f"second copy on {self.target()}",
            "last": None if self.last is None else self.last.said,
            "pending": self.pending,
        }

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
