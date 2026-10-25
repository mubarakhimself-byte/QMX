"""`qmx node setup`, `rebuild`, `pair` and `vault install` make the server ready to be home
(WRAPUP-PLAN WU9 and WU9b; DATA-PLAN DR2B, DR2D; engine AD-71)."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tomllib
from collections.abc import Sequence
from pathlib import Path

import pytest
from qmx_router.vault import MemorySource, VaultKey, VaultStore, as_text

from qmx_control.node import (
    SessionLost,
    host_unit,
    main,
    move_key_script,
    pair,
    pc_vault_document,
    rebuild,
    run,
    setup,
    setup_steps,
    source_archive,
)

REVISION = "0" * 40
RECOVER = "/usr/local/sbin/qmx-recover"


class Server:
    """The commands setup sends, answered as a fresh server would."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def __call__(self, command: list[str], text: str | None) -> str:
        self.sent.append(text if text is not None else command[-1])
        if command[-1] == "tailscale ip -4":
            return "100.64.0.9\n"
        if command[-1].startswith("sudo cat "):
            return "pairing-code\n"
        if command[-1].endswith("firewall status"):
            return (
                "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS\n"
                "last close  switched on at 2026-10-25 09:00:03 UTC  PASS"
            )
        return "PASS host"

    def sleep(self, seconds: float) -> None:
        self.sent.append(f"wait {seconds:g}")


class DropsOnClose(Server):
    """A server that resets the session which ran the close, as the real one did."""

    def __call__(self, command: list[str], text: str | None) -> str:
        answer = super().__call__(command, text)
        if text is not None and "firewall close" in text:
            raise SessionLost("ssh failed (255); inspect the node logs.")
        return answer


class ShutOut(Server):
    """A server whose fresh SSH login fails once the firewall is on."""

    def __call__(self, command: list[str], text: str | None) -> str:
        if command[-1].endswith("firewall status"):
            self.sent.append(command[-1])
            raise SessionLost("ssh failed (255); inspect the node logs.")
        return super().__call__(command, text)


def acts(sent: Sequence[str]) -> list[str]:
    """The service, firewall, wait and login acts setup sent after the bootstrap, in order."""
    return [
        line
        for text in sent[1:]
        for line in text.splitlines()
        if line.startswith(("systemctl", RECOVER, f"sudo {RECOVER}", "wait"))
    ]


@pytest.mark.parametrize("server", [Server(), DropsOnClose()], ids=["kept", "dropped"])
def test_setup_keeps_the_firewall_after_a_fresh_login_says_on_then_starts_the_host(
    tmp_path: Path, server: Server
) -> None:
    done = setup(
        "qmx-server",
        tmp_path,
        revision=REVISION,
        call=server,
        say=lambda _: None,
        sleep=server.sleep,
    )
    assert done == 0
    assert acts(server.sent) == [
        f"{RECOVER} firewall close",
        "wait 5",
        f"sudo {RECOVER} firewall status",
        f"sudo {RECOVER} firewall keep",
        "systemctl daemon-reload",
        "systemctl stop qmx-host || true",
        "systemctl disable --now qmx-hub qmx-node",
        "systemctl enable --now qmx-host",
    ]
    assert any("node import --home /var/lib/qmx --root /srv/qmx/library" in s for s in server.sent)
    with (tmp_path / "settings.toml").open("rb") as handle:
        assert tomllib.load(handle) == {"library": {"hub_url": "http://100.64.0.9:8766"}}
    assert (tmp_path / "vault" / "pairing-key").read_text(encoding="utf-8") == "pairing-code\n"
    twin = (tmp_path / "bin" / "qmx-recover.conf").read_text(encoding="utf-8").splitlines()
    assert twin[:3] == [
        "TARGET=qmx-server",
        "SERVER_TAILNET=100.64.0.9",
        "SERVER_HOME=/srv/qmx/home/.qmx",
    ]
    assert (
        (tmp_path / "bin" / "qmx-recover.ps1")
        .read_text(encoding="utf-8")
        .startswith("# qmx-recover.ps1")
    )


