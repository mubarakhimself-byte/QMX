"""What a copy holds by class, This PC's policy, the main switch, the stamp and the hold (design 06
sections 2, 4 and 5). Every folder and every storage is in pytest's tmp folder."""

from __future__ import annotations

import tomllib
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import filled_folder, folder

from qmx_home import Label, Layout
from qmx_home.backup import restore
from qmx_home.backup import round as module
from qmx_home.backup.plan import Keep, Plan, Policy
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import run_round
from qmx_home.classes import NEVER, class_of

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
PASTED = "sk-ant-api03-pastedByHandIntoSettings0000"
SETTINGS = f"""[engine]
host_name = "pc"

[[providers]]
id = "kimi"

[[providers]]
id = "glm"
api_key = "glm-planted-key"

[notes]
innocent = "{PASTED}"
"""


def storage_repo(layout: Layout, path: Path) -> FolderRepository:
    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    return FolderRepository(path / "QMX-backup" / home_id)


def test_a_copy_leaves_a_pasted_key_out_of_settings_and_names_it_to_fill_in(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, writers=True)
    (filled.layout.data / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    plan = Plan(storages=(folder(tmp_path / "usb"),))

    report = run_round(filled.layout, plan, now=NOW, floor=0)

    assert [p.result for p in report.places] == ["copied", "copied"]
    usb = storage_repo(filled.layout, tmp_path / "usb")
    copy = usb.manifest(usb.copies()[-1])
    assert copy.header["keys_to_fill"] == ["notes.innocent", "providers[1].api_key"]
    entry = next(e for e in copy.entries if e.path == "settings.toml")
    copied = usb.pool_path(entry.sha256).read_bytes()
    assert PASTED.encode() not in copied and b"glm-planted-key" not in copied
    assert tomllib.loads(copied.decode()) == {
        "engine": {"host_name": "pc"},
        "providers": [{"id": "kimi"}, {"id": "glm"}],
        "notes": {},
    }
    assert not [e.path for e in copy.entries if class_of(f"data/{e.path}") in NEVER]
    pooled = b"".join(p.read_bytes() for p in usb.root.rglob("*") if p.is_file())
    assert PASTED.encode() not in pooled
    assert not [v for v in filled.planted.values() if v in pooled]


def test_a_recipe_only_storage_holds_recipes_and_the_library_logs_and_its_restore_names_the_rest(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, writers=True)
    usb = folder(tmp_path / "usb")
    plan = Plan(storages=(replace(usb, policy=replace(usb.policy, save=("recipe",))),))

    run_round(filled.layout, plan, now=NOW, floor=0)

    repo = storage_repo(filled.layout, tmp_path / "usb")
    copy = repo.manifest(repo.copies()[-1])
    classes = {
        e.path: class_of(f"data/{e.path}")
        for e in copy.entries
        if not e.path.startswith(("library/refs/", "library/edges/", "library/annotations/"))
        and not e.path.startswith("library/blobs/tombstones/")
        and not e.path.startswith(("library/objects/", "library/blobs/"))
    }
    assert set(classes.values()) == {"recipe"}
    assert any(e.path.startswith("library/refs/") for e in copy.entries)
    assert copy.header["save"] == ["recipe"]
    left = [str(line) for line in copy.header["left_out"]]  # type: ignore[union-attr]
    assert left and all(line.endswith("(left out by your switches)") for line in left)
    found = restore.copies(repo)[0]
    assert set(left) <= set(found.lacks)


def test_this_pcs_cadence_and_keep_rule_come_from_its_policy(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3)
    plan = Plan(pc=Policy(every="2h", keep=Keep(hours=4)))
    changed = filled.layout.data / "chats" / "c1.json"
    results: list[str] = []
    for hour in range(12):
        changed.write_text(f'{{"n": {hour}}}', encoding="utf-8")
        report = run_round(filled.layout, plan, now=NOW + timedelta(hours=hour), floor=0)
        results.append(report.places[0].result)

    assert results == ["copied", "skipped"] * 6
    quick = FolderRepository(filled.layout.backups / "quick")
    assert quick.copies() == (
        "20261027T070000000000Z",
        "20261027T090000000000Z",
        "20261027T110000000000Z",
        "20261027T130000000000Z",
    )


def test_the_main_switch_off_copies_nothing_and_deletes_nothing(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3)
    plan = Plan(storages=(folder(tmp_path / "usb"),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    before = sorted(p for p in tmp_path.rglob("*") if "backups.jsonl" not in p.name)
    (filled.layout.data / "chats" / "c1.json").write_text('{"n": 2}', encoding="utf-8")

    off = run_round(filled.layout, replace(plan, on=False), now=NOW + timedelta(days=30), floor=0)

    assert [p.result for p in off.places] == ["skipped", "skipped"]
    assert off.places[0].line.startswith("Sync to my storage is off in Settings")
    assert sorted(p for p in tmp_path.rglob("*") if "backups.jsonl" not in p.name) == before


def test_a_stamp_after_the_clock_moved_back_is_later_than_every_storages_newest_copy(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3)
    plan = Plan(storages=(folder(tmp_path / "usb", every="1h"),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    for stamp in FolderRepository(filled.layout.backups / "quick").copies():
        FolderRepository(filled.layout.backups / "quick").drop(stamp)
    (filled.layout.data / "chats" / "c1.json").write_text('{"n": 2}', encoding="utf-8")

    back = run_round(filled.layout, plan, now=NOW - timedelta(hours=5), floor=0, only="usb")

    assert [p.result for p in back.places] == ["copied", "copied"]
    assert back.stamp == "20261027T030000000001Z"


def test_a_held_copy_goes_once_a_whole_copy_reaches_a_storage_on_another_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3)
    pre = filled.layout.backups / "pre-engine-1-2-20261026T000000000000Z"
    pre.mkdir(parents=True)
    module.log_line(
        filled.layout,
        {"kind": "pre-change", "path": f"backups/{pre.name}", "at": "2026-10-26T00:00:00+00:00"},
    )
    plan = Plan(storages=(folder(tmp_path / "usb"),))

    run_round(filled.layout, plan, now=NOW, floor=0)
    assert pre.is_dir(), "a storage on the folder's own disk does not release it"

    def apart(_storage: object, _layout: object) -> bool:
        return False

    monkeypatch.setattr(module, "same_drive", apart)
    (filled.layout.data / "chats" / "c1.json").write_text('{"n": 2}', encoding="utf-8")
    run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)
    assert not pre.exists()
