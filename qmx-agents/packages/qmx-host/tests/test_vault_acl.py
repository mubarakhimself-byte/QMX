"""The home's vault is readable by this user alone on every machine, repaired at start, and read
through one handle that never follows a link (C-32). Every vault is a throwaway folder under
pytest's tmp folder, and every key in it is a fake made here."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from qmx_apps.errors import AppError
from qmx_home import resolve

import qmx_host.host
import qmx_host.vault_acl
from qmx_host.host import pairing_key, serve_forever, vault_secrets
from qmx_host.vault_acl import VaultRefused, owner_only

windows = pytest.mark.skipif(sys.platform != "win32", reason="the vault's DACL is Windows only")
posix = pytest.mark.skipif(sys.platform == "win32", reason="mode bits are owner-only on POSIX")
USERS = "*S-1-5-32-545"
FAKE = "fake-key-made-by-this-test"
HARD_LINK = "has another name outside the vault (a hard link)"


def me() -> str:
    found = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return found.stdout.strip().rsplit(",", 1)[-1].strip('"')


def acl(path: Path, saved: Path) -> str:
    """The path's DACL as Windows writes it, read with `icacls /save`, not with this module."""
    target = saved / f"{path.name}.acl"
    subprocess.run(["icacls", str(path), "/save", str(target)], capture_output=True, check=True)  # noqa: S607
    return target.read_text(encoding="utf-16-le").splitlines()[1]


def access(path: Path, saved: Path) -> str:
    """Who may open the path: its DACL on Windows, its mode bits on POSIX."""
    if sys.platform == "win32":
        return acl(path, saved)
    return oct(stat.S_IMODE(path.stat().st_mode))


def grant_users_read(path: Path) -> None:
    rights = "(OI)(CI)R" if path.is_dir() else "R"
    granted = ["icacls", str(path), "/grant", f"{USERS}:{rights}"]
    subprocess.run(granted, capture_output=True, check=True)


def loosen(vault: Path) -> None:
    """Let other users in, so a start that went ahead would have to rewrite the vault's access."""
    if sys.platform == "win32":
        grant_users_read(vault)
    else:
        vault.chmod(0o755)


def planted(vault: Path, name: str = "pairing-key") -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    path = vault / name
    path.write_text(FAKE, encoding="utf-8")
    return path


def outside(tmp_path: Path) -> Path:
    path = tmp_path / "outside"
    path.write_text("outside-value", encoding="utf-8")
    return path


@windows
def test_a_new_vault_lets_in_only_this_user_and_system(tmp_path: Path) -> None:
    vault = tmp_path / "data" / "vault"

    assert owner_only(vault) == "made"
    key = planted(vault)

    user = me()
    assert acl(vault, tmp_path) == f"D:PAI(A;OICI;FA;;;{user})(A;OICI;FA;;;SY)"
    assert acl(key, tmp_path) == f"D:AI(A;ID;FA;;;{user})(A;ID;FA;;;SY)"
    assert owner_only(vault) == "kept"


@windows
def test_a_vault_users_can_read_is_repaired(tmp_path: Path) -> None:
    vault = tmp_path / "data" / "vault"
    key = planted(vault)
    granted = planted(vault, "run-pass-key")
    grant_users_read(vault)
    grant_users_read(granted)
    assert "BU)" in acl(key, tmp_path)

    assert owner_only(vault) == "repaired"

    user = me()
    assert acl(vault, tmp_path) == f"D:PAI(A;OICI;FA;;;{user})(A;OICI;FA;;;SY)"
    assert acl(key, tmp_path) == f"D:AI(A;ID;FA;;;{user})(A;ID;FA;;;SY)"
    assert acl(granted, tmp_path) == f"D:PAI(A;;FA;;;{user})(A;;FA;;;SY)"
    assert owner_only(vault) == "kept"


