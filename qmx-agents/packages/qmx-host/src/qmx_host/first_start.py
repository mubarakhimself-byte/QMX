"""The first start's backend (design 62 F steps 2 to 4, A1, guard 5): what the first-start card
offers, and its four choices, as functions, as `python -m qmx_host` commands and as routes.

1. Make a new QMX folder (`make_new`).
2. Open an existing QMX folder (`open_existing`).
3. Restore from a backup (`restore_into`, `check_restore`, `restore_copy`): a copy he picked
   by date from a backup place, into a new folder or into the folder QMX found and refused, after
   he saw what it replaces. A new folder is marked (`qmx_home.RESTORE_UNFINISHED`) until the
   restore finished and is pointed at only then.
4. Bring in the old QMX data (`bring_in_old`), offered and chosen first when his old folder is
   found at `~/.qmx`. The old folder is only read (`qmx_host.bring_in`).

Every choice refuses A1's "never" places by name before it writes anything (`Places.refusal`):
inside the Windows app folders, inside QMX's own program folder or checkout, a network drive, a
drive's root, and a folder a sync client syncs live (OneDrive, Dropbox, Google Drive, and any
client Windows lists as a sync root). Only a finished choice writes the pointer.

On the card's routes the bring-in and the restore run as jobs the card reads by id
(`qmx_host.jobs`), one at a time, and the card hands the folder of its own last finished choice
to the desktop app (`handover`), which then starts the host on it (loose strings P1, Appendix E).
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import sys
import tempfile
import threading
import tomllib
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Final, cast

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from qmx_control.library import UNFINISHED, old_library
from qmx_home import (
    LABEL,
    RESTORE_UNFINISHED,
    TREE,
    Label,
    Layout,
    NoQmxFolder,
    _default_root,  # pyright: ignore[reportPrivateUsage] - A1's default, one rule for both
    _fixed_drives,  # pyright: ignore[reportPrivateUsage]
    pointer_file,
    resolve,
)
from qmx_home.backup.plan import NO_SECOND_DRIVE, PlanRefused, proposal, source_of
from qmx_home.backup.repository import Repository
from qmx_home.backup.restore import (
    JOURNAL,
    Copy,
    Finished,
    HostServes,
    RestoreRefused,
    cancel,
    copies,
    finish,
    newer_than,
    stage,
)
from qmx_home.files import Busy, Held, copy_file, hold
from qmx_home.versions import check_open

from qmx_host.bring_in import (
    BUSY,
    Copier,
    Refused,
    Report,
    again,
    bring_in,
    brought_from,
    old_refusal,
    refusal_before_copy,
    unfinished_facts,
)
from qmx_host.jobs import Job, Jobs, Progress, Stopped
from qmx_host.process_record import recorded_host

OLD_FOLDER: Final = ".qmx"
"""The old folder's name in his user profile. It is looked at to offer the bring-in and only ever
read; it is never a QMX folder (`qmx_home.resolve` decides those)."""
LOCK: Final = "first-start.lock"
"""Beside the pointer: one first start at a time for this user, whatever folders they name."""
TEMP_LOCK: Final = "qmx-first-start.lock"
"""The same lock in the system temp folder when the OS names no pointer file, so nothing is
written beside a pointer that does not exist (ruling 143)."""
BRING_IN: Final = "bring-in"
NOTHING_CHOSEN: Final = (
    "no QMX folder was chosen in this first start yet; make a new one, open one or bring your old "
    "data in first"
)
RESTORE: Final = "restore"
NOT_CONFIRMED: Final = (
    "a restore needs confirmed: true, after you saw what it replaces; nothing was changed"
)
AGAIN_UPGRADES: Final = (
    "This copy was taken before an upgrade: a QMX newer than its stores upgrades them again when "
    "it starts, so to stay on them, install the older QMX first."
)
DRIVE_REMOTE: Final = 4
DRIVE_REMOVABLE: Final = 2
SYNC_ROOTS_KEY: Final = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SyncRootManager"
DRIVEFS_KEY: Final = r"Software\Google\DriveFS"


def default_old() -> Path:
    """Where his old QMX data sits: `.qmx` in his user profile."""
    return Path.home() / OLD_FOLDER


@dataclass(frozen=True, slots=True)
class Places:
    """Where a QMX folder may not go on this PC (design 62 A1, guard 5)."""

    environ: Mapping[str, str]
    sync: tuple[tuple[str, Path], ...] = ()
    """Each sync client's name and a folder it syncs live."""
    program: tuple[Path, ...] = ()
    """QMX's own program folders: the environment and the checkout it runs from."""
    drive_type: Callable[[str], int] = field(default=lambda _root: 3)
    """`GetDriveTypeW` of a drive root such as `D:\\`."""

    @classmethod
    def this_pc(cls) -> Places:
        environ = dict(os.environ)
        return cls(environ, sync_roots(environ, registered_roots()), program_folders(), _drive_type)

    def refusal(self, folder: Path) -> str | None:
        """Why `folder` may not be a QMX folder, by name, or None."""
        real = folder.absolute().resolve()
        drive = PureWindowsPath(real).drive
        if drive.startswith("\\\\") or str(real).startswith("\\\\"):
            return _never(folder, "a network folder", "QMX's databases need a local disk")
        if drive and self.drive_type(f"{drive}\\") == DRIVE_REMOTE:
            return _never(folder, f"the network drive {drive}", "QMX's databases need a local disk")
        if real.parent == real:
            return _never(
                folder, "a drive's root", "QMX keeps its own folder there, such as D:\\QMX"
            )
        for name, meaning in (("APPDATA", "AppData\\Roaming"), ("LOCALAPPDATA", "AppData\\Local")):
            value = self.environ.get(name)
            if value and real.is_relative_to(Path(value).resolve()):
                return _never(
                    folder,
                    f"Windows' app folder {meaning} ({value})",
                    "an uninstall or an app package can empty it",
                )
        for program in self.program:
            if real.is_relative_to(program.resolve()):
                return _never(
                    folder,
                    f"QMX's own program folder {program}",
                    "an update or a new install replaces it",
                )
        for client, root in self.sync:
            if real.is_relative_to(root.resolve()):
                return _never(
                    folder,
                    f"your {client} folder {root}",
                    f"{client} syncs it live, and a database synced while it is open is corrupted",
                )
        return None

    def warning(self, folder: Path) -> str | None:
        """A choice he may make but should know about: a removable drive."""
        drive = PureWindowsPath(folder.absolute()).drive
        if drive and self.drive_type(f"{drive}\\") == DRIVE_REMOVABLE:
            return f"{drive} is a removable drive: QMX stops working whenever it is unplugged"
        return None


