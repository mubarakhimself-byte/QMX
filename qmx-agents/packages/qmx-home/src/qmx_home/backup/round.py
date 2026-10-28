"""One round: a copy of `data/` into This PC's copies, sent to every storage that is due
(design 06 sections 4 and 5).

A round runs under `backups/backups.lock`, one at a time per QMX folder. It first removes what a
killed round left, makes one copy (`snapshot.make`) of every class some place keeps, writes This
PC's part of it (when This PC is due) unless nothing changed, then sends each due storage its own
part: the files its pool lacks, `backup.toml`, and the manifest last. Only then does it thin each
place by its keep rule and sweep its pool. With `[backup] on = false` a round copies nothing and
deletes nothing. Every round is one line in `backups/backups.jsonl`, which is also the record the
fork guard and `due` read: no other state file is kept.
"""

from __future__ import annotations

import os
import re
import shutil
import time as clock
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Final, Literal, cast

from qmx_home import Label, Layout
from qmx_home.backup.keep import kept, released, when
from qmx_home.backup.plan import Plan, PlanRefused, Storage, same_drive, storage_root
from qmx_home.backup.repository import (
    ABOUT,
    Entry,
    FolderRepository,
    Manifest,
    Mismatch,
    Unreadable,
)
from qmx_home.backup.snapshot import (
    Changing,
    NoRoom,
    RoadLease,
    library_kinds,
    make,
    needs_kinds,
)
from qmx_home.backup.snapshot import only as part_for
from qmx_home.classes import SENT, Class
from qmx_home.files import floor_of, hold, plain
from qmx_home.versions import log_line, log_lines

LOCK: Final = "backups.lock"
QUICK: Final = "quick"
STAMP: Final = "%Y%m%dT%H%M%S%fZ"
_STAMP: Final = re.compile(r"\d{8}T\d{12}Z")
OFF: Final = (
    "Sync to my storage is off in Settings, so QMX made no copy and deleted none; turn it on to "
    "copy again"
)

type Result = Literal["copied", "unchanged", "refused", "skipped"]


@dataclass(frozen=True, slots=True)
class Placed:
    """What one round did at one place, with its one line for him."""

    id: str
    where: str
    result: Result
    line: str
    key: str = QUICK
    stamp: str | None = None
    """The copy the place holds newest after the round."""
    files: int = 0
    bytes: int = 0
    seconds: float = 0.0
    partial: bool = False
    """The copy lacks a file it should hold; its manifest says which."""
    other_disk: bool = False
    """The place is a storage on another disk than the QMX folder's."""

    def document(self) -> dict[str, object]:
        return {
            "id": self.id,
            "key": self.key,
            "where": self.where,
            "result": self.result,
            "line": self.line,
            "stamp": self.stamp,
            "files": self.files,
            "bytes": self.bytes,
            "seconds": round(self.seconds, 3),
            "partial": self.partial,
            "other_disk": self.other_disk,
        }


@dataclass(frozen=True, slots=True)
class RoundReport:
    stamp: str
    why: str
    places: tuple[Placed, ...]
    seconds: float

    @property
    def result(self) -> Result:
        """`refused` when a place refused, `copied` when a place got a copy, else `unchanged`."""
        results = {place.result for place in self.places}
        for result in ("refused", "copied"):
            if result in results:
                return cast("Result", result)
        return "unchanged"

    @property
    def lines(self) -> tuple[str, ...]:
        return tuple(place.line for place in self.places)

    def document(self) -> dict[str, object]:
        return {
            "kind": "round",
            "stamp": self.stamp,
            "why": self.why,
            "result": self.result,
            "seconds": round(self.seconds, 3),
            "bytes": sum(place.bytes for place in self.places),
            "places": [place.document() for place in self.places],
        }


def due(last: datetime | None, now: datetime, every: timedelta, at: time) -> bool:
    """Whether a place copied last at `last` is due at `now`. Under a day: `every` after the
    last copy. A day or more: at the first `at` (local time, in `now`'s zone) once `every` less a
    day has passed since the last copy. A PC that was off is due at its next start."""
    if last is None:
        return True
    last = last.astimezone(now.tzinfo)
    if every < timedelta(days=1):
        return now - last >= every
    after = last + every - timedelta(days=1)
    slot = datetime.combine(after.date(), at, tzinfo=now.tzinfo)
    if slot <= after:
        slot += timedelta(days=1)
    return now >= slot


