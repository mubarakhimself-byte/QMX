"""The format 1 to 2 layout step, run on flat homes shaped like a PC test home and a server home."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from qmx_home import LABEL, Label, Layout, LayoutRefused, NoQmxFolder, resolve, step_to_tree
from qmx_home.__main__ import main

PC_HOME = {
    "settings.toml": "[telemetry]\nsend_to = 'off'\n",
    "claude/projects/d-work/chat-1.jsonl": '{"turn": 1}\n',
    "chats/chat-1.json": '{"id": "chat-1"}',
    "procs/chat-1.json": '{"pid": 41}',
    "state/gpt-probe.json": '{"ok": true}',
    "plugins/research/skill.md": "# research\n",
    "environments/ab12/pyvenv.cfg": "home = x\n",
    "library/catalog.db": "sqlite",
    "market/fx/eurusd/2024/01.parquet": "PAR1",
    "memory/memory.db": "fts5",
    "memory/hindsight/hf/hub/model.bin": "weights",
    "engine/engine.sqlite": "ledger",
    "vault/pairing-key": "pairing",
    "vault/control-token": "bearer",
    ".qmx/vault.key": "private",
    "logs/heartbeat.jsonl": '{"beat": 1}\n',
    "control.log": "host started\n",
    "control-process.json": '{"pid": 7}',
}
PC_TREE = {
    "data/settings.toml": PC_HOME["settings.toml"],
    "data/claude/projects/d-work/chat-1.jsonl": PC_HOME["claude/projects/d-work/chat-1.jsonl"],
    "data/chats/chat-1.json": PC_HOME["chats/chat-1.json"],
    "cache/run/procs/chat-1.json": PC_HOME["procs/chat-1.json"],
    "cache/run/state/gpt-probe.json": PC_HOME["state/gpt-probe.json"],
    "cache/plugins/research/skill.md": PC_HOME["plugins/research/skill.md"],
    "cache/envs/ab12/pyvenv.cfg": PC_HOME["environments/ab12/pyvenv.cfg"],
    "data/library/catalog.db": PC_HOME["library/catalog.db"],
    "data/market/fx/eurusd/2024/01.parquet": PC_HOME["market/fx/eurusd/2024/01.parquet"],
    "data/memory/memory.db": PC_HOME["memory/memory.db"],
    "cache/models/huggingface/hub/model.bin": PC_HOME["memory/hindsight/hf/hub/model.bin"],
    "data/engine/engine.sqlite": PC_HOME["engine/engine.sqlite"],
    "data/vault/pairing-key": PC_HOME["vault/pairing-key"],
    "keys/control-token": PC_HOME["vault/control-token"],
    "keys/vault.key": PC_HOME[".qmx/vault.key"],
    "data/logs/heartbeat.jsonl": PC_HOME["logs/heartbeat.jsonl"],
    "logs/host.log": PC_HOME["control.log"],
    "data/control-process.json": PC_HOME["control-process.json"],
}
SERVER_HOME = {
    "settings.toml": "[library]\nprimary = 'pc'\n",
    "vault/pairing-key": "pairing",
    "vault/control-token": "bearer",
    "vault/tokens.json": "{}",
    ".qmx/vault.key": "private",
    "library/objects/ab/cd": "blob",
    "node/state/rooms.json": "[]",
    "logs/connection.jsonl": "{}\n",
}
SERVER_TREE = {
    "data/settings.toml": SERVER_HOME["settings.toml"],
    "data/vault/pairing-key": SERVER_HOME["vault/pairing-key"],
    "keys/control-token": SERVER_HOME["vault/control-token"],
    "data/vault/tokens.json": SERVER_HOME["vault/tokens.json"],
    "keys/vault.key": SERVER_HOME[".qmx/vault.key"],
    "data/library/objects/ab/cd": SERVER_HOME["library/objects/ab/cd"],
    "data/node/state/rooms.json": SERVER_HOME["node/state/rooms.json"],
    "data/logs/connection.jsonl": SERVER_HOME["logs/connection.jsonl"],
}


def flat(root: Path, files: dict[str, str]) -> Path:
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def free_space(free: int) -> Callable[[object], SimpleNamespace]:
    """A drive with `free` bytes left, for `shutil.disk_usage`."""

    def usage(_path: object) -> SimpleNamespace:
        return SimpleNamespace(free=free)

    return usage


def files(root: Path) -> dict[str, str]:
    """Every file but the label and the step's own copy in backups/, which
    `test_the_step_copies_the_stores_and_settings_first` checks."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != LABEL and path.relative_to(root).parts[0] != "backups"
    }


