"""The format 1 to 2 layout step, run on flat homes shaped like a PC test home and a server home."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from qmx_home import LABEL, Label, Layout, LayoutRefused, resolve, step_to_tree
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


def files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != LABEL
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
    root = flat(tmp_path / "home", {"settings.toml": "", "cache/x": "mine"})

    with pytest.raises(LayoutRefused) as refused:
        step_to_tree(root)

    assert str(refused.value) == (
        f"{root.resolve()} already holds cache, which the tree uses; move it aside first"
    )
    assert files(root) == {"settings.toml": "", "cache/x": "mine"}


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to move an open file")
def test_a_step_stopped_by_an_open_file_finishes_on_the_next_run(tmp_path: Path) -> None:
    root = flat(tmp_path / "home", PC_HOME)

    with (root / "library" / "catalog.db").open("rb"), pytest.raises(LayoutRefused):
        step_to_tree(root)
    step_to_tree(root)

    assert files(root) == PC_TREE


def test_the_command_reports_each_move(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = flat(tmp_path / "home", {"settings.toml": "", "control.log": ""})

    assert main(["layout", str(root)]) == 0

    assert capsys.readouterr().out.splitlines() == [
        "moved settings.toml to data/settings.toml",
        "moved control.log to logs/host.log",
        f"{root.resolve()} is in the folder tree",
    ]