def run_round(
    layout: Layout,
    plan: Plan,
    *,
    now: datetime,
    floor: int,
    only: str | None = None,
    asked: bool = False,
    progress: Callable[[str], None] | None = None,
    road_lease: RoadLease | None = None,
) -> RoundReport:
    """One round at `now`: This PC's copies when due or `asked` (he asked for the round), and
    every storage that is due (or only the storage `only`, due or not). `floor` is the local
    floor on the folder's drive, which This PC's copies never cross. `road_lease` holds a mini
    app's road lease while its `road/` is copied. Raises Busy while another round holds the lock,
    and PlanRefused when `only` names no storage."""
    return _round(
        layout,
        plan,
        now=now,
        floor=floor,
        only=only,
        asked=asked,
        progress=progress,
        road_lease=road_lease,
    )


def quick(
    layout: Layout,
    why: str,
    *,
    floor: int,
    leave_out: Sequence[str] = (),
    now: datetime | None = None,
    road_lease: RoadLease | None = None,
) -> RoundReport:
    """One copy of every sent class into This PC's copies at once, tagged `why`, written even
    when nothing changed (a copy taken before an upgrade). It thins nothing: the next round thins
    by his own keep rule. Raises Busy while a round holds the lock."""
    return _round(
        layout,
        Plan(leave_out=tuple(leave_out)),
        now=now or datetime.now(UTC),
        floor=floor,
        why=why,
        force=True,
        road_lease=road_lease,
    )


def carry_on(layout: Layout, storage: Storage) -> str:
    """His choice to keep sending to a storage the fork guard refused: the storage's newest copy
    is taken as this folder's own from now on. The line to show."""
    repo = FolderRepository(storage_root(cast("Path", storage.path), _label(layout).home_id))
    stamps = repo.copies()
    log_line(
        layout,
        {
            "kind": "carry-on",
            "id": storage.id,
            "key": place_key(repo),
            "stamp": stamps[-1] if stamps else None,
        },
    )
    return f"QMX carries on sending this folder's copies to {repo.where}"