def _never(folder: Path, where: str, why: str) -> str:
    return f"{folder} is inside {where}, where a QMX folder never goes: {why}. Pick another folder"


def sync_roots(
    environ: Mapping[str, str], registered: Sequence[tuple[str, Path]] = ()
) -> tuple[tuple[str, Path], ...]:
    """Every folder a sync client syncs live: OneDrive's `OneDrive*` variables, Dropbox's
    `info.json` in the app folders, and `registered` (the roots Windows and Google Drive list)."""
    found: list[tuple[str, Path]] = [
        ("OneDrive", Path(value))
        for name, value in environ.items()
        if name.upper().startswith("ONEDRIVE") and value
    ]
    for base in ("APPDATA", "LOCALAPPDATA"):
        info = Path(environ.get(base) or "/nonexistent") / "Dropbox" / "info.json"
        try:
            accounts: object = json.loads(info.read_text(encoding="utf-8"))
        except OSError, ValueError:
            continue
        if not isinstance(accounts, dict):
            continue
        for account in cast("dict[str, object]", accounts).values():
            if not isinstance(account, dict):
                continue
            path = cast("dict[str, object]", account).get("path")
            if isinstance(path, str) and path:
                found.append(("Dropbox", Path(path)))
    found += registered
    return tuple(dict.fromkeys(found))


def registered_roots() -> list[tuple[str, Path]]:
    """The sync roots Windows lists for every user of this PC (the Cloud Files registry, where
    OneDrive, Google Drive, Dropbox, Box and iCloud register) and Google Drive's own mount
    setting. Only read; empty off Windows."""
    if sys.platform != "win32":
        return []
    import winreg  # noqa: PLC0415

    found: list[tuple[str, Path]] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SYNC_ROOTS_KEY) as providers:
            for index in range(winreg.QueryInfoKey(providers)[0]):
                provider = winreg.EnumKey(providers, index)
                try:
                    with winreg.OpenKey(providers, rf"{provider}\UserSyncRoots") as roots:
                        for value in range(winreg.QueryInfoKey(roots)[1]):
                            _, path, _ = winreg.EnumValue(roots, value)
                            if isinstance(path, str) and path:
                                found.append((provider.split("!", 1)[0], Path(path)))
                except OSError:
                    continue
    except OSError:
        pass
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, DRIVEFS_KEY) as drivefs:
                mount, _ = winreg.QueryValueEx(drivefs, "DefaultMountPoint")
        except OSError:
            continue
        if isinstance(mount, str) and mount:
            found.append(("Google Drive", Path(os.path.expandvars(mount))))
    return found