def folders(root: Path) -> list[str]:
    return sorted(path.name for path in root.iterdir())


@pytest.mark.parametrize(
    ("before", "after"), [(PC_HOME, PC_TREE), (SERVER_HOME, SERVER_TREE)], ids=["pc", "server"]
)
def test_the_step_moves_every_file_into_the_tree_and_takes_none_away(
    tmp_path: Path, before: dict[str, str], after: dict[str, str]
) -> None:
    root = flat(tmp_path / "home", before)

    step_to_tree(root)

    assert files(root) == after
    assert folders(root) == ["backups", "cache", "data", "keys", "logs", LABEL]
    assert Label.parse((root / LABEL).read_text(encoding="utf-8")).format_version == 2
    assert resolve(root, drives=[]) == Layout(root.resolve())


def test_the_step_copies_the_stores_and_settings_first(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {**PC_HOME, "engine/engine.sqlite-wal": "frames"})

    step_to_tree(root)
    step_to_tree(root)

    (copy,) = (root / "backups").glob("pre-layout-1-2-*")
    assert files(copy) == {
        "engine/engine.sqlite": "ledger",
        "engine/engine.sqlite-wal": "frames",
        "settings.toml": PC_HOME["settings.toml"],
        "layout-step.json": (copy / "layout-step.json").read_text(encoding="utf-8"),
    }
    (logged,) = (root / "backups" / "backups.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(logged)["path"] == f"backups/{copy.name}"
    assert files(root)["data/engine/engine.sqlite-wal"] == "frames"


def test_a_step_whose_copy_would_fill_the_disk_moves_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = flat(tmp_path / "home", PC_HOME)
    monkeypatch.setattr("qmx_home.versions.shutil.disk_usage", free_space(10 << 20))

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert "nothing was moved" in str(refused.value)
    assert "QMX keeps at least 1,024 MB free there" in str(refused.value)
    assert {k: v for k, v in files(root).items() if k != "layout-step.json"} == PC_HOME
    assert not (root / "backups").exists()


def test_a_step_whose_copy_failed_is_not_stuck_when_its_plan_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = flat(tmp_path / "home", PC_HOME)
    with monkeypatch.context() as full:
        full.setattr("qmx_home.versions.shutil.disk_usage", free_space(10 << 20))
        with pytest.raises(LayoutRefused):
            step_to_tree(root)
    (root / "backups").mkdir()
    (root / "layout-step.json").unlink()

    step_to_tree(root)

    assert files(root) == PC_TREE


def test_a_copy_cut_short_is_made_again_and_the_short_one_left_as_it_was(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", PC_HOME)
    cut = root / "backups" / "pre-layout-1-2-20261026T000000000000Z"
    (cut / "engine").mkdir(parents=True)
    (cut / "engine" / "engine.sqlite").write_text("led", encoding="utf-8")

    step_to_tree(root)

    copies = sorted(path.name for path in (root / "backups").glob("pre-layout-1-2-*"))
    (made,) = [name for name in copies if name != cut.name]
    assert files(root / "backups" / made)["engine/engine.sqlite"] == "ledger"
    assert files(cut) == {"engine/engine.sqlite": "led"}
    (logged,) = (root / "backups" / "backups.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(logged)["path"] == f"backups/{made}"
    assert files(root) == PC_TREE


def test_the_step_keeps_a_format_1_labels_home_id_and_runs_once(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"settings.toml": ""})
    (root / LABEL).write_text(Label("home-1", 1, "0.0.9", "0.0.9").dump(), encoding="utf-8")

    first = step_to_tree(root)
    again = step_to_tree(root)

    assert (first, again) == ([("settings.toml", "data/settings.toml")], [])
    assert Label.parse((root / LABEL).read_text(encoding="utf-8")) == Label(
        "home-1", 2, "0.0.9", "0.1.0"
    )


def test_a_flat_home_holding_a_tree_name_is_refused_untouched(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"control.db": "", "cache/x": "mine"})

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert str(refused.value) == (
        f"{root.resolve()} already holds cache, which the tree uses; move it aside first"
    )
    assert files(root) == {"control.db": "", "cache/x": "mine"}


def test_a_folder_that_is_not_a_qmx_home_is_refused_and_nothing_moves(tmp_path: Path) -> None:
    documents = flat(tmp_path / "Documents", {"cv.docx": "cv", "taxes/2025.pdf": "pdf"})

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(documents)

    assert str(refused.value) == (
        f"{documents.resolve()} is not a QMX folder: it has no qmx-home.toml and none of a QMX "
        "home's own files; pass the folder QMX made, or --create with an empty one; nothing in "
        "it was moved"
    )
    assert files(documents) == {"cv.docx": "cv", "taxes/2025.pdf": "pdf"}
    assert folders(documents) == ["cv.docx", "taxes"]


PROFILE = {
    ".qmx/chats/chat-1.json": '{"id": "chat-1"}',
    ".qmx/control.db": "sqlite",
    "Documents/cv.docx": "cv",
    "Desktop/note.txt": "note",
}
NOTES = {"vault/notes/idea.md": "# idea", "cv.docx": "cv"}
HIVE = {"NTUSER.DAT": "hive", "control.db": "sqlite"}
LANE_4_FLAT = {
    "agent-memory/flat-6fc76d0bcccf/MEMORY.md": "",
    "apps.db": "sqlite",
    "artifacts.db": "sqlite",
    "chats/chat-1.json": '{"id": "chat-1"}',
    "claude-relayed/settings.json": "{}",
    "control-process.json": '{"pid": 7}',
    "control.db": "sqlite",
    "engine/engine.sqlite": "ledger",
    "library/catalog.db": "sqlite",
    "logs/heartbeat.jsonl": "",
    "memory/memory.db": "fts5",
    "plugins/research/skill.md": "",
    "portfolio.db": "sqlite",
    "procs/chat-1.json": '{"pid": 41}',
    "router.port": "18000",
    "runs.db": "sqlite",
    "runs/chat-1/journal.jsonl": "",
    "state/gpt-probe.json": "{}",
    "workspaces/wf-1/notes.md": "",
}


@pytest.mark.parametrize(
    ("before", "why"),
    [
        (PROFILE, "none of a QMX home's own files"),
        (NOTES, "none of a QMX home's own files"),
        (HIVE, "it is a user profile (it holds NTUSER.DAT)"),
    ],
    ids=["profile-holding-the-old-home", "notes-vault", "ntuser-dat"],
)
def test_a_folder_that_only_looks_like_a_home_is_refused_and_nothing_moves(
    tmp_path: Path, before: dict[str, str], why: str
) -> None:
    root = flat(tmp_path / "someone", before)

    with pytest.raises(NoQmxFolder) as not_opened:
        resolve(root, drives=[])
    with pytest.raises(LayoutRefused) as not_moved:
        step_to_tree(root)

    assert why in str(not_opened.value)
    assert "python -m qmx_home layout" not in str(not_opened.value)
    assert str(not_moved.value).endswith("; nothing in it was moved")
    assert files(root) == before


def test_the_users_own_profile_is_refused_even_with_a_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = flat(tmp_path / "Mubarak", {"control.db": "sqlite", "Documents/cv.docx": "cv"})
    monkeypatch.setenv("USERPROFILE", str(root))
    monkeypatch.setenv("HOME", str(root))

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert str(refused.value) == (
        f"{root.resolve()} is not a QMX folder: it is your user profile; pass the folder QMX "
        "made; nothing in it was moved"
    )
    assert files(root) == {"control.db": "sqlite", "Documents/cv.docx": "cv"}


def test_a_drive_root_is_refused_without_looking_inside() -> None:
    drive = Path(Path.cwd().anchor)

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(drive)

    assert str(refused.value) == (
        f"{drive.resolve()} is not a QMX folder: it is a drive's root; pass the folder QMX made; "
        "nothing in it was moved"
    )


def test_a_flat_home_a_parent_host_made_still_moves_into_the_tree(tmp_path: Path) -> None:
    root = flat(tmp_path / "flat", LANE_4_FLAT)

    step_to_tree(root)

    assert folders(root) == ["backups", "cache", "data", "keys", "logs", LABEL]
    assert len(files(root)) == len(LANE_4_FLAT)
    assert files(root)["data/chats/chat-1.json"] == '{"id": "chat-1"}'
    assert files(root)["cache/run/procs/chat-1.json"] == '{"pid": 41}'


def test_a_layout_plan_cut_short_is_refused_by_name_and_moves_nothing(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"control.db": "", "layout-step.json": '[["control.db", "da'})

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert str(refused.value).startswith(
        f"{root.resolve() / 'layout-step.json'} cannot be read as a layout plan ("
    )
    assert str(refused.value).endswith(
        "); nothing has moved yet, so removing that file and running the step again is safe"
    )
    assert files(root) == {"control.db": "", "layout-step.json": '[["control.db", "da'}


