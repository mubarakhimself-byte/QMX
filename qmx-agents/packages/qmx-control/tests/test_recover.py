"""`qmx-recover`, the server's way back in without an agent (engine AD-71, ruling 139), run under
bash with stub system tools that log what they were asked."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "src" / "qmx_control" / "qmx-recover.sh"
PLANTED = {
    "pairing-key": "planted-pairing-key-4f1c",
    "control-token": "planted-control-token-9a7e",
}
VAULT_VALUE = "planted-vault-ciphertext-77d2"

STUBS = {
    "systemctl": """
echo "systemctl $*" >> "$PWD/calls.log"
unit="${@: -1}"
case "$1" in
  show) [[ "$3" == LoadState ]] && echo loaded || echo exit-code ;;
  is-active) [[ -e "$PWD/state/stopped-$unit" ]] && { echo inactive; exit 3; } || echo active ;;
  stop) touch "$PWD/state/stopped-$unit" ;;
  start | restart | try-restart) rm -f "$PWD/state/stopped-$unit" ;;
esac
exit 0
""",
    "ufw": """
echo "ufw $*" >> "$PWD/calls.log"
case "$*" in
  "status verbose")
    [[ -e "$PWD/state/ufw-on" ]] || { echo 'Status: inactive'; exit 0; }
    printf 'Status: active\\nDefault: deny (incoming)\\n' ;;
  "--force enable") touch "$PWD/state/ufw-on" ;;
  "--force disable") rm -f "$PWD/state/ufw-on" ;;
esac
""",
    "sshd": '[[ -e "$PWD/state/no-sshd" ]] || printf "port 22\\nlistenaddress 0.0.0.0:22\\n"',
    "systemd-run": """
echo "systemd-run $*" >> "$PWD/calls.log"
unit=
while [[ "${1:-}" == --* ]]; do
  [[ "$1" == --unit ]] && { unit="$2"; shift; }
  shift
done
printf '%q ' "$@" > "$PWD/state/queued-$unit"
""",
    "journalctl": 'echo "journalctl $*" >> "$PWD/calls.log"',
    "tailscale": '[[ "$1" == ip ]] && echo 100.64.0.9; exit 0',
    "curl": '[[ -e "$PWD/state/stopped-qmx-host" ]] && printf 000 || printf 401',
    "chown": 'echo "chown $*" >> "$PWD/calls.log"',
    "uv": 'echo "uv $*" >> "$PWD/calls.log"; exit 1',
    "install": """
echo "install $*" >> "$PWD/calls.log"
folder=0; paths=()
while (($#)); do
  case "$1" in -d) folder=1 ;; -D) ;; -o | -g | -m) shift ;; *) paths+=("$1") ;; esac
  shift
done
if ((folder)); then mkdir -p "${paths[@]}"; else cp "${paths[0]}" "${paths[1]}"; fi
""",
}


def git_bash() -> str | None:
    """Bash, but never the WSL launcher Windows puts first on PATH."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    folders = Path(git).resolve().parents if git else ()
    return next((str(f / "bin/bash.exe") for f in folders if (f / "bin/bash.exe").is_file()), None)


BASH = git_bash()
pytestmark = pytest.mark.skipif(BASH is None, reason="no bash on this machine")


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