def test_a_failed_fresh_login_stops_setup_before_the_host_and_lets_the_undo_fire(
    tmp_path: Path,
) -> None:
    server = ShutOut()
    said: list[str] = []
    done = setup(
        "qmx-server",
        tmp_path,
        revision=REVISION,
        call=server,
        say=said.append,
        sleep=server.sleep,
    )
    assert done == 1
    assert acts(server.sent) == [
        f"{RECOVER} firewall close",
        "wait 5",
        f"sudo {RECOVER} firewall status",
    ]
    assert said[-1] == (
        "A fresh SSH login to the server failed after the firewall closed. The undo switches the "
        "firewall off within five minutes; then run setup again. If SSH stays shut, Contabo's VNC "
        "console is the way back: log in there and run: sudo qmx-recover firewall open"
    )
    assert list(tmp_path.iterdir()) == []


def test_a_dropped_ssh_session_is_told_apart_from_a_command_that_failed(tmp_path: Path) -> None:
    def ssh_exiting(code: int) -> str:
        folder = tmp_path / str(code)
        folder.mkdir()
        if os.name == "nt":
            path = folder / "ssh.bat"
            path.write_text(f"@exit /b {code}\r\n", encoding="utf-8")
        else:
            path = folder / "ssh"
            path.write_text(f"#!/bin/sh\nexit {code}\n", encoding="utf-8")
            path.chmod(0o755)
        return str(path)

    with pytest.raises(SessionLost):
        run([ssh_exiting(255), "qmx-server", "true"])
    with pytest.raises(RuntimeError) as failed:
        run([ssh_exiting(1), "qmx-server", "true"])
    assert type(failed.value) is RuntimeError


def test_the_import_and_the_host_unit_name_the_one_root() -> None:
    importing = dict(setup_steps(REVISION))["import as qmx"]
    exec_start = next(line for line in host_unit().splitlines() if line.startswith("ExecStart="))
    assert exec_start == (
        "ExecStart=/opt/qmx/qmx-agents/.venv/bin/python -m qmx_host serve --home "
        "/srv/qmx/home/.qmx --port 8766 --role server --library-root /srv/qmx/library"
    )
    assert importing.endswith("--root /srv/qmx/library\n")


def test_a_dry_run_prints_the_order_and_writes_nothing(tmp_path: Path) -> None:
    said: list[str] = []
    setup("qmx-server", tmp_path, revision=REVISION, call=Server(), say=said.append, dry_run=True)
    assert [line for line in said if line.startswith("step ")] == [
        "step 1: bootstrap",
        "step 2: install the recovery script",
        "step 3: close the firewall",
        "step 4: install the host",
        "step 5: stop and disable the standalone Hub",
        "step 6: move the pairing key and the control token",
        "step 7: import as qmx",
        "step 8: start the host",
    ]
    assert list(tmp_path.iterdir()) == []