def program_folders() -> tuple[Path, ...]:
    """QMX's environment and the checkout it runs from."""
    here = Path(__file__).resolve()
    checkout = next((p for p in here.parents if (p / ".git").exists()), None)
    return tuple(p for p in (Path(sys.prefix), checkout) if p is not None)


def _drive_type(root: str) -> int:
    if sys.platform != "win32":
        return 3
    return int(ctypes.windll.kernel32.GetDriveTypeW(root))


@dataclass(frozen=True, slots=True)
class Offer:
    """What the first-start card shows (F step 2)."""

    found: str | None
    """A QMX folder this PC already has: no first start is needed."""
    default: str
    """A1's default folder for a new QMX folder."""
    drives: tuple[tuple[str, int], ...]
    """Each fixed drive and its free bytes."""
    old: str | None
    """His old QMX folder, when one is there to bring in."""
    choices: tuple[str, ...]
    unfinished: Mapping[str, str] | None = None
    """The folder a bring-in did not finish in (`folder`, `line`): offered again, never beside."""
    refused: Mapping[str, str | None] | None = None
    """A folder QMX found and refused, or whose store it refuses (`folder`, `line`): his data may
    sit there, so only "open" and "restore" into it are offered."""
    warning: str | None = None
    """What he should know about the default folder: a removable drive."""
    restoring: Mapping[str, str] | None = None
    """A folder made for a restore that did not finish (`folder`, `line`): offered again."""
    second_drive: str | None = None
    """The second drive QMX proposes for a daily copy (`qmx_home.backup.plan.proposal`)."""
    second_line: str = NO_SECOND_DRIVE

    def document(self) -> dict[str, object]:
        return {
            "found": self.found,
            "default": self.default,
            "drives": [{"drive": drive, "free": free} for drive, free in self.drives],
            "old": self.old,
            "choices": list(self.choices),
            "chosen": self.choices[0],
            "unfinished": None if self.unfinished is None else dict(self.unfinished),
            "refused": None if self.refused is None else dict(self.refused),
            "restore_unfinished": None if self.restoring is None else dict(self.restoring),
            "warning": self.warning,
            "second_drive": {"path": self.second_drive, "line": self.second_line},
        }

    def lines(self) -> list[str]:
        if self.found is not None:
            return [f"QMX already has its folder at {self.found}; no first start is needed."]
        if self.refused is not None:
            into = self.refused["folder"] or "<folder>"
            return [
                f"QMX found its folder but cannot open it: {self.refused['line']}",
                f"  Restore from a backup: {_restore_command(into)}",
                "  Open an existing QMX folder: python -m qmx_host open --home <folder>",
            ]
        if self.restoring is not None:
            return [
                self.restoring["line"],
                "  Restore it again (chosen): "
                + _restore_command(self.restoring["folder"], create=True),
                "  Open an existing QMX folder: python -m qmx_host open --home <folder>",
            ]
        if self.unfinished is not None:
            folder = self.unfinished["folder"]
            lines = [self.unfinished["line"]]
            if self.old is not None:
                lines.append(
                    f"  Bring it in again (chosen): python -m qmx_host bring-in --again --home "
                    f"{folder} --old {self.old}"
                )
            return [
                *lines,
                "  Open an existing QMX folder: python -m qmx_host open --home <folder>",
                f"  Restore from a backup: {_restore_command(folder)}",
            ]
        lines = ["No QMX folder was found on this PC. Pick one of these:"]
        if self.warning is not None:
            lines.append(f"  Note: {self.warning}")
        if self.old is not None:
            lines.append(
                f"  Bring in your old QMX data from {self.old} (chosen): python -m qmx_host "
                f"bring-in --home {self.default}"
            )
        lines += [
            f"  Make a new QMX folder: python -m qmx_host new --home {self.default}",
            "  Open an existing QMX folder: python -m qmx_host open --home <folder>",
            f"  Restore from a backup: {_restore_command(self.default, create=True)}",
            "Free space: " + ", ".join(f"{d} {free / (1 << 30):.1f} GB" for d, free in self.drives),
            f"Second copy: {self.second_line}",
        ]
        return lines


def _restore_command(folder: str, *, create: bool = False) -> str:
    made = " --create" if create else ""
    return f"python -m qmx_host restore --home {folder} --from <backup place>{made}"