class Server:
    """A scratch server: a QMX folder still in the flat layout an earlier setup built, with a
    planted key and token, a Library, stubs and a conf. `home` is the folder's `data/`."""

    def __init__(self, root: Path, **conf: str) -> None:
        assert BASH is not None
        self.root = root
        self.folder = root / "QMX"
        self.home = self.folder / "data"
        for folder in (self.folder / "vault", root / "library", root / "bin", root / "state"):
            folder.mkdir(parents=True)
        for name, value in PLANTED.items():
            (self.folder / "vault" / name).write_text(value + "\n", encoding="utf-8")
        (self.folder / "vault-store.json").write_text(
            f'{{"entries": [{{"name": "qmx/openrouter", "value": "{VAULT_VALUE}"}}]}}',
            encoding="utf-8",
        )
        (root / "defaults-ufw").write_text("IPV6=yes\n", encoding="utf-8")
        (root / "venv" / "bin").mkdir(parents=True)
        python = posix(Path(sys.executable))
        stubs = {
            **STUBS,
            "python3": f'exec "{python}" "$@"',
            "runuser": 'while [[ "$1" != -- ]]; do shift; done; shift; exec "$@"',
            "../venv/bin/python": f'[[ "$1" == -m ]] && exec "{python}" "$@"; exit 0',
        }
        for name, body in stubs.items():
            path = root / "bin" / name
            path.write_text(
                f"#!/usr/bin/env bash\n{body.strip()}\n", encoding="utf-8", newline="\n"
            )
            path.chmod(0o755)
        settings = {
            "QMX_FOLDER": posix(self.folder),
            "QMX_HOME": posix(self.home),
            "QMX_KEYS": posix(self.folder / "keys"),
            "LIBRARY": posix(root / "library"),
            "VENV": posix(root / "venv"),
            "UFW_DEFAULTS": posix(root / "defaults-ufw"),
            "OLD_VAULT": posix(root / "etc-vault"),
            "UNIT_COPY": posix(root / "no-unit-copy"),
            "WAIT_S": "3",
            **conf,
        }
        rows = "".join(f"{key}={value}\n" for key, value in settings.items())
        (root / "recover.conf").write_text(rows, encoding="utf-8", newline="\n")

    def run(self, *words: str) -> subprocess.CompletedProcess[str]:
        return self.bash('PATH="$PWD/bin:$PATH" exec bash "$0" "$@"', SCRIPT.as_posix(), *words)

    def fire(self, unit: str) -> subprocess.CompletedProcess[str]:
        """What systemd does when the timer `systemd-run` set for `unit` comes due."""
        return self.bash(f'PATH="$PWD/bin:$PATH"; eval "$(cat state/queued-{unit})"')

    def bash(self, script: str, *words: str) -> subprocess.CompletedProcess[str]:
        assert BASH is not None
        return subprocess.run(
            [BASH, "-c", script, *words],
            cwd=self.root,
            env={**os.environ, "QMX_RECOVER_CONF": posix(self.root / "recover.conf")},
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    def calls(self, *tools: str) -> list[str]:
        log = self.root / "calls.log"
        rows = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        ufw = posix(self.root / "bin" / "ufw")
        return [row.replace(ufw, "ufw") for row in rows if row.startswith(tools)]


def test_firewall_close_returns_before_ufw_switches_on_and_status_reports_the_switch(
    tmp_path: Path,
) -> None:
    server = Server(tmp_path, FIREWALL_STATUS=posix(tmp_path / "status" / "firewall-close"))
    closed = server.run("firewall", "close")
    sent_by_close = server.calls("ufw", "systemd-run")
    waiting = server.run("firewall", "status").stdout.splitlines()
    switched = server.fire("qmx-firewall-close")
    sent_by_switch = server.calls("ufw")
    after = server.run("firewall", "status").stdout.splitlines()

    assert closed.returncode == 0, closed.stderr
    assert closed.stdout.splitlines() == [
        "The firewall is being switched on: SSH (port 22), Tailscale and QMX's containers only.",
        "This SSH session may drop when it does. Log in again and check: "
        "sudo qmx-recover firewall status",
        "It turns itself off in five minutes unless you keep it: sudo qmx-recover firewall keep",
    ]
    assert sent_by_close[:5] == [
        "ufw allow 22/tcp",
        "ufw allow in on tailscale0",
        "ufw allow 41641/udp",
        "ufw allow in on docker0",
        "systemd-run --unit qmx-firewall-undo --on-active=300 --timer-property=AccuracySec=1s "
        "ufw --force disable",
    ]
    assert sent_by_close[5].startswith(
        "systemd-run --unit qmx-firewall-close --on-active=3 --timer-property=AccuracySec=1s "
    )
    assert sent_by_close[5].endswith(" firewall switch-on")
    assert len(sent_by_close) == 6
    assert waiting[0].endswith("FAIL")
    assert waiting[1].startswith("last close  still being switched on since ")
    assert waiting[1].endswith("; check again in a few seconds  FAIL")
    assert switched.returncode == 0, switched.stderr
    assert sent_by_switch[-4:] == [
        "ufw default deny incoming",
        "ufw default allow outgoing",
        "ufw --force enable",
        "ufw status verbose",
    ]
    assert after[0] == "firewall    on: only SSH, Tailscale and QMX's containers get in  PASS"
    assert after[1].startswith("last close  switched on at ")
    assert after[1].endswith(" UTC  PASS")


@pytest.mark.parametrize(
    ("blocker", "said"),
    [
        ("no-sshd", "Could not read which port SSH uses, so the firewall stays as it is."),
        ("ipv6-off", "The firewall is set to skip IPv6"),
    ],
)
def test_firewall_close_leaves_ufw_untouched_without_an_ssh_port_or_ipv6(
    tmp_path: Path, blocker: str, said: str
) -> None:
    server = Server(tmp_path)
    if blocker == "no-sshd":
        (tmp_path / "state" / "no-sshd").touch()
    else:
        (tmp_path / "defaults-ufw").write_text("IPV6=no\n", encoding="utf-8")
    done = server.run("firewall", "close")

    assert done.returncode == 1
    assert done.stderr.startswith(said)
    assert server.calls("ufw", "systemd-run") == []


def test_stop_repair_and_status_bring_the_host_back_and_no_key_is_ever_printed(
    tmp_path: Path,
) -> None:
    server = Server(tmp_path)
    stopped = server.run("stop", "host")
    before = server.run("status")
    repaired = server.run("repair")
    after = server.run("status")
    paired = server.run("pair")
    checked = server.run("vault")

    door = [line for line in after.stdout.splitlines() if line.startswith("door")]
    folder = posix(server.folder)
    assert stopped.stdout == "Stop qmx-host: done.\n"
    assert "door        does not answer on 127.0.0.1:8766  FAIL" in before.stdout
    assert (
        f"folder      {folder} is not in the folder tree; run: sudo qmx-recover repair  FAIL"
        in before.stdout
    )
    assert repaired.stdout.splitlines()[-1] == "QMX answers again."
    assert door == ["door        answers on 127.0.0.1:8766 and asks for its key  PASS"]
    assert f"folder      {folder} is in the folder tree  PASS" in after.stdout
    assert (server.folder / "keys" / "control-token").read_text(encoding="utf-8") == (
        PLANTED["control-token"] + "\n"
    )
    assert sorted(entry.name for entry in server.home.iterdir()) == ["vault", "vault-store.json"]
    assert paired.returncode == 0
    vault = server.home / "vault"
    assert (vault / "pairing-key.previous").read_text(encoding="utf-8") == (
        PLANTED["pairing-key"] + "\n"
    )
    shown = "".join(
        r.stdout + r.stderr for r in (stopped, before, repaired, after, paired, checked)
    )
    new_key = (vault / "pairing-key").read_text(encoding="utf-8").strip()
    for value in (*PLANTED.values(), VAULT_VALUE, new_key):
        assert value not in shown


def test_repair_refuses_to_change_owners_outside_the_home_and_library_it_names(
    tmp_path: Path,
) -> None:
    server = Server(tmp_path, LIBRARY="/srv/qmx")
    done = server.run("repair")

    assert done.returncode == 1
    assert "Not touching /srv/qmx: it is not QMX's folder or Library" in done.stdout
    assert not any("/srv/qmx" in call for call in server.calls("chown"))


def test_rollback_with_one_version_says_so_and_changes_nothing(tmp_path: Path) -> None:
    only = tmp_path / "versions" / ("a" * 40)
    only.mkdir(parents=True)
    server = Server(tmp_path, VERSIONS=posix(tmp_path / "versions"), CURRENT=posix(only))
    done = server.run("rollback")

    assert (done.returncode, done.stdout) == (
        1,
        "No earlier version is kept here. Nothing changed.\n",
    )
    assert server.calls("systemctl restart", "uv") == []


def test_reinstall_tries_offline_then_online_and_says_plainly_when_both_fail(
    tmp_path: Path,
) -> None:
    server = Server(tmp_path)
    done = server.run("reinstall")

    assert done.returncode == 1
    assert done.stdout.splitlines()[-2:] == [
        "Both tries failed, so the program files are as they were.",
        'Check the internet here, or run "qmx node setup" from your PC.',
    ]
    assert [call.endswith("--offline") for call in server.calls("uv")] == [True, False]
