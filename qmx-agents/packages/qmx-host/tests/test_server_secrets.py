"""On role `server` an app's declared secrets come from the home's owner-only vault, because a
headless server's keyring has no backend (C-05d, Part C `BLAST-RADIUS.md` C8). Every test forces
keyring's `fail` backend, which is what such a server has, and every secret is a fake made here."""

from __future__ import annotations

import os
import secrets
import shutil
from collections.abc import Generator
from pathlib import Path

import keyring
import pytest
from keyring.backends import fail
from qma.harness import QmxHome
from qmx_apps.errors import AppError
from qmx_control.service import ControlService

from qmx_host.host import control_for, vault_secrets

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
APP = "exchange-status"
SERVER = """import os

from fastmcp import FastMCP

mcp = FastMCP("Vault secret fixture")


@mcp.tool()
def holds(value: str) -> dict[str, bool]:
    return {"holds": os.environ.get("DECLARED_SECRET") == value}


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
"""


@pytest.fixture(autouse=True)
def headless_keyring() -> Generator[None]:
    previous = keyring.get_keyring()
    keyring.set_keyring(fail.Keyring())
    try:
        yield
    finally:
        keyring.set_keyring(previous)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "folder" / "data"


@pytest.fixture
def app(tmp_path: Path) -> Path:
    target = tmp_path / "app"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    (target / "server.py").write_text(SERVER, encoding="utf-8")
    with (target / "app.toml").open("a", encoding="utf-8") as file:
        file.write('\n[capabilities.secrets]\nDECLARED_SECRET = "qmx/fixture-secret"\n')
    return target


@pytest.fixture
def value() -> str:
    return secrets.token_hex(16)


def vault_file(home: Path, name: str, content: str) -> Path:
    path = home / "vault" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if os.name == "posix":
        path.chmod(0o600)
    return path


def installed(control: ControlService, app: Path) -> ControlService:
    control.app_runtime().install(app, trust="first_party")
    return control


def files_holding(folder: Path, value: str) -> list[str]:
    """Every file under `folder` but the vault that holds `value`. A held `.lock` file stays
    unreadable on Windows and holds no text."""
    return [
        str(path.relative_to(folder))
        for path in folder.rglob("*")
        if path.is_file()
        and "vault" not in path.parts
        and path.suffix != ".lock"
        and value.encode() in path.read_bytes()
    ]


def test_a_server_starts_an_app_with_its_vault_secret(home: Path, app: Path, value: str) -> None:
    vault_file(home, "fixture-secret", value)
    control = installed(control_for("server", QmxHome(home)), app)
    try:
        runtime = control.app_runtime()
        assert runtime.start(APP)["status"] == "running"
        assert runtime.call(APP, "holds", {"value": value})["result"] == {"holds": True}
        runtime.stop(APP)
    finally:
        control.close()
    assert files_holding(home.parent, value) == []


def test_the_keyring_reader_fails_the_start_on_a_headless_server(home: Path, app: Path) -> None:
    control = installed(control_for("pc", QmxHome(home)), app)
    try:
        with pytest.raises(AppError) as refused:
            control.app_runtime().start(APP)
        errors = [
            (row["reason"], row["error_type"])
            for row in control.app_runtime().logs(APP)
            if row["event"] == "process_error"
        ]
    finally:
        control.close()
    assert refused.value.code == "start_failed"
    assert errors == [("startup_failed", "NoKeyringError")]


def test_a_missing_vault_file_refuses_the_start_by_name(home: Path, app: Path) -> None:
    control = installed(control_for("server", QmxHome(home)), app)
    try:
        with pytest.raises(AppError) as refused:
            control.app_runtime().start(APP)
    finally:
        control.close()
    assert (refused.value.code, str(refused.value)) == (
        "missing_secret",
        "Missing declared credential qmx/fixture-secret.",
    )


def test_an_unreadable_vault_file_is_refused_by_name(home: Path) -> None:
    unreadable = home / "vault" / "fixture-secret"
    unreadable.mkdir(parents=True)
    if os.name == "posix":
        unreadable.chmod(0o700)
    with pytest.raises(AppError) as refused:
        vault_secrets(home / "vault")("qmx/fixture-secret", "fixture-secret")
    error = "IsADirectoryError" if os.name == "posix" else "PermissionError"
    assert (refused.value.code, str(refused.value)) == (
        "vault_refused",
        f"The vault file for qmx/fixture-secret cannot be read ({error}).",
    )


@pytest.mark.parametrize(
    "service",
    ["qmx/../outside", "qmx/sub/name", "qmx/sub\\name", "qmx/pairing-key", "qmx/control-token"],
)
def test_a_name_outside_the_apps_vault_is_refused(home: Path, value: str, service: str) -> None:
    vault_file(home, "pairing-key", value)
    (home / "outside").write_text(value, encoding="utf-8")
    with pytest.raises(AppError) as refused:
        vault_secrets(home / "vault")(service, service.split("/", 1)[1])
    assert (refused.value.code, str(refused.value)) == (
        "vault_refused",
        f"{service!r} is not a secret an app may declare.",
    )


@pytest.mark.skipif(os.name != "posix", reason="Windows mode bits hold no ACL to read")
def test_a_vault_file_others_can_read_is_refused_by_name(home: Path, value: str) -> None:
    vault_file(home, "fixture-secret", value).chmod(0o644)
    with pytest.raises(AppError) as refused:
        vault_secrets(home / "vault")("qmx/fixture-secret", "fixture-secret")
    assert (refused.value.code, str(refused.value)) == (
        "vault_refused",
        "The vault file for qmx/fixture-secret is readable by others; chmod 600 it.",
    )