def offer(old: Path, places: Places, drives: Sequence[Path] | None = None) -> Offer:
    """The first-start card's content. `old` is where his old data would be; `drives` the fixed
    drives, the machine's own when None.

    A folder QMX finds and refuses, or one whose bring-in did not finish, is never answered with
    "new": his data may sit there (ruling 141). A refused folder, or one with a store this
    release refuses, is offered "open" and the restore of a copy into it (design 62 B4). An
    unfinished bring-in is offered the bring-in again into the same folder, an unfinished restore
    the restore again; old flat data named by the pointer or a flag is offered the bring-in."""
    fixed = _fixed_drives() if drives is None else list(drives)
    found: str | None = None
    unfinished: dict[str, str] | None = None
    refused: dict[str, str | None] | None = None
    restoring: dict[str, str] | None = None
    default = _default_root(fixed)
    near = default
    try:
        layout = resolve(drives=fixed)
    except NoQmxFolder as missing:
        if missing.kind == "refused":
            refused = {"folder": _named(missing.folder), "line": str(missing)}
            near = missing.folder or default
        elif missing.kind == "old" and missing.folder is not None:
            old = missing.folder
    else:
        near = layout.root
        unfit = old_library(layout.home)
        facts = unfinished_facts(layout.root)
        if (layout.data / RESTORE_UNFINISHED).is_file():
            restoring = {"folder": str(layout.root), "line": _restoring_line(layout.root)}
        elif unfit is None:
            held = _refused_store(layout)
            if held is None:
                found = str(layout.root)
            else:
                refused = {"folder": str(layout.root), "line": held}
        elif facts is not None:
            unfinished = {"folder": str(layout.root), "line": _unfinished_line(layout)}
            old = Path(str(facts["old"])) if facts.get("old") else old
        else:
            refused = {"folder": str(layout.root), "line": unfit}
    room = tuple((str(drive), _free(drive)) for drive in fixed)
    seen = str(old) if old_refusal(old.resolve()) is None else None
    if found is not None:
        choices: tuple[str, ...] = ("open",)
    elif refused is not None:
        choices = ("open", "restore")
    elif restoring is not None:
        choices = ("restore", "open")
    elif unfinished is not None:
        choices = ("bring-in", "open", "restore") if seen else ("open", "restore")
    else:
        choices = ("bring-in", "new", "open", "restore") if seen else ("new", "open", "restore")
    warning = places.warning(default)
    second = proposal(Layout(near), fixed)
    return Offer(
        found,
        str(default),
        room,
        seen,
        choices,
        unfinished,
        refused,
        warning,
        restoring,
        None if second is None else str(second.path),
        NO_SECOND_DRIVE if second is None else second.line,
    )


def _refused_store(layout: Layout) -> str | None:
    """The line of the first store of the folder this release refuses, or None."""
    return next((v.line for v in check_open(layout).held_back if v.action == "refused"), None)


def _restoring_line(root: Path) -> str:
    return (
        f"Restoring a copy into {root} did not finish. Restore it again into the same folder; "
        "nothing of yours was in it."
    )


def _named(folder: Path | None) -> str | None:
    return None if folder is None else str(folder)


def _unfinished_line(layout: Layout) -> str:
    try:
        why = (layout.data / UNFINISHED).read_text(encoding="utf-8").strip()
    except OSError, ValueError:
        why = "its record cannot be read"
    return (
        f"Bringing your old QMX data into {layout.root} did not finish: {why}. Your old folder was "
        "never changed. Bring it in again into the same folder; QMX first clears only its own "
        "unfinished copy there."
    )


def _free(drive: Path) -> int:
    try:
        return shutil.disk_usage(drive).free
    except OSError:
        return -1


def lock_file() -> Path:
    """The per-user first-start lock: beside the pointer, or in the system temp folder when the OS
    names no pointer file."""
    pointer = pointer_file()
    return (
        pointer.with_name(LOCK) if pointer is not None else Path(tempfile.gettempdir()) / TEMP_LOCK
    )


def make_new(folder: Path, places: Places) -> Layout:
    """A new, empty QMX folder at `folder`, and the pointer to it."""
    _refuse(places, folder)
    with hold(lock_file(), BUSY, removed=True):
        try:
            layout = resolve(folder, create=True)
        except NoQmxFolder as refused:
            raise Refused(str(refused)) from None
        write_pointer(layout.root)
    return layout


def open_existing(folder: Path, places: Places) -> Layout:
    """The existing QMX folder at `folder`, and the pointer to it."""
    _refuse(places, folder)
    with hold(lock_file(), BUSY, removed=True):
        try:
            layout = resolve(folder)
        except NoQmxFolder as refused:
            raise Refused(str(refused)) from None
        unfit = old_library(layout.home)
        if unfit is not None:
            raise Refused(unfit)
        write_pointer(layout.root)
    return layout