def git_bash() -> str | None:
    """Bash, but never the WSL launcher Windows puts first on PATH."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    folders = Path(git).resolve().parents if git else ()
    return next((str(f / "bin/bash.exe") for f in folders if (f / "bin/bash.exe").is_file()), None)


def test_the_move_keeps_the_token_the_running_host_uses_and_takes_a_first_key(
    tmp_path: Path,
) -> None:
    bash = git_bash()
    if bash is None:
        pytest.skip("no bash on this machine")
    home, old, stubs = tmp_path / "home", tmp_path / "etc", tmp_path / "bin"
    for folder in (home / "vault", old, stubs):
        folder.mkdir(parents=True)
    (stubs / "chown").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (stubs / "chown").chmod(0o755)
    (home / "vault" / "control-token").write_text("in-use\n", encoding="utf-8")
    (old / "control-token").write_text("rerun\n", encoding="utf-8")
    (old / "pairing-key").write_text("first-key\n", encoding="utf-8")

    def posix(path: Path) -> str:
        shown = subprocess.run(
            [bash, "-c", 'cygpath -u "$0" 2>/dev/null || echo "$0"', path.as_posix()],
            capture_output=True,
            text=True,
            check=True,
        )
        return shown.stdout.strip()

    (tmp_path / "move.sh").write_text(
        move_key_script(posix(home), posix(old)), encoding="utf-8", newline="\n"
    )
    done = subprocess.run(
        [bash, "-c", 'PATH="$PWD/bin:$PATH" exec bash move.sh'],
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    assert (home / "vault" / "control-token").read_text(encoding="utf-8") == "in-use\n"
    assert (home / "vault" / "pairing-key").read_text(encoding="utf-8") == "first-key\n"
    assert list(old.iterdir()) == []


def test_the_source_archive_ships_shell_scripts_with_lf_from_an_autocrlf_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("no git on this machine")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repository = tmp_path / "repository"
    repository.mkdir()

    def git_in(*words: str) -> str:
        done = subprocess.run(
            [git, "-C", str(repository), *words], capture_output=True, text=True, check=True
        )
        return done.stdout.strip()

    git_in("init", "-q")
    git_in("config", "core.autocrlf", "true")
    (repository / "start.sh").write_bytes(b"#!/usr/bin/env bash\necho up\n")
    git_in("add", "start.sh")
    tree = git_in("write-tree")
    revision = git_in(
        "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit-tree", tree, "-m", "s"
    )

    archive = source_archive(git, str(repository), revision)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        member = tar.extractfile("start.sh")
        assert member is not None
        assert member.read() == b"#!/usr/bin/env bash\necho up\n"


def test_pair_hands_the_new_code_to_the_servers_recovery_script_on_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[tuple[list[str], str | None]] = []

    def run(command: list[str], *, input_text: str | None = None) -> str:
        sent.append((command, input_text))
        return ""

    monkeypatch.setattr("qmx_control.node.run", run)

    def which(_: str) -> str:
        return "ssh"

    monkeypatch.setattr("qmx_control.node.shutil.which", which)
    argv = ["qmx", "node", "pair", "--home", str(tmp_path), "--ssh-host", "qmx-server"]
    monkeypatch.setattr(sys, "argv", argv)

    assert main() == 0
    code = (tmp_path / "vault" / "pairing-key").read_text(encoding="utf-8").strip()
    assert sent == [(["ssh", "qmx-server", f"sudo {RECOVER} pair --from-stdin"], code)]


def test_rebuild_stops_the_services_before_it_restores(tmp_path: Path) -> None:
    calls: list[Sequence[str]] = []

    def runner(call: Sequence[str]) -> str:
        calls.append(call)
        return ""

    found = rebuild(remote="bucket", root=tmp_path / "library", runner=runner)
    assert calls[0] == ("systemctl", "stop", "qmx-host", "qmx-hub")
    assert [call[1] for call in calls[1:]] == ["copy"] * 4 + ["copyto"] * 2
    assert found["restored"] is True


def test_re_pairing_keeps_the_outgoing_key_for_its_passes(tmp_path: Path) -> None:
    pair(tmp_path, "first")
    (tmp_path / "vault" / "run-pass-key").write_bytes(b"x" * 32)
    pair(tmp_path, "second")
    vault = tmp_path / "vault"
    assert (vault / "pairing-key").read_text(encoding="utf-8") == "second\n"
    assert (vault / "pairing-key.previous").read_text(encoding="utf-8") == "first\n"
    assert not (vault / "run-pass-key").exists()


def test_the_pcs_vault_document_opens_on_the_server_and_carries_no_trade_key(
    tmp_path: Path,
) -> None:
    server_key = VaultKey.generate()
    source = MemorySource(
        {
            "qmx/read/ctrader-app": '{"clientId":"id","clientSecret":"app"}',
            "qmx/openrouter": "model-key",
            "qmx/ctrader-live": "trade-key",
        }
    )
    document = json.loads(
        pc_vault_document(
            tmp_path, as_text(server_key.public_bytes()), machine="contabo", source=source
        )
    )
    copy = VaultStore("contabo")
    copy.sync(document)
    assert copy.names() == ("qmx/openrouter", "qmx/read/ctrader-app")
    assert copy.open("qmx/read/ctrader-app", server_key) == '{"clientId":"id","clientSecret":"app"}'
    assert "trade-key" not in json.dumps(document)
    assert source.values["qmx/ctrader-live"] == "trade-key"
