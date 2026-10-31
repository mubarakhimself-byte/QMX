"""`python -m qmx_host restore`, and `serve` finishing a staged restore before any store opens
(plan B4). Every folder and profile is in pytest's tmp folder; `serve_forever` is replaced, so no
host, browser, Credential Manager or pg0 is started."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from collections.abc import Generator, Iterator, Mapping
from contextlib import closing, contextmanager
from pathlib import Path

import psutil
import pytest
from qmx_engine.ledger.migrations import STEPS
from qmx_home import RESTORE_UNFINISHED, Layout, resolve
from qmx_home.backup import restore
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import quick
from test_card_restore import AFTER, folder, home_id, notes, runs, sent

import qmx_host.__main__
import qmx_host.host
from qmx_host.__main__ import main
from qmx_host.first_start import AGAIN_UPGRADES

HOLD = """
import sys
handle = open(sys.argv[1], "a+b")
if sys.platform == "win32":
    import msvcrt
    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
else:
    import fcntl
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
print("held", flush=True)
sys.stdin.read()
"""


@pytest.fixture
def pc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    profile = tmp_path / "profile"
    for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (profile / part).mkdir(parents=True)
        monkeypatch.setenv(name, str(profile / part))
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("HOME", str(profile))
    monkeypatch.setenv("QMX_HOME", "")
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    monkeypatch.setattr(qmx_host.__main__, "scrub_process_env", unscrubbed)
    yield tmp_path


def unscrubbed(_environ: Mapping[str, str], _keep: object) -> list[str]:
    return []


@pytest.fixture
def served(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """The run ledger's event count each `serve` saw when the host would open its stores."""
    seen: list[int] = []

    def serve_forever(home: Path, **_kw: object) -> int:
        with closing(sqlite3.connect(home / "engine" / "engine.sqlite")) as db:
            seen.append(int(db.execute("SELECT count(*) FROM events").fetchone()[0]))
        return 0

    monkeypatch.setattr(qmx_host.host, "serve_forever", serve_forever)
    return seen


def events(layout: Layout) -> int:
    with closing(sqlite3.connect(layout.data / "engine" / "engine.sqlite")) as db:
        return int(db.execute("SELECT count(*) FROM events").fetchone()[0])