def bring_in_old(
    old: Path,
    folder: Path,
    places: Places,
    *,
    copy: Copier = copy_file,
    lock: Held | None = None,
    progress: Progress | None = None,
    anew: bool = False,
) -> Report:
    """His old data brought into a new QMX folder at `folder`; the pointer once it finished. A
    second copy of the same old folder into another folder is refused, so his data is never
    doubled. `lock` is the first start's lock when the caller holds it already; either way it is
    gone again when this returns. `anew` brings it in again into a folder where it did not
    finish (`qmx_host.bring_in.again`)."""
    try:
        already = _already_brought(old, folder)
        if already is not None:
            raise Refused(already)
        run = again if anew else bring_in
        report = run(
            old,
            folder,
            place_refusal=places.refusal,
            lock=lock or lock_file(),
            copy=copy,
            progress=progress,
        )
    finally:
        if lock is not None:
            lock.release()
    if report.finished:
        write_pointer(report.folder)
    return report


def _already_brought(old: Path, folder: Path) -> str | None:
    """Why `old` may not be brought into `folder`: it was brought into the folder QMX uses now."""
    try:
        current: Path | None = resolve(drives=[]).root
    except NoQmxFolder:
        current = None
    if current is None or current == folder.absolute().resolve():
        return None
    facts = brought_from(current)
    if facts is not None and Path(str(facts.get("old"))).resolve() == old.resolve():
        return (
            f"your old data from {old} was already brought into {current}; open that folder "
            "instead of copying it again"
        )
    return None


def _refuse(places: Places, folder: Path) -> None:
    refusal = places.refusal(folder)
    if refusal is not None:
        raise Refused(refusal)


@dataclass(frozen=True, slots=True)
class Into:
    """The folder a restore goes into."""

    layout: Layout
    new: bool
    """Made for this restore, or by one that did not finish: it holds nothing of his and takes
    the copy, its `home_id` included."""


def restore_into(folder: Path, places: Places, *, make: bool) -> Into:
    """`folder` as the folder a restore goes into: a QMX folder, one this release refuses for a
    newer folder format (the restore writes the copy's label), or a missing or empty folder,
    which `make` makes and marks with `RESTORE_UNFINISHED`; without `make` nothing is written.
    Raises Refused by name for A1's never places and for any other folder QMX does not restore
    into."""
    _refuse(places, folder)
    try:
        layout = resolve(folder)
    except NoQmxFolder as missing:
        root = folder.absolute().resolve()
        if missing.kind == "refused" and _newer_label(root):
            return Into(Layout(root), new=False)
        if missing.kind != "missing":
            raise Refused(str(missing)) from None
        if not make:
            return Into(Layout(root), new=True)
        try:
            layout = resolve(folder, create=True)
        except NoQmxFolder as refused:
            raise Refused(str(refused)) from None
        marker = layout.data / RESTORE_UNFINISHED
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            "QMX made this folder for a restore that has not finished; the first start offers "
            "the restore again\n",
            encoding="utf-8",
        )
        return Into(layout, new=True)
    return Into(layout, new=(layout.data / RESTORE_UNFINISHED).is_file())


def _newer_label(root: Path) -> bool:
    try:
        return Label.parse((root / LABEL).read_text(encoding="utf-8")).format_version > TREE
    except OSError, ValueError:
        return False


def backup_source(document: Mapping[str, object]) -> Repository:
    """The backup place a card's `source` or the command's `--from` names. Raises RestoreRefused
    naming what is missing."""
    try:
        return source_of(document)
    except PlanRefused as refused:
        raise RestoreRefused(str(refused)) from None


def picked(repository: Repository, stamp: str) -> Copy:
    """The copy `stamp` at `repository`. Raises RestoreRefused when the place holds no whole copy
    of that date."""
    found = next((copy for copy in copies(repository) if copy.stamp == stamp), None)
    if found is None:
        raise RestoreRefused(
            f"{repository.where} holds no whole copy {stamp}; list its copies and pick one"
        )
    return found


def check_restore(into: Into, copy: Copy) -> dict[str, object]:
    """What restoring `copy` into the folder replaces, read only, with the one line he reads
    before he confirms (E-M1)."""
    layout = into.layout
    other = not into.new and _other_home(layout, copy, "") is not None
    if into.new:
        line = f"Restoring the copy {copy.stamp} makes a new QMX folder at {layout.root} from it."
        newer = None
    else:
        counted = newer_than(layout, copy.stamp)
        newer = asdict(counted)
        line = (
            f"Restoring the copy {copy.stamp} into {layout.root} replaces what the folder holds "
            f"now: {counted.line}. The folder's data is set aside whole in {layout.backups} first."
        )
    if copy.partial:
        line += f" This copy is partial: it lacks {', '.join(copy.lacks)}."
    if other:
        line += (
            f" This copy is of another QMX folder ({copy.folder} on {copy.machine}); restoring it "
            "here needs replace."
        )
    if copy.why == "before-upgrade":
        line += f" {AGAIN_UPGRADES}"
    return {
        "folder": str(layout.root),
        "copy": copy.stamp,
        "new": into.new,
        "newer": newer,
        "partial": copy.partial,
        "lacks": list(copy.lacks),
        "other_home": other,
        "line": line,
    }


