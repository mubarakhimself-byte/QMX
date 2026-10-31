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
from qmx_home import resolve
from qmx_router.vault import MemorySource, VaultKey, VaultStore, as_text

from qmx_control.node import (
    HOST_UNIT,
    UNIT_COPY,
    SessionLost,
    bootstrap_script,
    host_unit,
    layout_script,
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
MACHINE = "home-server"
"""The place name he gives the server at setup."""
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


class LateSwitch(Server):
    """A server whose queued switch-on fires only after `pending` status checks."""

    def __init__(self, pending: int) -> None:
        super().__init__()
        self.pending = pending

    def __call__(self, command: list[str], text: str | None) -> str:
        if command[-1].endswith("firewall status") and self.pending:
            self.pending -= 1
            self.sent.append(command[-1])
            return (
                "firewall    off: every door answers the internet, each behind its key; run: "
                "sudo qmx-recover firewall close  FAIL\n"
                "last close  still being switched on since 2026-10-25 09:00:00 UTC; "
                "check again in a few seconds  FAIL"
            )
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
        machine=MACHINE,
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
        "systemctl stop qmx-host || true",
        "systemctl enable --now qmx-host",
    ]
    assert any("node import --home /var/lib/qmx --root /srv/qmx/library" in s for s in server.sent)
    assert any("-m qmx_home layout /srv/qmx/home/.qmx\n" in s for s in server.sent), (
        "the server's folder is laid out as the tree"
    )
    assert "sudo cat /srv/qmx/home/.qmx/data/vault/pairing-key" in server.sent
    with (tmp_path / "settings.toml").open("rb") as handle:
        assert tomllib.load(handle) == {"library": {"hub_url": "http://100.64.0.9:8766"}}
    assert (tmp_path / "vault" / "pairing-key").read_text(encoding="utf-8") == "pairing-code\n"
    twin = (tmp_path / "bin" / "qmx-recover.conf").read_text(encoding="utf-8").splitlines()
    assert twin[:5] == [
        "TARGET=qmx-server",
        "SERVER_TAILNET=100.64.0.9",
        "SERVER_HOME=/srv/qmx/home/.qmx/data",
        f"QMX_FOLDER={tmp_path.resolve().parent}",
        f"QMX_HOME={tmp_path.resolve()}",
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
        machine=MACHINE,
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


def test_setup_waits_past_six_checks_for_a_late_switch_on_then_keeps_the_firewall(
    tmp_path: Path,
) -> None:
    server = LateSwitch(pending=6)
    done = setup(
        "qmx-server",
        tmp_path,
        machine=MACHINE,
        revision=REVISION,
        call=server,
        say=lambda _: None,
        sleep=server.sleep,
    )
    assert done == 0
    assert acts(server.sent)[:16] == [
        f"{RECOVER} firewall close",
        *["wait 5", f"sudo {RECOVER} firewall status"] * 7,
        f"sudo {RECOVER} firewall keep",
    ]
    assert acts(server.sent)[-1] == "systemctl enable --now qmx-host"


def test_setup_stops_when_the_firewall_never_says_on_and_lets_the_undo_fire(
    tmp_path: Path,
) -> None:
    server = LateSwitch(pending=1000)
    said: list[str] = []
    done = setup(
        "qmx-server",
        tmp_path,
        machine=MACHINE,
        revision=REVISION,
        call=server,
        say=said.append,
        sleep=server.sleep,
    )
    assert done == 1
    assert acts(server.sent) == [
        f"{RECOVER} firewall close",
        *["wait 5", f"sudo {RECOVER} firewall status"] * 18,
    ]
    assert said[-1].startswith(
        "The firewall did not say on within a minute and a half, so setup stops here. If it "
        "came on later, the undo switches it off within five minutes. The server said:\n"
        "firewall    off: "
    )
    assert said[-1].endswith("\nRun setup again once that is fixed.")
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


def test_the_import_and_the_host_unit_name_the_one_root_and_the_servers_place() -> None:
    steps = dict(setup_steps(REVISION, machine=MACHINE))
    importing = steps["import as qmx"]
    installed = steps["install the host"]
    exec_start = next(line for line in installed.splitlines() if line.startswith("ExecStart="))
    assert exec_start == (
        "ExecStart=/opt/qmx/qmx-agents/.venv/bin/python -m qmx_host serve --home "
        "/srv/qmx/home/.qmx --port 8766 --role server --place home-server"
        " --library-root /srv/qmx/library"
    )
    assert (
        f"install -D -o root -g root -m 644 /etc/systemd/system/qmx-host.service {UNIT_COPY}"
        in installed
    )
    assert importing.endswith("--root /srv/qmx/library\n")
    with pytest.raises(ValueError, match=r"^a place name is lowercase letters"):
        host_unit("server", "Home Server")


def test_an_update_keeps_the_place_name_setup_wrote_into_the_host_unit() -> None:
    unit_path = f"/etc/systemd/system/{HOST_UNIT}"
    recover = (Path(__file__).parents[1] / "src/qmx_control/qmx-recover.sh").read_text("utf-8")

    assert unit_path not in bootstrap_script(REVISION)
    assert unit_path not in layout_script()
    assert 'install -m 644 "$UNIT_COPY" "$UNIT_DIR/$HOST_UNIT.service"' in recover


def test_setup_without_the_servers_place_name_stops_before_anything_runs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def run(command: list[str], **_: object) -> str:
        raise AssertionError(f"ran {command}")

    monkeypatch.setattr("qmx_control.node.run", run)
    monkeypatch.setattr(sys, "argv", ["qmx", "node", "setup", "qmx-server", "--dry-run"])

    with pytest.raises(SystemExit) as stopped:
        main()

    assert stopped.value.code == 2
    assert capsys.readouterr().err.splitlines()[-1] == (
        "qmx: error: Name the server's place with --machine, the name its host runs under."
    )


def test_a_dry_run_prints_the_order_and_writes_nothing(tmp_path: Path) -> None:
    said: list[str] = []
    setup(
        "qmx-server",
        tmp_path,
        machine=MACHINE,
        revision=REVISION,
        call=Server(),
        say=said.append,
        dry_run=True,
    )
    assert [line for line in said if line.startswith("step ")] == [
        "step 1: bootstrap",
        "step 2: install the recovery script",
        "step 3: close the firewall",
        "step 4: install the host",
        "step 5: stop and disable the standalone Hub",
        "step 6: lay out the QMX folder",
        "step 7: move the pairing key and the control token",
        "step 8: import as qmx",
        "step 9: start the host",
    ]
    assert list(tmp_path.iterdir()) == []


def git_bash() -> str | None:
    """Bash, but never the WSL launcher Windows puts first on PATH."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    folders = Path(git).resolve().parents if git else ()
    return next((str(f / "bin/bash.exe") for f in folders if (f / "bin/bash.exe").is_file()), None)


BASH = git_bash()
needs_bash = pytest.mark.skipif(BASH is None, reason="no bash on this machine")


def posix(path: Path) -> str:
    """The path as bash names it (Git Bash's `/d/...` on Windows)."""
    assert BASH is not None
    shown = subprocess.run(
        [BASH, "-c", 'cygpath -u "$0" 2>/dev/null || echo "$0"', path.as_posix()],
        capture_output=True,
        text=True,
        check=True,
    )
    return shown.stdout.strip()


def run_as_root(
    folder: Path, script: str, stubs: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """`script` under bash in `folder`, with each of `stubs` standing in for a system tool."""
    assert BASH is not None
    (folder / "bin").mkdir(exist_ok=True)
    for name, body in stubs.items():
        tool = folder / "bin" / name
        tool.parent.mkdir(parents=True, exist_ok=True)
        tool.write_text(f"#!/usr/bin/env bash\n{body.strip()}\n", encoding="utf-8", newline="\n")
        tool.chmod(0o755)
    (folder / "step.sh").write_text(script, encoding="utf-8", newline="\n")
    return subprocess.run(
        [BASH, "-c", 'PATH="$PWD/bin:$PATH" exec bash step.sh'],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
    )


@needs_bash
def test_the_move_keeps_the_token_the_running_host_uses_and_takes_a_first_key(
    tmp_path: Path,
) -> None:
    home, keys, old = tmp_path / "QMX" / "data", tmp_path / "QMX" / "keys", tmp_path / "etc"
    for folder in (home / "vault", keys, old):
        folder.mkdir(parents=True)
    (keys / "control-token").write_text("in-use\n", encoding="utf-8")
    (old / "control-token").write_text("rerun\n", encoding="utf-8")
    (old / "pairing-key").write_text("first-key\n", encoding="utf-8")

    done = run_as_root(
        tmp_path, move_key_script(posix(home), posix(keys), posix(old)), {"chown": "exit 0"}
    )

    assert done.returncode == 0, done.stderr
    assert (keys / "control-token").read_text(encoding="utf-8") == "in-use\n"
    assert (home / "vault" / "pairing-key").read_text(encoding="utf-8") == "first-key\n"
    assert list(old.iterdir()) == []


FLAT_SERVER_HOME = {
    "settings.toml": "[library]\n",
    "vault/pairing-key": "planted-pairing\n",
    "vault/control-token": "planted-token\n",
    "vault-store.json": "{}",
    ".qmx/vault.key": "planted-vault-key",
}
LAID_OUT = {
    "data/settings.toml": "[library]\n",
    "data/vault/pairing-key": "planted-pairing\n",
    "keys/control-token": "planted-token\n",
    "data/vault-store.json": "{}",
    "keys/vault.key": "planted-vault-key",
}
SERVER_TOOLS = {
    "systemctl": """
echo "systemctl $*" >> "$PWD/calls.log"
[[ "$1" == is-active ]] && { cat "$PWD/host-state" 2>/dev/null || echo active; }
exit 0
""",
    "runuser": 'while [[ "$1" != -- ]]; do shift; done; shift; exec "$@"',
    "install": """
folder=0; paths=()
while (($#)); do
  case "$1" in -d) folder=1 ;; -o | -g | -m) shift ;; *) paths+=("$1") ;; esac
  shift
done
((folder)) && mkdir -p "${paths[@]}"
""",
}


@needs_bash
@pytest.mark.parametrize(
    ("before", "after"), [({}, {}), (FLAT_SERVER_HOME, LAID_OUT)], ids=["fresh", "flat"]
)
def test_the_layout_step_makes_the_servers_folder_the_tree_and_starts_a_running_host_again(
    tmp_path: Path, before: dict[str, str], after: dict[str, str]
) -> None:
    folder = tmp_path / "srv" / ".qmx"
    for name, text in before.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding="utf-8")
    venv = tmp_path / "venv"
    python = {"venv/bin/python": f'exec "{posix(Path(sys.executable))}" "$@"'}
    stubs = {**SERVER_TOOLS, **{f"../{name}": body for name, body in python.items()}}

    done = run_as_root(tmp_path, layout_script(posix(folder), posix(venv)), stubs)

    assert done.returncode == 0, done.stderr
    assert sorted(entry.name for entry in folder.iterdir()) == [
        "backups",
        "cache",
        "data",
        "keys",
        "logs",
        "qmx-home.toml",
    ]
    assert resolve(folder).home == folder.resolve() / "data"
    found = {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in folder.rglob("*")
        if path.is_file() and path.parent != folder
    }
    assert found == after
    assert (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines() == [
        "systemctl is-active qmx-host",
        "systemctl stop qmx-host",
        "systemctl start qmx-host",
    ]


@needs_bash
@pytest.mark.parametrize(
    ("state", "started"), [("failed", True), ("activating", True), ("inactive", False)]
)
def test_after_an_update_a_host_that_refused_the_flat_folder_runs_on_the_laid_out_one(
    tmp_path: Path, state: str, started: bool
) -> None:
    folder = tmp_path / "srv" / ".qmx"
    for name, text in FLAT_SERVER_HOME.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding="utf-8")
    (tmp_path / "host-state").write_text(f"{state}\n", encoding="utf-8")
    python = f'exec "{posix(Path(sys.executable))}" "$@"'
    stubs = {**SERVER_TOOLS, "../venv/bin/python": python}

    done = run_as_root(tmp_path, layout_script(posix(folder), posix(tmp_path / "venv")), stubs)

    assert done.returncode == 0, done.stderr
    assert resolve(folder).home == folder.resolve() / "data"
    assert (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines() == [
        "systemctl is-active qmx-host",
        "systemctl stop qmx-host",
        *(["systemctl start qmx-host"] if started else []),
    ]


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
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    argv = ["qmx", "node", "pair", "--home", str(layout.root), "--ssh-host", "qmx-server"]
    monkeypatch.setattr(sys, "argv", argv)

    assert main() == 0
    code = (layout.home / "vault" / "pairing-key").read_text(encoding="utf-8").strip()
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
