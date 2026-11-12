"""preflight: once per run, before any dispatch. Runs every check; on any failure it arms nothing.
Then it applies the settings, each recorded in ARMED.md with its exact undo, and snapshots the main
checkout's `git status` for `main-check`.

Checks: git and gh present and signed in, the remote and build branch reachable with prompts off,
Windows LongPathsEnabled, `.gitattributes` with eol rules at the build tip, no pending reboot,
Windows updates paused, the test wrapper's fake keyring and credential guard working, and (only with
--protection-push-test) a push to each protected branch that must be rejected.
Settings: core.longpaths=true in the repo, the wrapper's runs folder, and the keep-awake helper.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

from ship import state as st
from ship.armed import Change, arm
from ship.gitx import GitError, git, remote_sha, run
from ship.layout import Program
from ship.settings import Settings
from ship.wrapper import run_timed

Check = tuple[bool, str]


def _reg(root: str, path: str, name: str):
    import winreg

    hive = {"HKLM": winreg.HKEY_LOCAL_MACHINE}[root]
    try:
        with winreg.OpenKey(hive, path) as key:
            return winreg.QueryValueEx(key, name)[0] if name else True
    except OSError:
        return None


def check_long_paths() -> Check:
    if sys.platform != "win32":
        return True, "not Windows"
    value = _reg("HKLM", r"SYSTEM\CurrentControlSet\Control\FileSystem", "LongPathsEnabled")
    if value == 1:
        return True, "LongPathsEnabled=1"
    return False, ("LongPathsEnabled is not 1; as admin run: New-ItemProperty -Path "
                   "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem -Name LongPathsEnabled -Value 1 "
                   "-PropertyType DWORD -Force")


def check_no_pending_reboot() -> Check:
    if sys.platform != "win32":
        return (not Path("/var/run/reboot-required").exists(), "/var/run/reboot-required")
    keys = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"]
    pending = [k for k in keys if _reg("HKLM", k, "")]
    return (not pending, "a reboot is pending: restart before the run" if pending else "no reboot pending")


def check_updates_paused(hours: float) -> Check:
    if sys.platform != "win32":
        return True, "not Windows; unattended upgrades are not checked"
    value = _reg("HKLM", r"SOFTWARE\Microsoft\WindowsUpdate\UX\Settings", "PauseUpdatesExpiryTime")
    if not value:
        return False, "Windows updates are not paused: Settings > Windows Update > Pause updates"
    until = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if until.tzinfo is None:
        until = until.replace(tzinfo=dt.timezone.utc)
    left = (until - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600
    return (left >= hours, f"updates paused until {until.isoformat()} ({left:.0f} hours)")


def check_gitattributes(repo: Path, remote: str, branch: str, settings: Settings) -> Check:
    try:
        text = git(repo, "show", f"{remote}/{branch}:.gitattributes", timeout=settings.git_timeout_s)
    except GitError:
        return False, f".gitattributes is missing at {remote}/{branch}"
    rules = [ln for ln in text.splitlines() if "eol=" in ln or "text=auto" in ln]
    return (bool(rules), f"{len(rules)} line-ending rules" if rules else ".gitattributes has no eol rules")


def check_fake_keyring(program: Program, settings: Settings) -> Check:
    code = ("import os,sys\n"
            "assert os.environ['PYTHON_KEYRING_BACKEND']=='keyring.backends.fail.Keyring'\n"
            "assert os.environ['GIT_TERMINAL_PROMPT']=='0'\n"
            "if sys.platform=='win32':\n"
            "    import ctypes\n"
            "    try:\n"
            "        ctypes.windll.advapi32.CredReadW\n"
            "        raise SystemExit('CredReadW was reachable')\n"
            "    except RuntimeError:\n"
            "        pass\n"
            "print('guarded')\n")
    log = program.dir / "preflight" / "fake-keyring.log"
    done = run_timed([sys.executable, "-c", code], program.dir, log, settings.fact_timeout_s, settings,
                     program.dir / "preflight" / "runs")
    return (done.rc == 0, f"wrapper env guarded, log {log}" if done.rc == 0 else f"guard failed, see {log}")


def check_tools(repo: Path, settings: Settings) -> Check:
    try:
        run([*settings.gh, "auth", "status"], repo, settings.net_timeout_s)
    except GitError as exc:
        return False, f"gh is not signed in or missing: {exc}"
    return True, "git and gh ready"


def protection_push_test(repo: Path, remote: str, settings: Settings) -> list[Check]:
    """Push a probe commit to each protected branch; the push must be rejected. If one is accepted,
    the branch is put back at once with a lease on the probe, and the check fails."""
    results = []
    t = settings.git_timeout_s
    for branch in settings.protected_branches:
        old = remote_sha(repo, remote, branch, t)
        if not old:
            results.append((True, f"{branch}: not on {remote}, nothing to protect"))
            continue
        git(repo, "fetch", "-q", remote, branch, timeout=t)
        tree = git(repo, "rev-parse", f"{old}^{{tree}}", timeout=t).strip()
        probe = git(repo, "commit-tree", tree, "-p", old, "-m", "ship preflight probe: this push must be rejected",
                    timeout=t).strip()
        done = run(["git", "push", "--porcelain", remote, f"{probe}:refs/heads/{branch}"], repo, t, check=False)
        if done.returncode != 0:
            results.append((True, f"{branch}: push rejected as required"))
            continue
        restore = run(["git", "push", f"--force-with-lease=refs/heads/{branch}:{probe}", remote,
                       f"{old}:refs/heads/{branch}"], repo, t, check=False)
        put_back = "put back" if restore.returncode == 0 else f"NOT put back ({restore.stderr.strip()})"
        results.append((False, f"{branch}: push was ACCEPTED, protection does not hold; branch {put_back} at {old}"))
    return results


def checks(program: Program, state: st.State, settings: Settings, protection: bool) -> list[tuple[str, Check]]:
    repo = Path(state.repo)
    found: list[tuple[str, Check]] = []
    try:
        tip = remote_sha(repo, state.remote, state.build_branch, settings.git_timeout_s)
        git(repo, "fetch", "-q", state.remote, state.build_branch, timeout=settings.git_timeout_s)
        found.append(("remote", (bool(tip), f"{state.build_branch} at {tip}" if tip else "build branch missing")))
    except GitError as exc:
        found.append(("remote", (False, str(exc))))
    found.append(("tools", check_tools(repo, settings)))
    found.append(("long-paths", check_long_paths()))
    found.append(("gitattributes", check_gitattributes(repo, state.remote, state.build_branch, settings)))
    found.append(("pending-reboot", check_no_pending_reboot()))
    found.append(("updates-paused", check_updates_paused(settings.updates_paused_min_h)))
    found.append(("fake-keyring", check_fake_keyring(program, settings)))
    if protection:
        found += [("protected-push", r) for r in protection_push_test(repo, state.remote, settings)]
    return found


def snapshot_main(repo: Path, settings: Settings) -> str:
    head = git(repo, "rev-parse", "HEAD", timeout=settings.git_timeout_s).strip()
    status = git(repo, "status", "--porcelain=v1", "--untracked-files=all", timeout=settings.git_timeout_s)
    return f"HEAD {head}\n{status}"


def main_check(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    """Compare the main checkout with its arm-time snapshot. Any change stops the run."""
    state = st.load(program)
    now = snapshot_main(Path(state.repo), settings)
    then = program.main_snapshot.read_text("utf-8")
    if now == then:
        return True, ["MAIN unchanged"]
    old, new = set(then.splitlines()), set(now.splitlines())
    return False, (["MAIN CHANGED: stop the run"] + [f"- {ln}" for ln in sorted(old - new)]
                   + [f"+ {ln}" for ln in sorted(new - old)])


def preflight(program: Program, settings: Settings, protection_push_test: bool = False,
              wanted: list[Change] | None = None) -> tuple[bool, list[str]]:
    state = st.load(program)
    results = checks(program, state, settings, protection_push_test)
    lines = [f"{'PASS' if ok else 'FAIL'} {name}: {detail}" for name, (ok, detail) in results]
    if not protection_push_test:
        lines.append("NOTRUN protected-push: off until the operator turns it on (--protection-push-test)")
    (program.dir / "preflight").mkdir(exist_ok=True)
    (program.dir / "preflight" / "checks.txt").write_text("\n".join(lines) + "\n", "utf-8", newline="\n")
    if any(not ok for _, (ok, _) in results):
        return False, lines + ["REFUSED: a check failed, nothing was armed"]
    if wanted is None:
        wanted = [Change("git-config", state.repo, "core.longpaths", "true"),
                  Change("created-dir", str(program.runs)),
                  Change("keep-awake", str(program.dir / "KEEP-AWAKE"))]
    lines += arm(program, wanted, settings)
    if not program.main_snapshot.exists():
        program.main_snapshot.write_text(snapshot_main(Path(state.repo), settings), "utf-8", newline="\n")
        lines.append(f"SNAPSHOT main checkout status in {program.main_snapshot}")
    lines += ["MANUAL set the lid action to 'do nothing' on mains and battery if the lid may close tonight",
              "MANUAL export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never GIT_EDITOR=true in the coordinator's shell"]
    return True, lines
