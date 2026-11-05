"""A repair reaches an installed app at the next host start and keeps its data, and a signed money
app keeps running what he signed until he signs again.

The supervisor, its road and its env step are real. `uv` is a small real executable that records
each call and makes the env folder, so "a host start does not call uv" is read from what ran. The
apps run on this interpreter, as `sup_proof.py` runs them."""

from __future__ import annotations

import json
import secrets
import shutil
import stat
import sys
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from qmx_apps.errors import Document
from qmx_apps.manifest import Definition
from qmx_apps.road.models import Stage
from qmx_apps.supervisor import BUILT_FROM, Supervisor

import qmx_host.connect  # noqa: F401 - connect_node loads through it  # pyright: ignore[reportUnusedImport]
from qmx_host import first_start
from qmx_host.first_start import FIRST_PARTY, enable_first_party

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "exchange-status"
SECOND = "second"
SERVER = """\
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Repair fixture")


@mcp.tool(annotations={"readOnlyHint": True})
def ping() -> dict[str, bool]:
    return {"pong": True}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
"""
OWN_TEST = """\
import unittest


class OwnTests(unittest.TestCase):
    def test_it_runs(self):
        self.assertTrue(True)
"""
LIBRARY_LOCK = """
[[package]]
name = "fixture-library"
version = "1.0.0"
source = { editable = "../library" }
"""
RECORD_CALL = """\
import os, sys
from pathlib import Path

Path(os.environ["UV_PROJECT_ENVIRONMENT"]).mkdir(parents=True, exist_ok=True)
with Path(sys.argv[1]).open("a", encoding="utf-8") as calls:
    calls.write(os.environ["UV_PROJECT_ENVIRONMENT"] + "\\n")
"""


@dataclass
class World:
    home: Path
    root: Path
    calls: Path
    runtime: Supervisor

    @property
    def uv_calls(self) -> list[str]:
        if not self.calls.is_file():
            return []
        return [Path(line).name for line in self.calls.read_text("utf-8").splitlines()]

    def start_host(self) -> list[str]:
        """What a host start does: a new supervisor over the same folder, then the first-party
        loop. The supervisor it replaces has stopped every app."""
        self.runtime.close()
        self.runtime = Supervisor(self.home, secret_getter=lambda _s, _u: "fixture")
        self.runtime.road.signing_key(KEY)
        return enable_first_party(self.home, self.runtime)


KEY = secrets.token_urlsafe(32)


def recording_uv(root: Path, calls: Path) -> Path:
    script = root / "record_call.py"
    script.write_text(RECORD_CALL, "utf-8")
    if sys.platform == "win32":
        program = root / "uv.cmd"
        program.write_text(f'@"{sys.executable}" "{script}" "{calls}"\n', "utf-8")
    else:
        program = root / "uv"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "{calls}"\n', "utf-8")
        program.chmod(program.stat().st_mode | stat.S_IEXEC)
    return program


def app_folder(root: Path, app_id: str, *, risk: str = "shows") -> Path:
    """A shipped-style app folder beside a real library its lock builds from."""
    library = root / "library" / "src"
    library.mkdir(parents=True, exist_ok=True)
    (library / "fixture_library.py").write_text("VERSION = 1\n", "utf-8")
    folder = root / app_id
    shutil.copytree(EXAMPLE, folder, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (folder / "server.py").write_text(SERVER, "utf-8")
    manifest = folder / "app.toml"
    manifest.write_text(
        manifest.read_text("utf-8")
        .replace(f'id = "{APP}"', f'id = "{app_id}"')
        .replace('risk = "shows"', f'risk = "{risk}"'),
        "utf-8",
    )
    lock = folder / "uv.lock"
    lock.write_text(lock.read_text("utf-8") + LIBRARY_LOCK, "utf-8")
    (folder / "tests").mkdir()
    (folder / "tests/test_own.py").write_text(OWN_TEST, "utf-8")
    (folder / "proofs").mkdir()
    for stage, origin in (("sandbox", "recorded"), ("shadow", "live")):
        case = {"tool": "ping", "arguments": {}, "expected": {"pong": True}}
        (folder / f"proofs/{stage}.json").write_text(
            json.dumps({"source": origin, "cases": [case]}), "utf-8"
        )
    return folder


def repair(folder: Path, version: str) -> None:
    """A repair landed in this app: a file changed and the version moved, as PR mechanics say."""
    (folder / "server.py").write_text(SERVER + "\n# a repair\n", "utf-8")
    manifest = folder / "app.toml"
    text = manifest.read_text("utf-8").replace('version = "1.0.0"', f'version = "{version}"')
    manifest.write_text(text, "utf-8")


def repair_library(root: Path) -> None:
    (root / "library/src/fixture_library.py").write_text("VERSION = 2\n", "utf-8")


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[World]:
    calls = tmp_path / "uv-calls.txt"
    program = recording_uv(tmp_path, calls)
    found = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: str(program) if name == "uv" else found(name))
    monkeypatch.setattr(Supervisor, "python", lambda _self, _hash: Path(sys.executable))
    monkeypatch.setattr(first_start, "APP_FOLDERS", {})
    home = tmp_path / "QMX" / "data"
    made = World(home, tmp_path, calls, Supervisor(home, secret_getter=lambda _s, _u: "fixture"))
    made.runtime.road.signing_key(KEY)
    try:
        yield made
    finally:
        made.runtime.close()


def shipped(world: World, monkeypatch: pytest.MonkeyPatch, *folders: Path) -> None:
    named = {folder.name: folder for folder in folders}
    monkeypatch.setattr(first_start, "APP_FOLDERS", named)
    (world.home / FIRST_PARTY).write_text(json.dumps({"enable": list(named)}), "utf-8")