@contextmanager
def held(path: Path) -> Generator[None]:
    """`path` locked by another process, as a running host holds `engine.lock`."""
    child = subprocess.Popen(
        [sys.executable, "-c", HOLD, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None and child.stdout.readline().strip() == "held"
        yield
    finally:
        child.communicate("")


def code(argv: list[str]) -> int:
    try:
        return main(argv)
    except SystemExit as stopped:
        return int(stopped.code or 0)


def test_the_command_lists_shows_what_a_copy_replaces_and_restores_only_with_yes(
    pc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    runs(layout, 2, AFTER)
    (layout.data / "notes" / "0.txt").write_text("changed", encoding="utf-8")
    base = ["restore", "--home", str(layout.root), "--from", str(usb)]
    place = FolderRepository(usb / "QMX-backup" / home_id(layout.root))

    listed = code(base)
    listing = capsys.readouterr().out
    shown = code([*base, "--copy", stamp])
    showing = capsys.readouterr().out
    unchanged = notes(layout)["0.txt"]
    me = psutil.Process()
    record = layout.data / "control-process.json"
    record.write_text(f'{{"pid": {me.pid}, "created": {me.create_time()}}}', encoding="utf-8")
    hosted = code([*base, "--copy", stamp, "--yes"])
    hosting = capsys.readouterr().err
    record.unlink()
    done = code([*base, "--copy", stamp, "--yes"])
    said = capsys.readouterr().out

    assert (listed, shown, hosted, done) == (0, 0, 1, 0)
    assert listing.splitlines() == [
        f"Copies in {place.where}, newest first:",
        f"  {stamp}  round  {len(place.manifest(stamp).entries)} files, 0 MB, made by QMX "
        f"{place.manifest(stamp).header['release']} on {place.manifest(stamp).header['machine']}",
        f"Restore one: python -m qmx_host restore --home {layout.root} --from {usb} --copy <date> "
        "--yes",
    ]
    assert showing.splitlines() == [
        f"Restoring the copy {stamp} into {layout.root} replaces what the folder holds now: "
        "since this copy the folder holds 2 runs started, 0 Library saves, 0 chats and 0 price "
        f"months. The folder's data is set aside whole in {layout.backups} first.",
        "Nothing was changed. Add --yes to restore it.",
    ]
    assert unchanged == "changed"
    assert hosting == (
        f"refused: QMX is running on {layout.root} (PID {me.pid}); close it, then restore\n"
    )
    assert said.splitlines()[-1].startswith(f"QMX restored the copy {stamp} from {place.where}.")
    assert notes(layout)["0.txt"] == "note 0"
    assert events(layout) == 1


def test_serve_finishes_a_staged_restore_before_any_store_opens(
    pc: Path, served: list[int]
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    runs(layout, 3, AFTER)
    place = FolderRepository(usb / "QMX-backup" / home_id(layout.root))
    restore.stage(layout, place, stamp, keep_free=0)

    started = code(["serve", "--home", str(layout.root)])

    assert (started, served) == (0, [1]), "the host read the copy's ledger, not the folder's"
    assert events(layout) == 1
    assert not (layout.backups / "restore.json").exists()


def test_serve_exits_2_and_keeps_the_staging_while_a_host_holds_the_folder(
    pc: Path, served: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    runs(layout, 3, AFTER)
    restore.stage(layout, FolderRepository(usb / "QMX-backup" / home_id(layout.root)), stamp)
    capsys.readouterr()

    with held(layout.data / "engine.lock"):
        started = code(["serve", "--home", str(layout.root)])
    said = capsys.readouterr().err

    assert (started, served) == (2, [])
    assert said == (
        f"QMX did not start: QMX is running on {layout.root}; close it, then start QMX again to "
        "finish the restore\n"
    )
    assert (layout.backups / f"restoring-{stamp}" / "data").is_dir()
    assert events(layout) == 4


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to move a folder in use")
def test_serve_exits_2_naming_what_to_close_when_the_folder_cannot_be_moved(
    pc: Path, served: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    layout, usb = folder(pc / "QMX"), pc / "usb"
    stamp = sent(layout, usb)
    restore.stage(layout, FolderRepository(usb / "QMX-backup" / home_id(layout.root)), stamp)
    capsys.readouterr()

    with (layout.data / "notes" / "1.txt").open("rb"):
        started = code(["serve", "--home", str(layout.root)])
    said = capsys.readouterr().err

    assert (started, served) == (2, [])
    assert said.startswith(f"QMX did not start: QMX could not move {layout.data} (")
    assert said.endswith("nothing changed and the copy stays staged\n")
    assert (layout.backups / f"restoring-{stamp}" / "data").is_dir()
    assert notes(layout)["1.txt"] == "note 1"


def test_a_store_that_upgrades_gets_a_copy_of_the_folder_first_and_a_failed_copy_is_one_line(
    pc: Path, served: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    def old_ledger(layout: Layout) -> None:
        path = layout.data / "engine" / "engine.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path, isolation_level=None)) as db:
            for statement in (*STEPS[0], *STEPS[1]):
                db.execute(statement)
            db.execute("INSERT INTO meta VALUES ('schema_version', '2')")

    roomy = resolve(pc / "Roomy", create=True)
    old_ledger(roomy)
    tight = resolve(pc / "Tight", create=True)
    old_ledger(tight)
    (tight.data / "settings.toml").write_text(
        '[engine]\n"disk.floor_gb" = 100000\n', encoding="utf-8"
    )

    first = code(["serve", "--home", str(roomy.root)])
    copied = capsys.readouterr().err
    second = code(["serve", "--home", str(tight.root)])
    refused = capsys.readouterr().err

    quick = FolderRepository(roomy.backups / "quick")
    (copy,) = quick.copies()
    manifest = quick.manifest(copy)
    ledger = next(e for e in manifest.entries if e.path == "engine/engine.sqlite")
    held = roomy.cache / "ledger-copy.sqlite"
    quick.fetch(ledger.sha256, held)
    with closing(sqlite3.connect(held)) as db:
        copied_at = db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    assert (first, second, served) == (0, 0, [0, 0])
    assert (manifest.header["why"], copied_at) == ("before-update", ("2",))
    assert copied.splitlines()[-1].startswith("before the upgrade: copied ")
    assert not (tight.backups / "quick" / "snapshots").exists() or not any(
        (tight.backups / "quick" / "snapshots").iterdir()
    )
    last = refused.splitlines()[-1]
    assert last.startswith("QMX made no copy of the folder before the upgrade: ")
    assert last.endswith("The start goes on; each store still copies itself before it upgrades.")


def test_a_refused_store_is_restored_by_the_command_its_line_names(
    pc: Path, served: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    layout = folder(pc / "QMX")
    quick(layout, "before-upgrade", floor=0)
    (stamp,) = FolderRepository(layout.backups / "quick").copies()
    with closing(sqlite3.connect(layout.data / "engine" / "engine.sqlite")) as db:
        db.execute("PRAGMA user_version = 99")
        db.execute("UPDATE meta SET value = '99' WHERE key = 'min_reader'")
        db.commit()
    named = ["restore", "--home", str(layout.root), "--from", str(layout.backups / "quick")]
    capsys.readouterr()

    refused = code(["serve", "--home", str(layout.root)])
    said = capsys.readouterr().err
    back = code([*named, "--copy", stamp, "--yes"])
    restored = capsys.readouterr().out
    started = code(["serve", "--home", str(layout.root)])

    assert refused == 2
    assert (
        "or restore a copy from before the upgrade, with Restore from a backup on the start "
        f"screen or python -m qmx_host {' '.join(named)}."
    ) in said
    assert back == 0
    assert restored.splitlines()[-1].endswith(f". {AGAIN_UPGRADES}")
    assert (started, served) == (0, [1])


def test_serve_exits_3_for_a_folder_whose_restore_did_not_finish(
    pc: Path, served: list[int], capsys: pytest.CaptureFixture[str]
) -> None:
    layout = resolve(pc / "New", create=True)
    (layout.data / RESTORE_UNFINISHED).parent.mkdir(parents=True, exist_ok=True)
    (layout.data / RESTORE_UNFINISHED).write_text("restoring", encoding="utf-8")

    started = code(["serve", "--home", str(layout.root)])
    starting = code(["start", "--home", str(layout.root)])

    assert (started, starting, served) == (3, 3, [])
    assert capsys.readouterr().err.splitlines()[-1] == (
        f"QMX did not start: restoring a copy into {layout.root} did not finish. Start the first "
        "start and restore it again into the same folder."
    )