@windows
def test_a_vault_that_passes_nothing_down_to_new_files_is_repaired(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    user = me()
    only_here = ["icacls", str(vault), "/grant:r", f"*{user}:F", "*S-1-5-18:F"]
    subprocess.run(only_here, capture_output=True, check=True)
    subprocess.run(["icacls", str(vault), "/inheritance:r"], capture_output=True, check=True)  # noqa: S607
    assert acl(vault, tmp_path) == f"D:PAI(A;;FA;;;SY)(A;;FA;;;{user})"

    assert owner_only(vault) == "repaired"

    assert acl(vault, tmp_path) == f"D:PAI(A;OICI;FA;;;{user})(A;OICI;FA;;;SY)"
    assert owner_only(vault) == "kept"


@windows
def test_a_vault_file_another_user_owns_refuses_the_start_and_nothing_is_rewritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """This user cannot make a file another user owns (no SeRestorePrivilege), so the owner Windows
    reports for the planted key is stubbed with another user's SID."""
    vault = tmp_path / "vault"
    key = planted(vault)
    loosen(vault)
    held = (acl(vault, tmp_path), acl(key, tmp_path))
    owner_of = qmx_host.vault_acl._owner_of  # pyright: ignore[reportPrivateUsage]

    def planter_owns_the_key(path: Path) -> str:
        return "S-1-5-21-1111111111-2222222222-3333333333-1001" if path == key else owner_of(path)

    monkeypatch.setattr(qmx_host.vault_acl, "_owner_of", planter_owns_the_key)

    with pytest.raises(VaultRefused) as refused:
        owner_only(vault)

    assert str(refused.value) == (
        f"your keys folder holds {key}, which belongs to another user, so QMX cannot make it "
        "readable by you alone; give it back to your user, then start QMX again"
    )
    assert (acl(vault, tmp_path), acl(key, tmp_path)) == held


@posix
def test_on_linux_the_vault_is_0700_and_each_file_0600(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh" / "vault"
    assert owner_only(fresh) == "made"
    vault = tmp_path / "data" / "vault"
    key = planted(vault)
    vault.chmod(0o755)
    key.chmod(0o644)

    assert owner_only(vault) == "repaired"

    modes = [stat.S_IMODE(path.stat().st_mode) for path in (fresh, vault, key)]
    assert modes == [0o700, 0o700, 0o600]
    assert owner_only(vault) == "kept"


def test_a_link_in_the_vault_refuses_the_start_and_leaves_its_target_alone(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    planted(vault)
    target = tmp_path / "elsewhere"
    target.mkdir()
    if sys.platform == "win32":
        import _winapi

        link = vault / "elsewhere"
        _winapi.CreateJunction(str(target), str(link))
    else:
        link = vault / "pairing-key.previous"
        target = outside(tmp_path)
        link.symlink_to(target)
    loosen(vault)
    held = access(target, tmp_path)

    with pytest.raises(VaultRefused) as refused:
        owner_only(vault)

    assert str(refused.value) == (
        f"{link} in your keys folder is a link, and QMX reads no key through a link; remove the "
        "link, then start QMX again"
    )
    assert access(target, tmp_path) == held


def test_a_hard_link_in_the_vault_refuses_the_start_and_leaves_the_other_name_alone(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    planted(vault, "run-pass-key")
    elsewhere = outside(tmp_path)
    os.link(elsewhere, vault / "pairing-key")
    loosen(vault)
    held = access(elsewhere, tmp_path)

    with pytest.raises(VaultRefused) as refused:
        owner_only(vault)

    assert str(refused.value) == (
        f"{vault / 'pairing-key'} in your keys folder {HARD_LINK}; remove it, then start QMX again"
    )
    assert access(elsewhere, tmp_path) == held


def test_an_apps_secret_that_is_a_hard_link_is_refused_and_never_read(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    planted(vault, "other-secret")
    owner_only(vault)
    os.link(outside(tmp_path), vault / "fixture-secret")
    read = vault_secrets(vault)

    with pytest.raises(AppError) as refused:
        read("qmx/fixture-secret", "fixture-secret")

    assert (refused.value.code, str(refused.value)) == (
        "vault_refused",
        f"The vault file for qmx/fixture-secret {HARD_LINK}.",
    )
    assert read("qmx/other-secret", "other-secret") == FAKE
    assert read("qmx/missing", "missing") is None


def test_an_apps_secret_that_is_a_link_is_refused_and_never_read(tmp_path: Path) -> None:
    """A junction on Windows, which needs no privilege to make; a symlink elsewhere."""
    vault = tmp_path / "vault"
    owner_only(vault)
    if sys.platform == "win32":
        import _winapi

        (tmp_path / "elsewhere").mkdir()
        _winapi.CreateJunction(str(tmp_path / "elsewhere"), str(vault / "fixture-secret"))
    else:
        (vault / "fixture-secret").symlink_to(outside(tmp_path))

    with pytest.raises(AppError) as refused:
        vault_secrets(vault)("qmx/fixture-secret", "fixture-secret")

    assert (refused.value.code, str(refused.value)) == (
        "vault_refused",
        "The vault file for qmx/fixture-secret is a link, and QMX reads no key through a link.",
    )


def test_the_pairing_key_reads_through_the_vault_and_a_hard_link_stops_it(
    tmp_path: Path,
) -> None:
    home = tmp_path / "data"
    key = planted(home / "vault")
    owner_only(home / "vault")
    read = pairing_key(home)
    assert read() == FAKE

    key.unlink()
    os.link(outside(tmp_path), key)

    with pytest.raises(VaultRefused) as refused:
        read()
    assert str(refused.value) == f"the vault file pairing-key {HARD_LINK}"


def test_a_start_on_a_vault_holding_a_link_stops_with_one_line_and_exit_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = resolve(tmp_path / "QMX", create=True, drives=[]).home
    os.link(outside(tmp_path), planted(home / "vault", "run-pass-key").with_name("pairing-key"))

    def opened(*_args: object) -> object:
        raise AssertionError("the host went past a vault it refused")

    monkeypatch.setattr(qmx_host.host, "control_for", opened)

    code = serve_forever(home, port=0, role="pc", ui_origin="", scrubbed=(), keep=())

    assert code == 2
    assert capsys.readouterr().err == (
        f"QMX did not start: {home / 'vault' / 'pairing-key'} in your keys folder {HARD_LINK}; "
        "remove it, then start QMX again\n"
    )
