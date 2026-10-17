"""E23: can an agent do real work with the built-in write tools off and a sandbox served as MCP?

A raw `claude_agent_sdk` client runs on the ship home's plan login (`CLAUDE_CONFIG_DIR` on
`D:/QMX-worktrees/qma-ship/home/claude`, never copied) with a throwaway HOME, on `haiku`, the
first plan-profile row of the `triage` role. Each of the ten tasks in `tasks/` runs twice,
interleaved task by task, mode B first as the baseline:

- Mode B: the built-in `Read`, `Glob`, `Grep`, `Bash`, `Write` and `Edit` in a scratch folder.
- Mode A: the same built-ins plus `NotebookEdit`, with `Bash`, `Write`, `Edit` and
  `NotebookEdit` removed through `disallowed_tools`, and an in-process SDK MCP server with
  `sandbox_bash`, `sandbox_write` and `sandbox_read`. They run in a `qmx-probe` Docker container
  when Docker answers and a local Python image is present, else as subprocesses in a scratch
  folder. The CLI's own cwd is an empty folder, so the work folder is reachable only through
  the sandbox.

Each pair runs under the lane lock. Writes `ep1-mode-a.log`, `ep1-mode-b.log` and
`e23-results.json` to the EP1 evidence folder.

    <ep1-venv>/Scripts/python.exe scripts/probes/engine/p_runner_outside.py
    <ep1-venv>/Scripts/python.exe scripts/probes/engine/p_runner_outside.py --ask-bash

`--ask-bash` runs one mode A task whose prompt asks for `Bash` by name, into `ep1-disallow.log`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final, Literal, Protocol

from raw_client import (
    EVIDENCE,
    HOMES,
    PLAN_CONFIG_DIR,
    TRIAGE_PLAN_MODEL,
    Log,
    home_env,
    lane_lock,
    scrub_process_env,
)
from tasks import Task, load

Mode = Literal["A", "B"]
RUNS: Final = HOMES / "ep1-runs"
BLOCKED_BUILTINS: Final = ("Bash", "Write", "Edit", "NotebookEdit")
MODE_A_TOOLS: Final = ["Read", "Glob", "Grep", *BLOCKED_BUILTINS]
MODE_B_TOOLS: Final = ["Read", "Glob", "Grep", "Bash", "Write", "Edit"]
SANDBOX_TOOLS: Final = ("sandbox_bash", "sandbox_write", "sandbox_read")
GIT_BASH: Final = Path("C:/Program Files/Git/bin/bash.exe")
DOCKER: Final = shutil.which("docker") or "docker"
DOCKER_IMAGE: Final = "python:3.12-slim"
COMMAND_TIMEOUT_S: Final = 60
OUTPUT_CAP: Final = 20_000
MAX_TURNS: Final = 30
TASK_TIMEOUT_S: Final = 420.0
SLOWDOWN_RISK: Final = 0.5

PREFACE: Final[dict[Mode, str]] = {
    "A": (
        "Your work folder is inside a sandbox. Reach it only through the sandbox tools: "
        "sandbox_bash runs a bash command in the work folder, sandbox_write writes a whole file, "
        "sandbox_read reads a file. Paths are relative to the work folder."
    ),
    "B": "Your work folder is the current directory.",
}


class Sandbox(Protocol):
    backend: str

    def bash(self, command: str) -> str: ...
    def write(self, path: str, content: str) -> str: ...
    def read(self, path: str) -> str: ...
    def close(self) -> None: ...


def capped(code: int, out: str) -> str:
    return f"exit {code}\n{out[-OUTPUT_CAP:]}"


class FolderSandbox:
    """The fallback when Docker is not running: Git Bash subprocesses in the work folder, with
    an env cut to PATH and the Windows basics, so no plan path or key reaches a command."""

    backend = "scratch-folder subprocess"

    def __init__(self, work: Path) -> None:
        self.work = work.resolve()
        keep = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TMP", "TEMP")
        self.env = {name: os.environ[name] for name in keep if name in os.environ}

    def inside(self, path: str) -> Path:
        target = (self.work / path).resolve()
        if not target.is_relative_to(self.work):
            raise ValueError(f"{path} is outside the work folder")
        return target

    def bash(self, command: str) -> str:
        done = subprocess.run(
            [str(GIT_BASH), "-c", command],
            cwd=self.work,
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_S,
            check=False,
        )
        return capped(done.returncode, done.stdout + done.stderr)

    def write(self, path: str, content: str) -> str:
        target = self.inside(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        return f"wrote {len(content)} chars to {path}"

    def read(self, path: str) -> str:
        return self.inside(path).read_text(encoding="utf-8")[:OUTPUT_CAP]

    def close(self) -> None:
        return None


class DockerSandbox:
    """A hardened `qmx-probe` container with the work folder at `/work`, no network and no
    host env. Every call is a `docker exec`, so a write lands through the container."""

    backend = "docker container"

    def __init__(self, work: Path, name: str) -> None:
        self.name = name
        subprocess.run([DOCKER, "rm", "-f", name], capture_output=True, check=False)
        subprocess.run(
            [DOCKER, "run", "-d", "--rm", "--name", name, "--pull", "never", "--network", "none",
             "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",  # noqa: S108
             "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "512m",
             "-v", f"{work.resolve()}:/work", "-w", "/work", DOCKER_IMAGE, "sleep", "3600"],
            capture_output=True, check=True,
        )  # fmt: skip

    def exec(self, command: str, *args: str, stdin: str | None = None) -> tuple[int, str]:
        done = subprocess.run(
            [DOCKER, "exec", "-i", self.name, "bash", "-c", command, "sandbox", *args],
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_S,
            check=False,
        )
        return done.returncode, done.stdout + done.stderr

    def bash(self, command: str) -> str:
        return capped(*self.exec(command))

    def write(self, path: str, content: str) -> str:
        code, out = self.exec('mkdir -p "$(dirname "$1")" && cat > "$1"', path, stdin=content)
        return f"wrote {len(content)} chars to {path}" if code == 0 else capped(code, out)

    def read(self, path: str) -> str:
        code, out = self.exec('cat "$1"', path)
        return out[:OUTPUT_CAP] if code == 0 else capped(code, out)

    def close(self) -> None:
        subprocess.run([DOCKER, "rm", "-f", self.name], capture_output=True, check=False)


def docker_ready() -> bool:
    try:
        info = subprocess.run([DOCKER, "info"], capture_output=True, timeout=20, check=False)
        image = subprocess.run(
            [DOCKER, "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return info.returncode == 0 and image.returncode == 0


def open_sandbox(work: Path, slug: str, use_docker: bool) -> Sandbox:
    return DockerSandbox(work, f"qmx-probe-{slug}") if use_docker else FolderSandbox(work)


def sandbox_server(sandbox: Sandbox) -> Any:
    from claude_agent_sdk import create_sdk_mcp_server, tool  # noqa: PLC0415

    def reply(call: Any) -> Any:
        async def handler(args: dict[str, Any]) -> dict[str, Any]:
            try:
                out = await asyncio.to_thread(call, args)
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                return {"content": [{"type": "text", "text": f"error: {error}"}], "is_error": True}
            return {"content": [{"type": "text", "text": out}]}

        return handler

    tools = [
        tool("sandbox_bash", "Run a bash command in the work folder; returns exit code and output.",
             {"command": str})(reply(lambda a: sandbox.bash(a["command"]))),
        tool("sandbox_write", "Write a whole file in the work folder, replacing it.",
             {"path": str, "content": str})(reply(lambda a: sandbox.write(a["path"], a["content"]))),  # noqa: E501
        tool("sandbox_read", "Read a file in the work folder.",
             {"path": str})(reply(lambda a: sandbox.read(a["path"]))),
    ]  # fmt: skip
    return create_sdk_mcp_server("sandbox", tools=tools)


@dataclass
class Outcome:
    task: str
    mode: Mode
    passed: bool
    check: str
    turns: int | None
    wall_s: float
    backend: str
    tool_calls: list[str] = field(default_factory=list)
    init_tools: list[str] = field(default_factory=list)
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)
    result: str = ""

    @property
    def blocked_calls(self) -> list[str]:
        return [name for name in self.tool_calls if name in BLOCKED_BUILTINS]

    @property
    def disallow_honoured(self) -> bool:
        return not set(BLOCKED_BUILTINS) & set(self.init_tools)

    @property
    def server_loaded(self) -> bool:
        return any(
            s.get("name") == "sandbox" and s.get("status") == "connected" for s in self.mcp_servers
        )


async def run_task(
    task: Task, mode: Mode, env: dict[str, str], use_docker: bool, prompt_extra: str = ""
) -> Outcome:
    from claude_agent_sdk import (  # noqa: PLC0415
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        ResultMessage,
        SystemMessage,
        ToolUseBlock,
    )

    base = RUNS / mode / task.slug
    work, runner = base / "work", base / "runner"
    task.seed(work)
    shutil.rmtree(runner, ignore_errors=True)
    runner.mkdir(parents=True)
    common: dict[str, Any] = {
        "env": env,
        "setting_sources": [],
        "settings": json.dumps({"forceLoginMethod": "claudeai"}),
        "strict_mcp_config": True,
        "model": TRIAGE_PLAN_MODEL,
        "permission_mode": "bypassPermissions",
        "max_turns": MAX_TURNS,
    }
    sandbox: Sandbox | None = None
    if mode == "A":
        sandbox = open_sandbox(work, task.slug, use_docker)
        options = ClaudeAgentOptions(
            **common,
            cwd=str(runner),
            tools=MODE_A_TOOLS,
            disallowed_tools=list(BLOCKED_BUILTINS),
            mcp_servers={"sandbox": sandbox_server(sandbox)},
            allowed_tools=[f"mcp__sandbox__{name}" for name in SANDBOX_TOOLS],
        )
    else:
        options = ClaudeAgentOptions(**common, cwd=str(work), tools=MODE_B_TOOLS)
    outcome = Outcome(
        task.slug, mode, False, "", None, 0.0, sandbox.backend if sandbox else "built-in tools"
    )
    prompt = f"{PREFACE[mode]}\n\n{prompt_extra}{task.prompt}\n\nEnd with a one-line summary."
    started = time.monotonic()
    try:
        async with asyncio.timeout(TASK_TIMEOUT_S), ClaudeSDKClient(options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    outcome.init_tools = list(message.data.get("tools", []))
                    outcome.mcp_servers = list(message.data.get("mcp_servers", []))
                elif isinstance(message, AssistantMessage):
                    outcome.tool_calls += [
                        b.name for b in message.content if isinstance(b, ToolUseBlock)
                    ]
                elif isinstance(message, ResultMessage):
                    outcome.turns = message.num_turns
                    outcome.result = f"{message.subtype} is_error={message.is_error}"
    except TimeoutError:
        outcome.result = f"timeout after {TASK_TIMEOUT_S:.0f} s"
    finally:
        outcome.wall_s = round(time.monotonic() - started, 1)
        if sandbox:
            sandbox.close()
    outcome.passed, outcome.check = task.check(work)
    return outcome


def describe(o: Outcome) -> str:
    line = (
        f"RESULT mode={o.mode} task={o.task} pass={o.passed} turns={o.turns} wall={o.wall_s}s "
        f"backend={o.backend!r} result={o.result!r} tools={o.tool_calls}"
    )
    if o.mode == "A":
        servers = [(s.get("name"), s.get("status")) for s in o.mcp_servers]
        offered = [name for name in o.init_tools if not name.startswith("mcp__")]
        line += f" offered_builtins={offered} disallow_honoured={o.disallow_honoured}"
        line += f" sandbox_server={servers}"
    return line + (f" check={o.check!r}" if o.check else "")


def plan_folder_snapshot() -> dict[str, tuple[int, float]]:
    """Names, sizes and mtimes under the plan folder; never contents."""
    return {
        str(p.relative_to(PLAN_CONFIG_DIR)): (p.stat().st_size, p.stat().st_mtime)
        for p in PLAN_CONFIG_DIR.rglob("*")
        if p.is_file()
    }


def summarise(outcomes: list[Outcome], logs: dict[Mode, Log]) -> dict[str, Any]:
    by_mode = {m: [o for o in outcomes if o.mode == m] for m in ("A", "B")}
    rates = {m: f"{sum(o.passed for o in rows)}/{len(rows)}" for m, rows in by_mode.items()}
    walls = {m: [o.wall_s for o in rows] for m, rows in by_mode.items()}
    turns = {m: sum(o.turns or 0 for o in rows) for m, rows in by_mode.items()}
    slow = []
    for a, b in zip(by_mode["A"], by_mode["B"], strict=True):
        ratio = a.wall_s / b.wall_s - 1 if b.wall_s else 0.0
        slow.append({"task": a.task, "b_s": b.wall_s, "a_s": a.wall_s, "slowdown": round(ratio, 2)})
    median_slowdown = statistics.median(s["slowdown"] for s in slow) if slow else 0.0
    summary = {
        "pass_rate": rates,
        "median_wall_s": {m: statistics.median(w) if w else None for m, w in walls.items()},
        "total_wall_s": {m: round(sum(w), 1) for m, w in walls.items()},
        "plan_turns": turns,
        "per_task_wall": slow,
        "median_slowdown": round(median_slowdown, 2),
        "slowdown_risk": median_slowdown > SLOWDOWN_RISK,
    }
    for log in logs.values():
        for row in slow:
            log(
                f"WALL task={row['task']} B={row['b_s']}s A={row['a_s']}s"
                f" slowdown={row['slowdown']:+.0%}"
            )
        log(f"SUMMARY {json.dumps(summary)}")
    return summary


def main_pairs(env: dict[str, str], use_docker: bool, only: list[str] | None) -> int:
    logs: dict[Mode, Log] = {"A": Log("ep1-mode-a"), "B": Log("ep1-mode-b")}
    backend = "docker container" if use_docker else "scratch-folder subprocess"
    for log in logs.values():
        log(
            f"model {TRIAGE_PLAN_MODEL}; plan folder {PLAN_CONFIG_DIR};"
            f" mode A sandbox backend: {backend}"
        )
    before = plan_folder_snapshot()
    outcomes: list[Outcome] = []
    for task in load():
        if only and task.slug not in only:
            continue
        with lane_lock(logs["B"]):
            for mode in ("B", "A"):
                outcome = asyncio.run(run_task(task, mode, env, use_docker))
                logs[mode](describe(outcome))
                outcomes.append(outcome)
    after = plan_folder_snapshot()
    changed = sorted(k for k in after if before.get(k) != after[k])
    removed = sorted(set(before) - set(after))
    logs["A"](
        f"plan folder files changed or added: {len(changed)}; removed: {removed};"
        f" sample: {changed[:12]}"
    )
    summary = summarise(outcomes, logs)
    a_rows = [o for o in outcomes if o.mode == "A"]
    b_rows = [o for o in outcomes if o.mode == "B"]
    logs["A"].check(
        "every mode A task recorded a result", all(o.result for o in a_rows), len(a_rows)
    )
    logs["A"].check(
        "no built-in Bash, Write, Edit or NotebookEdit call in any mode A transcript",
        not any(o.blocked_calls for o in a_rows),
        {o.task: o.blocked_calls for o in a_rows if o.blocked_calls},
    )
    logs["A"](
        f"FINDING disallow list honoured in every mode A init: "
        f"{all(o.disallow_honoured for o in a_rows)}"
    )
    logs["A"](
        f"FINDING sandbox server connected in every mode A client: "
        f"{all(o.server_loaded for o in a_rows)}"
    )
    logs["B"].check(
        "every mode B task recorded a result", all(o.result for o in b_rows), len(b_rows)
    )
    (EVIDENCE / "e23-results.json").write_text(
        json.dumps({"summary": summary, "outcomes": [asdict(o) for o in outcomes]}, indent=2),
        encoding="utf-8",
    )
    return logs["A"].verdict() | logs["B"].verdict()


def main_ask_bash(env: dict[str, str], use_docker: bool) -> int:
    log = Log("ep1-disallow")
    task = load()[0]
    ask = "First run `python --version` with the tool named Bash, by name, not sandbox_bash. "
    with lane_lock(log):
        outcome = asyncio.run(run_task(task, "A", env, use_docker, prompt_extra=ask))
    log(describe(outcome))
    log.check(
        "Bash is absent from the tools the CLI offered",
        outcome.disallow_honoured,
        outcome.init_tools,
    )
    log.check("no built-in Bash call ran", not outcome.blocked_calls, outcome.blocked_calls)
    log.check(
        "the agent fell back to sandbox_bash",
        "mcp__sandbox__sandbox_bash" in outcome.tool_calls,
        outcome.tool_calls,
    )
    return log.verdict()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ask-bash", action="store_true")
    parser.add_argument("--only", nargs="*", help="task slugs to run, for a smoke run")
    args = parser.parse_args()
    scrub_process_env(os.environ)
    if not (PLAN_CONFIG_DIR / ".credentials.json").exists():
        raise SystemExit("BLOCKED: the ship home has no plan login")
    env = home_env(HOMES / "ep1-home", PLAN_CONFIG_DIR)
    use_docker = docker_ready()
    if args.ask_bash:
        return main_ask_bash(env, use_docker)
    return main_pairs(env, use_docker, args.only)


if __name__ == "__main__":
    sys.exit(main())