def _round(
    layout: Layout,
    plan: Plan,
    *,
    now: datetime,
    floor: int,
    why: str = "round",
    force: bool = False,
    only: str | None = None,
    asked: bool = False,
    progress: Callable[[str], None] | None = None,
    road_lease: RoadLease | None = None,
) -> RoundReport:
    started = clock.monotonic()
    told = progress or _quiet
    busy = f"a backup round is already running for {layout.root}; it ends by itself"
    with hold(layout.backups / LOCK, busy):
        quick_repo = FolderRepository(layout.backups / QUICK)
        quick_repo.clean()
        log = log_lines(layout)
        home_id = _label(layout).home_id
        if only is not None and not any(s.id == only for s in plan.folders):
            raise PlanRefused(f"there is no storage {only!r} in Settings")
        if not plan.on and not force:
            places = (
                Placed(QUICK, quick_repo.where, "skipped", OFF),
                *(
                    Placed(s.id, plain(s.path), "skipped", OFF, storage_key(s, home_id))
                    for s in plan.folders
                ),
            )
            return _logged(layout, RoundReport(_stamp(now, (quick_repo,), log), why, places, 0.0))
        chosen = [
            storage
            for storage in plan.folders
            if (storage.id == only)
            or (
                only is None
                and storage.policy.on
                and due(
                    _last(log, storage_key(storage, home_id)),
                    now,
                    storage.policy.interval,
                    storage.policy.at,
                )
            )
        ]
        pc_due = (
            force
            or asked
            or only is not None
            or due(_last(log, QUICK), now, plan.pc.interval, plan.pc.at)
        )
        previous = _newest(quick_repo)
        repos = [quick_repo, *(_repository(s, home_id) for s in chosen)]
        stamp = _stamp(now, repos, log)
        saves = [plan.pc.save, *(s.policy.save for s in chosen)]
        union: tuple[Class, ...] = tuple(c for c in SENT if any(c in save for save in saves))
        kinds = library_kinds(layout.data) if needs_kinds(*saves) else {}
        try:
            copy = make(
                layout,
                previous=previous,
                stamp=stamp,
                why=why,
                leave_out=plan.leave_out,
                save=union,
                kinds=kinds,
                keep_free=floor,
                progress=told,
                road_lease=road_lease,
            )
        except (NoRoom, Changing) as refused:
            places = (
                Placed(QUICK, quick_repo.where, "refused", str(refused)),
                *(
                    Placed(
                        s.id,
                        plain(s.path),
                        "skipped",
                        f"no copy was made, so none went to {plain(s.path)}",
                        storage_key(s, home_id),
                    )
                    for s in chosen
                ),
            )
            return _logged(layout, RoundReport(stamp, why, places, clock.monotonic() - started))
        if pc_due:
            pc_copy = part_for(copy, plan.pc.save, kinds)
            placed = [_quick_place(quick_repo, pc_copy, previous, force, started)]
        else:
            line = (
                f"This PC's copies are made every {plan.pc.every}; the newest in "
                f"{quick_repo.where} is not that old yet"
            )
            placed = [Placed(QUICK, quick_repo.where, "skipped", line)]
        for storage in chosen:
            told(f"sending the copy to {plain(storage.path)}")
            part = part_for(copy, storage.policy.save, kinds)
            placed.append(_send(layout, plan, storage, part, quick_repo, log, home_id))
        if not force and any(place.result == "copied" for place in placed):
            placed[0] = _thin_quick(quick_repo, plan, log, placed)
            _thin_pre_change(layout, log, placed)
        return _logged(layout, RoundReport(stamp, why, tuple(placed), clock.monotonic() - started))


def _quick_place(
    repo: FolderRepository,
    copy: Manifest,
    previous: Manifest | None,
    force: bool,
    started: float,
) -> Placed:
    if not force and previous is not None and previous.files == copy.files:
        line = f"nothing changed since the last copy; This PC's copies in {repo.where} hold it"
        return Placed(
            QUICK, repo.where, "unchanged", line, stamp=previous.stamp, partial=_partial(previous)
        )
    repo.put_copy(copy)
    old: frozenset[tuple[str, str]] = frozenset() if previous is None else previous.files
    new = [e for e in copy.entries if e.at == "pool" and (e.path, e.sha256) not in old]
    size = sum(e.size for e in new)
    line = (
        f"copied {_count(len(new), 'changed file')} ({_mb(size)}) into This PC's copies in "
        f"{repo.where}"
    ) + _lacks(cast("list[str]", copy.header.get("unread", [])))
    return Placed(
        QUICK,
        repo.where,
        "copied",
        line,
        stamp=copy.stamp,
        files=len(new),
        bytes=size,
        seconds=clock.monotonic() - started,
        partial=_partial(copy),
    )