def stages_to_shadow(runtime: Supervisor, app_id: str, definition_hash: str) -> None:
    for stage in ("tests", "sandbox", "shadow"):
        runtime.road.advance(app_id, definition_hash, cast(Stage, stage), auto_publish=False)


def sign(runtime: Supervisor, app_id: str, definition_hash: str) -> None:
    active = runtime.road.active_revision(app_id)
    signature = runtime.road.sign(app_id, definition_hash, active)
    runtime.road.publish(app_id, definition_hash, active, signature)


def signed_money_app(world: World, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    folder = app_folder(world.root, APP, risk="money")
    shipped(world, monkeypatch, folder)
    installed = world.runtime.install(folder, trust="first_party")
    signed = str(installed["definition_hash"])
    stages_to_shadow(world.runtime, APP, signed)
    sign(world.runtime, APP, signed)
    world.runtime.stop(APP)
    return folder, signed


def notice_of(runtime: Supervisor, app_id: str) -> str:
    return str(runtime.status(app_id).get("notice", ""))


@pytest.mark.parametrize("published", [False, True], ids=["installed", "published"])
def test_a_changed_app_runs_its_new_hash_with_its_data_at_the_next_start(
    world: World, monkeypatch: pytest.MonkeyPatch, published: bool
) -> None:
    folder = app_folder(world.root, APP)
    shipped(world, monkeypatch, folder)
    assert world.start_host() == [APP]
    old = str(world.runtime.status(APP)["definition_hash"])
    marker = world.home / "apps" / APP / "data" / "marker.txt"
    marker.write_text("kept", "utf-8")
    if published:
        world.runtime.stop(APP)
        stages_to_shadow(world.runtime, APP, old)
        world.runtime.road.publish(APP, old, None)

    repair(folder, "1.0.1")
    new = Definition.load(folder).hash

    assert world.start_host() == [APP]
    status = world.runtime.status(APP)
    assert new != old
    assert status["status"] == "running"
    assert status["definition_hash"] == new
    assert status["version"] == "1.0.1"
    assert marker.read_text("utf-8") == "kept"
    assert "notice" not in status


def test_a_money_app_keeps_its_signed_version_until_he_signs(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder, signed = signed_money_app(world, monkeypatch)
    repair(folder, "1.0.1")
    new = Definition.load(folder).hash

    world.start_host()

    status = world.runtime.status(APP)
    assert status["status"] == "running"
    assert status["definition_hash"] == signed
    assert status["version"] == "1.0.0"
    assert world.runtime.get(APP)["definition_hash"] == new
    assert "1.0.1 waits for your signature" in notice_of(world.runtime, APP)
    assert "1.0.0 keeps running" in notice_of(world.runtime, APP)

    stages_to_shadow(world.runtime, APP, new)
    sign(world.runtime, APP, new)

    status = world.runtime.status(APP)
    assert (status["status"], status["definition_hash"]) == ("running", new)
    assert "notice" not in status


def test_a_library_repair_does_not_touch_a_signed_money_app(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    _folder, signed = signed_money_app(world, monkeypatch)
    record = world.runtime.environments / signed / BUILT_FROM
    recorded = record.read_bytes()
    builds = list(world.uv_calls)
    repair_library(world.root)

    world.start_host()

    status = world.runtime.status(APP)
    assert builds == [signed]
    assert world.uv_calls == builds
    assert record.read_bytes() == recorded
    assert status["status"] == "running"
    assert status["definition_hash"] == signed
    assert "library repair waits for a new signed version" in notice_of(world.runtime, APP)


def test_a_library_repair_rebuilds_a_non_money_app_with_its_data(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = app_folder(world.root, APP)
    shipped(world, monkeypatch, folder)
    world.start_host()
    definition_hash = str(world.runtime.status(APP)["definition_hash"])
    record = world.runtime.environments / definition_hash / BUILT_FROM
    recorded = cast(Document, json.loads(record.read_text("utf-8")))
    marker = world.home / "apps" / APP / "data" / "marker.txt"
    marker.write_text("kept", "utf-8")
    repair_library(world.root)

    world.start_host()

    rebuilt = cast(Document, json.loads(record.read_text("utf-8")))
    status = world.runtime.status(APP)
    assert world.uv_calls == [definition_hash, definition_hash]
    assert rebuilt["fixture-library"] != recorded["fixture-library"]
    assert (status["status"], status["definition_hash"]) == ("running", definition_hash)
    assert marker.read_text("utf-8") == "kept"

    world.start_host()

    assert world.uv_calls == [definition_hash, definition_hash], "an unchanged library builds nothing"


def test_one_bad_app_does_not_stop_the_others(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = app_folder(world.root, APP)
    good = app_folder(world.root, SECOND)
    shipped(world, monkeypatch, bad, good)
    assert world.start_host() == [APP, SECOND]
    old = str(world.runtime.status(APP)["definition_hash"])

    (bad / "server.py").write_text(SERVER + "\n# changed with no new version\n", "utf-8")

    assert world.start_host() == [APP, SECOND]
    status = world.runtime.status(APP)
    assert (status["status"], status["definition_hash"]) == ("running", old)
    assert "Changed content requires a new version" in str(status["notice"])
    assert world.runtime.status(SECOND)["status"] == "running"


def test_an_app_that_never_installed_is_named_and_the_next_one_starts(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    good = app_folder(world.root, SECOND)
    shipped(world, monkeypatch, world.root / "not-shipped", good)

    assert world.start_host() == [SECOND]

    assert "not-shipped" in capsys.readouterr().err
    assert world.runtime.status(SECOND)["status"] == "running"