def test_a_qmx_entry_that_is_a_file_moves_into_data_like_any_other(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"control.db": "", ".qmx": "not a folder"})

    step_to_tree(root)

    assert files(root) == {"data/control.db": "", "data/.qmx": "not a folder"}


def test_a_layout_plan_left_after_the_label_is_removed_by_the_next_run(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"control.db": ""})
    step_to_tree(root)
    (root / "layout-step.json").write_text('[["control.db", "data/control.db"]]', "utf-8")

    assert step_to_tree(root) == []
    assert folders(root) == ["backups", "cache", "data", "keys", "logs", LABEL]


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to move an open file")
def test_a_step_stopped_by_an_open_file_finishes_on_the_next_run(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", PC_HOME)

    with (root / "library" / "catalog.db").open("rb"), pytest.raises(LayoutRefused):
        step_to_tree(root)
    step_to_tree(root)

    assert files(root) == PC_TREE


def test_the_command_reports_each_move(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = flat(tmp_path / "home", {"control.db": "", "settings.toml": "", "control.log": ""})

    assert main(["layout", str(root)]) == 0

    assert capsys.readouterr().out.splitlines() == [
        "moved control.db to data/control.db",
        "moved settings.toml to data/settings.toml",
        "moved control.log to logs/host.log",
        f"{root.resolve()} is in the folder tree",
    ]


def everything(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.mark.parametrize("part", ["data", "cache/run", "backups/2026-10-26"])
def test_a_part_of_a_qmx_folder_is_refused_and_named_as_inside_it(
    tmp_path: Path, part: str
) -> None:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    for relative in ("data/control.db", "data/runs.db", "data/chats/chat-1.json"):
        (layout.root / relative).parent.mkdir(parents=True, exist_ok=True)
        (layout.root / relative).write_text("kept", encoding="utf-8")
    (layout.root / "cache/run/procs").mkdir(parents=True)
    (layout.root / "cache/run/procs/chat-1.json").write_text("kept", encoding="utf-8")
    (layout.root / "backups/2026-10-26").mkdir(parents=True)
    (layout.root / "backups/2026-10-26/control.db").write_text("kept", encoding="utf-8")
    before = everything(layout.root)
    inside = (layout.root / part).resolve()
    said = f"{inside} is inside the QMX folder {layout.root}; pass {layout.root}"

    with pytest.raises(NoQmxFolder) as not_opened:
        resolve(inside, create=True, drives=[])
    with pytest.raises(LayoutRefused) as not_moved:
        step_to_tree(inside)

    assert str(not_opened.value) == said
    assert str(not_moved.value) == f"{said}; nothing in it was moved"
    assert everything(layout.root) == before


def test_no_profile_folder_skips_only_the_profile_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def homeless() -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "home", staticmethod(homeless))
    documents = flat(tmp_path / "Documents", {"cv.docx": "cv"})
    home = flat(tmp_path / "home", {"control.db": "sqlite"})

    with pytest.raises(NoQmxFolder, match="is not a QMX folder"):
        resolve(documents, drives=[])
    moved = step_to_tree(home)

    assert moved == [("control.db", "data/control.db")]
    assert files(documents) == {"cv.docx": "cv"}


@pytest.mark.parametrize(
    "source",
    ["../outside.txt", "data/../../outside.txt", "{absolute}", "C:/outside.txt", "a\\\\..\\\\x"],
    ids=["dotdot", "dotdot-inside", "absolute", "drive", "backslash"],
)
def test_a_plan_naming_a_path_outside_the_folder_is_refused_and_nothing_moves(
    tmp_path: Path, source: str
) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("his", encoding="utf-8")
    named = source.replace("{absolute}", str(outside))
    plan = json.dumps([["control.db", "data/control.db"], [named, "data/outside.txt"]])
    root = flat(tmp_path / "home", {"control.db": "sqlite", "layout-step.json": plan})

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert str(refused.value) == (
        f"{root.resolve() / 'layout-step.json'} names {named!r} to 'data/outside.txt', which is "
        f"not a move the layout step makes inside {root.resolve()}; nothing was moved"
    )
    assert files(root) == {"control.db": "sqlite", "layout-step.json": plan}
    assert outside.read_text(encoding="utf-8") == "his"


def test_a_layout_plan_alone_does_not_make_a_folder_a_qmx_home(tmp_path: Path) -> None:
    plan = json.dumps([["Documents", "data/Documents"]])
    root = flat(tmp_path / "someone", {"Documents/cv.docx": "cv", "layout-step.json": plan})

    with pytest.raises(LayoutRefused, match="is not a QMX folder"):
        step_to_tree(root)

    assert files(root) == {"Documents/cv.docx": "cv", "layout-step.json": plan}


def test_a_fresh_folder_whose_labelling_stopped_finishes_on_the_next_run(tmp_path: Path) -> None:
    root = tmp_path / "QMX"
    for part in ("data", "keys", "backups", "cache", "logs"):
        (root / part).mkdir(parents=True)
    (root / "layout-step.json").write_text("[]", encoding="utf-8")

    assert step_to_tree(root) == []
    assert folders(root) == ["backups", "cache", "data", "keys", "logs", LABEL]


def test_a_plan_row_the_step_would_never_write_is_refused_and_nothing_moves(
    tmp_path: Path,
) -> None:
    plan = json.dumps([["Documents", "keys/Documents"]])
    before = {"data/control.db": "sqlite", "Documents/cv.docx": "cv", "layout-step.json": plan}
    root = flat(tmp_path / "home", before)

    with pytest.raises(LayoutRefused, match="which is not a move the layout step makes"):
        step_to_tree(root)

    assert files(root) == before


def test_a_flat_home_holding_a_qmx_folder_is_refused_and_nothing_moves(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", {"control.db": "sqlite"})
    inner = resolve(root / "QMX", create=True, drives=[])
    before = files(root)

    with pytest.raises(NoQmxFolder) as not_opened:
        resolve(root, drives=[])
    with pytest.raises(LayoutRefused):
        step_to_tree(root)

    assert str(not_opened.value) == (
        f"{root.resolve()} holds the QMX folder {inner.root}, which the layout step would move; "
        f"move it out of {root.resolve()} first"
    )
    assert files(root) == before
    assert (inner.root / LABEL).is_file()


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to move an open file")
def test_the_data_part_of_a_stopped_step_is_refused_and_the_step_still_finishes(
    tmp_path: Path,
) -> None:
    root = flat(tmp_path / "home", PC_HOME)
    with (root / "library" / "catalog.db").open("rb"), pytest.raises(LayoutRefused):
        step_to_tree(root)
    stopped = everything(root)
    assert stopped["data/chats/chat-1.json"] == PC_HOME["chats/chat-1.json"], "stopped part-way"
    data = (root / "data").resolve()
    said = (
        f"{data} is inside the QMX folder {root.resolve()}, whose layout step stopped; run "
        f"python -m qmx_home layout {root.resolve()} again"
    )

    with pytest.raises(NoQmxFolder) as not_opened:
        resolve(data, drives=[])
    with pytest.raises(LayoutRefused) as not_moved:
        step_to_tree(data)
    unchanged = everything(root)
    step_to_tree(root)

    assert str(not_opened.value) == said
    assert str(not_moved.value) == f"{said}; nothing in it was moved"
    assert unchanged == stopped
    assert files(root) == PC_TREE


def test_a_folder_with_a_label_that_cannot_be_read_still_holds_its_parts(tmp_path: Path) -> None:
    root = flat(tmp_path / "QMX", {LABEL: "not toml [", "data/control.db": "sqlite"})
    before = everything(root)
    data = (root / "data").resolve()
    said = f"{data} is inside the QMX folder {root.resolve()}; pass {root.resolve()}"

    with pytest.raises(NoQmxFolder) as not_opened:
        resolve(data, drives=[])
    with pytest.raises(LayoutRefused) as not_moved:
        step_to_tree(data)

    assert str(not_opened.value) == said
    assert str(not_moved.value) == f"{said}; nothing in it was moved"
    assert everything(root) == before


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows folds case and trailing dots")
@pytest.mark.parametrize("forged", ["Keys", "keys.", "keys ", "KEYS. "])
def test_a_plan_row_naming_keys_in_another_spelling_is_refused(tmp_path: Path, forged: str) -> None:
    plan = json.dumps([[forged, f"data/{forged}"]])
    before = {"data/control.db": "sqlite", "keys/vault.key": "private", "layout-step.json": plan}
    root = flat(tmp_path / "home", before)

    with pytest.raises(LayoutRefused, match="which is not a move the layout step makes"):
        step_to_tree(root)

    assert files(root) == before
