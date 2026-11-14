"""The Windows scheduled task that restarts dead conveyors at logon and every 15 minutes (his H1 yes).

`plan(plans, settings)` returns what would be registered: the task XML (a logon trigger and a 15-minute
repeat, least privilege, run as him) and the `schtasks` command lines, with the exact undo. Nothing is
registered unless `apply=True` (`ship chain --install-task --install`); without it the commands are only
printed. `remove` deletes the task the same way. The task runs
`<pythonw> <kit> chain --resume-all --plans <plans>`, which starts a detached conveyor for every program
whose `phase.json` says running and whose `chain.lock` is dead.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from ship.settings import Settings

TASK = "factory-resume"


def python_exe() -> str:
    """pythonw beside the running python when there is one, so the logon run opens no window."""
    here = Path(sys.executable)
    quiet = here.with_name("pythonw.exe")
    return str(quiet if quiet.exists() else here)


def action(plans: Path) -> tuple[str, str]:
    from ship.launch import KIT

    return python_exe(), f'"{KIT}" chain --resume-all --plans "{Path(plans)}"'


def task_xml(plans: Path, user: str | None = None) -> str:
    exe, args = action(plans)
    user = user or os.environ.get("USERNAME") or ""
    principal = f"<UserId>{escape(user)}</UserId>" if user else ""
    logon_user = f"<UserId>{escape(user)}</UserId>" if user else ""
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Restart the factory's conveyors that a restart or power cut left dead.</Description></RegistrationInfo>
  <Triggers>
    <LogonTrigger><Enabled>true</Enabled>{logon_user}</LogonTrigger>
    <TimeTrigger>
      <Enabled>true</Enabled>
      <StartBoundary>2026-01-01T00:00:00</StartBoundary>
      <Repetition><Interval>PT15M</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
    </TimeTrigger>
  </Triggers>
  <Principals><Principal id="Author">{principal}<LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author"><Exec><Command>{escape(exe)}</Command><Arguments>{escape(args)}</Arguments></Exec></Actions>
</Task>
"""


def install_commands(xml_path: Path) -> list[list[str]]:
    return [["schtasks", "/Create", "/F", "/TN", TASK, "/XML", str(xml_path)]]


def remove_commands() -> list[list[str]]:
    return [["schtasks", "/Delete", "/F", "/TN", TASK]]


def show(argv: list[str]) -> str:
    return " ".join(f'"{a}"' if " " in a else a for a in argv)


def install(plans: Path, settings: Settings, apply: bool = False) -> tuple[int, list[str]]:
    from ship.locks import run_dir

    xml_path = run_dir(settings) / f"{TASK}.xml"
    xml = task_xml(plans)
    exe, args = action(plans)
    lines = [f"TASK {TASK}: at logon and every 15 minutes, least privilege, runs:",
             f"    {exe} {args}"]
    commands = install_commands(xml_path)
    lines += [f"{'RUN' if apply else 'WOULD RUN'} {show(c)}" for c in commands]
    lines.append(f"UNDO {show(remove_commands()[0])}")
    if not apply:
        lines.append(f"DRY nothing registered; the XML is printed below. Run `chain --install-task --install` to register.")
        return 0, lines + xml.splitlines()
    if sys.platform != "win32":
        return 1, lines + ["REFUSED scheduled tasks are a Windows feature"]
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml, "utf-16")
    for argv in commands:
        done = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        lines.append(f"EXIT {done.returncode} {done.stdout.strip()} {done.stderr.strip()}".rstrip())
        if done.returncode != 0:
            return 1, lines
    return 0, lines


def remove(settings: Settings, apply: bool = False) -> tuple[int, list[str]]:
    commands = remove_commands()
    lines = [f"{'RUN' if apply else 'WOULD RUN'} {show(c)}" for c in commands]
    if not apply:
        return 0, lines + ["DRY nothing removed; add --install to remove it"]
    for argv in commands:
        done = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        lines.append(f"EXIT {done.returncode} {done.stdout.strip()} {done.stderr.strip()}".rstrip())
        if done.returncode != 0:
            return 1, lines
    return 0, lines + [f"UNDO register it again with `chain --install-task --install`"]
