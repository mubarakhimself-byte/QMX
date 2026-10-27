"""One backup round: a copy of `data/` into the quick undo, sent to every place that is due
(design 62 C2, Appendix D).

A round runs under `backups/backups.lock`, one at a time per QMX folder. It first removes what a
killed round left, makes one copy (`snapshot.make`), writes it to the quick undo unless nothing
changed, then sends it to each due target: the files its pool lacks, the sealed key copy when
there is one, `backup.toml`, and the manifest last. Only then does it thin each place by its keep
rule and sweep its pool. Every round is one line in `backups/backups.jsonl`, which is also the
record the fork guard and `due` read: no other state file is kept.
"""

from __future__ import annotations

import os
import shutil
import time as clock
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Final, Literal, cast

from qmx_home import Label, Layout
from qmx_home.backup.keep import kept, released, when
from qmx_home.backup.plan import Every, Plan, PlanRefused, Target, same_drive, target_root
from qmx_home.backup.repository import (
    ABOUT,
    Entry,
    FolderRepository,
    Manifest,
    Mismatch,
    Unreadable,
)
from qmx_home.backup.snapshot import Changing, NoRoom, make
from qmx_home.files import hold, plain
from qmx_home.versions import FLOOR_BYTES, log_line, log_lines

LOCK: Final = "backups.lock"
QUICK: Final = "quick"
SEALED: Final = "keys.sealed.json"
STAMP: Final = "%Y%m%dT%H%M%S%fZ"

type Result = Literal["copied", "unchanged", "refused", "skipped"]
type SealedKeys = Callable[[], tuple[bytes, str]]
"""The sealed key copy's bytes and a digest of what it seals; a changed digest makes a new copy
even when the data did not change (B7)."""


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


def due(last: datetime | None, now: datetime, every: Every, at: time) -> bool:
    """Whether a place copied last at `last` is due at `now`. Hourly: an hour after the last
    copy. Daily: once `at` (local time, in `now`'s zone) has passed since the last copy. Weekly:
    at the first `at` six days after the last copy. A PC that was off is due at its next
    start."""
    if last is None:
        return True
    last = last.astimezone(now.tzinfo)
    if every == "hour":
        return now - last >= timedelta(hours=1)
    after = last + timedelta(days=6) if every == "week" else last
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
    sealed_keys: SealedKeys | None = None,
    progress: Callable[[str], None] | None = None,
) -> RoundReport:
    """One round at `now`: the quick undo, and every target that is due (or only the target
    `only`, due or not). `floor` is the room the host keeps on the folder's drive; the quick
    undo never takes the drive below it or below 1 GiB. Raises Busy while another round holds
    the lock, and PlanRefused when `only` names no target."""
    return _round(
        layout, plan, now=now, floor=floor, only=only, sealed_keys=sealed_keys, progress=progress
    )


def quick(
    layout: Layout,
    why: str,
    *,
    floor: int,
    leave_out: Sequence[str] = (),
    now: datetime | None = None,
) -> RoundReport:
    """One copy into the quick undo at once, tagged `why`, written even when nothing changed
    (a copy taken before an upgrade). It thins nothing: the next round thins by his own keep
    rule. Raises Busy while a round holds the lock."""
    return _round(
        layout,
        Plan(leave_out=tuple(leave_out)),
        now=now or datetime.now(UTC),
        floor=floor,
        why=why,
        force=True,
    )


