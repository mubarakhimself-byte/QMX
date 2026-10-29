"""QMX's own monthly upkeep of a storage (design 06 section 6): the re-pack and the check. The
drill is `restore.drill`.

The re-pack lets go of every pack no kept copy needs and rewrites a pack whose unused share is
past `repack_past`, or that holds a damaged file, in four steps: new packs, one merged index
naming every pack a kept copy uses, the index files it replaces removed, then the old packs. A
re-pack killed after any step leaves every index naming only packs that exist. The check reads
every index file and every copy's list, then reads back a slice of the packs, a different slice
each month. A pack's slice follows from its name, which never changes, so every pack is read
within `check_slice` months however packs come and go; a file whose bytes are damaged goes on the
storage's bad list. His lines name files by their path in `data/`, never a pack or a hash.
"""

from __future__ import annotations

import math
import shutil
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

from qmx_home.backup.repository import Packed, Pruned, pack_list, unpack
from qmx_home.files import long_path


@dataclass(frozen=True, slots=True)
class Checked:
    """What one check found."""

    where: str
    packs: int
    """Packs read back."""
    files: int
    damaged: tuple[str, ...]
    """Each damaged file's path in `data/`, as a kept copy names it."""
    torn: tuple[str, ...]
    """Index files and copies whose list is not whole."""

    @property
    def line(self) -> str:
        read = f"the check read back {_count(self.files, 'stored file')} of {self.where}"
        if not self.damaged and not self.torn:
            return f"{read}, and every one held its bytes"
        found = [
            *(f"{d} is damaged and goes on the list of damaged files" for d in self.damaged),
            *(f"{t} is not whole" for t in self.torn),
        ]
        return f"{read}: {'; '.join(found)}; the next round sends each damaged file again"


def repack(
    repo: Packed,
    *,
    past: float,
    per_run: int | None,
    safety: timedelta,
    now: datetime | None = None,
    step: Callable[[str], None] | None = None,
) -> Pruned:
    """One re-pack of `repo`. Writes nothing while another job holds the storage: the caller
    holds the storage's lock."""
    return repo.prune(
        safety=safety, now=now or datetime.now(UTC), past=past, per_run=per_run, step=step
    )


def check(repo: Packed, *, slice: int, month: int, work: Path) -> Checked:
    """Read every index file and copy, then read back the `month`th slice of the packs (a
    `slice`th of them, rounded up, at least one) in `work`, which this removes."""
    repo.refresh()
    held = repo.index()
    whole, torn = repo.manifests()
    paths = {e.sha256: e.path for copy in whole.values() for e in copy.entries}
    chosen = _slice(sorted(repo.packs()), slice, month)
    damaged: list[str] = []
    files = 0
    folder = work / f"check-{uuid.uuid4().hex[:8]}"
    long_path(folder).mkdir(parents=True, exist_ok=True)
    try:
        for name in chosen:
            path = repo.local_pack(name)
            listed = pack_list(path)
            named = [
                (sha, at)
                for sha, places in held.where.items()
                for at in places
                if at.pack == name and (sha, name) not in held.bad
            ]
            if listed is None:
                for sha, _ in named:
                    repo.mark_bad(sha, pack=name)
                    damaged.append(paths.get(sha, UNUSED))
                continue
            for sha, at in named:
                target = folder / uuid.uuid4().hex
                got = unpack(path, at, target)
                long_path(target).unlink(missing_ok=True)
                files += 1
                if got != sha:
                    repo.mark_bad(sha, pack=name)
                    damaged.append(paths.get(sha, UNUSED))
    finally:
        repo.let_go()
        shutil.rmtree(long_path(folder), ignore_errors=True)
    return Checked(
        repo.where,
        len(chosen),
        files,
        tuple(dict.fromkeys(damaged)),
        (
            *(f"a list of where files are kept ({name})" for name in held.torn),
            *(f"the copy {stamp}" for stamp in torn),
        ),
    )


UNUSED: Final = "a stored file no kept copy uses"


def _slice(packs: Sequence[str], slice: int, month: int) -> list[str]:
    """The packs to read back in `month`: every pack whose name falls in this month's slice,
    topped up from the next slices to a `slice`th of them, rounded up, at least one."""
    width = max(slice, 1)
    count = max(1, math.ceil(len(packs) / width)) if packs else 0
    after = sorted(packs, key=lambda name: ((int(name[:8], 16) - month) % width, name))
    own = sum(1 for name in packs if (int(name[:8], 16) - month) % width == 0)
    return after[: max(count, own)]


def _count(count: int, word: str) -> str:
    return f"{count:,} {word}" if count == 1 else f"{count:,} {word}s"