def _send(
    layout: Layout,
    plan: Plan,
    storage: Storage,
    copy: Manifest,
    quick_repo: FolderRepository,
    log: Sequence[Mapping[str, object]],
    home_id: str,
) -> Placed:
    """Send one copy to one folder storage. A file whose bytes do not match its hash is left out
    of the storage's copy by name, and the copy is marked partial; the rest is sent. The place's
    result is logged as soon as its manifest is up, so a round killed later never makes this
    folder's own copy look like another folder's."""
    started = clock.monotonic()
    path = cast("Path", storage.path)
    repo = _repository(storage, home_id)
    key, where = place_key(repo), repo.where
    apart = not same_drive(storage, layout)

    def placed(
        result: Result,
        line: str,
        *,
        stamp: str | None = None,
        files: int = 0,
        size: int = 0,
        partial: bool = False,
    ) -> Placed:
        seconds = clock.monotonic() - started
        return Placed(
            storage.id, where, result, line, key, stamp, files, size, seconds, partial, apart
        )

    anchor = Path(path.anchor or "/")
    if not anchor.exists():
        return placed(
            "skipped",
            f"{plain(path)} is not there (is its drive plugged in?); the copy waits for it",
        )
    try:
        refusal = _guard(log, key, repo)
        if refusal is not None:
            return placed("refused", refusal)
        repo.clean()
        newest = _newest(repo)
        if (
            newest is not None
            and _intended(newest) == copy.files
            and all(repo.pool_has(entry.sha256) for entry in newest.entries)
        ):
            if repo.about() is None:
                repo.set_about(_about(home_id, layout, newest))
            return placed(
                "unchanged",
                f"nothing changed since the last copy to {where}",
                stamp=newest.stamp,
                partial=_partial(newest),
            )
        unique = {entry.sha256: entry for entry in copy.entries}
        missing = [e for e in unique.values() if not repo.pool_has(e.sha256)]
        need = sum(e.size for e in missing) + len(copy.dump())
        room = repo.room()
        keep_free = floor_of(plan.floor_gb, room)
        if room - need < keep_free:
            return placed(
                "refused",
                f"{where} needs {_mb(need)} for this copy and its drive has {_mb(room)} free; "
                f"QMX keeps at least {_whole_mb(keep_free)} free there, so nothing was written. "
                "Free some space on it, or connect another storage in Settings",
            )
        written, damaged = 0, set[str]()
        for entry in missing:
            source = (
                quick_repo.pool_path(entry.sha256)
                if entry.at == "pool"
                else layout.data / entry.path
            )
            try:
                written += repo.put_pool(entry.sha256, source)
            except Mismatch:
                damaged.add(entry.sha256)
        skipped = [e for e in copy.entries if e.sha256 in damaged]
        held = _without(copy, skipped)
        repo.set_about(_about(home_id, layout, held))
        repo.put_copy(held)
        log_line(layout, {"kind": "sent", "id": storage.id, "key": key, "stamp": held.stamp})
        thinned = _thin(repo, storage, log, key)
    except OSError as failed:
        return placed(
            "refused", f"the copy to {where} stopped: {_why(failed)}; the next round tries again"
        )
    line = f"copied {_count(len(missing) - len(damaged), 'file')} ({_mb(written)}) to {where}"
    if not apart:
        line += "; it is on the same drive as the QMX folder, so it does not survive that disk"
    if thinned:
        line += f"; {thinned}"
    line += _lacks(
        [
            *cast("list[str]", copy.header.get("unread", [])),
            *(f"{e.path} ({DAMAGED})" for e in skipped),
        ]
    )
    return placed(
        "copied",
        line,
        stamp=held.stamp,
        files=len(missing) - len(damaged),
        size=written,
        partial=_partial(held),
    )


DAMAGED: Final = (
    "it does not hold the bytes its name says: it changed while it was copied, or it is damaged"
)


def _without(copy: Manifest, skipped: Sequence[Entry]) -> Manifest:
    """The copy a storage holds: every file in its pool, less the files it could not take,
    which its header names, so the copy reads as partial and a later round knows what it meant
    to hold."""
    if not skipped:
        return copy.pooled()
    gone = {entry.path for entry in skipped}
    pooled = copy.pooled(partial=True, skipped=[[entry.path, entry.sha256] for entry in skipped])
    return Manifest(pooled.header, tuple(e for e in pooled.entries if e.path not in gone))


def _intended(manifest: Manifest) -> frozenset[tuple[str, str]]:
    """The files a copy meant to hold: those it holds and those its header says it lacks."""
    skipped = cast("list[list[str]]", manifest.header.get("skipped", []))
    return manifest.files | {(path, sha) for path, sha in skipped}


def _partial(manifest: Manifest) -> bool:
    return manifest.header.get("partial") is True


def _lacks(missing: Sequence[str]) -> str:
    if not missing:
        return ""
    return f"; this copy lacks {_count(len(missing), 'file')}: {', '.join(missing)}"


def _about(home_id: str, layout: Layout, copy: Manifest) -> dict[str, str]:
    """`backup.toml`: which folder sends here, and its newest copy."""
    return {
        "home_id": home_id,
        "folder": str(layout.root),
        "last_copy": copy.stamp,
        "written_by": str(copy.header.get("release", "")),
    }