def refuse_restore(into: Into, repository: Repository, copy: Copy, *, replace: bool) -> None:
    """The restore's refusals that answer at once, before anything is written. Raises HostServes
    while a host serves the folder, and RestoreRefused for another folder's copy into a folder
    holding data, unless `replace`."""
    if into.new:
        return
    layout = into.layout
    pid = recorded_host(layout.data)
    if pid is not None:
        raise HostServes(f"QMX is running on {layout.root} (PID {pid}); close it, then restore")
    other = None if replace else _other_home(layout, copy, repository.where)
    if other is not None:
        raise RestoreRefused(other)


def _other_home(layout: Layout, copy: Copy, where: str) -> str | None:
    """Why `copy` may not go into the folder without replace: it is of another QMX folder and
    the folder's `data/` holds files. `stage` refuses the same case with the same line."""
    try:
        ours = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    except OSError, ValueError:
        return None
    if copy.home_id == ours or not any(names for _, _, names in os.walk(layout.data)):
        return None
    return (
        f"the copy {copy.stamp} in {where} is of another QMX folder ({copy.folder} on "
        f"{copy.machine}), not of {layout.root}. Choose replace to restore it here: this "
        "folder's data is set aside whole first"
    )


@dataclass(frozen=True, slots=True)
class Restored:
    folder: Path
    finished: Finished
    why: str
    """Why the copy was made: `round`, `before-upgrade`, and so on."""

    @property
    def line(self) -> str:
        line = self.finished.line
        return f"{line}. {AGAIN_UPGRADES}" if self.why == "before-upgrade" else line

    def document(self) -> dict[str, object]:
        return {
            "folder": str(self.folder),
            "copy": self.finished.stamp,
            "where": self.finished.where,
            "aside": str(self.finished.aside),
            "line": self.line,
        }


def restore_copy(
    into: Into,
    repository: Repository,
    copy: Copy,
    *,
    replace: bool,
    progress: Callable[[str], None] | None = None,
) -> Restored:
    """Stage `copy` into the folder, finish it, and only then point this user at the folder.
    Raises RestoreRefused (HostServes while a host serves the folder) and Busy while a backup
    round or another restore holds the folder; a refusal before the finish leaves the folder as
    it was, and a folder made for the restore keeps its mark."""
    layout = into.layout
    if into.new and (layout.backups / JOURNAL).is_file():
        cancel(layout)
    stage(layout, repository, copy.stamp, replace=replace or into.new, progress=progress)
    done = finish(layout, running=recorded_host)
    if done is None:
        raise RestoreRefused(
            f"the restore of the copy {copy.stamp} into {layout.root} was cancelled while it ran"
        )
    write_pointer(layout.root)
    return Restored(layout.root, done, copy.why)


def write_pointer(root: Path) -> None:
    """Point this user at `root`, first in the recent list (design 62 A2)."""
    pointer = pointer_file()
    if pointer is None:
        return
    recent = [str(root)]
    try:
        kept: object = tomllib.loads(pointer.read_text(encoding="utf-8-sig")).get("recent", [])
    except OSError, ValueError:
        kept = []
    if isinstance(kept, list):
        recent += [
            str(p) for p in cast("list[object]", kept) if isinstance(p, str) and p != str(root)
        ]
    text = f"home = {_basic(str(root))}\nrecent = [{', '.join(map(_basic, recent))}]\n"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    staged = pointer.with_name(f"{pointer.name}.new")
    staged.write_text(text, encoding="utf-8")
    staged.replace(pointer)


def _basic(text: str) -> str:
    """A TOML basic string: JSON's escapes are TOML's, and TOML also escapes DEL."""
    return json.dumps(text).replace("\x7f", "\\u007f")


def old_layout_hint(folder: Path) -> str | None:
    """What a command says when it is pointed at his old folder, or None when `folder` is not
    one: QMX does not start on it, never changes it, and the first start brings it in."""
    if old_refusal(folder.resolve()) is not None:
        return None
    return (
        f"{folder} holds your old QMX data in the old layout. QMX does not start on it and never "
        "changes it. Bring it into a new QMX folder with the first start: python -m qmx_host "
        f"bring-in --home <new QMX folder> --old {folder}"
    )


class Chosen(BaseModel):
    folder: str
    old: str | None = None
    again: bool = False
    """Bring-in only: into a folder where a bring-in from the same old folder did not finish."""


