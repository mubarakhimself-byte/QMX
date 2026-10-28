"""One class table for every path of a QMX folder (design 06 section 2): what each path is,
which values of `settings.toml` are keys, and that every path the writers make has a rule."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from backup_fixtures import WRITER_APP, filled_folder

from qmx_home.classes import (
    NEVER,
    SENT,
    Class,
    class_of,
    rule_of,
    secret_paths,
    secret_values,
    sent,
    without,
)


@pytest.mark.parametrize(
    ("path", "kind", "expected"),
    [
        ("data/settings.toml", None, "recipe"),
        ("data/profiles/kimi.toml", None, "recipe"),
        ("data/apps.db", None, "recipe"),
        ("data/library/kinds/workflow.schema.json", None, "recipe"),
        ("data/library/objects/ab/cd/x.json", "workflow", "recipe"),
        ("data/library/objects/ab/cd/x.json", "backtest-result", "result"),
        ("data/library/objects/ab/cd/x.json", "note", "content"),
        ("data/library/objects/ab/cd/x.json", None, "content"),
        ("data/library/blobs/ab/cd/abcd", ("note", "strategy"), "recipe"),
        ("data/claude/projects/D--work/c.jsonl", None, "content"),
        ("data/chats/c1.json", None, "content"),
        ("data/apps/demo/app.db", None, "content"),
        ("data/apps/demo/road/steps.jsonl", None, "content"),
        ("data/migration/pre/library.db", None, "content"),
        ("data/a-path-no-rule-names.txt", None, "content"),
        ("data/engine/engine.sqlite", None, "result"),
        ("data/engine/runs/r1/trace-3.jsonl", None, "result"),
        ("data/control.db", None, "result"),
        ("data/market/binance/btc/ticks/raw/2026-01/state.json", None, "prices"),
        ("data/market/series/x/open.parquet", None, "prices"),
        ("data/library/catalog.db", None, "rebuildable"),
        ("data/memory/hindsight/pg/PG_VERSION", None, "rebuildable"),
        ("data/apps/demo/logs/app.log", None, "rebuildable"),
        ("cache/prices/p.parquet", None, "rebuildable"),
        ("logs/host.log", None, "rebuildable"),
        ("keys/vault.key", None, "secret"),
        ("data/vault/pairing-key", None, "secret"),
        ("data/rclone.conf", None, "secret"),
        ("data/rclone.conf.unreadable-20261028T030000Z", None, "secret"),
        ("data/claude/.credentials.json", None, "secret"),
        ("data/claude-relayed/projects", None, "scratch"),
        ("data/claude/settings.json", None, "scratch"),
        ("data/chats/c1/launch.json", None, "scratch"),
        ("data/apps/demo/app.db-wal", None, "scratch"),
        ("data/library/refs/.claims.json.0123456789abcdef0123456789abcdef", None, "scratch"),
        ("data/migration/restore-unfinished.txt", None, "scratch"),
    ],
)
def test_each_row_of_the_table_answers_its_class(
    path: str, kind: str | tuple[str, ...] | None, expected: str
) -> None:
    assert class_of(path, kind) == expected


def test_a_path_no_rule_names_reads_content_from_the_default_not_a_rule() -> None:
    assert rule_of("data/a-path-no-rule-names.txt") is None
    assert rule_of("data/settings.toml") is not None


def test_the_library_logs_travel_with_any_library_class_and_never_alone() -> None:
    assert sent("data/library/refs/log.jsonl", ("recipe",))
    assert sent("data/library/edges/pc.jsonl", ("result",))
    assert not sent("data/library/refs/log.jsonl", ("prices",))
    assert not sent("data/library/objects/ab/cd/x.json", ("recipe",), "note")


DRIVE_ROW = {
    "via": "rclone",
    "type": "drive",
    "can": ["keep"],
    "client_secret": "GOCSPX-publicDesktopClientSecret",
}


def test_secret_values_name_key_named_and_key_shaped_values_at_any_depth() -> None:
    settings: dict[str, object] = {
        "providers": [{"id": "kimi"}, {"id": "glm", "api_key": "k-planted-1"}],
        "connections": {"bot": {"token": "t-planted-2"}},
        "notes": {"innocent": "sk-ant-api03-planted3planted3planted3"},
        "engine": {"host_name": "pc", "placement": {"gdrive": DRIVE_ROW}},
        "elsewhere": "GOCSPX-publicDesktopClientSecret",
        "model": "sk-short",
    }

    found = secret_values(settings)

    assert found == {
        "providers[1].api_key": "k-planted-1",
        "connections.bot.token": "t-planted-2",
        "notes.innocent": "sk-ant-api03-planted3planted3planted3",
        "elsewhere": "GOCSPX-publicDesktopClientSecret",
    }
    assert without(settings, found) == {
        "providers": [{"id": "kimi"}, {"id": "glm"}],
        "connections": {"bot": {}},
        "notes": {},
        "engine": {"host_name": "pc", "placement": {"gdrive": DRIVE_ROW}},
        "model": "sk-short",
    }


@pytest.mark.parametrize(
    "name",
    [
        "key",
        "api_key",
        "apikey",
        "token",
        "password",
        "secret",
        "client_key",
        "access_token",
        "refresh_token",
        "bot_token",
        "private_key",
        "client_secret",
        "Access-Token",
        "SMTP_PASSWORD",
        "webhookSecret",
    ],
)
def test_a_value_under_a_name_that_ends_like_a_secret_is_named(name: str) -> None:
    assert secret_values({"connections": {"bot": {name: "planted-value"}}}) == {
        f"connections.bot.{name}": "planted-value"
    }


@pytest.mark.parametrize("name", ["max_tokens", "keep", "keys_to_fill", "token_budget", "host"])
def test_a_value_under_an_ordinary_name_is_not_named(name: str) -> None:
    assert secret_values({"engine": {name: "plain-value"}}) == {}


def test_a_table_named_by_the_operator_like_a_secret_keeps_its_ordinary_values() -> None:
    settings: dict[str, object] = {
        "engine": {
            "placement": {
                "usb-key": {
                    "id": "usb-key",
                    "via": "folder",
                    "path": "E:/qmx",
                    "can": ["copies"],
                    "api_key": "planted-usb",
                }
            }
        },
        "claude": {
            "remembered": {"d:/work/turkey": {"allow": ["Bash(git status)"]}},
            "access_token": "planted-claude",
        },
    }

    assert secret_values(settings) == {
        "engine.placement.usb-key.api_key": "planted-usb",
        "claude.access_token": "planted-claude",
    }


def test_only_a_drive_storage_rows_client_secret_travels() -> None:
    settings: dict[str, object] = {
        "engine": {
            "placement": {
                "gdrive": DRIVE_ROW,
                "onedrive": {**DRIVE_ROW, "type": "onedrive"},
                "folder": {"via": "folder", "client_secret": "planted-folder"},
            }
        },
        "connections": {"oauth": {"client_secret": "planted-oauth"}},
    }

    assert secret_values(settings) == {
        "engine.placement.onedrive.client_secret": "GOCSPX-publicDesktopClientSecret",
        "engine.placement.folder.client_secret": "planted-folder",
        "connections.oauth.client_secret": "planted-oauth",
    }


BLOB = "data/library/blobs/ab/cd/abcd"


@pytest.mark.parametrize(
    ("save", "expected"),
    [
        (("content",), True),
        (("recipe",), True),
        (("result",), False),
        (("prices",), False),
    ],
)
def test_a_blob_named_by_several_kinds_travels_with_any_kept_class_of_them(
    save: tuple[Class, ...], expected: bool
) -> None:
    assert sent(BLOB, save, ("strategy", "note")) is expected


def test_the_secret_paths_are_the_fixed_secret_rules() -> None:
    assert secret_paths() == (
        "keys",
        "data/vault",
        "data/vault-store.json",
        "data/passes",
        "data/rclone.conf",
        "data/claude/.credentials.json",
        "data/claude/.claude.json",
        "data/claude-relayed/.credentials.json",
        "data/claude-relayed/.claude.json",
    )


def walk(root: Path) -> tuple[list[str], list[str]]:
    """Every file and every link under `root`, relative to it, never through a link."""
    files: list[str] = []
    links: list[str] = []
    for folder, names, found in os.walk(root):
        here = Path(folder)
        for name in list(names):
            if (here / name).is_junction() or (here / name).is_symlink():
                links.append((here / name).relative_to(root).as_posix())
                names.remove(name)
        files += [(here / name).relative_to(root).as_posix() for name in found]
    return files, links


def test_every_path_the_writers_make_has_a_rule_and_the_classes_cover_the_whole_walk(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, writers=True)
    files, links = walk(filled.layout.root)

    unnamed = [path for path in files + links if rule_of(path) is None]
    assert unnamed == []
    assert links == ["data/claude-relayed/projects"]
    assert class_of("data/claude-relayed/projects") == "scratch"
    assert not [path for path in files if path.startswith("data/claude-relayed/projects/")]
    written = {class_of(path) for path in files}
    assert written == {*SENT, *NEVER}
    sent_paths = {p for p in files if class_of(p) in SENT}
    never = {p for p in files if class_of(p) in NEVER}
    assert sent_paths | never == set(files) and not sent_paths & never
    assert f"data/apps/{WRITER_APP}/road/steps.jsonl" in sent_paths
    assert f"data/apps/{WRITER_APP}/logs/app.log" in never
    assert any(p.startswith("data/market/series/") for p in sent_paths)
    assert any(p.startswith("data/library/objects/") for p in sent_paths)