def _guard(log: Sequence[Mapping[str, object]], key: str, repo: FolderRepository) -> str | None:
    """Why a round must not send to this place (E-S7): another QMX folder with this one's id
    sent there since this one last did, or a place copied to before lost its `backup.toml`,
    which is another disk on the same letter. His carry-on clears either."""
    events = _events(log, key)
    stamps = repo.copies()
    newest = stamps[-1] if stamps else None
    carried = bool(events) and events[-1] == ("carry-on", newest)
    if any(kind == "sent" for kind, _ in events) and repo.about() is None and not carried:
        return (
            f"{repo.where} is not the place QMX copied to before: its {ABOUT} is missing, so this "
            "may be another disk on the same drive letter. Plug in the disk QMX copied to, or "
            "carry on to copy there anyway"
        )
    ours = events[-1][1] if events else None
    if newest is not None and newest != ours:
        try:
            head = repo.manifest(newest).header
            made = f"{head.get('machine')} ({head.get('folder')})"
        except Unreadable:
            made = "another QMX folder"
        return (
            f"{repo.where} holds a copy another QMX folder made since this one last sent there: "
            f"the newest, {newest}, is from {made}. Carry on to keep sending this folder's copies "
            "there, or pick another storage"
        )
    return None


def _events(log: Sequence[Mapping[str, object]], key: str) -> list[tuple[str, str | None]]:
    """What this folder did at one place, oldest first: copies it sent (each logged as its
    manifest went up, and again in its round's line) or found unchanged, restores from it, and
    his carry-ons."""
    found: list[tuple[str, str | None]] = []
    for line in log:
        kind = line.get("kind")
        if kind == "round":
            for place in cast("list[dict[str, object]]", line.get("places", [])):
                if place.get("key") == key and place.get("result") in ("copied", "unchanged"):
                    found.append(("sent", cast("str | None", place.get("stamp"))))
        elif kind in ("sent", "carry-on", "restored") and line.get("key") == key:
            found.append((str(kind), cast("str | None", line.get("stamp"))))
    return found


def _last(log: Sequence[Mapping[str, object]], key: str) -> datetime | None:
    """When the place last got a copy or was found unchanged."""
    for line in reversed(log):
        if line.get("kind") == "sent" and line.get("key") == key:
            return when(str(line["stamp"]))
        if line.get("kind") != "round":
            continue
        for place in cast("list[dict[str, object]]", line.get("places", [])):
            if place.get("key") == key and place.get("result") in ("copied", "unchanged"):
                return when(str(line["stamp"]))
    return None


def _drilled(log: Sequence[Mapping[str, object]], key: str) -> str | None:
    """The newest copy at a place that passed a drill."""
    for line in reversed(log):
        if line.get("kind") == "drill" and line.get("key") == key and line.get("passed") is True:
            return cast("str | None", line.get("stamp"))
    return None


def _thin(
    repo: FolderRepository, storage: Storage, log: Sequence[Mapping[str, object]], key: str
) -> str:
    """Drop the copies the keep rule lets go, then sweep the pool. Returns a line when the sweep
    could not run."""
    readable, whole = _readable(repo)
    keep = kept(list(readable), storage.policy.keep, drilled=_drilled(log, key), held=whole)
    for stamp in readable:
        if stamp not in keep:
            repo.drop(stamp)
    return repo.sweep().blocked or ""


def _readable(repo: FolderRepository) -> tuple[dict[str, Manifest], set[str]]:
    """The copies whose manifest is whole, oldest first, and the newest of them that is not
    partial. A copy whose manifest is not whole is never dropped, and neither is the newest
    complete copy, so copies that lack a file never thin away the last one that has them all."""
    readable: dict[str, Manifest] = {}
    for stamp in repo.copies():
        try:
            readable[stamp] = repo.manifest(stamp)
        except Unreadable:
            continue
    complete = [stamp for stamp, manifest in readable.items() if not _partial(manifest)]
    return readable, set(complete[-1:])