class Place(BaseModel):
    source: dict[str, object]
    """`{"kind": "folder", "path": ..., "home_id": optional}`."""


class Checking(Place):
    model_config = ConfigDict(populate_by_name=True)

    folder: str
    stamp: str = Field(alias="copy")


class Restoring(Checking):
    confirmed: StrictBool = False
    """Only JSON `true` confirms: no string or number a client may send by mistake."""
    replace: StrictBool = False
    """Restore another QMX folder's copy into a folder that holds data, set aside first."""


def _document(report: Report) -> dict[str, object]:
    return {
        "finished": report.finished,
        "folder": str(report.folder),
        "report": list(report.lines),
        "facts": dict(report.facts),
    }


def first_start_router(
    places: Places,
    old: Path,
    drives: Sequence[Path] | None = None,
    *,
    port: int,
    on_handover: Callable[[Path], None] | None = None,
) -> APIRouter:
    """The card's routes. A refusal answers 409 with its line. The copies a backup place holds
    and what restoring one replaces are read at once; the bring-in and a confirmed restore answer
    202 with their job, read by id, one job at a time. The handover answers the folder of this
    card's own last finished choice and the card's `port`, then calls `on_handover`; before any
    finished choice, or while a job runs, it answers 409."""
    jobs = Jobs()
    starting = threading.Lock()
    chosen: list[Path] = []
    """The folder of the last finished choice in this card, once there is one."""
    targets: dict[str, Path] = {}
    """Each job's folder, by job id."""
    newest: list[Job] = []
    """The card's newest job as it started; read again by id."""

    def finished(root: Path) -> None:
        chosen[:] = [root]

    def latest() -> Job | None:
        return jobs.get(newest[0].id) if newest else None

    def running() -> Job | None:
        job = latest()
        return job if job is not None and job.state == "running" else None

    def started(kind: str, work: Callable[[Progress], dict[str, object]], folder: Path) -> Job:
        job = jobs.start(kind, work).job
        targets[job.id] = folder
        newest[:] = [job]
        return job

    def card() -> dict[str, object]:
        job = latest()
        shown = offer(old, places, drives).document()
        target = None if job is None or job.state != "running" else targets.get(job.id)
        folder = None if target is None else str(target)
        for name in ("unfinished", "restore_unfinished"):
            again = cast("dict[str, str] | None", shown[name])
            if folder is not None and again is not None and again["folder"] == folder:
                shown[name] = None
        return {**shown, "running": folder, "job": None if job is None else job.document()}

    def new(choice: Chosen) -> dict[str, object]:
        root = _answer(lambda: make_new(Path(choice.folder), places)).root
        finished(root)
        return {"folder": str(root), "warning": places.warning(root)}

    def existing(choice: Chosen) -> dict[str, object]:
        root = _answer(lambda: open_existing(Path(choice.folder), places)).root
        finished(root)
        return {"folder": str(root), "warning": places.warning(root)}

    def listed(place: Place) -> dict[str, object]:
        repository = _answer(lambda: backup_source(place.source))
        return {
            "where": repository.where,
            "copies": [{**asdict(copy), "lacks": list(copy.lacks)} for copy in copies(repository)],
        }

    def checked(asked: Checking) -> dict[str, object]:
        def check() -> dict[str, object]:
            into = restore_into(Path(asked.folder), places, make=False)
            return check_restore(into, picked(backup_source(asked.source), asked.stamp))

        return _answer(check)

    def restore(asked: Restoring) -> JSONResponse:
        if not asked.confirmed:
            raise HTTPException(400, detail=NOT_CONFIRMED)
        with starting:
            _one_job(running())
            held = _answer(lambda: hold(lock_file(), BUSY, removed=True))
            try:

                def ready() -> tuple[Into, Repository, Copy]:
                    into = restore_into(Path(asked.folder), places, make=False)
                    repository = backup_source(asked.source)
                    copy = picked(repository, asked.stamp)
                    refuse_restore(into, repository, copy, replace=asked.replace)
                    if into.new:
                        into = restore_into(Path(asked.folder), places, make=True)
                    return into, repository, copy

                into, repository, copy = _answer(ready)
            except BaseException:
                held.release()
                raise
            chosen.clear()

            def work(progress: Progress) -> dict[str, object]:
                try:
                    done = restore_copy(
                        into,
                        repository,
                        copy,
                        replace=asked.replace,
                        progress=progress,
                    )
                except (Busy, RestoreRefused) as refused:
                    raise Stopped(str(refused)) from None
                finally:
                    held.release()
                finished(done.folder)
                return done.document()

            job = started(RESTORE, work, into.layout.root)
        return JSONResponse(
            {**job.document(), "warning": places.warning(into.layout.root)}, status_code=202
        )

    def bring(choice: Chosen) -> JSONResponse:
        folder = Path(choice.folder)
        saved = unfinished_facts(folder.absolute())
        source = Path(choice.old) if choice.old else old
        if choice.again and not choice.old and saved and saved.get("old"):
            source = Path(str(saved["old"]))
        with starting:
            _one_job(running())
            held = _answer(lambda: hold(lock_file(), BUSY, removed=True))
            try:
                refusal = _bring_in_refusal(source, folder, places, saved, again=choice.again)
            except BaseException:
                held.release()
                raise
            if refusal is not None:
                held.release()
                raise HTTPException(409, detail=refusal)
            chosen.clear()

            def work(progress: Progress) -> dict[str, object]:
                try:
                    report = bring_in_old(
                        source, folder, places, lock=held, progress=progress, anew=choice.again
                    )
                except Refused as refused:
                    raise Stopped(str(refused)) from None
                if not report.finished:
                    raise Stopped(report.lines[0], _document(report))
                finished(report.folder)
                return _document(report)

            job = started(BRING_IN, work, folder.absolute().resolve())
        return JSONResponse(
            {**job.document(), "warning": places.warning(folder.absolute())}, status_code=202
        )

    def read_job(job_id: str) -> dict[str, object]:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(
                404,
                detail=f"no job {job_id} in this first start; the card started again since, so "
                "read GET /api/first-start for the latest one",
            )
        return job.document()

    def handover() -> dict[str, object]:
        with starting:
            busy = running()
            if busy is not None:
                raise HTTPException(409, detail=f"the {busy.kind} (job {busy.id}) is still running")
            if not chosen:
                raise HTTPException(409, detail=NOTHING_CHOSEN)
            try:
                layout = resolve(chosen[0])
            except NoQmxFolder as refused:
                raise HTTPException(409, detail=str(refused)) from None
            unfit = old_library(layout.home)
            if unfit is not None:
                raise HTTPException(409, detail=unfit)
            if on_handover is not None:
                on_handover(layout.root)
        return {"folder": str(layout.root), "port": port}

    router = APIRouter(prefix="/api/first-start")
    router.add_api_route("", card, methods=["GET"])
    router.add_api_route("/new", new, methods=["POST"])
    router.add_api_route("/open", existing, methods=["POST"])
    router.add_api_route("/copies", listed, methods=["POST"])
    router.add_api_route("/restore/check", checked, methods=["POST"])
    router.add_api_route("/restore", restore, methods=["POST"], status_code=202)
    router.add_api_route("/bring-in", bring, methods=["POST"], status_code=202)
    router.add_api_route("/jobs/{job_id}", read_job, methods=["GET"])
    router.add_api_route("/handover", handover, methods=["POST"])
    return router


