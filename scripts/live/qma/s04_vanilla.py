"""The vanilla side of S4 and of the HP6 perf metric: the bundled CLI as `claude -p`, in the
plan home of `--home`, from a throwaway HOME, in the same workspace a QMA chat uses. The QMX
home's `[claude]` deny rules are passed as `--disallowedTools`, so both sides run under the
operator's same rules.

    s04_vanilla.py check2 --workspace D:/Temp/ws     operator check 2; PASS when it reads the
                                                     README and the turn succeeds
    s04_vanilla.py first-delta                       one `say ok` run; prints the seconds from
                                                     process start to the first text delta
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import tomllib
from common import FAKE_HOME, Log, boot, chat_args, require_login, use_fake_home

CHECK2 = "What is in this folder? Summarise the README."


def deny_rules(home: Path) -> list[str]:
    path = home / "settings.toml"
    if not path.exists():
        return []
    claude = tomllib.loads(path.read_text(encoding="utf-8")).get("claude", {})
    return list(claude.get("permissions", {}).get("deny", []))


def vanilla(
    home: Path, model: str, workspace: Path, prompt: str, *, deny: bool = True
) -> tuple[float | None, list[dict[str, Any]]]:
    """One `claude -p` run; `deny=False` leaves the [claude] deny rules out."""
    from qma.launcher import bundled_cli  # noqa: PLC0415

    command = [str(bundled_cli()), "-p", prompt, "--model", model, "--output-format", "stream-json"]
    command += ["--verbose", "--include-partial-messages"]
    denied = deny_rules(home) if deny else []
    if denied:
        command += ["--disallowedTools", ",".join(denied)]
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(home / "claude")}
    workspace.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    first: float | None = None
    lines: list[dict[str, Any]] = []
    with subprocess.Popen(
        command,
        cwd=workspace,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ) as process:
        for raw in process.stdout or ():
            message = json.loads(raw)
            lines.append(message)
            delta = message.get("event", {}).get("delta", {})
            if first is None and delta.get("type") == "text_delta":
                first = time.monotonic() - started
    return first, lines


def main() -> int:
    parser = chat_args(__doc__)
    parser.add_argument("mode", choices=["check2", "first-delta"])
    args = parser.parse_args()
    log = Log(f"hp6-s04-{args.mode}")
    boot()
    use_fake_home()
    require_login(log)
    log(f"HOME {FAKE_HOME}; deny rules from {args.home}: {deny_rules(args.home)}")
    if args.mode == "first-delta":
        first, lines = vanilla(args.home, args.model, args.workspace, "say ok")
        result = next((m for m in lines if m.get("type") == "result"), {})
        log(f"vanilla first text delta after {first:.2f} s" if first else "no text delta")
        log.check("vanilla turn succeeded", result.get("is_error") is False, result.get("result"))
        return log.verdict()
    _, lines = vanilla(args.home, args.model, args.workspace, CHECK2)
    tools = [
        (part["name"], json.dumps(part["input"])[:200])
        for message in lines
        if message.get("type") == "assistant"
        for part in message["message"]["content"]
        if part.get("type") == "tool_use"
    ]
    for name, arguments in tools:
        log(f"  [tool] {name} {arguments}")
    result = next((m for m in lines if m.get("type") == "result"), {})
    log(f"  [result] {str(result.get('result'))[:400]}")
    read = any(name == "Read" and "README" in arguments for name, arguments in tools)
    log.check("vanilla read the README", read, [name for name, _ in tools])
    log.check("vanilla turn succeeded", result.get("is_error") is False, result.get("subtype"))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