def _thin_quick(
    repo: FolderRepository,
    plan: Plan,
    log: Sequence[Mapping[str, object]],
    placed: Sequence[Placed],
) -> Placed:
    elsewhere = _copies_elsewhere(log, placed)
    readable, held = _readable(repo)
    for stamp, manifest in readable.items():
        if manifest.header.get("why") == "before-upgrade" and not released(when(stamp), elsewhere):
            held.add(stamp)
    keep = kept(list(readable), plan.pc.keep, drilled=_drilled(log, QUICK), held=held)
    for stamp in readable:
        if stamp not in keep:
            repo.drop(stamp)
    blocked = repo.sweep().blocked
    first = placed[0]
    if blocked is None:
        return first
    return replace(first, line=f"{first.line}; {blocked}")


def _thin_pre_change(
    layout: Layout, log: Sequence[Mapping[str, object]], placed: Sequence[Placed]
) -> None:
    """Remove each store's pre-change copy (LF3's `backups/pre-*`) once a whole copy made after
    it reached a storage on another disk."""
    elsewhere = _copies_elsewhere(log, placed)
    for line in log:
        if line.get("kind") != "pre-change":
            continue
        folder = layout.root / str(line.get("path", ""))
        if (
            folder.parent != layout.backups
            or not folder.name.startswith("pre-")
            or not folder.is_dir()
        ):
            continue
        made = datetime.fromisoformat(str(line["at"]))
        if released(made, elsewhere):
            shutil.rmtree(folder)


def _copies_elsewhere(
    log: Sequence[Mapping[str, object]], placed: Sequence[Placed]
) -> list[datetime]:
    """When each whole copy that reached a storage on another disk was made."""
    rows = [
        place
        for line in log
        if line.get("kind") == "round"
        for place in cast("list[dict[str, object]]", line.get("places", []))
    ]
    rows += [p.document() for p in placed]
    return [
        when(str(row["stamp"]))
        for row in rows
        if row.get("id") != QUICK
        and row.get("result") == "copied"
        and row.get("other_disk") is True
        and row.get("partial") is not True
        and row.get("stamp")
    ]


def _newest(repo: FolderRepository) -> Manifest | None:
    """The newest copy whose manifest is whole."""
    for stamp in reversed(repo.copies()):
        try:
            return repo.manifest(stamp)
        except Unreadable:
            continue
    return None


def _stamp(
    now: datetime, repos: Sequence[FolderRepository], log: Sequence[Mapping[str, object]]
) -> str:
    """The copy's stamp: `now` in UTC, after the newest copy on every place it joins and after
    the last stamp in the backup log, so a clock moved back never makes this folder's own copy
    look like another folder's."""
    stamp = now.astimezone(UTC).strftime(STAMP)
    seen = [s for repo in repos for s in repo.copies()[-1:]]
    seen += [str(line["stamp"]) for line in log if _STAMP.fullmatch(str(line.get("stamp", "")))]
    latest = max(seen, default=None)
    if latest is not None and stamp <= latest:
        stamp = (when(latest) + timedelta(microseconds=1)).strftime(STAMP)
    return stamp


def place_key(repo: FolderRepository) -> str:
    """A place's key in the backup log: its folder, as the OS compares names."""
    return f"folder:{os.path.normcase(os.path.abspath(repo.root))}"


def storage_key(storage: Storage, home_id: str) -> str:
    return place_key(_repository(storage, home_id))


def _repository(storage: Storage, home_id: str) -> FolderRepository:
    return FolderRepository(storage_root(cast("Path", storage.path), home_id))


def _label(layout: Layout) -> Label:
    return Label.parse(layout.label.read_text(encoding="utf-8"))


def _quiet(_line: str) -> None:
    return None


def _logged(layout: Layout, report: RoundReport) -> RoundReport:
    log_line(layout, report.document())
    return report


def _count(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _mb(count: int) -> str:
    return f"{max(count, 0) / (1 << 20):,.1f} MB"


def _whole_mb(count: int) -> str:
    """As every floor refusal names the floor."""
    return f"{max(count, 0) / (1 << 20):,.0f} MB"


def _why(error: OSError) -> str:
    return f"{error.strerror or type(error).__name__}" + (
        f" ({plain(error.filename)})" if error.filename else ""
    )