def _bring_in_refusal(
    old: Path,
    folder: Path,
    places: Places,
    saved: Mapping[str, object] | None,
    *,
    again: bool,
) -> str | None:
    """The bring-in's refusals that answer at once, before its job starts."""
    if again and saved is None:
        return f"{folder} holds no unfinished bring-in; nothing was cleared"
    if not again and saved is not None:
        return (
            f"bringing your old QMX data into {folder} did not finish; choose to bring it in "
            "again into the same folder, which clears only QMX's own unfinished copy there"
        )
    return _already_brought(old, folder) or refusal_before_copy(old, folder, places.refusal)


def _answer[T](act: Callable[[], T]) -> T:
    try:
        return act()
    except (Busy, RestoreRefused) as refused:
        raise HTTPException(409, detail=str(refused)) from None


def _one_job(running: Job | None) -> None:
    """One job at a time in the card: the bring-in and a restore both hold the first start."""
    if running is not None:
        raise HTTPException(
            409,
            detail=f"a {running.kind} is already running (job {running.id}); wait for it to end",
        )


def first_start_app(
    places: Places,
    old: Path,
    ui_origin: str,
    *,
    port: int,
    on_handover: Callable[[Path], None] | None = None,
) -> FastAPI:
    """The first start's own app on the loopback, before any QMX folder exists. A first-start
    lock a killed card left behind, which no process holds, is removed first."""
    lock = lock_file()
    if lock.exists():
        with suppress(Busy, OSError):
            hold(lock, BUSY, removed=True).release()
    app = FastAPI(title="QMX first start")
    app.include_router(first_start_router(places, old, port=port, on_handover=on_handover))
    if ui_origin:
        app.add_middleware(CORSMiddleware, allow_origins=[ui_origin], allow_methods=["GET", "POST"])
    return app