def carry_on(layout: Layout, target: Target) -> str:
    """His choice to keep sending to a place the fork guard refused: the place's newest copy is
    taken as this folder's own from now on. The line to show."""
    repo = FolderRepository(target_root(target.path, _label(layout).home_id))
    stamps = repo.copies()
    log_line(
        layout,
        {
            "kind": "carry-on",
            "id": target.id,
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
    sealed_keys: SealedKeys | None = None,
    progress: Callable[[str], None] | None = None,
) -> RoundReport:
    started = clock.monotonic()
    told = progress or _quiet
    busy = f"a backup round is already running for {layout.root}; it ends by itself"
    with hold(layout.backups / LOCK, busy):
        quick_repo = FolderRepository(layout.backups / QUICK)
        quick_repo.clean()
        log = log_lines(layout)
        home_id = _label(layout).home_id
        if only is not None and not any(t.id == only for t in plan.targets):
            raise PlanRefused(f"there is no backup place {only!r} in Settings")
        chosen = [
            target
            for target in plan.targets
            if (target.id == only)
            or (
                only is None
                and target.on
                and due(_last(log, _target_key(target, home_id)), now, target.every, target.at)
            )
        ]
        previous = _newest(quick_repo)
        stamp = _stamp(now, quick_repo)
        quick_where = quick_repo.where
        try:
            copy = make(
                layout,
                previous=previous,
                stamp=stamp,
                why=why,
                leave_out=plan.leave_out,
                keep_free=max(FLOOR_BYTES, floor),
                progress=told,
            )
        except (NoRoom, Changing) as refused:
            places = (
                Placed(QUICK, quick_where, "refused", str(refused)),
                *(
                    Placed(
                        t.id,
                        plain(t.path),
                        "skipped",
                        f"no copy was made, so none went to {plain(t.path)}",
                        _target_key(t, home_id),
                    )
                    for t in chosen
                ),
            )
            return _logged(layout, RoundReport(stamp, why, places, clock.monotonic() - started))
        placed = [_quick_place(quick_repo, copy, previous, force, started)]
        sealed = sealed_keys() if sealed_keys is not None and chosen else None
        for target in chosen:
            told(f"sending the copy to {plain(target.path)}")
            placed.append(_send(layout, target, copy, quick_repo, sealed, log, home_id))
        if not force and any(place.result == "copied" for place in placed):
            placed[0] = _thin_quick(quick_repo, plan, log, placed, now)
            _thin_pre_change(layout, log, placed, now)
        return _logged(layout, RoundReport(stamp, why, tuple(placed), clock.monotonic() - started))


def _quick_place(
    repo: FolderRepository,
    copy: Manifest,
    previous: Manifest | None,
    force: bool,
    started: float,
) -> Placed:
    if not force and previous is not None and previous.files == copy.files:
        line = f"nothing changed since the last copy; the quick undo in {repo.where} holds it"
        return Placed(
            QUICK, repo.where, "unchanged", line, stamp=previous.stamp, partial=_partial(previous)
        )
    repo.put_copy(copy)
    old: frozenset[tuple[str, str]] = frozenset() if previous is None else previous.files
    new = [e for e in copy.entries if e.at == "pool" and (e.path, e.sha256) not in old]
    size = sum(e.size for e in new)
    line = (
        f"copied {_count(len(new), 'changed file')} ({_mb(size)}) into the quick undo in "
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
    target: Target,
    copy: Manifest,
    quick_repo: FolderRepository,
    sealed: tuple[bytes, str] | None,
    log: Sequence[Mapping[str, object]],
    home_id: str,
) -> Placed:
    """Send one copy to one target. A file whose bytes do not match its hash is left out of
    the target's copy by name, and the copy is marked partial; the rest is sent. The place's
    result is logged as soon as its manifest is up, so a round killed later never makes this
    folder's own copy look like another folder's."""
    started = clock.monotonic()
    repo = FolderRepository(target_root(target.path, home_id))
    key, where = place_key(repo), repo.where

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
        return Placed(target.id, where, result, line, key, stamp, files, size, seconds, partial)

    anchor = Path(target.path.anchor or "/")
    if not anchor.exists():
        return placed(
            "skipped",
            f"{plain(target.path)} is not there (is its drive plugged in?); the copy waits for it",
        )
    try:
        refusal = _guard(log, key, repo)
        if refusal is not None:
            return placed("refused", refusal)
        repo.clean()
        newest = _newest(repo)
        keys = {"keys": sealed[1]} if sealed else {}
        if (
            newest is not None
            and _intended(newest) == copy.files
            and newest.header.get("keys") == keys.get("keys")
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
        if room < need:
            return placed(
                "refused",
                f"{where} needs {_mb(need)} for this copy and has {_mb(room)} free; nothing was "
                "written there. Free some space on it, or name another place in Settings",
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
        held = _without(copy, skipped, keys)
        repo.set_about(_about(home_id, layout, held))
        repo.put_copy(held, {SEALED: sealed[0]} if sealed else None)
        log_line(layout, {"kind": "sent", "id": target.id, "key": key, "stamp": held.stamp})
        thinned = _thin(repo, target, log, key)
    except OSError as failed:
        return placed(
            "refused", f"the copy to {where} stopped: {_why(failed)}; the next round tries again"
        )
    line = f"copied {_count(len(missing) - len(damaged), 'file')} ({_mb(written)}) to {where}"
    if same_drive(target, layout):
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


def _without(copy: Manifest, skipped: Sequence[Entry], keys: Mapping[str, str]) -> Manifest:
    """The copy a target holds: every file in its pool, less the files it could not take, which
    its header names, so the copy reads as partial and a later round knows what it meant to
    hold."""
    if not skipped:
        return copy.pooled(**keys)
    gone = {entry.path for entry in skipped}
    pooled = copy.pooled(
        **keys, partial=True, skipped=[[entry.path, entry.sha256] for entry in skipped]
    )
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
            "there, or name another place"
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
    repo: FolderRepository, target: Target, log: Sequence[Mapping[str, object]], key: str
) -> str:
    """Drop the copies the keep rule lets go, then sweep the pool. Returns a line when the sweep
    could not run."""
    readable, whole = _readable(repo)
    keep = kept(list(readable), target.keep, drilled=_drilled(log, key), held=whole)
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
    now: datetime,
) -> Placed:
    elsewhere = _target_copies(log, placed)
    readable, held = _readable(repo)
    for stamp, manifest in readable.items():
        if manifest.header.get("why") == "before-upgrade" and not released(
            when(stamp), elsewhere, now
        ):
            held.add(stamp)
    keep = kept(list(readable), plan.quick_undo, drilled=_drilled(log, QUICK), held=held)
    for stamp in readable:
        if stamp not in keep:
            repo.drop(stamp)
    blocked = repo.sweep().blocked
    first = placed[0]
    if blocked is None:
        return first
    return replace(first, line=f"{first.line}; {blocked}")


def _thin_pre_change(
    layout: Layout, log: Sequence[Mapping[str, object]], placed: Sequence[Placed], now: datetime
) -> None:
    """Remove each store's pre-change copy (LF3's `backups/pre-*`) once a copy to another place
    made after it is 30 days old (design 62 B3)."""
    elsewhere = _target_copies(log, placed)
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
        if released(made, elsewhere, now):
            shutil.rmtree(folder)


def _target_copies(log: Sequence[Mapping[str, object]], placed: Sequence[Placed]) -> list[datetime]:
    moments = [
        when(str(place.get("stamp")))
        for line in log
        if line.get("kind") == "round"
        for place in cast("list[dict[str, object]]", line.get("places", []))
        if place.get("id") != QUICK and place.get("result") == "copied" and place.get("stamp")
    ]
    moments += [when(p.stamp) for p in placed if p.id != QUICK and p.result == "copied" and p.stamp]
    return moments


def _newest(repo: FolderRepository) -> Manifest | None:
    """The newest copy whose manifest is whole."""
    for stamp in reversed(repo.copies()):
        try:
            return repo.manifest(stamp)
        except Unreadable:
            continue
    return None


def _stamp(now: datetime, repo: FolderRepository) -> str:
    """The copy's stamp: `now` in UTC, after every copy the quick undo holds."""
    stamp = now.astimezone(UTC).strftime(STAMP)
    stamps = repo.copies()
    if stamps and stamp <= stamps[-1]:
        stamp = (when(stamps[-1]) + timedelta(microseconds=1)).strftime(STAMP)
    return stamp


def place_key(repo: FolderRepository) -> str:
    """A place's key in the backup log: its folder, as the OS compares names."""
    return f"folder:{os.path.normcase(os.path.abspath(repo.root))}"


def _target_key(target: Target, home_id: str) -> str:
    return place_key(FolderRepository(target_root(target.path, home_id)))


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


def _why(error: OSError) -> str:
    return f"{error.strerror or type(error).__name__}" + (
        f" ({plain(error.filename)})" if error.filename else ""
    )
